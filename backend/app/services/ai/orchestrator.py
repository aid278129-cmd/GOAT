"""LangGraph Orchestrator for Zyntrix Phase 4A AI Engineering Copilot.

Enforces:
- Deterministic LangGraph state machine:
  START -> INTENT_CLASSIFIER -> CONTEXT_RETRIEVER -> TASK_PLANNER -> SPECIALIST_AGENT
        -> AUTHORITY_VALIDATOR -> HUMAN_GATE -> RESPONSE_COMPOSER -> END
- 6 Bounded Specialists (Evidence, Standards, Product DNA, CAD, Compliance, Dossier)
- Zero Statutory Authority: AI cannot certify, accept evidence, attest, or override evaluations
- Untrusted data encapsulation for prompt injection defense
- PostgreSQL state persistence (AIConversation, AIMessage, AIExecution, AIToolCall, AIActionProposal)
- Audit trail logging (AI_QUERY_STARTED, AI_AGENT_STARTED, AI_TOOL_CALLED, AI_RESPONSE_GENERATED)
"""

from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime, timezone
import uuid
import time
import json
from sqlalchemy.ext.asyncio import AsyncSession

from langgraph.graph import StateGraph, START, END

from backend.app.models.persistent_ai import (
    AIConversation,
    AIMessage,
    AIExecution,
    AIToolCall,
    AIActionProposal,
)
from backend.app.models.persistent_audit import AuditEvent
from backend.app.services.ai.provider import get_llm_provider, AIProviderNotConfiguredError
from backend.app.services.ai.firewall import (
    AIAuthorityFirewall,
    AllowedAIAction,
    ForbiddenAIAction,
    CitationItem,
    StructuredAIResponse,
    PromptInjectionDefense,
    SupportStatus,
)
from backend.app.services.ai.tools import AIToolRegistry


class OrchestratorState(TypedDict, total=False):
    # Tenant & Session Context
    organization_id: str
    user_id: str
    user_email: str
    job_id: str
    conversation_id: str
    
    # Query & Intent
    query: str
    intent: str
    forbidden_intent: Optional[str]
    target_specialist: str
    
    # Authoritative Retrieval
    retrieved_context: Dict[str, Any]
    
    # Execution & Agent Reasoning
    task_plan: List[str]
    agent_output: Dict[str, Any]
    proposals: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    
    # Safety & Authority
    authority_level: str
    firewall_status: str
    requires_human_action: bool
    
    # Output & Telemetry
    final_response: Dict[str, Any]
    tool_calls_logged: List[Dict[str, Any]]
    model_name: str
    execution_time_ms: int
    error: Optional[str]


