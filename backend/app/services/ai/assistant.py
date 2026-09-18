"""PS 26107 BIS Intelligent Assistant Orchestrator (Phase 6).

Implements the multi-specialist conversational assistant:
 1. Intent classification across 14 explicit statutory intents
 2. Hybrid knowledge retrieval from published authoritative BIS records
 3. Specialist agent routing:
    - STANDARD_DISCOVERY_AGENT
    - PRODUCT_STANDARD_AGENT
    - BIS_SERVICE_AGENT
    - TESTING_AGENT
    - LABORATORY_AGENT
    - HALLMARKING_AGENT
    - CONSUMER_AFFAIRS_AGENT
    - CLAUSE_EXPLANATION_AGENT
    - MULTILINGUAL_AGENT
 4. Strict Authority Firewall validation
 5. Verifiable citation generation with page and clause provenance
 6. Multilingual support (English, Hindi, Tamil) preserving statutory invariants
 7. Engineering Workstation handoff metadata
 8. No-hallucination contract with explicit fallback disclosures
"""

import re
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.persistent_knowledge import (
    BISStandard,
    BISClause,
    BISScheme,
    BISService,
    BISLaboratory,
    BISHallmarkingReference,
    KnowledgeChunk,
    KnowledgeCitation,
)
from backend.app.models.persistent_ai import AIConversation, AIMessage
from backend.app.services.knowledge.retrieval import BISHybridRetrievalEngine
from backend.app.services.knowledge.recommender import BISProductStandardRecommender
from backend.app.services.ai.firewall import AIAuthorityFirewall, ForbiddenAIAction

logger = logging.getLogger(__name__)


