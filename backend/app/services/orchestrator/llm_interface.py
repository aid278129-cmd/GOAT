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

        # 2. Intent: General BIS Information Assistant (Milestones M25.4A & M25.4B)
        if intent == OrchestratorIntent.GENERAL_BIS_INFORMATION:
            NON_ISSUANCE_DISCLAIMER = (
                "\n\n*General Guidance Disclaimer: Zyntrix is an informational compliance tool and does not issue BIS licenses, registrations, or official certifications. All certifications are granted exclusively by the Bureau of Indian Standards (BIS) through official government portals (Manakonline / crsbis.in).*"
            )

            # 1. Unverified / Fake Scheme check (e.g. "Scheme 99", "Scheme X")
            unverified_sch = verified_knowledge_selector.check_unverified_scheme(sanitized_query)
            if unverified_sch:
                return OrchestratedAIResponse(
                    answer=f"SOURCE_UNAVAILABLE: Verified scheme information for '{unverified_sch}' is not available in the Bureau of Indian Standards verified knowledge base. The system strictly refuses to speculate or invent unverified certification schemes.",
                    intent=intent,
                    grounding_status=GroundingStatus.NOT_IN_KNOWLEDGE_BASE,
                    confidence_score=0.0,
                    citations=[],
                    deterministic_fallback_used=True,
                    regulatory_conclusion="NONE",
                )

            # 2. Stale / Obsolete Procedure check (e.g. manual offline paper application)
            obsolete_info = verified_knowledge_selector.check_obsolete_procedure(sanitized_query)
            if obsolete_info:
                answer = (
                    f"**Statutory Regulatory Notice — Superseded / Obsolete Procedure**:\n\n"
                    f"{obsolete_info['explanation']}\n\n"
                    f"- **Governing Regulation**: {obsolete_info['governing_regulation']}\n"
                    f"- **Current Mandatory Online Portals**: {obsolete_info['modern_portals']}"
                    f"{NON_ISSUANCE_DISCLAIMER}"
                )
                citations = [
                    CitationItem(
                        standard_number="BIS (Conformity Assessment) Regulations, 2018",
                        clause_number="Regulation 3(1)",
                        clause_title="Manner of Applying for Licence or Certificate of Conformity",
                        source_authority="Bureau of Indian Standards",
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

            # 3. Check for unverified standard reference in query (e.g. "What is IS 99999?")
            m_std = re.search(r"\bIS\s*(\d+(?:-\d+)*(?:-\d+)*)(?::(\d{4}))?\b", sanitized_query, re.IGNORECASE)
            std_num = m_std.group(1) if m_std else None

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

            # 4. Scheme Applicability Determination ("Which BIS certification scheme applies?")
            is_scheme_applicability = any(phrase in q_lower for phrase in [
                "which bis certification scheme applies", "which scheme applies", "what scheme applies",
                "which certification scheme applies", "which scheme is for", "does scheme i or scheme ii apply",
                "which scheme",
            ])
            if is_scheme_applicability:
                sch_key, sch_data, explanation = verified_knowledge_selector.determine_applicable_scheme(sanitized_query, product_dna=context.product_name)
                if sch_key and sch_data:
                    answer = (
                        f"**Applicable BIS Certification Scheme Analysis**:\n\n"
                        f"- **Applicable Scheme**: {sch_data['scheme_name']}\n"
                        f"- **Mark Granted**: {sch_data['mark']}\n"
                        f"- **Governing Regulation**: {sch_data['governing_regulation']}\n"
                        f"- **Statutory Act**: {sch_data.get('statutory_act', 'BIS Act 2016')}\n"
                        f"- **Assessment Model**: {sch_data['key_features']}\n\n"
                        f"**Applicability Rationale**: {explanation}"
                        f"{NON_ISSUANCE_DISCLAIMER}"
                    )
                    citations = [
                        CitationItem(
                            standard_number=sch_data["scheme_name"],
                            clause_number="Schedule II",
                            clause_title="Conformity Assessment Schemes",
                            source_authority=sch_data["governing_regulation"],
                            verified=True,
                        ),
                        CitationItem(
                            standard_number=sch_data.get("statutory_act", "BIS Act 2016"),
                            clause_number="Section 13",
                            clause_title="Grant of Licence and Certificate of Conformity",
                            source_authority="Bureau of Indian Standards",
                            verified=True,
                        ),
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
                else:
                    return OrchestratedAIResponse(
                        answer=explanation + NON_ISSUANCE_DISCLAIMER,
                        intent=intent,
                        grounding_status=GroundingStatus.UNKNOWN,
                        confidence_score=0.0,
                        citations=[],
                        missing_information_notes="Product category, type, or Indian Standard number required to determine applicable scheme.",
                        deterministic_fallback_used=True,
                        regulatory_conclusion="NONE",
                    )

            # 5. Required Documents Query ("What documents are generally required?")
            is_docs_query = any(phrase in q_lower for phrase in [
                "what documents are generally required", "what documents are required", "documents required for",
                "documents generally required", "documents needed", "what documents are needed", "required documents",
            ])
            if is_docs_query:
                sch1 = VERIFIED_SCHEMES_CATALOG["SCHEME_I"]
                sch2 = VERIFIED_SCHEMES_CATALOG["SCHEME_II"]
                docs_sch1 = "\n".join([f"- {d}" for d in sch1["required_documents"]])
                docs_sch2 = "\n".join([f"- {d}" for d in sch2["required_documents"]])

                if "scheme ii" in q_lower or "scheme 2" in q_lower or "crs" in q_lower:
                    answer = (
                        f"**Documents Generally Required for BIS Scheme II (Compulsory Registration Scheme — CRS)**:\n\n"
                        f"{docs_sch2}\n\n"
                        f"- **Governing Authority**: {sch2['governing_regulation']}\n"
                        f"- **Official Portal**: {sch2['official_guideline_url']}"
                        f"{NON_ISSUANCE_DISCLAIMER}"
                    )
                    citations = [
                        CitationItem(
                            standard_number="BIS Scheme II (CRS)",
                            clause_number="Schedule II, Scheme II",
                            clause_title="Compulsory Registration Scheme Documentation Requirements",
                            source_authority="BIS (Conformity Assessment) Regulations, 2018",
                            verified=True,
                        )
                    ]
                elif "scheme i" in q_lower or "scheme 1" in q_lower or "isi" in q_lower:
                    answer = (
                        f"**Documents Generally Required for BIS Scheme I (Product Certification Scheme — ISI Mark)**:\n\n"
                        f"{docs_sch1}\n\n"
                        f"- **Governing Authority**: {sch1['governing_regulation']}\n"
                        f"- **Official Portal**: {sch1['official_guideline_url']}"
                        f"{NON_ISSUANCE_DISCLAIMER}"
                    )
                    citations = [
                        CitationItem(
                            standard_number="BIS Scheme I (ISI Mark)",
                            clause_number="Schedule II, Scheme I",
                            clause_title="Product Certification Scheme Documentation Requirements",
                            source_authority="BIS (Conformity Assessment) Regulations, 2018",
                            verified=True,
                        )
                    ]
                else:
                    answer = (
                        f"**Documents Generally Required for BIS Certification**:\n\n"
                        f"### 1. Scheme I (Product Certification Scheme — ISI Mark):\n{docs_sch1}\n\n"
                        f"### 2. Scheme II (Compulsory Registration Scheme — CRS):\n{docs_sch2}\n\n"
                        f"- **Statutory Source**: BIS (Conformity Assessment) Regulations, 2018"
                        f"{NON_ISSUANCE_DISCLAIMER}"
                    )
                    citations = [
                        CitationItem(
                            standard_number="BIS (Conformity Assessment) Regulations, 2018",
                            clause_number="Schedule II",
                            clause_title="Documentation Requirements for Conformity Assessment Schemes",
                            source_authority="Bureau of Indian Standards",
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

            # 6. Major Testing & Application Steps / General Certification Process
            is_steps_query = any(phrase in q_lower for phrase in [
                "major testing", "application steps", "testing steps", "testing/application steps",
                "testing and application steps", "major testing/application steps",
                "certification process", "certification workflow", "how does bis certification work",
                "how does certification work", "general bis certification process",
            ])
            if is_steps_query:
                sch1 = VERIFIED_SCHEMES_CATALOG["SCHEME_I"]
                sch2 = VERIFIED_SCHEMES_CATALOG["SCHEME_II"]
                steps_sch1 = "\n".join([f"- {s}" for s in sch1["major_testing_and_application_steps"]])
                steps_sch2 = "\n".join([f"- {s}" for s in sch2["major_testing_and_application_steps"]])

                if "scheme ii" in q_lower or "scheme 2" in q_lower or "crs" in q_lower:
                    answer = (
                        f"**Major Testing and Application Steps for BIS Scheme II (CRS)**:\n\n"
                        f"{steps_sch2}\n\n"
                        f"- **Statutory Provenance**: {sch2['governing_regulation']}"
                        f"{NON_ISSUANCE_DISCLAIMER}"
                    )
                    citations = [
                        CitationItem(
                            standard_number="BIS Scheme II (CRS)",
                            clause_number="Schedule II, Scheme II",
                            clause_title="Compulsory Registration Scheme Workflow",
                            source_authority="BIS (Conformity Assessment) Regulations, 2018",
                            verified=True,
                        )
                    ]
                elif "scheme i" in q_lower or "scheme 1" in q_lower or "isi" in q_lower:
                    answer = (
                        f"**Major Testing and Application Steps for BIS Scheme I (ISI Mark)**:\n\n"
                        f"{steps_sch1}\n\n"
                        f"- **Statutory Provenance**: {sch1['governing_regulation']}"
                        f"{NON_ISSUANCE_DISCLAIMER}"
                    )
                    citations = [
                        CitationItem(
                            standard_number="BIS Scheme I (ISI Mark)",
                            clause_number="Schedule II, Scheme I",
                            clause_title="Product Certification Scheme Workflow",
                            source_authority="BIS (Conformity Assessment) Regulations, 2018",
                            verified=True,
                        )
                    ]
                else:
                    answer = (
                        f"**General BIS Certification Process & Major Testing/Application Steps**:\n\n"
                        f"### 1. Scheme I (Product Certification Scheme — ISI Mark):\n{steps_sch1}\n\n"
                        f"### 2. Scheme II (Compulsory Registration Scheme — CRS):\n{steps_sch2}\n\n"
                        f"- **Statutory Authority**: BIS Act 2016, Section 13 & BIS (Conformity Assessment) Regulations, 2018"
                        f"{NON_ISSUANCE_DISCLAIMER}"
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
                    confidence_score=0.98,
                    citations=citations,
                    deterministic_fallback_used=False,
                    regulatory_conclusion="NONE",
                )

            # 7. Standard Information Query (e.g. "What is IS 4151?", "What does this standard cover?")
            is_scheme_query = "scheme" in q_lower or "crs" in q_lower
            is_service_query = any(w in q_lower for w in ["service", "services", "bis care", "manakonline", "hallmark"])
            is_procedure_query = any(w in q_lower for w in ["how does", "procedure", "process", "workflow", "work?", "steps"])

            if not matched_std and not (is_scheme_query or is_service_query or is_procedure_query):
                if context.target_standard and context.target_standard in VERIFIED_STANDARDS_CATALOG:
                    matched_std = (context.target_standard, VERIFIED_STANDARDS_CATALOG[context.target_standard])

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
                    f"{NON_ISSUANCE_DISCLAIMER}"
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

            # 8. Certification Scheme Query (e.g. "What is a BIS certification scheme?", "Difference between Scheme I and Scheme II")
            if "scheme" in q_lower or "crs" in q_lower:
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
                        f"{NON_ISSUANCE_DISCLAIMER}"
                    )
                elif "scheme ii" in q_lower or "scheme 2" in q_lower or "crs" in q_lower:
                    answer = (
                        f"**{sch2['scheme_name']}**:\n\n"
                        f"- **Governing Regulation**: {sch2['governing_regulation']}\n"
                        f"- **Mark Granted**: {sch2['mark']}\n"
                        f"- **Key Features**: {sch2['key_features']}\n"
                        f"- **Description**: {sch2['description']}\n"
                        f"- **Official Portal**: {sch2['official_guideline_url']}"
                        f"{NON_ISSUANCE_DISCLAIMER}"
                    )
                else:
                    answer = (
                        f"**Bureau of Indian Standards (BIS) Certification Schemes**:\n\n"
                        f"BIS operates official conformity assessment schemes under the BIS (Conformity Assessment) Regulations, 2018:\n\n"
                        f"1. **{sch1['scheme_name']}**: Requires factory audit, sample testing, and surveillance for grant of the ISI mark.\n"
                        f"2. **{sch2['scheme_name']}**: Compulsory registration scheme for electronics/IT products based on recognized lab test reports.\n"
                        f"3. **{VERIFIED_SCHEMES_CATALOG['HALLMARKING']['scheme_name']}**: Statutory hallmarking of gold and silver jewelry with digital 6-digit HUID."
                        f"{NON_ISSUANCE_DISCLAIMER}"
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

            # 9. BIS Services Overview Query
            if any(w in q_lower for w in ["service", "services", "bis care", "hallmark"]):
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
                    f"{NON_ISSUANCE_DISCLAIMER}"
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
                answer="UNKNOWN / MORE_INFORMATION_REQUIRED: The query does not specify a recognized Indian Standard, certification scheme, or official BIS service. Please specify an Indian Standard number (e.g. IS 4151) or a specific BIS service or scheme." + NON_ISSUANCE_DISCLAIMER,
                intent=intent,
                grounding_status=GroundingStatus.UNKNOWN,
                confidence_score=0.0,
                citations=[],
                missing_information_notes="Specific standard number or BIS service required.",
                deterministic_fallback_used=True,
                regulatory_conclusion="NONE",
            )

        # 2.5. Intent: BIS Consumer Assistance (Milestone M25.4C)
        if intent == OrchestratorIntent.CONSUMER_ASSISTANCE:
            NON_ISSUANCE_DISCLAIMER = (
                "\n\n*General Guidance Disclaimer: Zyntrix is an informational compliance tool and does not issue BIS licenses, registrations, or official certifications. All certifications and consumer verifications are administered exclusively by the Bureau of Indian Standards (BIS) through official government portals (Manakonline / crsbis.in / BIS CARE app).*"
            )

            # 1. Intercept Unsupported Consumer Assumptions / False Guarantees
            unsupported_claim = verified_knowledge_selector.check_unsupported_consumer_claim(sanitized_query)
            if unsupported_claim:
                citations = []
                if unsupported_claim["claim_type"] == "UNOFFICIAL_COMPLAINT_CHANNEL":
                    citations.append(
                        CitationItem(
                            standard_number="BIS Rules 2018",
                            clause_number="Rule 30",
                            clause_title="Redressal of Consumer Complaints",
                            source_authority="Bureau of Indian Standards",
                            verified=True,
                        )
                    )
                elif unsupported_claim["claim_type"] == "MONETARY_REFUND_GUARANTEE":
                    citations.append(
                        CitationItem(
                            standard_number="Consumer Protection Act, 2019",
                            clause_number="Section 35",
                            clause_title="Manner in which complaint shall be made",
                            source_authority="Central Consumer Protection Authority",
                            verified=True,
                        )
                    )
                return OrchestratedAIResponse(
                    answer=(
                        f"**Official Consumer Guidance — Clarification on Consumer Rights & Scope**:\n\n"
                        f"{unsupported_claim['explanation']}\n\n"
                        f"- **Governing Framework**: {unsupported_claim['statutory_authority']}"
                        f"{NON_ISSUANCE_DISCLAIMER}"
                    ),
                    intent=intent,
                    grounding_status=GroundingStatus.SUPPORTED,
                    confidence_score=0.98,
                    citations=citations,
                    deterministic_fallback_used=False,
                    regulatory_conclusion="NONE",
                )

            # 2. Check for foreign or unverified non-BIS marks asked in query (e.g. CE mark, FCC mark, UL mark)
            if any(w in q_lower for w in ["ce mark", "fcc mark", "ul mark", "ccc mark", "ukca"]):
                return OrchestratedAIResponse(
                    answer="SOURCE_UNAVAILABLE: The query references a non-BIS / foreign conformity mark (such as CE, FCC, UL, or CCC). The Bureau of Indian Standards oversees Indian Standards (ISI, CRS, Hallmark). Verified BIS consumer procedures are not applicable to foreign certification marks.",
                    intent=intent,
                    grounding_status=GroundingStatus.NOT_IN_KNOWLEDGE_BASE,
                    confidence_score=0.0,
                    citations=[],
                    deterministic_fallback_used=True,
                    regulatory_conclusion="NONE",
                )

            # 3. Match Verified Consumer Service Topic
            topic_data = verified_knowledge_selector.match_consumer_query_topic(sanitized_query)
            if topic_data:
                topic_id = topic_data["topic"]
                title = topic_data["title"]
                instructions = topic_data["instructions"]
                portal = topic_data["official_portal"]
                provenance = topic_data["statutory_provenance"]

                answer = (
                    f"**BIS Consumer Assistance — {title}**\n\n"
                    f"{instructions}\n\n"
                    f"- **Official Portal / Channel**: {portal}\n"
                    f"- **Statutory Source**: {provenance}"
                    f"{NON_ISSUANCE_DISCLAIMER}"
                )

                citations = []
                if topic_id in ("MARK_VERIFICATION", "LICENCE_REGISTRATION_CHECK"):
                    citations.append(
                        CitationItem(
                            standard_number="BIS Act 2016",
                            clause_number="Section 15",
                            clause_title="Prohibition to use certain names and marks",
                            source_authority="Bureau of Indian Standards",
                            verified=True,
                        )
                    )
                    citations.append(
                        CitationItem(
                            standard_number="BIS (Conformity Assessment) Regulations, 2018",
                            clause_number="Schedule II",
                            clause_title="Conformity Assessment Schemes",
                            source_authority="Bureau of Indian Standards",
                            verified=True,
                        )
                    )
                elif topic_id == "CONSUMER_COMPLAINT":
                    citations.append(
                        CitationItem(
                            standard_number="BIS Rules 2018",
                            clause_number="Rule 30",
                            clause_title="Redressal of Consumer Complaints",
                            source_authority="Bureau of Indian Standards",
                            verified=True,
                        )
                    )
                    citations.append(
                        CitationItem(
                            standard_number="BIS Act 2016",
                            clause_number="Section 30",
                            clause_title="Investigation of Complaints",
                            source_authority="Bureau of Indian Standards",
                            verified=True,
                        )
                    )
                elif topic_id == "SUSPECTED_NON_CONFORMING_PRODUCT":
                    citations.append(
                        CitationItem(
                            standard_number="BIS Act 2016",
                            clause_number="Section 28",
                            clause_title="Power of Search and Seizure",
                            source_authority="Bureau of Indian Standards",
                            verified=True,
                        )
                    )
                    citations.append(
                        CitationItem(
                            standard_number="BIS Act 2016",
                            clause_number="Section 30",
                            clause_title="Investigation of Complaints",
                            source_authority="Bureau of Indian Standards",
                            verified=True,
                        )
                    )
                elif topic_id == "BIS_MARK_SIGNIFICANCE":
                    citations.append(
                        CitationItem(
                            standard_number="BIS Act 2016",
                            clause_number="Section 13",
                            clause_title="Grant of Licence and Certificate of Conformity",
                            source_authority="Bureau of Indian Standards",
                            verified=True,
                        )
                    )
                    citations.append(
                        CitationItem(
                            standard_number="BIS Act 2016",
                            clause_number="Section 14",
                            clause_title="Hallmarking of Precious Metals",
                            source_authority="Bureau of Indian Standards",
                            verified=True,
                        )
                    )

                return OrchestratedAIResponse(
                    answer=answer,
                    intent=intent,
                    grounding_status=GroundingStatus.SUPPORTED,
                    confidence_score=0.98,
                    citations=citations,
                    deterministic_fallback_used=False,
                    regulatory_conclusion="NONE",
                )

            # Fallback for unclassified consumer assistance query
            return OrchestratedAIResponse(
                answer="SOURCE_UNAVAILABLE / MORE_INFORMATION_REQUIRED: The query does not match any recognized official BIS consumer service or verification procedure. Available verified procedures include: BIS/ISI mark verification, licence status directory search, consumer complaint redressal under Rule 30, and reporting suspected non-conforming products." + NON_ISSUANCE_DISCLAIMER,
                intent=intent,
                grounding_status=GroundingStatus.NOT_IN_KNOWLEDGE_BASE,
                confidence_score=0.0,
                citations=[],
                missing_information_notes="Specific consumer query (e.g. mark verification, licence check, complaint procedure) required.",
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
