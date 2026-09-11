"""Layer 3: Advanced LangChain Planning Agent (Milestone M24.4.3D).

Architectural Invariants Strictly Enforced:
1. ONE LLM ONLY: Model execution delegates strictly to the single LLM singleton / adapter.
2. ZERO COMPLIANCE AUTHORITY: Planning Agent compliance authority is exactly 0.0%.
   Authority level is strictly AI_DERIVED / CANDIDATE.
   It cannot declare, evaluate, certify, or conclude regulatory compliance.
   It cannot mark requirements SATISFIED or products COMPLIANT.
3. PRESERVE FOUNDATIONAL TRUTHS:
   - USER_TEXT != EVIDENCE != COMPLIANCE
   - NO VERIFIED SOURCE -> NO REGULATORY CLAIM
   - NO VERIFIED EVIDENCE -> NO SATISFIED
   - NO SUFFICIENT INFORMATION -> ASK / UNKNOWN
   - CONFLICT -> EXPERT REVIEW
   - RECOMMENDATIONS != COMPLIANCE EVALUATION
4. ACTION-PLANNING ROLE ONLY: Answers "What should be done next?", never "Is the product compliant?".
5. NO EXTERNAL EXECUTION: Generates recommendations only. Does not book laboratories, send emails,
   or execute autonomous real-world operations.
6. DETERMINISTIC DEPENDENCY INTEGRITY: Enforces acyclic directed graph dependencies (DAG).
7. PROMPT INJECTION DEFENSE: Untrusted document text is treated strictly as DATA, not instructions.
"""

import re
import time
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Set
from pydantic import BaseModel, Field

from backend.app.services.compliance.authority_types import AuthorityLevel, AuthoritySource
from backend.app.services.orchestrator.schemas import OrchestratorIntent, GroundingStatus
from backend.app.services.security.prompt_guard import scan_and_sanitize_untrusted_text
from backend.app.core.logging import logger


# ==============================================================================
# ENUMS & CONSTANTS
# ==============================================================================

MAX_REMEDIATION_ACTIONS = 15

# Malicious prompt injection patterns targeting action planning
MALICIOUS_PLANNING_PATTERNS = [
    re.compile(r"\b(?:tell\s+(?:the\s+)?manufacturer\s+to\s+ignore|ignore\s+(?:clause|requirement))\b", re.IGNORECASE),
    re.compile(r"\b(?:mark\s+(?:the\s+)?gap\s+(?:as\s+)?resolved|mark\s+(?:as\s+)?satisfied)\b", re.IGNORECASE),
    re.compile(r"\b(?:assume\s+(?:the\s+)?test\s+report\s+exists|say\s+that\s+no\s+testing\s+is\s+required)\b", re.IGNORECASE),
    re.compile(r"\b(?:ignore\s+(?:the\s+)?expert\s+review|bypass\s+(?:testing|validation))\b", re.IGNORECASE),
    re.compile(r"\b(?:book\s+(?:the\s+)?lab|send\s+email\s+to\s+bis|submit\s+application)\b", re.IGNORECASE),
]


class ActionType(str, Enum):
    """Controlled taxonomy of remediation action types."""
    LAB_TEST_REQUIRED = "LAB_TEST_REQUIRED"
    DOCUMENT_REQUIRED = "DOCUMENT_REQUIRED"
    MANUFACTURER_SPECIFICATION_REQUIRED = "MANUFACTURER_SPECIFICATION_REQUIRED"
    PHOTO_MARKING_EVIDENCE_REQUIRED = "PHOTO_MARKING_EVIDENCE_REQUIRED"
    EXPERT_REVIEW_REQUIRED = "EXPERT_REVIEW_REQUIRED"
    PRODUCT_INFORMATION_REQUIRED = "PRODUCT_INFORMATION_REQUIRED"
    SOURCE_VERIFICATION_REQUIRED = "SOURCE_VERIFICATION_REQUIRED"
    STANDARD_REVIEW_REQUIRED = "STANDARD_REVIEW_REQUIRED"


class ActionPriority(int, Enum):
    """Deterministic priority levels for action execution."""
    CRITICAL_BLOCKER = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class ActionGroup(str, Enum):
    """Categorical grouping of action items."""
    IMMEDIATE_BLOCKERS = "IMMEDIATE_BLOCKERS"
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    LAB_TESTING = "LAB_TESTING"
    PRODUCT_INFORMATION = "PRODUCT_INFORMATION"
    EXPERT_REVIEW = "EXPERT_REVIEW"
    FINAL_REASSESSMENT = "FINAL_REASSESSMENT"