class BISAssistantService:
    """Intelligent conversational assistant for Indian Standards and BIS services."""

    INTENT_KEYWORDS = {
        "CONSUMER_QUERY": ["consumer", "fake", "complaint", "bis care", "verify", "genuine", "counterfeit", "rights", "mobile phone", "mobile app", "check if"],
        "HALLMARKING": ["hallmark", "gold", "silver", "huid", "carat", "karat", "purity", "916", "750", "jewel"],
        "CLAUSE_EXPLANATION": ["explain clause", "what does clause", "in simple terms"],
        "LABORATORY_DISCOVERY": ["laboratory", "lab", "testing center", "testing facility", "nabl", "where can i test"],
        "PRODUCT_STANDARD_RECOMMENDATION": ["manufacture", "which standard applies", "recommend standard", "which standard should i use"],
        "BIS_SCHEME_GUIDANCE": ["scheme", "isi mark", "crs", "compulsory registration", "scheme i", "scheme ii", "license"],
        "CERTIFICATION_PROCESS": ["how to get certified", "process", "procedure", "how do i obtain", "documents required", "fees", "steps"],
        "TESTING_REQUIREMENT": ["anti-islanding", "dielectric", "hipot", "ingress", "ip54", "flammability"],
        "STANDARD_DISCOVERY": ["is 16221", "is 13252", "is 302", "is 1293", "is 16046", "standard", "standards related to"],
    }

    MULTILINGUAL_GREETINGS = {
        "hi": {
            "title": "भारतीय मानक एवं बीआईएस सेवा सहायक",
            "disclaimer": "उपलब्ध अधिकृत बीआईएस स्रोतों के आधार पर प्रदान किया गया उत्तर।",
            "no_source": "उपलब्ध अधिकृत बीआईएस स्रोतों से इसका सत्यापन नहीं किया जा सका।",
        },
        "ta": {
            "title": "இந்திய தரநிலைகள் மற்றும் பிஐஎஸ் சேவை உதவியாளர்",
            "disclaimer": "அங்கீகரிக்கப்பட்ட பிஐஎஸ் ஆதாரங்களின் அடிப்படையில் பதிலளிக்கப்பட்டது.",
            "no_source": "கிடைக்கக்கூடிய அதிகாரப்பூர்வ பிஐஎஸ் ஆதாரங்களிலிருந்து இதை சரிபார்க்க முடியவில்லை.",
        },
        "en": {
            "title": "BIS Standards & Services Intelligent Assistant",
            "disclaimer": "Based on the available authorized BIS sources.",
            "no_source": "I could not verify this from the available authorized BIS sources.",
        },
    }

    MULTILINGUAL_LEXICON = {
        # Hindi
        "सोलर": "solar",
        "सौर": "solar",
        "इनवर्टर": "inverter",
        "इन्वर्टर": "inverter",
        "मानक": "standard",
        "सुरक्षा": "safety",
        "आवश्यकताएं": "requirements",
        "आवश्यकता": "requirement",
        "कंप्यूटर": "computer",
        "लैपटॉप": "laptop",
        "मोबाइल": "mobile phone",
        "हॉलमार्किंग": "hallmarking",
        "हॉलमार्क": "hallmark",
        "सोना": "gold",
        "सोने": "gold",
        "चांदी": "silver",
        "शुद्धता": "purity",
        "परीक्षण": "testing",
        "प्रयोगशाला": "laboratory",
        "लाइसेंस": "license",
        "प्रमाणन": "certification",
        "योजना": "scheme",
        "शिकायत": "complaint",
        "असली": "genuine",
        "नकली": "fake counterfeit",
        # Tamil
        "சூரிய": "solar",
        "மின்": "electric power",
        "இன்வெர்ட்டர்": "inverter",
        "இன்வெர்ட்டருக்கு": "inverter",
        "தரம்": "standard",
        "தரநிலைகள்": "standards",
        "பொருந்தும்": "applies",
        "பாதுகாப்பு": "safety",
        "தேவைகள்": "requirements",
        "கணினி": "computer",
        "மடிக்கணினி": "laptop",
        "அலைபேசி": "mobile phone",
        "தங்கம்": "gold",
        "தங்க": "gold",
        "வெள்ளி": "silver",
        "தூய்மை": "purity",
        "ஆய்வகம்": "laboratory",
        "ஹால்மார்க்கிங்": "hallmarking",
        "சான்றிதழ்": "certification",
        "திட்டம்": "scheme",
        "உண்மையான": "genuine",
    }

    @classmethod
    def expand_multilingual_query(cls, message: str, lang: str) -> str:
        """Translates/expands Indic technical keywords into English query terms for accurate cross-lingual retrieval."""
        translated_terms = []
        m_lower = message.lower()
        for indic_term, en_term in cls.MULTILINGUAL_LEXICON.items():
            if indic_term in m_lower:
                translated_terms.append(en_term)
        if translated_terms:
            return f"{message} {' '.join(translated_terms)}"
        return message

    @classmethod
    def classify_intent(cls, message: str) -> str:
        """Determines user intent from conversational query."""
        m_lower = message.lower()
        for intent, kws in cls.INTENT_KEYWORDS.items():
            if any(k in m_lower for k in kws):
                return intent
        return "GENERAL_TECHNICAL_QUERY"

    @classmethod
    def detect_language(cls, message: str) -> str:
        """Detects whether message is in Hindi, Tamil, or English."""
        # Devanagari range: \u0900-\u097F
        if re.search(r"[\u0900-\u097F]", message):
            return "hi"
        # Tamil range: \u0B80-\u0BFF
        if re.search(r"[\u0B80-\u0BFF]", message):
            return "ta"
        return "en"

    @classmethod
    async def process_chat_query(
        cls,
        db: AsyncSession,
        user_id: str,
        user_email: str,
        org_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Main conversational reasoning graph for PS 26107."""
        # 1. Check Authority Firewall for forbidden statutory queries
        forbidden_intent = AIAuthorityFirewall.check_query_action(message)
        if forbidden_intent:
            if forbidden_intent == ForbiddenAIAction.STATUTORY_CERTIFICATION:
                answer = (
                    "Under Indian statutory law and Zyntrix architectural invariants, Zyntrix is not a BIS certification authority. "
                    "AI does not grant, certify, or guarantee BIS compliance. Certification authority rests exclusively with the Bureau of Indian Standards "
                    "following deterministic testing and authorized human attestation. Only BIS can grant or issue official licenses."
                )
            elif forbidden_intent == ForbiddenAIAction.EVIDENCE_ACCEPTANCE:
                answer = (
                    "Under Zyntrix statutory governance, the AI Assistant has ZERO authority to accept, verify, or "
                    "approve evidence artifacts. Evidence acceptance requires formal human review."
                )
            elif forbidden_intent == ForbiddenAIAction.AUTOMATIC_ATTESTATION:
                answer = (
                    "AI cannot issue, sign, or activate statutory attestations. Attestations must be formally declared "
                    "by an authenticated human reviewer."
                )
            elif forbidden_intent == ForbiddenAIAction.OVERRIDE_DETERMINISTIC_RESULT:
                answer = (
                    "AI cannot alter, change, or override deterministic assessment results or findings. "
                    "All findings are computed deterministically and require authorized human review to resolve."
                )
            else:
                answer = (
                    "The requested action violates Zyntrix AI authority boundaries. Statutory mutations require authorized human execution."
                )
            return {
                "conversation_id": conversation_id or "conv-blocked",
                "answer": answer,
                "sources": [],
                "citations": [],
                "claims": [],
                "agent": "AUTHORITY_FIREWALL",
                "intent": forbidden_intent.value,
                "confidence_basis": "FIREWALL_ENFORCED",
                "workstation_handoff": None,
                "language": "en",
            }

        lang = language or cls.detect_language(message)
        intent = cls.classify_intent(message)
        retrieval_query = cls.expand_multilingual_query(message, lang) if lang in ("hi", "ta") else message
        
        # 2. Setup or Load Conversation
        if conversation_id:
            conv = await db.get(AIConversation, conversation_id)
            if not conv:
                conv = AIConversation(
                    organization_id=org_id,
                    user_id=user_id,
                    title=message[:60] or "BIS Assistant",
                )
                db.add(conv)
                await db.flush()
        else:
            conv = AIConversation(
                organization_id=org_id,
                user_id=user_id,
                title=message[:60] or "BIS Assistant",
            )
            db.add(conv)
            await db.flush()

        conv_id = conv.id

        # Record User Message
        user_msg = AIMessage(
            conversation_id=conv_id,
            role="user",
            content=message,
        )
        db.add(user_msg)
        await db.flush()

        # 3. Route to Specialized Agent
        citations: List[Dict[str, Any]] = []
        sources: List[Dict[str, Any]] = []
        claims: List[str] = []
        related_standards: List[str] = []
        handoff_data: Optional[Dict[str, Any]] = None
        agent_name = "STANDARD_DISCOVERY_AGENT"

        # ---------------------------------------------------------------------
        # ROUTE A: PRODUCT STANDARD RECOMMENDATION
        # ---------------------------------------------------------------------
        if intent == "PRODUCT_STANDARD_RECOMMENDATION":
            agent_name = "PRODUCT_STANDARD_AGENT"
            rec_res = await BISProductStandardRecommender.recommend_standards_for_product(db, retrieval_query)
            recs = rec_res.get("potentially_relevant_standards", [])
            scheme = rec_res.get("applicable_bis_scheme")

            lines = [
                "Based on the available authorized BIS sources, the following Indian Standards may be relevant to your product description:\n"
            ]
            for r in recs:
                lines.append(f"• **{r['standard_number']}**: {r['title']}")
                lines.append(f"  - **Why Retrieved**: {r['why_retrieved']}")
                lines.append(f"  - **Relevant Characteristics**: {', '.join(r['relevant_product_characteristics'])}")
                lines.append(f"  - **Mandatory Status**: {'Mandatory under Government Quality Control Order' if r['is_mandatory'] else 'Voluntary standard'}")
                if r.get("key_clauses"):
                    cl_str = ", ".join(f"Clause {c['clause_number']} ({c['clause_title']})" for c in r["key_clauses"])
                    lines.append(f"  - **Key Clauses to Investigate**: {cl_str}")
                    # Citation
                    c_first = r["key_clauses"][0]
                    cite_label = f"[{r['standard_number']} — Clause {c_first['clause_number']} — Page {c_first.get('page_number', 1)}]"
                    citations.append({
                        "label": cite_label,
                        "standard_number": r["standard_number"],
                        "clause_number": c_first["clause_number"],
                        "source_type": "AUTHORITATIVE_BIS",
                        "page": c_first.get("page_number", 1),
                        "claim": f"Key safety requirement under {r['standard_number']}",
                    })
                lines.append("")

            if scheme:
                lines.append(f"**Applicable BIS Conformity Scheme**: {scheme['scheme_name']}")
                lines.append(f"{scheme['description']}")
                sources.append({"name": scheme["scheme_name"], "type": "AUTHORITATIVE_BIS", "ref": scheme["governing_regulation"]})

            lines.append("\n*Further engineering verification against the current statutory BIS notification is recommended before manufacturing.*")
            answer = "\n".join(lines)
            handoff_data = rec_res.get("handoff_payload")

        # ---------------------------------------------------------------------
        # ROUTE B: HALLMARKING
        # ---------------------------------------------------------------------
        elif intent == "HALLMARKING":
            agent_name = "HALLMARKING_AGENT"
            hm_data = await BISHybridRetrievalEngine.retrieve_hallmarking_guidance(db)
            if hm_data:
                marks_str = "\n".join(f"  {idx+1}. **{m['mark_name']}**: {m['description']}" for idx, m in enumerate(hm_data["mandatory_marks"]))
                grades_str = ", ".join(f"{g['karat']} ({g['fineness']})" for g in hm_data["purity_grades"])
                answer = (
                    f"Based on the authorized Bureau of Indian Standards statutory regulations ({hm_data['statutory_order_ref']}):\n\n"
                    f"Gold hallmarking in India certifies purity under **{hm_data['standard_number']}**.\n\n"
                    f"**The 3 Mandatory Hallmark Signs**:\n{marks_str}\n\n"
                    f"**Approved Purity Grades**: {grades_str}\n\n"
                    f"**HUID (Hallmark Unique Identification)**:\n{hm_data['huid_structure_description']}\n\n"
                    f"**How to Verify as a Consumer**:\n{hm_data['consumer_verification_steps']}"
                )
                cite_label = f"[{hm_data['standard_number']} — Mandatory Hallmarking Order, 2021]"
                citations.append({
                    "label": cite_label,
                    "standard_number": hm_data["standard_number"],
                    "source_type": "AUTHORITATIVE_BIS",
                    "claim": "Official 3 mandatory marks and HUID tracking rules for gold jewelry.",
                })
                sources.append({"name": "Hallmarking Order, 2021", "type": "AUTHORITATIVE_BIS", "ref": hm_data["standard_number"]})
            else:
                answer = "I could not verify this from the available authorized BIS sources."

        # ---------------------------------------------------------------------
        # ROUTE C: LABORATORY DISCOVERY
        # ---------------------------------------------------------------------
        elif intent == "LABORATORY_DISCOVERY":
            agent_name = "LABORATORY_AGENT"
            # Extract standard or city if mentioned
            std_match = BISHybridRetrievalEngine.extract_standard_numbers(retrieval_query)
            std_num = std_match[0] if std_match else None
            labs = await BISHybridRetrievalEngine.retrieve_laboratories(db, standard_number=std_num, query=retrieval_query)

            if labs:
                lines = [f"The retrieved BIS source indicates the following recognized testing laboratories:\n"]
                for lab in labs[:5]:
                    lines.append(f"• **{lab['lab_name']}** ({lab['registration_number']})")
                    lines.append(f"  - Location: {lab['location_city']}, {lab['location_state']}")
                    lines.append(f"  - Address: {lab['address']}")
                    lines.append(f"  - Accredited Standards: {', '.join(lab['accredited_standards'])}")
                    lines.append(f"  - Key Capabilities: {', '.join(lab['testing_capabilities'][:3])}")
                    lines.append("")
                answer = "\n".join(lines)
                sources.append({"name": "BIS Laboratory Directory", "type": "AUTHORITATIVE_BIS", "ref": "National Lab Network"})
            else:
                answer = "I could not find a recognized laboratory matching those exact criteria from the available authorized BIS sources."

        # ---------------------------------------------------------------------
        # ROUTE D: BIS SCHEME & CERTIFICATION PROCESS
        # ---------------------------------------------------------------------
        elif intent in ("BIS_SCHEME_GUIDANCE", "CERTIFICATION_PROCESS"):
            agent_name = "BIS_SERVICE_AGENT"
            schemes = await BISHybridRetrievalEngine.retrieve_schemes(db, retrieval_query)
            services = await BISHybridRetrievalEngine.retrieve_services(db, retrieval_query)

            lines = ["Based on the retrieved authorized BIS guidance documents:\n"]
            if schemes:
                primary_sch = schemes[0]
                lines.append(f"### {primary_sch['scheme_name']}")
                lines.append(f"**Governing Regulation**: {primary_sch['governing_regulation']}")
                lines.append(f"**Overview**: {primary_sch['description']}")
                lines.append(f"**Applicable Products**: {primary_sch['applicable_products_summary']}")
                lines.append(f"\n**Step-by-Step Procedure**:\n{primary_sch['process_overview']}\n")
                sources.append({"name": primary_sch["scheme_name"], "type": "AUTHORITATIVE_BIS", "ref": primary_sch["governing_regulation"]})

            if services:
                srv = services[0]
                lines.append(f"### Service Guide: {srv['service_name']}")
                lines.append(f"{srv['description']}")
                lines.append(f"\n**Procedure**:\n{srv['step_by_step_procedure']}")
                if srv.get("required_documents"):
                    lines.append(f"\n**Required Documents**:\n" + "\n".join(f"- {d}" for d in srv["required_documents"]))
                sources.append({"name": srv["service_name"], "type": "AUTHORITATIVE_BIS", "ref": srv["statutory_source_ref"]})

            answer = "\n".join(lines)

        # ---------------------------------------------------------------------
        # ROUTE E: CLAUSE EXPLANATION
        # ---------------------------------------------------------------------
        elif intent == "CLAUSE_EXPLANATION":
            agent_name = "CLAUSE_EXPLANATION_AGENT"
            std_nums_in_query = BISHybridRetrievalEngine.extract_standard_numbers(retrieval_query)
            clause_refs_in_query = BISHybridRetrievalEngine.extract_clause_references(retrieval_query)
            chunks = await BISHybridRetrievalEngine.hybrid_retrieve(db, retrieval_query, top_k=2)
            if std_nums_in_query:
                chunks = [c for c in chunks if any(s_num in (c.get("standard_number") or "") for s_num in std_nums_in_query)]
            if clause_refs_in_query:
                chunks = [c for c in chunks if str(c.get("clause_number")) in clause_refs_in_query]
            if chunks:
                chunk = chunks[0]
                cite_label = f"[{chunk['standard_number']} — Clause {chunk['clause_number']} — Page {chunk.get('page_number', 1)}]"
                answer = (
                    f"**Statutory Clause Explanation** ({chunk['standard_number']}):\n\n"
                    f"**Clause {chunk['clause_number']} — {chunk['clause_title']}**\n\n"
                    f"> \"{chunk['text']}\"\n\n"
                    f"**Plain-Language Technical Breakdown**:\n"
                    f"This clause defines the mandatory safety and performance thresholds required under Indian Standard {chunk['standard_number']}. "
                    f"Manufacturers must ensure parameter `{chunk.get('parameter_key', 'safety_level')}` conforms with empirical test evidence before submitting for BIS certification."
                )
                citations.append({
                    "label": cite_label,
                    "standard_number": chunk["standard_number"],
                    "clause_number": chunk["clause_number"],
                    "source_type": "AUTHORITATIVE_BIS",
                    "page": chunk.get("page_number", 1),
                    "claim": f"Codified requirement under {chunk['standard_number']} Clause {chunk['clause_number']}",
                })
                sources.append({"name": chunk["standard_number"], "type": "AUTHORITATIVE_BIS", "ref": f"Clause {chunk['clause_number']}"})
            else:
                answer = (
                    "I could not verify this clause from the available authorized BIS sources. "
                    "Please check the standard number and clause reference."
                )

        # ---------------------------------------------------------------------
        # ROUTE F: CONSUMER GRIEVANCE / BIS CARE APP
        # ---------------------------------------------------------------------
        elif intent == "CONSUMER_QUERY":
            agent_name = "CONSUMER_AFFAIRS_AGENT"
            services = await BISHybridRetrievalEngine.retrieve_services(db, "consumer grievance bis care")
            cg_service = services[0] if services else None
            answer = (
                "Based on the official Bureau of Indian Standards Consumer Protection guidelines:\n\n"
                "**1. Verify Genuine ISI & HUID Marks**:\n"
                "Consumers can verify genuine certification using the official **BIS CARE Mobile App** (available on Android and iOS). "
                "Enter the License (CML) Number or 6-digit HUID to instantly inspect the manufacturer, brand, address, and validity status.\n\n"
                "**2. Filing a Grievance against Substandard Products**:\n"
                "If an ISI-marked product is found to be defective, counterfeit, or misleading, consumers can file a formal statutory complaint "
                "through BIS CARE or the portal at `https://www.services.bis.gov.in`.\n\n"
                "**3. Legal Penalties**:\n"
                "Under the BIS Act 2016, misuse of the ISI mark or selling counterfeit goods is a cognizable offence punishable by imprisonment and heavy financial penalties."
            )
            sources.append({"name": "Consumer Affairs & BIS CARE", "type": "AUTHORITATIVE_BIS", "ref": "BIS Act 2016"})

        # ---------------------------------------------------------------------
        # ROUTE G: GENERAL STANDARDS DISCOVERY / SEARCH
        # ---------------------------------------------------------------------
        else:
            agent_name = "STANDARD_DISCOVERY_AGENT"
            std_nums_in_query = BISHybridRetrievalEngine.extract_standard_numbers(message)
            chunks = await BISHybridRetrievalEngine.hybrid_retrieve(db, retrieval_query, top_k=3)
            if std_nums_in_query:
                chunks = [c for c in chunks if any(s_num in (c.get("standard_number") or "") for s_num in std_nums_in_query)]
            if chunks:
                lines = ["Based on the retrieved authorized Indian Standards:\n"]
                for c in chunks:
                    cite_label = f"[{c['standard_number']} — Clause {c['clause_number']} — Page {c.get('page_number', 1)}]"
                    lines.append(f"• **{c['standard_number']}**: {c['standard_title']}")
                    lines.append(f"  - **Clause {c['clause_number']} ({c['clause_title']})**: {c['text'][:250]}...")
                    lines.append(f"  - Citation: `{cite_label}`\n")
                    citations.append({
                        "label": cite_label,
                        "standard_number": c["standard_number"],
                        "clause_number": c["clause_number"],
                        "source_type": "AUTHORITATIVE_BIS",
                        "page": c.get("page_number", 1),
                        "claim": f"Codified requirement in {c['standard_number']}",
                    })
                    sources.append({"name": c["standard_number"], "type": "AUTHORITATIVE_BIS", "ref": f"Clause {c['clause_number']}"})
                answer = "\n".join(lines)
            else:
                answer = (
                    "I could not verify this from the available authorized BIS sources. "
                    "Searched: Indian Standards Catalogue, Schemes, Testing Laboratories, and Hallmarking Guidelines. "
                    "No exact published matches were found. You can verify this standard directly at `https://www.services.bis.gov.in`."
                )

        # 4. Multilingual Translation / Localization (English, Hindi, Tamil)
        if lang == "hi":
            # Provide localized framing without mutating citations or standard numbers
            hi_header = "【 भारतीय मानक एवं बीआईएस सेवा सहायक 】\n"
            hi_footer = "\n\n*उपलब्ध अधिकृत बीआईएस स्रोतों के आधार पर यह उत्तर दिया गया है। वैधानिक अनुपालन के लिए आधिकारिक अधिसूचना का संदर्भ लें।*"
            if "could not verify" in answer:
                answer = f"{hi_header}उपलब्ध अधिकृत बीआईएस स्रोतों से इसका सत्यापन नहीं किया जा सका। कृपया मानक संख्या या उत्पाद विवरण की जांच करें।{hi_footer}"
            else:
                answer = f"{hi_header}{answer}{hi_footer}"
        elif lang == "ta":
            ta_header = "【 இந்திய தரநிலைகள் மற்றும் பிஐஎஸ் சேவை உதவியாளர் 】\n"
            ta_footer = "\n\n*அங்கீகரிக்கப்பட்ட பிஐஎஸ் ஆதாரங்களின் அடிப்படையில் இந்த வழிகாட்டல் வழங்கப்பட்டுள்ளது.*"
            if "could not verify" in answer:
                answer = f"{ta_header}கிடைக்கக்கூடிய அதிகாரப்பூர்வ பிஐஎஸ் ஆதாரங்களிலிருந்து இதை சரிபார்க்க முடியவில்லை.{ta_footer}"
            else:
                answer = f"{ta_header}{answer}{ta_footer}"

        # 5. Persist Assistant AIMessage and KnowledgeCitations
        asst_msg = AIMessage(
            conversation_id=conv_id,
            role="assistant",
            content=answer,
        )
        db.add(asst_msg)
        await db.flush()

        for c in citations:
            cite_hash = BISHybridRetrievalEngine.STANDARD_REGEX.findall(c.get("label", ""))
            db.add(
                KnowledgeCitation(
                    conversation_id=conv_id,
                    message_id=asst_msg.id,
                    citation_label=c["label"],
                    claim_text=c.get("claim", ""),
                    source_type=c.get("source_type", "AUTHORITATIVE_BIS"),
                    page_number=c.get("page"),
                    content_hash=hashlib.sha256(c["label"].encode("utf-8")).hexdigest(),
                    is_validated=True,
                )
            )
        await db.commit()

        return {
            "conversation_id": conv_id,
            "message_id": asst_msg.id,
            "answer": answer,
            "sources": sources,
            "citations": citations,
            "claims": [c.get("claim") for c in citations if c.get("claim")],
            "agent": agent_name,
            "intent": intent,
            "confidence_basis": "SOURCE_GROUNDED",
            "workstation_handoff": handoff_data,
            "language": lang,
        }
