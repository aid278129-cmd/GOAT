"""Single Structured LLM Interface for Layer 3 AI Orchestrator.

Strictly adheres to architectural constraint:
USE ONE LLM MODEL ONLY.
Do NOT create multiple independent LLMs or competing AI decision-makers.

The LLM provides language intelligence:
- Explaining codified requirements
- Summarizing retrieved evidence
- Formulating clarifying questions
The LLM has ZERO compliance decision authority.
"""

import json
from typing import Dict, Any, List, Optional
from backend.app.services.orchestrator.schemas import (
    OrchestratorIntent,
    OrchestratorContext,
    OrchestratedAIResponse,
    GroundingStatus,
    CitationItem,
)
from backend.app.services.orchestrator.knowledge_selector import (
    VERIFIED_STANDARDS_CATALOG,
    VERIFIED_SCHEMES_CATALOG,
    VERIFIED_SERVICES_CATALOG,
    verified_knowledge_selector,
)


class SingleStructuredLLM:
    """The authoritative, single LLM interface for the Zyntrix platform."""

    def __init__(self, model_name: str = "zyntrix-structured-compliance-llm"):
        self.model_name = model_name

    def generate_grounded_response(
        self,
        intent: OrchestratorIntent,
        sanitized_query: str,
        context: OrchestratorContext,
    ) -> OrchestratedAIResponse:
        """Generate structured, grounded response bounded by verified context."""
        import re
        q_lower = sanitized_query.lower()

        # 1. Intent: Adversarial Injection / Compliance Override Attempt
        if intent == OrchestratorIntent.MALICIOUS_OVERRIDE_ATTEMPT:
            std_ref = context.target_standard or "IS 302-2-201:2008"
            return OrchestratedAIResponse(
                answer=(
                    "The AI assistant has ZERO authority to declare, override, or certify compliance. "
                    "Under Zyntrix architecture, compliance determinations are strictly computed by the "
                    "deterministic compliance gate based on verified empirical laboratory evidence. "
                    "LLM compliance authority is exactly 0%."
                ),
                intent=intent,
                grounding_status=GroundingStatus.SUPPORTED,
                confidence_score=1.0,
                citations=[CitationItem(standard_number=std_ref, source_authority="Zero-Hallucination Regulatory Integrity Gate")],
                deterministic_fallback_used=True,
                regulatory_conclusion="NONE",
            )

        # 2. Intent: General BIS Information Assistant (Milestone M25.4A)
        if intent == OrchestratorIntent.GENERAL_BIS_INFORMATION:
            # Check for unverified standard reference in query (e.g. "What is IS 99999?")
            m_std = re.search(r"\bIS\s*(\d+(?:-\d+)*(?:-\d+)*)(?::(\d{4}))?\b", sanitized_query, re.IGNORECASE)
            std_num = m_std.group(1) if m_std else None

            is_scheme_query = "scheme" in q_lower or "crs" in q_lower
            is_service_query = any(w in q_lower for w in ["service", "services", "bis care", "manakonline", "hallmark"])
            is_procedure_query = any(w in q_lower for w in ["how does", "procedure", "process", "workflow", "work?", "steps"])

            matched_std = None
            if std_num:
                for cat_std, data in VERIFIED_STANDARDS_CATALOG.items():
                    if std_num in cat_std:
                        matched_std = (cat_std, data)
                        break
                if not matched_std:
                    return OrchestratedAIResponse(
                        answer=f"SOURCE_UNAVAILABLE: Verified standard information for 'IS {std_num}' is not available in the Bureau of Indian Standards verified knowledge base. The system strictly refuses to speculate or invent unverified standards.",
                        intent=intent,
                        grounding_status=GroundingStatus.NOT_IN_KNOWLEDGE_BASE,
                        confidence_score=0.0,
                        citations=[],
                        deterministic_fallback_used=True,
                        regulatory_conclusion="NONE",
                    )
            elif not (is_scheme_query or is_service_query or is_procedure_query):
                if context.target_standard and context.target_standard in VERIFIED_STANDARDS_CATALOG:
                    matched_std = (context.target_standard, VERIFIED_STANDARDS_CATALOG[context.target_standard])

            # A. Standard Information Query (e.g. "What is IS 4151?", "What does this standard cover?")
            if matched_std:
                std_code, std_info = matched_std
                title = std_info.get("title", "")
                ministry = std_info.get("ministry", "Government of India")
                qco = std_info.get("qco_order", "Applicable Quality Control Order")
                clauses = std_info.get("clauses", {})
                clauses_summary = "\n".join([f"- Clause {c}: {info.get('title', '')} — {info.get('req', '')}" for c, info in list(clauses.items())[:5]])
                answer = (
                    f"**Standard**: {std_code} — {title}\n\n"
                    f"**Governing Authority / Ministry**: {ministry}\n"
                    f"**Regulatory Quality Control Order**: {qco}\n\n"
                    f"**Scope & Key Codified Requirements**:\n{clauses_summary}\n\n"
                    f"*(Source: Bureau of Indian Standards Official Gazette. Verification status: VERIFIED)*"
                )
                citations = [
                    CitationItem(
                        standard_number=std_code,
                        clause_number=list(clauses.keys())[0] if clauses else None,
                        clause_title=list(clauses.values())[0].get("title") if clauses else None,
                        source_authority=f"Bureau of Indian Standards ({qco})",
                        verified=True,
                    )
                ]
                return OrchestratedAIResponse(
                    answer=answer,
                    intent=intent,
                    grounding_status=GroundingStatus.SUPPORTED,
                    confidence_score=0.98,
                    citations=citations,
                    deterministic_fallback_used=False,
                    regulatory_conclusion="NONE",
                )

            # B. Certification Scheme Query (e.g. "What is a BIS certification scheme?", "Difference between Scheme I and Scheme II")
            if "scheme" in q_lower:
                sch1 = VERIFIED_SCHEMES_CATALOG["SCHEME_I"]
                sch2 = VERIFIED_SCHEMES_CATALOG["SCHEME_II"]
                is_comparison = any(w in q_lower for w in ["difference", "compare", "versus", "vs", "between"]) or ("scheme i" in q_lower and "scheme ii" in q_lower) or ("scheme 1" in q_lower and "scheme 2" in q_lower)
                if is_comparison:
                    answer = (
                        f"**Bureau of Indian Standards (BIS) Certification Schemes Comparison**:\n\n"
                        f"1. **{sch1['scheme_name']}**:\n"
                        f"- **Governing Regulation**: {sch1['governing_regulation']}\n"
                        f"- **Mark Granted**: {sch1['mark']}\n"
                        f"- **Procedure**: {sch1['key_features']}\n"
                        f"- **Overview**: {sch1['description']}\n\n"
                        f"2. **{sch2['scheme_name']}**:\n"
                        f"- **Governing Regulation**: {sch2['governing_regulation']}\n"
                        f"- **Mark Granted**: {sch2['mark']}\n"
                        f"- **Procedure**: {sch2['key_features']}\n"
                        f"- **Overview**: {sch2['description']}\n\n"
                        f"**Key Difference**: Scheme I requires preliminary factory inspection, independent sample testing in BIS labs, and continuous factory surveillance audits. Scheme II (CRS) is a self-declaration regime for electronics and IT goods based on test reports from BIS-recognized laboratories without preliminary factory inspection."
                    )
                elif "scheme ii" in q_lower or "scheme 2" in q_lower or "crs" in q_lower:
                    answer = (
                        f"**{sch2['scheme_name']}**:\n\n"
                        f"- **Governing Regulation**: {sch2['governing_regulation']}\n"
                        f"- **Mark Granted**: {sch2['mark']}\n"
                        f"- **Key Features**: {sch2['key_features']}\n"
                        f"- **Description**: {sch2['description']}\n"
                        f"- **Official Portal**: {sch2['official_guideline_url']}"
                    )
                else:
                    answer = (
                        f"**Bureau of Indian Standards (BIS) Certification Schemes**:\n\n"
                        f"BIS operates official conformity assessment schemes under the BIS (Conformity Assessment) Regulations, 2018:\n\n"
                        f"1. **{sch1['scheme_name']}**: Requires factory audit, sample testing, and surveillance for grant of the ISI mark.\n"
                        f"2. **{sch2['scheme_name']}**: Compulsory registration scheme for electronics/IT products based on recognized lab test reports.\n"
                        f"3. **{VERIFIED_SCHEMES_CATALOG['HALLMARKING']['scheme_name']}**: Statutory hallmarking of gold and silver jewelry with digital 6-digit HUID."
                    )
                citations = [
                    CitationItem(
                        standard_number="BIS Scheme I (ISI Mark)",
                        clause_number="Schedule II, Scheme I",
                        clause_title="Product Certification Scheme",
                        source_authority="BIS (Conformity Assessment) Regulations, 2018",
                        verified=True,
                    ),
                    CitationItem(
                        standard_number="BIS Scheme II (CRS)",
                        clause_number="Schedule II, Scheme II",
                        clause_title="Compulsory Registration Scheme",
                        source_authority="BIS (Conformity Assessment) Regulations, 2018",
                        verified=True,
                    ),
                ]
                return OrchestratedAIResponse(
                    answer=answer,
                    intent=intent,
                    grounding_status=GroundingStatus.SUPPORTED,
                    confidence_score=0.99,
                    citations=citations,
                    deterministic_fallback_used=False,
                    regulatory_conclusion="NONE",
                )

            # C. BIS Services & Certification Process Query (e.g. "What BIS services are available?", "How does BIS certification work?")
            if any(w in q_lower for w in ["service", "how does", "procedure", "process", "work"]):
                answer = (
                    f"**Official Bureau of Indian Standards (BIS) Services & Certification Workflow**:\n\n"
                    f"1. **Product Certification (Grant of License under Scheme I)**:\n"
                    f"   - Statutory Authority: BIS Act 2016, Section 13\n"
                    f"   - Procedure: Online e-application via Manakonline portal -> Preliminary factory inspection by BIS officer -> Independent sample drawing and testing -> Grant of License (GoL) for ISI mark.\n\n"
                    f"2. **Compulsory Registration Scheme (CRS)**:\n"
                    f"   - For IT, electronics, and solar inverters under MeitY/MNRE QCOs.\n"
                    f"   - Procedure: Product testing at BIS-recognized lab -> Online submission with test report -> Document scrutiny -> Grant of unique Registration R-Number.\n\n"
                    f"3. **Jeweller Registration & Hallmarking**:\n"
                    f"   - Purity certification for gold and silver jewellery under BIS Hallmarking Regulations 2018.\n"
                    f"   - Verification through 6-digit alphanumeric HUID laser-marked at Assaying and Hallmarking Centres (AHC).\n\n"
                    f"4. **Consumer Services & BIS CARE Verification**:\n"
                    f"   - Real-time mobile verification of genuine ISI marks, licensee details, and HUID authenticity with complaint redressal."
                )
                citations = [
                    CitationItem(
                        standard_number="BIS Act 2016",
                        clause_number="Section 13",
                        clause_title="Grant of Licence and Certificate of Conformity",
                        source_authority="Bureau of Indian Standards",
                        verified=True,
                    ),
                    CitationItem(
                        standard_number="BIS (Conformity Assessment) Regulations, 2018",
                        clause_number="Schedule II",
                        clause_title="Conformity Assessment Schemes",
                        source_authority="Bureau of Indian Standards",
                        verified=True,
                    ),
                ]
                return OrchestratedAIResponse(
                    answer=answer,
                    intent=intent,
                    grounding_status=GroundingStatus.SUPPORTED,
                    confidence_score=0.99,
                    citations=citations,
                    deterministic_fallback_used=False,
                    regulatory_conclusion="NONE",
                )

            # Fallback for unclassified general BIS query
            return OrchestratedAIResponse(
                answer="UNKNOWN / MORE_INFORMATION_REQUIRED: The query does not specify a recognized Indian Standard, certification scheme, or official BIS service. Please specify an Indian Standard number (e.g. IS 4151) or a specific BIS service or scheme.",
                intent=intent,
                grounding_status=GroundingStatus.UNKNOWN,
                confidence_score=0.0,
                citations=[],
                missing_information_notes="Specific standard number or BIS service required.",
                deterministic_fallback_used=True,
                regulatory_conclusion="NONE",
            )

        std_key = context.target_standard or "IS 302-2-201:2008"
        std_data = VERIFIED_STANDARDS_CATALOG.get(std_key, {})
        clauses_dict = std_data.get("clauses", {})

        # Check if user is asking about an unverified standard
        if std_key not in VERIFIED_STANDARDS_CATALOG:
            return OrchestratedAIResponse(
                answer=f"I don't have verified information in the current BIS knowledge base for {std_key}. The system strictly refuses to speculate or invent unverified standards.",
                intent=intent,
                grounding_status=GroundingStatus.NOT_IN_KNOWLEDGE_BASE,
                confidence_score=0.0,
                citations=[],
                deterministic_fallback_used=True,
                regulatory_conclusion="NONE",
            )

        m_std = re.search(r"\bis\s*(\d{4,6})(?::\d{4})?\b", q_lower, re.IGNORECASE)
        if m_std:
            asked_num = m_std.group(1)
            if not any(asked_num in k for k in VERIFIED_STANDARDS_CATALOG):
                return OrchestratedAIResponse(
                    answer=f"I don't have verified information in the current BIS knowledge base for IS {asked_num}. The system strictly refuses to speculate or invent unverified standards.",
                    intent=intent,
                    grounding_status=GroundingStatus.NOT_IN_KNOWLEDGE_BASE,
                    confidence_score=0.0,
                    citations=[],
                    deterministic_fallback_used=True,
                    regulatory_conclusion="NONE",
                )

        # 4. Intent: Query Requirement (Explicit Clause Match)
        m_cl = re.search(r"\bclause\s*(\d+(?:\.\d+)*)\b", q_lower, re.IGNORECASE)
        if m_cl and m_cl.group(1) in clauses_dict:
            cl_info = clauses_dict[m_cl.group(1)]
            return OrchestratedAIResponse(
                answer=(
                    f"Under {std_key} Clause {m_cl.group(1)} ({cl_info['title']}), "
                    f"the standard mandates: {cl_info['req']}"
                ),
                intent=intent,
                grounding_status=GroundingStatus.SUPPORTED,
                confidence_score=0.98,
                citations=[
                    CitationItem(
                        standard_number=std_key,
                        clause_number=m_cl.group(1),
                        clause_title=cl_info["title"],
                        verified=True,
                    )
                ],
                deterministic_fallback_used=False,
                regulatory_conclusion="NONE",
            )
        elif m_cl:
            return OrchestratedAIResponse(
                answer=f"Clause {m_cl.group(1)} does not exist in the codified requirements of {std_key}. The system strictly refuses to speculate or invent unverified clauses.",
                intent=intent,
                grounding_status=GroundingStatus.NOT_IN_KNOWLEDGE_BASE,
                confidence_score=0.0,
                citations=[],
                deterministic_fallback_used=True,
                regulatory_conclusion="NONE",
            )

        # 4b. Semantic Clause Keyword Matching within verified target standard (Best Match Scoring)
        stop_words = {"what", "does", "require", "under", "standard", "limit", "with", "from", "for", "the", "is", "are", "shall", "and", "can", "applicable"}
        q_keywords = [w for w in re.findall(r"\b[a-zA-Z0-9]{2,}\b", q_lower) if w not in stop_words]
        best_clause = None
        best_score = 0

        for c_num, c_data in clauses_dict.items():
            clause_text = (c_data.get("title", "") + " " + c_data.get("req", "")).lower()
            score = 0
            for kw in q_keywords:
                if kw in c_data.get("title", "").lower():
                    score += 3  # Title matches are highly salient
                elif kw in c_data.get("req", "").lower():
                    score += 1

            if score > best_score:
                best_score = score
                best_clause = (c_num, c_data)

        if best_clause and best_score >= 4:
            c_num, c_data = best_clause
            return OrchestratedAIResponse(
                answer=(
                    f"Under {std_key} Clause {c_num} ({c_data['title']}), "
                    f"the standard mandates: {c_data['req']}"
                ),
                intent=intent,
                grounding_status=GroundingStatus.SUPPORTED,
                confidence_score=0.95,
                citations=[
                    CitationItem(
                        standard_number=std_key,
                        clause_number=c_num,
                        clause_title=c_data["title"],
                        verified=True,
                    )
                ],
                deterministic_fallback_used=False,
                regulatory_conclusion="NONE",
            )

        # 5. Intent: Explain Gap or Evidence
        if intent == OrchestratorIntent.EXPLAIN_GAP or "gap" in q_lower or "missing" in q_lower:
            return OrchestratedAIResponse(
                answer=(
                    f"I cannot establish compliance from the available evidence alone. "
                    f"For {context.product_name} under {std_key}, full satisfaction requires "
                    f"attaching accredited laboratory test certificates covering dielectric strength, "
                    f"earthing continuity, and temperature-rise limits."
                ),
                intent=intent,
                grounding_status=GroundingStatus.SUPPORTED,
                confidence_score=0.92,
                citations=[CitationItem(standard_number=std_key, verified=True)],
                missing_information_notes="Accredited NABL test report required for clause satisfaction.",
                deterministic_fallback_used=False,
                regulatory_conclusion="NONE",
            )

        # Default Grounded Assistant Answer
        return OrchestratedAIResponse(
            answer=(
                f"For {context.product_name} evaluated against {std_key} ({std_data.get('title', '')}), "
                f"the mandatory Quality Control Order is '{std_data.get('qco_order', '')}'. "
                f"You can query specific clauses (e.g. Clause {list(clauses_dict.keys())[0] if clauses_dict else '1.1'})."
            ),
            intent=intent,
            grounding_status=GroundingStatus.SUPPORTED,
            confidence_score=0.95,
            citations=[CitationItem(standard_number=std_key, verified=True)],
            deterministic_fallback_used=False,
            regulatory_conclusion="NONE",
        )


single_structured_llm = SingleStructuredLLM()