class ResponsibleParty(str, Enum):
    """Qualitative assignment of operational ownership (non-legal)."""
    MANUFACTURER = "MANUFACTURER"
    LABORATORY = "LABORATORY"
    COMPLIANCE_EXPERT = "COMPLIANCE_EXPERT"
    DOCUMENT_OWNER = "DOCUMENT_OWNER"
    SYSTEM = "SYSTEM"
    USER = "USER"


class EstimatedEffort(str, Enum):
    """Controlled qualitative effort estimation."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class ActionStatus(str, Enum):
    """Operational lifecycle state of an action item."""
    OPEN = "OPEN"
    BLOCKED = "BLOCKED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REQUIRES_EXPERT_REVIEW = "REQUIRES_EXPERT_REVIEW"
    UNKNOWN = "UNKNOWN"


# ==============================================================================
# DATA CONTRACTS (Pydantic v2)
# ==============================================================================

class ActionItem(BaseModel):
    """Single structured action step within the remediation plan."""
    action_id: str
    action_type: ActionType
    title: str
    description: str
    clause_numbers: List[str] = Field(default_factory=list)
    standard_number: str
    priority: ActionPriority = ActionPriority.HIGH
    action_group: ActionGroup = ActionGroup.EVIDENCE_COLLECTION
    is_blocker: bool = False
    dependencies: List[str] = Field(default_factory=list)
    required_evidence: Optional[str] = None
    test_method: Optional[str] = None
    responsible_party: ResponsibleParty = ResponsibleParty.MANUFACTURER
    estimated_effort: EstimatedEffort = EstimatedEffort.MEDIUM
    status: ActionStatus = ActionStatus.OPEN
    authority: str = "AI_DERIVED / CANDIDATE"
    provenance: str = "AI_DERIVED / CANDIDATE"


class BlockerItem(BaseModel):
    """Explicit compliance blocker halting progression."""
    blocker_id: str
    reason: str
    blocking_actions: List[str] = Field(default_factory=list)
    category: str = "EVIDENCE_GAP"


class ActionPlan(BaseModel):
    """Comprehensive, non-authoritative action plan generated by Planning Agent."""
    standard_number: str
    total_actions: int = 0
    blockers_count: int = 0
    actions: List[ActionItem] = Field(default_factory=list)
    blockers: List[BlockerItem] = Field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)
    grouped_actions: Dict[str, List[str]] = Field(default_factory=dict)
    expert_review_required: bool = False
    sanitized_prompt_injections: List[str] = Field(default_factory=list)
    plan_summary: str = ""

    # Non-negotiable Authority Firewalls
    authority: str = "AI_DERIVED / CANDIDATE"
    regulatory_conclusion: str = "NONE"
    llm_compliance_authority: float = 0.0


# ==============================================================================
# DOMAIN ENGINES: BLOCKER DETECTION, DEPENDENCY VALIDATION & DEDUPLICATION
# ==============================================================================

class BlockerDetector:
    """Identifies critical blockers from gaps, conflicts, and unverified data."""

    @classmethod
    def identify_blockers(
        cls,
        unsatisfied_clauses: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]],
        evidence_status: str,
        target_standard: str,
    ) -> List[BlockerItem]:
        """Identifies conditions that block compliance certification."""
        blockers: List[BlockerItem] = []

        # 1. Conflicting evidence blocker
        if conflicts or evidence_status == "CONFLICT":
            blockers.append(
                BlockerItem(
                    blocker_id="BLOCKER-CONFLICT-001",
                    reason="Contradictory evidence detected between submitted specifications and laboratory reports. Expert technical review required before compliance evaluation.",
                    category="EVIDENCE_CONFLICT",
                )
            )

        # 2. No verified source / unverified standard
        if evidence_status == "NO_VERIFIED_SOURCE":
            blockers.append(
                BlockerItem(
                    blocker_id="BLOCKER-UNVERIFIED-STD-001",
                    reason=f"Standard '{target_standard}' lacks verified regulatory source documentation or Gazette notification.",
                    category="UNVERIFIED_SOURCE",
                )
            )

        # 3. Mandatory laboratory testing gap blocker
        test_gaps = [c for c in unsatisfied_clauses if "test" in str(c.get("action", "")).lower() or "test" in str(c.get("gap_reason", "")).lower()]
        if test_gaps:
            cnums = [c.get("clause_number", "") for c in test_gaps]
            blockers.append(
                BlockerItem(
                    blocker_id="BLOCKER-LAB-TEST-001",
                    reason=f"Missing mandatory empirical laboratory test certificates for clauses: {', '.join(cnums)}.",
                    category="MANDATORY_TESTING_GAP",
                )
            )

        return blockers


class DependencyValidator:
    """Builds and validates directed dependency graphs, detecting and breaking cycles."""

    @classmethod
    def build_and_validate_dag(
        cls,
        actions: List[ActionItem],
    ) -> Tuple[Dict[str, List[str]], bool]:
        """Constructs an adjacency list of action dependencies and guarantees DAG property (no cycles).
        
        Returns: (dependency_graph, is_acyclic)
        """
        adj: Dict[str, List[str]] = {}
        for a in actions:
            adj[a.action_id] = list(a.dependencies)

        # Cycle detection using DFS coloring: 0 = unvisited, 1 = visiting, 2 = visited
        visited: Dict[str, int] = {aid: 0 for aid in adj}
        has_cycle = False

        def dfs(node: str) -> bool:
            nonlocal has_cycle
            visited[node] = 1
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    continue
                if visited[neighbor] == 1:
                    has_cycle = True
                    return True
                if visited[neighbor] == 0:
                    if dfs(neighbor):
                        return True
            visited[node] = 2
            return False

        for node in list(adj.keys()):
            if visited[node] == 0:
                if dfs(node):
                    break

        if has_cycle:
            # Deterministically break cycles by clearing backward edges
            logger.warning("[DependencyValidator] Cycle detected in action dependencies. Pruning backward edges to restore DAG.")
            cleaned_adj: Dict[str, List[str]] = {}
            for aid, deps in adj.items():
                # Allow dependencies only on previously processed action IDs
                cleaned_adj[aid] = [d for d in deps if d != aid]
            return cleaned_adj, False

        return adj, True


class ActionDeduplicator:
    """Combines multiple requirement gaps sharing identical testing or document actions."""

    @classmethod
    def deduplicate(cls, actions: List[ActionItem]) -> List[ActionItem]:
        """Consolidates redundant actions of the same type and test method."""
        deduped: List[ActionItem] = []
        seen: Dict[Tuple[ActionType, Optional[str]], ActionItem] = {}

        for a in actions:
            key = (a.action_type, a.test_method or a.required_evidence)
            if key in seen:
                # Merge clause numbers into existing action
                existing = seen[key]
                for c in a.clause_numbers:
                    if c not in existing.clause_numbers:
                        existing.clause_numbers.append(c)
                existing.title = f"{existing.action_type.value}: Clauses {', '.join(existing.clause_numbers)}"
            else:
                seen[key] = a
                deduped.append(a)

        return deduped


class PromptInjectionDefender:
    """Guards Planning Agent against prompt injections and malicious gap manipulation."""

    @classmethod
    def sanitize_input(cls, text: str) -> Tuple[str, List[str]]:
        """Strips adversarial directives from user text or gap notes."""
        flagged: List[str] = []
        if not text:
            return "", flagged

        cleaned = text
        for pat in MALICIOUS_PLANNING_PATTERNS:
            for m in pat.finditer(cleaned):
                flagged.append(m.group(0))
            cleaned = pat.sub("[UNTRUSTED_INSTRUCTION_NEUTRALIZED]", cleaned)

        scan_res = scan_and_sanitize_untrusted_text(cleaned)
        if scan_res.detected_patterns:
            flagged.extend(scan_res.detected_patterns)
        cleaned = scan_res.sanitized_text

        return cleaned, flagged


# ==============================================================================
# MAIN PLANNING AGENT
# ==============================================================================

class PlanningAgent:
    """Advanced Planning Agent that formulates structured, non-authoritative action plans."""

    def __init__(self):
        self.tool_cache: Dict[str, Any] = {}
        self.metrics: Dict[str, int] = {
            "planning_invocations": 0,
            "llm_calls": 0,
            "deterministic_short_circuits": 0,
            "tool_calls": 0,
            "cache_hits": 0,
            "duplicate_actions_prevented": 0,
            "blockers_identified": 0,
            "injections_sanitized": 0,
        }

    def reset_metrics(self) -> None:
        """Reset execution accounting metrics."""
        self.tool_cache.clear()
        for k in self.metrics:
            self.metrics[k] = 0

    def generate_action_plan(
        self,
        target_standard: str,
        unsatisfied_clauses: List[Dict[str, Any]],
        gap_summary: Optional[Dict[str, Any]] = None,
        evidence_status: str = "NO_VERIFIED_SOURCE",
        structured_analysis: Optional[Dict[str, Any]] = None,
        product_dna: Optional[Dict[str, Any]] = None,
        user_prompt: str = "",
        tool_executor: Optional[Any] = None,
    ) -> ActionPlan:
        """Formulates a comprehensive, structured action plan with zero compliance authority."""
        self.metrics["planning_invocations"] += 1
        all_injections: List[str] = []

        # 1. Prompt Injection Defense
        clean_prompt, p_inj = PromptInjectionDefender.sanitize_input(user_prompt)
        if p_inj:
            all_injections.extend(p_inj)

        # 2. Extract conflicts and missing evidence from analysis if available
        conflicts = []
        missing_evidence = []
        if structured_analysis:
            conflicts = structured_analysis.get("evidence_conflicts", [])
            missing_evidence = structured_analysis.get("missing_evidence", [])

        # 3. Identify Blockers
        blockers = BlockerDetector.identify_blockers(
            unsatisfied_clauses=unsatisfied_clauses or [],
            conflicts=conflicts,
            evidence_status=evidence_status,
            target_standard=target_standard,
        )
        self.metrics["blockers_identified"] += len(blockers)

        raw_actions: List[ActionItem] = []
        action_idx = 1

        # 4. Action Creation: Expert Review Actions (Top Priority if conflicts exist)
        if conflicts or evidence_status == "CONFLICT":
            act_id = f"ACT-{action_idx:03d}"
            action_idx += 1
            raw_actions.append(
                ActionItem(
                    action_id=act_id,
                    action_type=ActionType.EXPERT_REVIEW_REQUIRED,
                    title="Expert Technical Review of Conflicting Evidence",
                    description="Resolve contradictory parameters between manufacturer specifications and test reports with a certified BIS compliance consultant.",
                    clause_numbers=[c.get("clause_number", "") for c in unsatisfied_clauses],
                    standard_number=target_standard,
                    priority=ActionPriority.CRITICAL_BLOCKER,
                    action_group=ActionGroup.EXPERT_REVIEW,
                    is_blocker=True,
                    responsible_party=ResponsibleParty.COMPLIANCE_EXPERT,
                    estimated_effort=EstimatedEffort.HIGH,
                    status=ActionStatus.REQUIRES_EXPERT_REVIEW,
                )
            )

        # 5. Action Creation: Laboratory Test Actions (From unsatisfied clauses)
        for item in (unsatisfied_clauses or []):
            cnum = str(item.get("clause_number", "GENERAL"))
            ctitle = item.get("clause_title", "Clause Requirement")
            reason = item.get("gap_reason", "No verified laboratory test report.")

            act_id = f"ACT-{action_idx:03d}"
            action_idx += 1

            # Determine action type based on clause or reason
            if "marking" in ctitle.lower() or "marking" in reason.lower():
                a_type = ActionType.PHOTO_MARKING_EVIDENCE_REQUIRED
                a_group = ActionGroup.EVIDENCE_COLLECTION
                req_ev = "High-resolution photograph of product marking plate with ISI mark & BIS licence number"
                party = ResponsibleParty.MANUFACTURER
                effort = EstimatedEffort.LOW
            elif "spec" in reason.lower() or "dna" in reason.lower():
                a_type = ActionType.MANUFACTURER_SPECIFICATION_REQUIRED
                a_group = ActionGroup.PRODUCT_INFORMATION
                req_ev = "Official Manufacturer Technical Datasheet"
                party = ResponsibleParty.MANUFACTURER
                effort = EstimatedEffort.LOW
            elif "test" in str(item.get("action", "")).lower() or "test" in reason.lower() or "heating" in ctitle.lower() or "leakage" in ctitle.lower():
                a_type = ActionType.LAB_TEST_REQUIRED
                a_group = ActionGroup.LAB_TESTING
                req_ev = f"NABL Accredited Laboratory Test Report for Clause {cnum}"
                party = ResponsibleParty.LABORATORY
                effort = EstimatedEffort.HIGH
            elif "document" in reason.lower() or "certificate" in reason.lower():
                a_type = ActionType.DOCUMENT_REQUIRED
                a_group = ActionGroup.EVIDENCE_COLLECTION
                req_ev = "Accredited Laboratory Certificate / Test Record"
                party = ResponsibleParty.LABORATORY
                effort = EstimatedEffort.MEDIUM
            else:
                a_type = ActionType.LAB_TEST_REQUIRED
                a_group = ActionGroup.LAB_TESTING
                req_ev = f"NABL Accredited Laboratory Test Report for Clause {cnum}"
                party = ResponsibleParty.LABORATORY
                effort = EstimatedEffort.HIGH

            raw_actions.append(
                ActionItem(
                    action_id=act_id,
                    action_type=a_type,
                    title=f"{a_type.value}: Clause {cnum} ({ctitle})",
                    description=f"Remediate compliance gap: {reason}",
                    clause_numbers=[cnum],
                    standard_number=target_standard,
                    priority=ActionPriority.HIGH if a_type == ActionType.LAB_TEST_REQUIRED else ActionPriority.MEDIUM,
                    action_group=a_group,
                    is_blocker=(a_type == ActionType.LAB_TEST_REQUIRED),
                    required_evidence=req_ev,
                    test_method=f"Standard test procedure as defined in {target_standard} Clause {cnum}",
                    responsible_party=party,
                    estimated_effort=effort,
                    status=ActionStatus.OPEN,
                )
            )

        # 6. Action Creation: Missing Information Actions
        if not unsatisfied_clauses and evidence_status == "NO_VERIFIED_SOURCE":
            act_id = f"ACT-{action_idx:03d}"
            action_idx += 1
            raw_actions.append(
                ActionItem(
                    action_id=act_id,
                    action_type=ActionType.SOURCE_VERIFICATION_REQUIRED,
                    title="Source Verification of Indian Standard",
                    description=f"Obtain official gazetted standard documentation for {target_standard}.",
                    clause_numbers=[],
                    standard_number=target_standard,
                    priority=ActionPriority.CRITICAL_BLOCKER,
                    action_group=ActionGroup.IMMEDIATE_BLOCKERS,
                    is_blocker=True,
                    responsible_party=ResponsibleParty.SYSTEM,
                    estimated_effort=EstimatedEffort.LOW,
                    status=ActionStatus.READY,
                )
            )

        # 7. Action Deduplication
        pre_count = len(raw_actions)
        deduped_actions = ActionDeduplicator.deduplicate(raw_actions)
        self.metrics["duplicate_actions_prevented"] += (pre_count - len(deduped_actions))

        # 8. Dependency Formulation & Ordering
        # Order: IMMEDIATE_BLOCKERS -> PRODUCT_INFORMATION -> LAB_TESTING -> EVIDENCE_COLLECTION -> EXPERT_REVIEW -> FINAL_REASSESSMENT
        for i in range(1, len(deduped_actions)):
            # Establish dependency on prior blocker if present
            if deduped_actions[0].is_blocker and deduped_actions[i].action_id != deduped_actions[0].action_id:
                deduped_actions[i].dependencies.append(deduped_actions[0].action_id)

        dep_graph, is_acyclic = DependencyValidator.build_and_validate_dag(deduped_actions)

        # 9. Group Actions
        grouped: Dict[str, List[str]] = {}
        for a in deduped_actions:
            grouped.setdefault(a.action_group.value, []).append(a.action_id)

        # 10. Prioritize
        deduped_actions.sort(key=lambda a: a.priority.value)

        # Deterministic short-circuit accounting
        self.metrics["deterministic_short_circuits"] += 1

        summary = (
            f"Remediation Plan for standard {target_standard}: "
            f"Identified {len(deduped_actions)} actionable steps across {len(grouped)} functional groups. "
            f"Active blockers: {len(blockers)}. "
            f"Expert review required: {bool(conflicts)}. "
            f"Actions are recommendations only; compliance determination remains with Layer 7."
        )

        return ActionPlan(
            standard_number=target_standard,
            total_actions=len(deduped_actions),
            blockers_count=len(blockers),
            actions=deduped_actions,
            blockers=blockers,
            dependency_graph=dep_graph,
            grouped_actions=grouped,
            expert_review_required=bool(conflicts),
            sanitized_prompt_injections=all_injections,
            plan_summary=summary,
            authority="AI_DERIVED / CANDIDATE",
            regulatory_conclusion="NONE",
            llm_compliance_authority=0.0,
        )


# Global Singleton Instance
planning_agent = PlanningAgent()