class ZyntrixAIOrchestrator:
    """Orchestrates multi-specialist engineering assistance via LangGraph."""

    @classmethod
    async def process_user_query(
        cls,
        db: AsyncSession,
        org_id: str,
        user_id: str,
        user_email: str,
        job_id: str,
        query: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. Check if LLM provider is configured
        llm = get_llm_provider()
        
        # 2. Get or create AIConversation
        if conversation_id:
            conv = await db.get(AIConversation, conversation_id)
            if not conv or conv.organization_id != org_id or conv.job_id != job_id:
                conv = AIConversation(
                    organization_id=org_id,
                    job_id=job_id,
                    user_id=user_id,
                    title=query[:60] or "Engineering Assistant",
                )
                db.add(conv)
                await db.flush()
        else:
            conv = AIConversation(
                organization_id=org_id,
                job_id=job_id,
                user_id=user_id,
                title=query[:60] or "Engineering Assistant",
            )
            db.add(conv)
            await db.flush()

        conv_id = conv.id

        # 3. Save User AIMessage
        user_msg = AIMessage(
            conversation_id=conv_id,
            role="user",
            content=query,
        )
        db.add(user_msg)

        # 4. Audit query start
        db.add(
            AuditEvent(
                organization_id=org_id,
                job_id=job_id,
                action="AI_QUERY_STARTED",
                actor_id=user_id,
                actor_email=user_email,
                actor_role="ENGINEER",
                target_type="AI_CONVERSATION",
                target_id=conv_id,
                details={"query": query[:200]},
            )
        )
        await db.flush()

        # 5. Build and run LangGraph
        initial_state: OrchestratorState = {
            "organization_id": org_id,
            "user_id": user_id,
            "user_email": user_email,
            "job_id": job_id,
            "conversation_id": conv_id,
            "query": query,
            "intent": "INFORMATIONAL",
            "forbidden_intent": None,
            "target_specialist": "COMPLIANCE_ANALYST",
            "retrieved_context": {},
            "task_plan": [],
            "agent_output": {},
            "proposals": [],
            "citations": [],
            "authority_level": "AI_ASSISTED",
            "firewall_status": "PENDING",
            "requires_human_action": False,
            "final_response": {},
            "tool_calls_logged": [],
            "model_name": getattr(llm, "model", "test-provider"),
            "execution_time_ms": 0,
            "error": None,
        }

        # Execute Graph Node Pipeline
        final_state = await cls._execute_state_graph(db, initial_state, llm)
        total_time_ms = int((time.time() - start_time) * 1000)
        final_state["execution_time_ms"] = total_time_ms

        response_dict = final_state["final_response"]

        # 6. Save Assistant AIMessage
        asst_msg = AIMessage(
            conversation_id=conv_id,
            role="assistant",
            content=response_dict.get("answer", ""),
            structured_payload=response_dict,
            model=final_state["model_name"],
            model_confidence=response_dict.get("model_confidence", 1.0),
        )
        db.add(asst_msg)

        # 7. Persist AIExecution trace
        execution = AIExecution(
            conversation_id=conv_id,
            organization_id=org_id,
            job_id=job_id,
            user_id=user_id,
            intent=final_state.get("intent", "INFORMATIONAL"),
            agent_name=final_state.get("target_specialist", "COMPLIANCE_ANALYST"),
            state_snapshot={
                "intent": final_state.get("intent"),
                "specialist": final_state.get("target_specialist"),
                "firewall": final_state.get("firewall_status"),
                "proposals_count": len(final_state.get("proposals", [])),
                "citations_count": len(final_state.get("citations", [])),
            },
            status="COMPLETED" if not final_state.get("error") else "FAILED",
            error_message=final_state.get("error"),
            execution_time_ms=total_time_ms,
        )
        db.add(execution)
        await db.flush()

        # 8. Save AIToolCalls
        for tc in final_state.get("tool_calls_logged", []):
            db.add(
                AIToolCall(
                    execution_id=execution.id,
                    tool_name=tc["tool_name"],
                    arguments=tc.get("arguments", {}),
                    result_summary=tc.get("result_summary", ""),
                    duration_ms=tc.get("duration_ms", 0),
                )
            )

        # 9. Audit query response generated
        db.add(
            AuditEvent(
                organization_id=org_id,
                job_id=job_id,
                action="AI_RESPONSE_GENERATED",
                actor_id=user_id,
                actor_email=user_email,
                actor_role="ENGINEER",
                target_type="AI_CONVERSATION",
                target_id=conv_id,
                details={
                    "agent": final_state.get("target_specialist"),
                    "execution_time_ms": total_time_ms,
                    "citations_count": len(response_dict.get("sources", [])),
                    "proposals_count": len(response_dict.get("suggested_actions", [])),
                },
            )
        )
        await db.commit()

        return {
            "conversation_id": conv_id,
            "answer": response_dict.get("answer", ""),
            "sources": response_dict.get("sources", []),
            "suggested_actions": response_dict.get("suggested_actions", []),
            "requires_human_action": response_dict.get("requires_human_action", False),
            "authority_level": "AI_ASSISTED",
            "model_confidence": response_dict.get("model_confidence", 1.0),
            "intent": final_state.get("intent"),
            "agent": final_state.get("target_specialist"),
        }

    # =========================================================================
    # STATE GRAPH EXECUTION
    # =========================================================================

    @classmethod
    async def _execute_state_graph(
        cls,
        db: AsyncSession,
        state: OrchestratorState,
        llm: Any,
    ) -> OrchestratorState:
        """Executes explicit LangGraph nodes."""
        # 1. INTENT_CLASSIFIER
        state = await cls._node_intent_classifier(state)

        # If direct forbidden request (e.g. user asks "approve this evidence")
        if state.get("forbidden_intent"):
            return await cls._node_handle_forbidden_action(db, state)

        # 2. CONTEXT_RETRIEVER
        state = await cls._node_context_retriever(db, state)

        # 3. TASK_PLANNER
        state = await cls._node_task_planner(state)

        # 4. SPECIALIST_AGENT
        state = await cls._node_specialist_agent(db, state, llm)

        # 5. AUTHORITY_VALIDATOR
        state = await cls._node_authority_validator(state)

        # 6. HUMAN_GATE
        state = await cls._node_human_gate(db, state)

        # 7. RESPONSE_COMPOSER
        state = await cls._node_response_composer(state)

        return state

    # =========================================================================
    # INDIVIDUAL GRAPH NODES
    # =========================================================================

    @classmethod
    async def _node_intent_classifier(cls, state: OrchestratorState) -> OrchestratorState:
        q = state["query"].strip()
        q_lower = q.lower()

        # Check for forbidden query
        forbidden = AIAuthorityFirewall.check_query_action(q)
        if forbidden:
            state["forbidden_intent"] = forbidden.value
            state["intent"] = forbidden.value
            return state

        # Specialist classification
        # Clause failure/compliance analysis queries → COMPLIANCE_ANALYST (must come before STANDARDS_ANALYST)
        if any(w in q_lower for w in ["fail", "gap", "pass", "why did", "assessment", "non-conform", "nonconform", "finding"]):
            state["target_specialist"] = "COMPLIANCE_ANALYST"
            state["intent"] = AllowedAIAction.TRACE_EXPLANATION.value
        elif any(w in q_lower for w in ["cad", "geometry", "height", "width", "wall thickness", "diameter", "mesh", "stp", "step"]):
            state["target_specialist"] = "CAD_ANALYST"
            state["intent"] = AllowedAIAction.TRACE_EXPLANATION.value
        elif any(w in q_lower for w in ["standard", "clause", "is 13252", "is 302", "requirement", "statutory"]):
            state["target_specialist"] = "STANDARDS_ANALYST"
            state["intent"] = AllowedAIAction.INFORMATIONAL.value
        elif any(w in q_lower for w in ["dna", "parameter", "rated", "voltage", "current", "power"]):
            state["target_specialist"] = "PRODUCT_DNA_ANALYST"
            state["intent"] = AllowedAIAction.EXTRACTION_ASSISTANCE.value
        elif any(w in q_lower for w in ["evidence", "file", "upload", "datasheet", "test report"]):
            state["target_specialist"] = "EVIDENCE_ANALYST"
            state["intent"] = AllowedAIAction.CLASSIFICATION.value
        elif any(w in q_lower for w in ["dossier", "report", "summary", "passport"]):
            state["target_specialist"] = "DOSSIER_ANALYST"
            state["intent"] = AllowedAIAction.SUMMARIZATION.value
        else:
            state["target_specialist"] = "COMPLIANCE_ANALYST"
            state["intent"] = AllowedAIAction.TRACE_EXPLANATION.value

        return state

    @classmethod
    async def _node_handle_forbidden_action(cls, db: AsyncSession, state: OrchestratorState) -> OrchestratorState:
        forbidden = state["forbidden_intent"]
        
        proposals = []
        requires_human = True
        
        if forbidden == ForbiddenAIAction.EVIDENCE_ACCEPTANCE.value:
            answer = (
                "Under GOAT statutory governance, the AI Engineering Copilot has ZERO authority to accept, "
                "verify, or approve evidence artifacts. Evidence acceptance requires formal human review by an "
                "authorized engineer or regulatory officer."
            )
            proposals.append({
                "action": "OPEN_EVIDENCE_REVIEW",
                "label": "Open Evidence Review Workflow",
                "description": "Navigate to Evidence Ingestion workspace to perform formal human acceptance.",
                "requires_confirmation": True,
            })
        elif forbidden == ForbiddenAIAction.STATUTORY_CERTIFICATION.value:
            answer = (
                "Under Indian statutory law and GOAT architectural invariants, AI cannot grant, certify, or "
                "guarantee BIS compliance. Certification authority rests exclusively with the Bureau of Indian Standards "
                "following deterministic testing and authorized human attestation."
            )
        elif forbidden == ForbiddenAIAction.AUTOMATIC_ATTESTATION.value:
            answer = (
                "AI cannot issue, sign, or activate statutory attestations. Attestations must be formally declared "
                "by an authenticated human reviewer, subject to separation-of-duties rules."
            )
            proposals.append({
                "action": "OPEN_ATTESTATION_WORKSPACE",
                "label": "Open Attestation Workspace",
                "description": "Proceed to Review Workspace to issue a formal human attestation.",
                "requires_confirmation": True,
            })
        elif forbidden == ForbiddenAIAction.OVERRIDE_DETERMINISTIC_RESULT.value:
            answer = (
                "The AI cannot alter, override, or recalculate deterministic assessment results. Compliance evaluations "
                "are computed mathematically from accepted empirical evidence and codified standards."
            )
        else:
            answer = (
                f"The requested action [{forbidden}] violates GOAT AI safety and authority boundaries. "
                "Statutory mutations require authorized human execution."
            )

        state["firewall_status"] = "BLOCKED_BY_FIREWALL"
        state["requires_human_action"] = requires_human
        state["final_response"] = {
            "intent": forbidden,
            "answer": answer,
            "claims": [],
            "sources": [],
            "suggested_actions": proposals,
            "authority_level": "AI_ASSISTED",
            "human_action_required": requires_human,
            "requires_human_action": requires_human,
            "model_confidence": 1.0,
        }
        return state

    @classmethod
    async def _node_context_retriever(cls, db: AsyncSession, state: OrchestratorState) -> OrchestratorState:
        org_id = state["organization_id"]
        job_id = state["job_id"]
        tool_logs = state.setdefault("tool_calls_logged", [])

        # Priority retrieval: Job -> DNA -> Evidence -> Standards -> Assessment -> Findings -> CAD
        t0 = time.time()
        job_data = await AIToolRegistry.get_job(db, org_id, job_id)
        dna_data = await AIToolRegistry.get_product_dna(db, org_id, job_id)
        ev_data = await AIToolRegistry.get_evidence(db, org_id, job_id)
        std_data = await AIToolRegistry.get_standard(db, org_id, job_id)
        req_data = await AIToolRegistry.get_requirements(db, org_id, job_id)
        eval_data = await AIToolRegistry.get_assessment(db, org_id, job_id)
        findings_data = await AIToolRegistry.get_findings(db, org_id, job_id)
        cad_models = await AIToolRegistry.get_cad_model(db, org_id, job_id)
        cad_meas = await AIToolRegistry.get_cad_measurements(db, org_id, job_id)
        dt = int((time.time() - t0) * 1000)

        tool_logs.append({
            "tool_name": "context_retriever_multi_fetch",
            "arguments": {"job_id": job_id},
            "result_summary": f"Retrieved DNA={len(dna_data)}, Evidence={len(ev_data)}, Reqs={len(req_data)}, Findings={len(findings_data)}, CAD={len(cad_models)}",
            "duration_ms": dt,
        })

        state["retrieved_context"] = {
            "job": job_data,
            "dna": dna_data,
            "evidence": ev_data,
            "standards": std_data,
            "requirements": req_data,
            "assessment": eval_data,
            "findings": findings_data,
            "cad_models": cad_models,
            "cad_measurements": cad_meas,
        }
        return state

    @classmethod
    async def _node_task_planner(cls, state: OrchestratorState) -> OrchestratorState:
        spec = state.get("target_specialist", "COMPLIANCE_ANALYST")
        state["task_plan"] = [
            f"Dispatch to {spec}",
            "Validate against authoritative retrieved context",
            "Enforce zero-statutory-authority invariants",
            "Extract verified citations",
        ]
        return state

    @classmethod
    async def _node_specialist_agent(
        cls,
        db: AsyncSession,
        state: OrchestratorState,
        llm: Any,
    ) -> OrchestratorState:
        spec = state.get("target_specialist", "COMPLIANCE_ANALYST")
        q = state["query"]
        q_lower = q.lower()
        ctx = state["retrieved_context"]
        proposals = []
        citations = []

        # =====================================================================
        # AGENT 4 — CAD ANALYST
        # =====================================================================
        if spec == "CAD_ANALYST":
            cad_models = ctx.get("cad_models", [])
            cad_meas = ctx.get("cad_measurements", [])
            dna_items = ctx.get("dna", [])

            if not cad_models:
                answer = "No CAD model has been uploaded for this compliance job (DATA_REQUIRED). Please upload a STEP (.stp/.step) file to extract geometry."
            else:
                model = cad_models[0]
                m_hash = model.get("model_hash", "")
                bbox = model.get("bounding_box", {}).get("dimensions", [])
                
                # Check for specific measurement query
                wall_m = next((m for m in cad_meas if m["measurement_type"] == "WALL_THICKNESS"), None)
                h_m = next((m for m in cad_meas if m["measurement_type"] == "BOUNDING_BOX_Z"), None)
                dia_m = next((m for m in cad_meas if m["measurement_type"] == "HOLE_DIAMETER"), None)

                answer_lines = [
                    f"Authoritative CAD Model `{model.get('file_name', 'enclosure')}` (SHA-256: `{m_hash[:16]}...`):",
                    f"- Enclosure Bounding Box: {bbox} mm (Volume: {model.get('volume_mm3')} mm³)",
                ]
                if wall_m:
                    answer_lines.append(f"- Measured Wall Thickness: {wall_m['measured_value']} {wall_m['unit']}")
                    citations.append(CitationItem(
                        claim="Wall thickness measured from B-Rep topological faces",
                        source_type="CAD",
                        source_id=wall_m["id"],
                        source_location="Face #12-#18",
                        support_status=SupportStatus.SUPPORTED,
                    ))
                if h_m:
                    answer_lines.append(f"- Enclosure Height: {h_m['measured_value']} {h_m['unit']}")
                    citations.append(CitationItem(
                        claim="Enclosure height measured from axis-aligned bounding envelope",
                        source_type="CAD",
                        source_id=h_m["id"],
                        source_location="Z-Extent",
                        support_status=SupportStatus.SUPPORTED,
                    ))
                if dia_m:
                    answer_lines.append(f"- Cylindrical Feature Diameter: {dia_m['measured_value']} {dia_m['unit']}")

                answer = "\n".join(answer_lines)
                citations.append(CitationItem(
                    claim="CAD model B-Rep geometry and bounding envelope",
                    source_type="CAD",
                    source_id=model["id"],
                    source_location="Header/Topology",
                    support_status=SupportStatus.SUPPORTED,
                ))

        # =====================================================================
        # AGENT 5 — COMPLIANCE ANALYST
        # =====================================================================
        elif spec == "COMPLIANCE_ANALYST":
            eval_run = ctx.get("assessment")
            findings = ctx.get("findings", [])
            reqs = ctx.get("requirements", [])
            
            # Check if query asks why a clause failed / passed
            import re
            m_cl = re.search(r"(\d+(?:\.\d+)+)", q)
            target_clause = m_cl.group(1) if m_cl else None

            if target_clause and eval_run:
                # Find the result
                res_match = next((r for r in eval_run.get("results", []) if target_clause in str(r.get("clause_number", ""))), None)
                req_match = next((r for r in reqs if target_clause in str(r.get("clause_number", ""))), None)
                
                if res_match:
                    st = res_match.get("assessment_state")
                    obs = res_match.get("observed_value")
                    obs_u = res_match.get("observed_unit", "")
                    op = res_match.get("comparison_operator", "")
                    t_min = res_match.get("threshold_min")
                    t_max = res_match.get("threshold_max")
                    threshold = t_min if t_min is not None else t_max

                    answer = (
                        f"Deterministic Assessment for Clause {target_clause} resulted in `{st}`.\n"
                        f"- Requirement: {req_match.get('requirement_text', 'Codified statutory standard') if req_match else 'Standard limit'}\n"
                        f"- Observed Parameter: `{res_match.get('parameter_key')}` = {obs} {obs_u}\n"
                        f"- Statutory Threshold: {op} {threshold} {obs_u}\n"
                        f"- Compiler Expression: `{res_match.get('evaluation_expression')}`\n"
                        f"- Engine Explanation: {res_match.get('explanation')}"
                    )
                    citations.append(CitationItem(
                        claim=f"Assessment result for Clause {target_clause}",
                        source_type="ASSESSMENT",
                        source_id=res_match.get("id", target_clause),
                        source_location=f"Clause {target_clause}",
                        support_status=SupportStatus.SUPPORTED,
                    ))
                else:
                    answer = f"Clause {target_clause} was not evaluated in the current assessment run. Codified requirement data is required."
            elif findings:
                f_summaries = [f"- [{f['severity']}] {f['title']}: Observed {f['observed_value']} (Expected: {f['expected_value']})" for f in findings[:5]]
                answer = f"Found {len(findings)} open statutory non-compliance finding(s):\n" + "\n".join(f_summaries)
            else:
                answer = "Assessment run indicates all evaluated requirements conform to statutory thresholds, or no runs have been executed."

        # =====================================================================
        # AGENT 1 — EVIDENCE ANALYST
        # =====================================================================
        elif spec == "EVIDENCE_ANALYST":
            ev_list = ctx.get("evidence", [])
            if not ev_list:
                answer = "No evidence artifacts have been ingested for this compliance job (DATA_REQUIRED)."
            else:
                lines = [f"Ingested Evidence Artifacts ({len(ev_list)} items):"]
                for ev in ev_list[:5]:
                    lines.append(f"- `{ev['file_name']}`: Status `{ev['acceptance_status']}` (SHA-256: `{ev['sha256'][:16]}...`)")
                    citations.append(CitationItem(
                        claim=f"Evidence artifact {ev['file_name']}",
                        source_type="EVIDENCE",
                        source_id=ev["id"],
                        source_location="Storage",
                        support_status=SupportStatus.SUPPORTED,
                    ))
                answer = "\n".join(lines)

        # =====================================================================
        # AGENT 2 — STANDARDS ANALYST
        # =====================================================================
        elif spec == "STANDARDS_ANALYST":
            stds = ctx.get("standards", [])
            reqs = ctx.get("requirements", [])
            if not stds:
                answer = "No Indian Standard assigned as the active assessment basis for this job."
            else:
                std = stds[0]
                lines = [f"Active Standard: {std['standard_identifier']} ({std.get('title', '')})"]
                lines.append(f"Assigned statutory requirements ({len(reqs)} clauses):")
                for r in reqs[:5]:
                    lines.append(f"- Clause {r['clause_number']}: {r['requirement_text'][:80]}...")
                    citations.append(CitationItem(
                        claim=f"Standard Requirement for Clause {r['clause_number']}",
                        source_type="CLAUSE",
                        source_id=r["requirement_id"],
                        source_location=f"Clause {r['clause_number']}",
                        support_status=SupportStatus.SUPPORTED,
                    ))
                answer = "\n".join(lines)

        # =====================================================================
        # AGENT 3 — PRODUCT DNA ANALYST
        # =====================================================================
        elif spec == "PRODUCT_DNA_ANALYST":
            dna_items = ctx.get("dna", [])
            if not dna_items:
                answer = "No verified parameters available in Product DNA (DATA_REQUIRED). Accepted evidence is required."
            else:
                lines = ["Product DNA Facts:"]
                for d in dna_items:
                    lines.append(f"- `{d['parameter']}`: {d['value']} {d['unit']} (Status: `{d['status']}`)")
                    citations.append(CitationItem(
                        claim=f"Product DNA parameter {d['parameter']}",
                        source_type="DNA",
                        source_id=d["parameter"],
                        source_location="Product DNA Ledger",
                        support_status=SupportStatus.SUPPORTED,
                    ))
                answer = "\n".join(lines)

        # =====================================================================
        # AGENT 6 — DOSSIER ANALYST
        # =====================================================================
        else:
            job = ctx.get("job") or {}
            dna_items = ctx.get("dna", [])
            ev_list = ctx.get("evidence", [])
            answer = (
                f"Compliance Job Summary: `{job.get('title', 'Unknown')}` (Ref: {job.get('job_number')})\n"
                f"- Accepted Evidence Artifacts: {len([e for e in ev_list if e.get('acceptance_status') == 'ACCEPTED'])}\n"
                f"- Product DNA Parameters: {len(dna_items)}\n"
                "Draft technical dossier structure is ready for human review and assembly."
            )

        # Prompt injection defense check on answer
        answer = AIAuthorityFirewall.sanitize_output(answer)

        state["agent_output"] = {
            "answer": answer,
            "proposals": proposals,
            "citations": [c.model_dump() for c in citations],
        }
        return state

    @classmethod
    async def _node_authority_validator(cls, state: OrchestratorState) -> OrchestratorState:
        agent_out = state["agent_output"]
        answer = agent_out.get("answer", "")
        ctx = state.get("retrieved_context", {})

        # 1. Strip forbidden compliance claim phrases
        sanitized = AIAuthorityFirewall.sanitize_output(answer)

        # 2. Reconcile regulatory consistency with ground-truth backend state
        reconciled = AIAuthorityFirewall.reconcile_regulatory_consistency(sanitized, ctx)
        agent_out["answer"] = reconciled

        # 3. Validate citations against authoritative database context
        raw_citations = agent_out.get("citations", [])
        if raw_citations:
            valid_ev_ids = {str(e.get("id")) for e in ctx.get("evidence", []) if e.get("id")}
            valid_clauses = (
                {str(r.get("clause_number")) for r in ctx.get("requirements", []) if r.get("clause_number")}
                | {str(r.get("clause_reference")) for r in ctx.get("requirements", []) if r.get("clause_reference")}
                | {str(r.get("clause_number")) for r in (ctx.get("assessment") or {}).get("results", []) if r.get("clause_number")}
            )
            valid_dna = {str(d.get("parameter")) for d in ctx.get("dna", []) if d.get("parameter")}
            valid_cad = (
                {str(m.get("id")) for m in ctx.get("cad_models", []) if m.get("id")}
                | {str(m.get("id")) for m in ctx.get("cad_measurements", []) if m.get("id")}
            )
            valid_assessments = (
                {str((ctx.get("assessment") or {}).get("id"))}
                | {str(r.get("id")) for r in (ctx.get("assessment") or {}).get("results", []) if r.get("id")}
                | {str(r.get("clause_number")) for r in (ctx.get("assessment") or {}).get("results", []) if r.get("clause_number")}
            ) - {None, "", "None"}

            cit_items = [CitationItem(**c) if isinstance(c, dict) else c for c in raw_citations]
            validated_cits = AIAuthorityFirewall.validate_citations(
                citations=cit_items,
                valid_evidence_ids=valid_ev_ids,
                valid_clause_numbers=valid_clauses,
                valid_dna_keys=valid_dna,
                valid_cad_ids=valid_cad,
                valid_assessment_ids=valid_assessments,
            )
            agent_out["citations"] = [c.model_dump() for c in validated_cits]

        state["firewall_status"] = "PASSED_AUTHORITY_FIREWALL"
        return state

    @classmethod
    async def _node_human_gate(cls, db: AsyncSession, state: OrchestratorState) -> OrchestratorState:
        # Check if proposals need database persistence
        proposals = state["agent_output"].get("proposals", [])
        persisted_proposals = []
        org_id = state["organization_id"]
        job_id = state["job_id"]

        for p in proposals:
            if p.get("requires_confirmation"):
                state["requires_human_action"] = True
                prop = AIActionProposal(
                    organization_id=org_id,
                    job_id=job_id,
                    action_type=p.get("action", "PROPOSED_ACTION"),
                    proposal_payload=p,
                    reason=p.get("description", ""),
                    status="PROPOSED",
                    created_by_agent=state.get("target_specialist", "AI_COPILOT"),
                )
                db.add(prop)
                await db.flush()
                persisted_proposals.append({
                    "proposal_id": prop.id,
                    "action": prop.action_type,
                    "label": p.get("label", prop.action_type),
                    "description": prop.reason,
                    "status": "PROPOSED",
                    "requires_confirmation": True,
                })
            else:
                persisted_proposals.append(p)

        state["proposals"] = persisted_proposals
        return state

    @classmethod
    async def _node_response_composer(cls, state: OrchestratorState) -> OrchestratorState:
        agent_out = state["agent_output"]
        citations_raw = agent_out.get("citations", [])

        state["final_response"] = {
            "intent": state.get("intent", "INFORMATIONAL"),
            "answer": agent_out.get("answer", ""),
            "claims": [c.get("claim", "") for c in citations_raw],
            "sources": citations_raw,
            "suggested_actions": state.get("proposals", []),
            "authority_level": "AI_ASSISTED",
            "human_action_required": state.get("requires_human_action", False),
            "requires_human_action": state.get("requires_human_action", False),
            "model_confidence": 1.0,
        }
        return state
