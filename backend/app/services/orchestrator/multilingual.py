"""Layer 3: Multilingual BIS Interaction Engine (Milestone M25.4F).

Provides multilingual input normalization and grounded output translation for the
Layer 3 AI Orchestrator while preserving all canonical technical content in its
original, unmodified form:
- IS numbers (e.g., IS 302-2-201:2008, IS 17526:2021, IS 4151:2020, IS 1417:2016, IS 13252)
- Standard editions and revisions
- Clause numbers (e.g., Clause 8, Clause 13, Clause 19.1, Clause 22.101)
- QCO references (e.g., Quality Control Orders)
- Legal/regulatory references (e.g., BIS Act 2016, Regulation 18, Scheme I, Scheme II)
- Numerical values, units, tolerances and ranges (e.g., <= 0.75 mA, 65 deg C, 22K916)
- Laboratory names and identifiers (e.g., BIS Central Laboratory, Sahibabad, BIS-CL)
- Evidence/provenance metadata (e.g., https://lims.bis.gov.in)
- Compliance states (regulatory_conclusion="NONE", LLM compliance authority = 0.0%)

Cardinal Invariants:
1. Translation NEVER creates, modifies, infers, or normalizes authoritative technical facts.
2. Canonical retrieved source remains the authority. Translate only user-facing explanations.
3. Preserve regulatory_conclusion="NONE" unconditionally.
4. LLM compliance authority is exactly 0.0%.
5. Safe abstention on missing, stale, or unverified records.
6. Multilingual prompt-injection defenses intercept adversarial attacks in Indic languages.
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Set
from backend.app.services.orchestrator.schemas import (
    OrchestratedAIResponse,
    OrchestratorIntent,
    GroundingStatus,
    CitationItem,
)
from backend.app.core.logging import logger


# ==============================================================================
# 1. LANGUAGE DETECTION
# ==============================================================================

# Unicode Ranges for Indic Scripts
RE_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
RE_TAMIL = re.compile(r"[\u0B80-\u0BFF]")
RE_TELUGU = re.compile(r"[\u0C00-\u0C7F]")
RE_KANNADA = re.compile(r"[\u0C80-\u0CFF]")
RE_MALAYALAM = re.compile(r"[\u0D00-\u0D7F]")
RE_BENGALI = re.compile(r"[\u0980-\u09FF]")
RE_GUJARATI = re.compile(r"[\u0A80-\u0AFF]")


def detect_language(text: str) -> str:
    """Detect the language of user input text.
    
    Returns ISO 639-1 code ('hi', 'ta', 'te', 'kn', 'ml', 'bn', 'gu', or 'en').
    """
    if not text:
        return "en"
    
    # Check Indic Unicode blocks
    if RE_DEVANAGARI.search(text):
        return "hi"
    if RE_TAMIL.search(text):
        return "ta"
    if RE_TELUGU.search(text):
        return "te"
    if RE_KANNADA.search(text):
        return "kn"
    if RE_MALAYALAM.search(text):
        return "ml"
    if RE_BENGALI.search(text):
        return "bn"
    if RE_GUJARATI.search(text):
        return "gu"
    
    return "en"


# ==============================================================================
# 2. MULTILINGUAL LEXICON & QUERY NORMALIZATION
# ==============================================================================

# Comprehensive Indic-to-English domain mapping for cross-lingual intent routing
INDIC_DOMAIN_LEXICON: Dict[str, str] = {
    # Hindi - Standards & General BIS
    "मानक": "standard indian standard",
    "भारतीय मानक": "indian standard",
    "बीआईएस": "bis bureau of indian standards",
    "मानक क्या है": "what is standard",
    "दायरा": "scope",
    "कवर": "cover",
    "नियम": "regulation rule",
    "गुणवत्ता नियंत्रण": "quality control order qco",
    "क्यूसीओ": "quality control order qco",
    "क्या है": "what is",
    # Hindi - Laboratories & Testing
    "प्रयोगशाला": "laboratory recognized laboratory",
    "प्रयोगशालाएं": "laboratories recognized laboratories",
    "प्रयोगशालाओं": "laboratories",
    "लैब": "lab laboratory",
    "परीक्षण": "testing",
    "जांच": "testing test verify check bis licence",
    "परीक्षण श्रेणी": "testing category",
    "परीक्षण केंद्र": "testing laboratory",
    "मान्यता प्राप्त": "recognized bis-recognized",
    "मान्यता स्थिति": "recognition status laboratory recognition status",
    "मान्यता": "recognition recognized laboratory recognition status",
    "निर्देशिका": "directory laboratory directory",
    "साहिबाबाद": "central laboratory sahibabad bis central laboratory sahibabad bis-cl",
    "मुंबई": "western regional laboratory mumbai bis-wrl",
    "चेन्नई": "southern regional laboratory chennai bis-srl",
    "कोलकाता": "eastern regional laboratory kolkata bis-erl",
    "मोहाली": "northern regional laboratory mohali bis-nrl",
    "लिम्स": "lims lims.bis.gov.in",
    "शुल्क": "fees cost",
    "फीस": "fees cost",
    "बुकिंग": "booking appointment",
    "रैंकिंग": "ranking top rated",
    "सस्ती": "cheapest rank ranking",
    # Hindi - Schemes & Services
    "प्रमाणन योजना": "certification scheme",
    "योजना": "scheme certification scheme",
    "स्कीम": "scheme certification scheme",
    "योजना १": "scheme i",
    "योजना 1": "scheme i",
    "स्कीम १": "scheme i",
    "स्कीम 1": "scheme i",
    "योजना २": "scheme ii",
    "योजना 2": "scheme ii",
    "स्कीम २": "scheme ii",
    "स्कीम 2": "scheme ii",
    "सीआरएस": "crs compulsory registration scheme",
    "सेवाएं": "services bis services",
    "प्रक्रिया": "process procedure",
    "दस्तावेज": "documents required",
    "आवेदन": "application apply",
    "ऑफ़लाइन": "offline paper submission",
    # Hindi - Hallmarking
    "हॉलमार्किंग": "hallmarking bis hallmarking",
    "हॉलमार्क": "hallmark gold hallmark",
    "सोना": "gold gold hallmark 22k916",
    "सोने": "gold gold hallmark 22k916",
    "चांदी": "silver silver hallmark",
    "शुद्धता": "gold purity purity grade 22k916",
    "शुद्धता श्रेणियां": "gold purity grade 22k916 18k750 14k585 is 1417",
    "एचयूआईडी": "huid verify huid 6-digit huid",
    "आभूषण": "jewellery jewelry gold hallmark",
    "आभूषणों": "jewellery jewelry gold hallmark",
    "ज्वेलर्स": "jeweller registration",
    "मुआवजा": "compensation",
    # Hindi - Consumer Assistance
    "शिकायत": "complaint consumer complaint file a complaint",
    "शिकायत कहां दर्ज करें": "file a complaint raise a bis consumer complaint",
    "उपभोक्ता": "consumer assistance",
    "नकली": "fake counterfeit mark fake isi fake mark",
    "जाली": "counterfeit fake fake mark",
    "असली": "genuine verify mark",
    "लाइसेंस": "license check bis license verify licence",
    "लाइसेंस संख्या": "cml number license status",
    "सत्यापन": "verification verify check bis mark",
    "जांच कैसे करें": "verify check bis mark how to verify",
    "बीआईएस केयर": "bis care app bis care",
    "खराब उत्पाद": "substandard defective product",
    "घटिया उत्पाद": "substandard product",
    # Hindi - Products
    "इमर्शन हीटर": "immersion water heater",
    "गीज़र": "water heater",
    "पानी गर्म करने वाला": "water heater",
    "हेलमेट": "helmet protective helmet",
    "थर्मस": "flask vacuum flask",
    "बिजली": "electrical electric",
    "विद्युत": "electrical electric",

    # Tamil - Standards & General BIS
    "தரநிலை": "standard indian standard",
    "தரநிலைகள்": "standards indian standards",
    "தரம்": "standard quality",
    "இந்திய தரநிலைகள்": "indian standards",
    "பிஐஎஸ்": "bis bureau of indian standards",
    "வரம்பு": "scope",
    "தரக்கட்டுப்பாடு": "quality control order qco",
    "என்ன": "what is",
    # Tamil - Laboratories & Testing
    "ஆய்வகம்": "laboratory recognized laboratory",
    "ஆய்வக": "laboratory recognized laboratory",
    "ஆய்வகங்கள்": "laboratories recognized laboratories",
    "ஆய்வகத்தின்": "laboratory recognized laboratory recognition status",
    "சோதனைக்கூடம்": "testing laboratory",
    "சோதனை": "testing testing required",
    "பரிசோதனை": "testing test",
    "சோதனை வகை": "testing category",
    "அங்கீகரிக்கப்பட்ட": "recognized bis-recognized",
    "அங்கீகாரம்": "recognition recognized laboratory recognition status",
    "அங்கீகார நிலை": "laboratory recognition status recognition status",
    "அடைவு": "directory laboratory directory",
    "சாகிபாபாத்": "central laboratory sahibabad bis central laboratory sahibabad bis-cl",
    "மத்திய ஆய்வகம்": "central laboratory sahibabad bis central laboratory sahibabad bis-cl",
    "மும்பை": "western regional laboratory mumbai bis-wrl",
    "சென்னை": "southern regional laboratory chennai bis-srl",
    "கொல்கத்தா": "eastern regional laboratory kolkata bis-erl",
    "மொகாலி": "northern regional laboratory mohali bis-nrl",
    "கட்டணம்": "fees cost",
    "முன்பதிவு": "booking appointment",
    "தரவரிசை": "ranking top rated",
    "உள்ளதா": "recognition status available",
    # Tamil - Schemes & Services
    "சான்றிதழ் திட்டம்": "certification scheme",
    "திட்டம்": "scheme certification scheme",
    "திட்டம் 1": "scheme i",
    "திட்டம் I": "scheme i",
    "திட்டம் 2": "scheme ii",
    "திட்டம் II": "scheme ii",
    "சேவைகள்": "services bis services",
    "செயல்முறை": "process procedure",
    "நடைமுறை": "procedure process",
    "ஆவணங்கள்": "documents required",
    "விண்ணப்பம்": "application apply",
    # Tamil - Hallmarking
    "ஹால்மார்க்கிங்": "hallmarking bis hallmarking",
    "ஹால்மார்க்": "hallmark gold hallmark",
    "தங்கம்": "gold gold hallmark 22k916",
    "தங்க": "gold gold hallmark 22k916",
    "வெள்ளி": "silver silver hallmark",
    "தூய்மை": "gold purity purity grade 22k916",
    "தூய்மை வரம்புகள்": "gold purity grade 22k916 18k750 14k585 is 1417",
    "ஹச்யுஐடி": "huid verify huid 6-digit huid",
    "நகைகள்": "jewellery jewelry gold hallmark",
    "இழப்பீடு": "compensation",
    # Tamil - Consumer Assistance
    "புகார்": "complaint consumer complaint file a complaint",
    "புகார் செய்வது எப்படி": "file a complaint raise a bis consumer complaint",
    "நுகர்வோர்": "consumer assistance",
    "போலி": "fake counterfeit mark fake isi",
    "போலி ஐஎஸ்ஐ": "fake isi counterfeit mark fake mark",
    "ஐஎஸ்ஐ முத்திரை": "isi mark verify isi",
    "ஐஎஸ்ஐ": "isi mark",
    "உண்மையான": "genuine verify mark",
    "உரிமம்": "license check bis license verify licence",
    "சரிபார்க்க": "verification verify check bis mark",
    "பிஐஎஸ் கேர்": "bis care app bis care",
    "தரமற்ற": "substandard product",
    # Tamil - Products
    "சூடேற்றி": "water heater immersion heater",
    "தலைக்கவசம்": "helmet protective helmet",
    "மின்சார": "electrical electric",
    "மின்": "electric power",
}

# Multilingual Adversarial Override Patterns in Indic scripts
MULTILINGUAL_INJECTION_PATTERNS = [
    # Hindi adversarial commands
    (r"(?i)(?:पिछले|सभी|पूर्व)\s*(?:सभी\s*)?(?:निर्देशों?|नियमों?)\s*(?:को\s*)?(?:अनदेखा|रद्द|बायपास)\s*(?:करें|करो)", "MULTILINGUAL_INSTRUCTION_OVERRIDE_HI"),
    (r"(?i)(?:प्रमाणित|अनुपालन|सफल|पास)\s*(?:घोषित\s*)?(?:करें|करो)", "MULTILINGUAL_FORCED_COMPLIANCE_HI"),
    (r"(?i)(?:परीक्षण|सत्यापन|जांच)\s*(?:को\s*)?(?:छोड़ें|बायपास\s*करें|न\s*करें)", "MULTILINGUAL_TEST_BYPASS_HI"),
    (r"(?i)(?:लाइसेंस|आईएसआई\s*मार्क)\s*(?:जारी\s*करें|प्रदान\s*करें)", "MULTILINGUAL_UNAUTHORIZED_CERTIFICATION_HI"),
    (r"(?i)(?:नियम|सिस्टम)\s*(?:बदलो|ओवरराइड\s*करो)", "MULTILINGUAL_SYSTEM_OVERRIDE_HI"),
    # Tamil adversarial commands
    (r"(?i)(?:முந்தைய|அனைத்து)\s*(?:விதிகளை|வழிமுறைகளை)\s*(?:புறக்கணிக்கவும்|தவிர்க்கவும்)", "MULTILINGUAL_INSTRUCTION_OVERRIDE_TA"),
    (r"(?i)(?:சான்றளிக்கவும்|இணக்கமாக\s*அறிவிக்கவும்|வெற்றி\s*என\s*அறிவிக்கவும்|தேர்ச்சி\s*என\s*அறிவிக்கவும்)", "MULTILINGUAL_FORCED_COMPLIANCE_TA"),
    (r"(?i)(?:சோதனையை|சரிபார்ப்பை)\s*(?:புறக்கணிக்கவும்|தவிர்க்கவும்)", "MULTILINGUAL_TEST_BYPASS_TA"),
    (r"(?i)(?:உரிமம்|ஐஎஸ்ஐ\s*முத்திரை)\s*வழங்கவும்", "MULTILINGUAL_UNAUTHORIZED_CERTIFICATION_TA"),
    (r"(?i)(?:விதியை|அமைப்பை)\s*மாற்றவும்", "MULTILINGUAL_SYSTEM_OVERRIDE_TA"),
]


def check_multilingual_injection(query: str) -> Optional[Tuple[str, str]]:
    """Detect prompt injection attempts written in Indian languages.
    
    Returns (detected_pattern_name, matched_substring) if injection is detected, else None.
    """
    for pattern, name in MULTILINGUAL_INJECTION_PATTERNS:
        match = re.search(pattern, query)
        if match:
            return name, match.group(0)
    return None


def normalize_multilingual_query(query: str) -> str:
    """Expands Indic technical and domain keywords into canonical English terms.
    
    Appends the normalized English equivalents to the query so downstream intent
    classification, knowledge selectors, and entity extractors function seamlessly
    without destroying the original query text.
    """
    if not query:
        return ""
    
    # Transliteration of standard prefix: e.g. "आईएस 4151" or "ஐஎஸ் 4151" -> "IS 4151"
    normalized_q = re.sub(r"(?i)(?:आईएस|आई\.एस\.|ഐഎസ്|ஐஎஸ்)\s*(\d+)", r"IS \1", query)
    
    q_lower = query.lower()
    expanded_terms: List[str] = []
    
    for indic_term, en_terms in INDIC_DOMAIN_LEXICON.items():
        if indic_term in q_lower:
            expanded_terms.append(en_terms)
            
    if expanded_terms:
        # Join unique expanded terms
        unique_en = " ".join(dict.fromkeys(" ".join(expanded_terms).split()))
        return f"{normalized_q} {unique_en}"
    
    return normalized_q


# ==============================================================================
# 3. DETERMINISTIC CANONICAL TOKEN PRESERVATION ENGINE
# ==============================================================================

# Regex definitions for canonical technical elements that MUST NEVER be translated or modified:
CANONICAL_TOKEN_PATTERNS = [
    # 1. Official Indian Standards (e.g. IS 302-2-201:2008, IS 13252 (Part 1):2010, IS 4151:2020)
    re.compile(r"\bIS\s*\d+(?:[-/]\d+)*(?::\d{4})?(?:\s*\([A-Za-z0-9\s]+\)(?::\d{4})?)?\b", re.IGNORECASE),
    # 2. Specific Clause designations (e.g. Clause 8, Clause 13.2, Cl. 19.1, Clause 22.101)
    re.compile(r"\b(?:Clause|Cl\.)\s*\d+(?:\.\d+)*\b", re.IGNORECASE),
    # 3. Statutory & Quality Control Orders
    re.compile(r"\b(?:BIS Act\s*2016|Bureau of Indian Standards Act|Regulation\s*\d+|Section\s*\d+|Quality Control Order|QCO)\b", re.IGNORECASE),
    # 4. Hallmarking purity codes & designations
    re.compile(r"\b(?:24K995|23K958|22K916|20K833|18K750|14K585)\b"),
    # 5. Numerical values with engineering units, tolerances, or comparison operators
    re.compile(r"\b(?:<=|>=|<|>|±)?\s*\d+(?:\.\d+)?\s*(?:mA|A|V|kV|W|kW|deg\s*C|°C|mm|cm|m|kg|g|litres?|L|ml|%|ohms?|k\u03A9|M\u03A9)\b", re.IGNORECASE),
    # 6. Recognized Laboratory names & codes
    re.compile(
        r"\b(?:BIS Central Laboratory, Sahibabad|BIS Central Laboratory|Central Laboratory \(Sahibabad\)|"
        r"Western Regional Laboratory \(Mumbai\)|Western Regional Laboratory|"
        r"Southern Regional Laboratory \(Chennai\)|Southern Regional Laboratory|"
        r"Eastern Regional Laboratory \(Kolkata\)|Eastern Regional Laboratory|"
        r"Northern Regional Laboratory \(Mohali\)|Northern Regional Laboratory|"
        r"Branch Laboratories Network|SAMPLE_STALE_LABORATORY|SAMPLE_UNVERIFIED_THIRD_PARTY|"
        r"BIS-CL|BIS-WRL|BIS-SRL|BIS-ERL|BIS-NRL)\b"
    ),
    # 7. Authoritative portals and URLs
    re.compile(r"https?://[^\s)\]]+"),
    re.compile(r"\b(?:lims\.bis\.gov\.in|services\.bis\.gov\.in|bis\.gov\.in|manakonline\.in)\b", re.IGNORECASE),
    # 8. Identifiers and Mark designations
    re.compile(r"\b(?:CML-\d+|CM/L-\d+|HUID|R-\d{8}|ISI Mark|ISI mark|ISI|BIS CARE)\b"),
    # 9. Invariant Architectural Markers
    re.compile(r"\b(?:OPERATIVE_RECOGNIZED|VERIFIED|UNVERIFIED|VERIFICATION_REQUIRED|EXPIRED|0\.0%|0%)\b"),
]


class CanonicalTokenEngine:
    """Masks and unmasks authoritative technical tokens to guarantee 100% preservation."""

    @classmethod
    def mask_tokens(cls, text: str) -> Tuple[str, Dict[str, str]]:
        """Extracts canonical technical entities and replaces them with invariant placeholders.
        
        Returns:
            masked_text: Text with __CANONICAL_TOKEN_N__ placeholders
            token_map: Mapping from placeholder to original canonical token string
        """
        if not text:
            return "", {}
        
        found_spans: List[Tuple[int, int, str]] = []
        for pattern in CANONICAL_TOKEN_PATTERNS:
            for match in pattern.finditer(text):
                found_spans.append((match.start(), match.end(), match.group(0)))
                
        # Resolve overlapping spans: favor longer spans first
        found_spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
        non_overlapping: List[Tuple[int, int, str]] = []
        last_end = 0
        for start, end, token in found_spans:
            if start >= last_end:
                non_overlapping.append((start, end, token))
                last_end = end
                
        # Build masked text and replacement map
        token_map: Dict[str, str] = {}
        chunks: List[str] = []
        prev_idx = 0
        for idx, (start, end, token) in enumerate(non_overlapping):
            placeholder = f"__CANONICAL_TOKEN_{idx}__"
            token_map[placeholder] = token
            chunks.append(text[prev_idx:start])
            chunks.append(placeholder)
            prev_idx = end
        chunks.append(text[prev_idx:])
        
        masked_text = "".join(chunks)
        return masked_text, token_map

    @classmethod
    def unmask_tokens(cls, masked_text: str, token_map: Dict[str, str]) -> str:
        """Restores exact canonical technical tokens into translated text.
        
        Verifies that every single original token is restored with 100% fidelity.
        """
        unmasked = masked_text
        for placeholder, original_token in token_map.items():
            unmasked = unmasked.replace(placeholder, original_token)
        return unmasked

    @classmethod
    def verify_token_preservation(cls, original_text: str, translated_text: str, token_map: Dict[str, str]) -> bool:
        """Confirms that all extracted canonical tokens from the source exist verbatim in translated text."""
        for placeholder, original_token in token_map.items():
            if original_token not in translated_text:
                logger.warning(f"[CanonicalTokenEngine] Token missing from translation: {original_token}")
                return False
        return True


# ==============================================================================
# 4. EXPLANATORY FRAMING TRANSLATION (HINDI & TAMIL)
# ==============================================================================

# User-facing explanation phrase translations (preserving placeholders)
HINDI_EXPLANATION_MAP = {
    # Section Headers
    "### BIS Recognized Laboratory Directory": "### बीआईएस मान्यता प्राप्त प्रयोगशाला निर्देशिका",
    "### Laboratory Information": "### प्रयोगशाला विवरण",
    "### Testing Scope and Categories": "### परीक्षण दायरा एवं श्रेणियां",
    "### BIS Hallmarking Scheme": "### बीआईएस हॉलमार्किंग योजना",
    "### BIS Consumer Grievance": "### बीआईएस उपभोक्ता शिकायत एवं निवारण",
    "### Consumer Guidance": "### उपभोक्ता मार्गदर्शन",
    "### BIS Certification Scheme": "### बीआईएस प्रमाणन योजना",
    "### Verification Notice": "### सत्यापन सूचना",
    "### Statutory Notice": "### वैधानिक सूचना",
    # Framing Sentences
    "Based on verified BIS authoritative records:": "सत्यापित बीआईएस आधिकारिक अभिलेखों के आधार पर:",
    "Based on the official Bureau of Indian Standards Consumer Protection guidelines:": "भारतीय मानक ब्यूरो के आधिकारिक उपभोक्ता संरक्षण दिशानिर्देशों के अनुसार:",
    "Based on the retrieved authorized BIS guidance documents:": "अधिकृत बीआईएस मार्गदर्शन दस्तावेजों के आधार पर:",
    "According to the official BIS Laboratory Recognition Scheme (LRS):": "आधिकारिक बीआईएस प्रयोगशाला मान्यता योजना (LRS) के अनुसार:",
    "Under the BIS Act 2016:": "बीआईएस अधिनियम 2016 के अंतर्गत:",
    "Under the BIS Act 2016, misuse of the ISI mark or selling counterfeit goods is a cognizable offence:": "बीआईएस अधिनियम 2016 के तहत, आईएसआई मार्क का दुरुपयोग या नकली सामान बेचना एक संज्ञेय अपराध है:",
    "Under Indian statutory law and Zyntrix architectural invariants, Zyntrix has ZERO authority to declare compliance:": "भारतीय वैधानिक कानून और Zyntrix वास्तुकला के अनुसार, Zyntrix के पास अनुपालन घोषित करने का शून्य अधिकार है:",
    # Laboratory Guidance
    "The recognized testing scope covers:": "मान्यता प्राप्त परीक्षण दायरे में शामिल हैं:",
    "Testing Categories:": "परीक्षण श्रेणियां:",
    "Official Source:": "आधिकारिक स्रोत:",
    "Recognition Status:": "मान्यता स्थिति:",
    "Current Recognition Status:": "वर्तमान मान्यता स्थिति:",
    "Verification Status:": "सत्यापन स्थिति:",
    "Provenance Chain:": "प्रमाणिकता श्रृंखला (Provenance Chain):",
    "Record downgraded to VERIFICATION_REQUIRED": "अभिलेख को VERIFICATION_REQUIRED में पदावनत किया गया है",
    "Safe abstention enforced: Authoritative evidence is missing or stale.": "सुरक्षित परहेज (Safe Abstention) लागू: आधिकारिक साक्ष्य अनुपलब्ध या पुराना है।",
    "Safe abstention enforced": "सुरक्षित परहेज (Safe Abstention) लागू",
    "Commercial booking availability, live slots, fees, and rankings cannot be inferred without official BIS publication.": "आधिकारिक बीआईएस प्रकाशन के बिना व्यावसायिक बुकिंग उपलब्धता, शुल्क और रैंकिंग का अनुमान नहीं लगाया जा सकता।",
    "Zyntrix strictly refuses to infer commercial booking availability or rankings.": "Zyntrix व्यावसायिक बुकिंग उपलब्धता या रैंकिंग का अनुमान लगाने से पूरी तरह परहेज करता है।",
    # Consumer & Hallmarking
    "Verify genuine certification using the official BIS CARE Mobile App:": "आधिकारिक BIS CARE मोबाइल ऐप का उपयोग करके वास्तविक प्रमाणन का सत्यापन करें:",
    "Enter the License (CML) Number or 6-digit HUID to inspect validity:": "वैधता की जांच के लिए लाइसेंस (CML) संख्या या 6-अंकीय HUID दर्ज करें:",
    "Filing a Grievance against Substandard Products:": "घटिया या गैर-मानक उत्पादों के खिलाफ शिकायत दर्ज करना:",
    "File a formal complaint through the BIS CARE app or portal:": "BIS CARE ऐप या पोर्टल के माध्यम से औपचारिक शिकायत दर्ज करें:",
    "Hallmarking consists of three mandatory marks:": "हॉलमार्किंग में तीन अनिवार्य चिह्न शामिल होते हैं:",
    "Purity Grades:": "शुद्धता श्रेणियां:",
    "Assaying and Hallmarking Centre (AHC):": "परख एवं हॉलमार्किंग केंद्र (AHC):",
    # Requirement & Clause
    "Mandatory safety and performance requirement under": "के अंतर्गत अनिवार्य सुरक्षा एवं प्रदर्शन आवश्यकता",
    "The leakage current shall not exceed": "रिसाव धारा (leakage current) इससे अधिक नहीं होनी चाहिए",
    "Temperature rise limit:": "तापमान वृद्धि सीमा:",
    "Plain-Language Technical Breakdown:": "सरल भाषा में तकनीकी विवरण:",
    # Safe Abstention & Statutory Phrases
    "SOURCE_UNAVAILABLE: Verified scheme information for": "स्रोत अनुपलब्ध (SOURCE_UNAVAILABLE): सत्यापित योजना विवरण",
    "is not available in the Bureau of Indian Standards verified knowledge base. The system strictly refuses to speculate or invent unverified certification schemes.": "भारतीय मानक ब्यूरो के सत्यापित ज्ञानकोष में उपलब्ध नहीं है। प्रणाली असत्यापित प्रमाणन योजनाओं का अनुमान लगाने से पूर्णतः परहेज करती है।",
    "SOURCE_UNAVAILABLE: Verified laboratory record for": "स्रोत अनुपलब्ध (SOURCE_UNAVAILABLE): सत्यापित प्रयोगशाला अभिलेख",
    "is not available in the official BIS Laboratory Directory. The system strictly refuses to speculate on unverified testing facilities.": "आधिकारिक बीआईएस प्रयोगशाला निर्देशिका में उपलब्ध नहीं है। प्रणाली असत्यापित परीक्षण सुविधाओं पर अनुमान लगाने से इनकार करती है।",
    "is unverified due to missing authoritative source citation and expired recognition status.": "अनुपलब्ध आधिकारिक स्रोत उद्धरण और समाप्त हो चुकी मान्यता स्थिति के कारण असत्यापित है।",
    "Downgraded to VERIFICATION_REQUIRED due to lack of authenticated official BIS Gazette publication.": "प्रमाणीकृत आधिकारिक बीआईएस राजपत्र प्रकाशन के अभाव के कारण VERIFICATION_REQUIRED में पदावनत किया गया।",
    "General Guidance Disclaimer: Zyntrix is an informational compliance tool and does not issue BIS licenses, registrations, or official certifications.": "सामान्य मार्गदर्शन अस्वीकरण: Zyntrix एक सूचनात्मक उपकरण है और यह बीआईएस लाइसेंस या आधिकारिक प्रमाणन जारी नहीं करता है।",
    "General Guidance Disclaimer: Zyntrix is an informational compliance tool and does not conduct laboratory tests, book laboratory appointments, or issue BIS certifications.": "सामान्य मार्गदर्शन अस्वीकरण: Zyntrix एक सूचनात्मक उपकरण है और यह प्रयोगशाला परीक्षण आयोजित नहीं करता है, न ही बीआईएस प्रमाणन जारी करता है।",
    # Invariant Notices & Footers
    "The AI assistant has ZERO authority to declare, override, or certify compliance.": "एआई सहायक के पास अनुपालन घोषित, अधिलेखित या प्रमाणित करने का शून्य (0.0%) अधिकार है।",
    "Under Zyntrix architecture, compliance determinations are strictly computed by the deterministic compliance gate based on verified empirical laboratory evidence.": "Zyntrix वास्तुकला के तहत, अनुपालन निर्धारण केवल सत्यापित प्रयोगशाला साक्ष्यों के आधार पर आधिकारिक बीआईएस द्वारा किया जाता है।",
    "LLM compliance authority is exactly 0%.": "एआई अनुपालन अधिकार बिल्कुल 0% (शून्य) है।",
}

TAMIL_EXPLANATION_MAP = {
    # Section Headers
    "### BIS Recognized Laboratory Directory": "### பிஐஎஸ் அங்கீகரிக்கப்பட்ட ஆய்வக அடைவு",
    "### Laboratory Information": "### ஆய்வக விவரங்கள்",
    "### Testing Scope and Categories": "### சோதனை வரம்பு மற்றும் பிரிவுகள்",
    "### BIS Hallmarking Scheme": "### பிஐஎஸ் ஹால்மார்க்கிங் திட்டம்",
    "### BIS Consumer Grievance": "### பிஐஎஸ் நுகர்வோர் குறைதீர்ப்பு",
    "### Consumer Guidance": "### நுகர்வோர் வழிகாட்டல்",
    "### BIS Certification Scheme": "### பிஐஎஸ் சான்றிதழ் திட்டம்",
    "### Verification Notice": "### சரிபார்ப்பு அறிவிப்பு",
    "### Statutory Notice": "### சட்டப்பூர்வ அறிவிப்பு",
    # Framing Sentences
    "Based on verified BIS authoritative records:": "சரிபார்க்கப்பட்ட பிஐஎஸ் அதிகாரப்பூர்வ பதிவுகளின் அடிப்படையில்:",
    "Based on the official Bureau of Indian Standards Consumer Protection guidelines:": "இந்திய தரநிலைகள் பணியகத்தின் அதிகாரப்பூர்வ நுகர்வோர் பாதுகாப்பு வழிகாட்டுதல்களின்படி:",
    "Based on the retrieved authorized BIS guidance documents:": "அங்கீகரிக்கப்பட்ட பிஐஎஸ் வழிகாட்டுதல் ஆவணங்களின் அடிப்படையில்:",
    "According to the official BIS Laboratory Recognition Scheme (LRS):": "அதிகாரப்பூர்வ பிஐஎஸ் ஆய்வக அங்கீகார திட்டத்தின் (LRS) படி:",
    "Under the BIS Act 2016:": "பிஐஎஸ் சட்டம் 2016 இன் கீழ்:",
    "Under the BIS Act 2016, misuse of the ISI mark or selling counterfeit goods is a cognizable offence:": "பிஐஎஸ் சட்டம் 2016 இன் கீழ், ஐஎஸ்ஐ முத்திரையை தவறாகப் பயன்படுத்துவது அல்லது போலிப் பொருட்களை விற்பது தண்டனைக்குரிய குற்றமாகும்:",
    "Under Indian statutory law and Zyntrix architectural invariants, Zyntrix has ZERO authority to declare compliance:": "இந்திய சட்ட விதிகளின்படி, Zyntrix-க்கு இணக்கத்தை அறிவிக்க பூஜ்ஜிய அதிகாரம் மட்டுமே உள்ளது:",
    # Laboratory Guidance
    "The recognized testing scope covers:": "அங்கீகரிக்கப்பட்ட சோதனை வரம்பில் உள்ளவை:",
    "Testing Categories:": "சோதனை பிரிவுகள்:",
    "Official Source:": "அதிகாரப்பூர்வ ஆதாரம்:",
    "Recognition Status:": "அங்கீகார நிலை:",
    "Current Recognition Status:": "தற்போதைய அங்கீகார நிலை:",
    "Verification Status:": "சரிபார்ப்பு நிலை:",
    "Provenance Chain:": "ஆதார சங்கிலி (Provenance Chain):",
    "Record downgraded to VERIFICATION_REQUIRED": "பதிவு VERIFICATION_REQUIRED நிலைக்கு மாற்றப்பட்டுள்ளது",
    "Safe abstention enforced: Authoritative evidence is missing or stale.": "பாதுகாப்பான விலகல் நடைமுறைப்படுத்தப்பட்டது: அதிகாரப்பூர்வ சான்றுகள் இல்லை அல்லது காலாவதியாகிவிட்டன.",
    "Safe abstention enforced": "பாதுகாப்பான விலகல் நடைமுறைப்படுத்தப்பட்டது",
    "Commercial booking availability, live slots, fees, and rankings cannot be inferred without official BIS publication.": "அதிகாரப்பூர்வ பிஐஎஸ் வெளியீடு இல்லாமல் வணிக முன்பதிவு, கட்டணம் மற்றும் தரவரிசைகளை ஊகிக்க முடியாது.",
    "Zyntrix strictly refuses to infer commercial booking availability or rankings.": "வணிக முன்பதிவு அல்லது தரவரிசைகளை ஊகிப்பதை Zyntrix திட்டவட்டமாக மறுக்கிறது.",
    # Consumer & Hallmarking
    "Verify genuine certification using the official BIS CARE Mobile App:": "அதிகாரப்பூர்வ BIS CARE மொபைல் செயலியைப் பயன்படுத்தி உண்மையான சான்றிதழைச் சரிபார்க்கவும்:",
    "Enter the License (CML) Number or 6-digit HUID to inspect validity:": "செல்லுபடியாகும் நிலையைச் சரிபார்க்க உரிமம் (CML) எண் அல்லது 6-இலக்க HUID ஐ உள்ளிடவும்:",
    "Filing a Grievance against Substandard Products:": "தரமற்ற தயாரிப்புகளுக்கு எதிராக புகார் அளித்தல்:",
    "File a formal complaint through the BIS CARE app or portal:": "BIS CARE செயலி அல்லது இணையதளம் மூலம் முறையான புகாரைப் பதிவு செய்யவும்:",
    "Hallmarking consists of three mandatory marks:": "ஹால்மார்க்கிங்கில் மூன்று கட்டாய முத்திரைகள் உள்ளன:",
    "Purity Grades:": "தூய்மை பிரிவுகள்:",
    "Assaying and Hallmarking Centre (AHC):": "மதிப்பீட்டு மற்றும் ஹால்மார்க்கிங் மையம் (AHC):",
    # Requirement & Clause
    "Mandatory safety and performance requirement under": "கட்டாய பாதுகாப்பு மற்றும் செயல்திறன் தேவை",
    "The leakage current shall not exceed": "கசிவு மின்னோட்டம் (leakage current) இதை விட அதிகமாக இருக்கக்கூடாது",
    "Temperature rise limit:": "வெப்பநிலை உயர்வு வரம்பு:",
    "Plain-Language Technical Breakdown:": "எளிய மொழி தொழில்நுட்ப விளக்கம்:",
    # Safe Abstention & Statutory Phrases
    "SOURCE_UNAVAILABLE: Verified scheme information for": "ஆதாரம் கிடைக்கவில்லை (SOURCE_UNAVAILABLE): சரிபார்க்கப்பட்ட திட்டம்",
    "is not available in the Bureau of Indian Standards verified knowledge base. The system strictly refuses to speculate or invent unverified certification schemes.": "இந்திய தரநிலைகள் பணியகத்தின் சரிபார்க்கப்பட்ட அறிவுக் களஞ்சியத்தில் கிடைக்கவில்லை. இந்த அமைப்பு சரிபார்க்கப்படாத சான்றிதழ் திட்டங்களை ஊகிக்க திட்டவட்டமாக மறுக்கிறது.",
    "SOURCE_UNAVAILABLE: Verified laboratory record for": "ஆதாரம் கிடைக்கவில்லை (SOURCE_UNAVAILABLE): சரிபார்க்கப்பட்ட ஆய்வகப் பதிவு",
    "is not available in the official BIS Laboratory Directory. The system strictly refuses to speculate on unverified testing facilities.": "அதிகாரப்பூர்வ பிஐஎஸ் ஆய்வக அடைவில் கிடைக்கவில்லை. சரிபார்க்கப்படாத சோதனை வசதிகளை ஊகிப்பதை இந்த அமைப்பு திட்டவட்டமாக மறுக்கிறது.",
    "is unverified due to missing authoritative source citation and expired recognition status.": "அதிகாரப்பூர்வ ஆதாரம் இல்லாததாலும் காலாவதியான அங்கீகார நிலையினாலும் சரிபார்க்கப்படவில்லை.",
    "Downgraded to VERIFICATION_REQUIRED due to lack of authenticated official BIS Gazette publication.": "அங்கீகரிக்கப்பட்ட அதிகாரப்பூர்வ பிஐஎஸ் அரசிதழ் வெளியீடு இல்லாததால் VERIFICATION_REQUIRED நிலைக்கு மாற்றப்பட்டது.",
    "Statutory Regulatory Notice — Superseded / Obsolete Procedure": "சட்டப்பூர்வ ஒழுங்குமுறை அறிவிப்பு — மாற்றப்பட்ட / வழக்கற்றுப்போன நடைமுறை",
    "General Guidance Disclaimer: Zyntrix is an informational compliance tool and does not issue BIS licenses, registrations, or official certifications.": "பொது வழிகாட்டல் மறுப்பு: Zyntrix என்பது ஒரு தகவல் கருவி மட்டுமே, இது பிஐஎஸ் உரிமங்கள் அல்லது அதிகாரப்பூர்வ சான்றிதழ்களை வழங்காது.",
    "General Guidance Disclaimer: Zyntrix is an informational compliance tool and does not conduct laboratory tests, book laboratory appointments, or issue BIS certifications.": "பொது வழிகாட்டல் மறுப்பு: Zyntrix என்பது ஒரு தகவல் கருவி மட்டுமே, இது ஆய்வக சோதனைகளை நடத்துவதில்லை அல்லது பிஐஎஸ் சான்றிதழ்களை வழங்குவதில்லை.",
    # Invariant Notices & Footers
    "The AI assistant has ZERO authority to declare, override, or certify compliance.": "ஏஐ உதவியாளருக்கு இணக்கத்தை அறிவிக்கவோ, மாற்றவோ அல்லது சான்றளிக்கவோ பூஜ்ஜிய (0.0%) அதிகாரம் உள்ளது.",
    "Under Zyntrix architecture, compliance determinations are strictly computed by the deterministic compliance gate based on verified empirical laboratory evidence.": "Zyntrix கட்டமைப்பின் கீழ், இணக்க நிர்ணயம் சரிபார்க்கப்பட்ட ஆய்வக சான்றுகளின் அடிப்படையில் மட்டுமே கணக்கிடப்படுகிறது.",
    "LLM compliance authority is exactly 0%.": "ஏஐ இணக்க அதிகாரம் துல்லியமாக 0% (பூஜ்ஜியம்) ஆகும்.",
}


def translate_explanatory_text(masked_text: str, target_lang: str) -> str:
    """Translates the framing explanations in masked text while leaving placeholders untouched."""
    if target_lang == "hi":
        mapping = HINDI_EXPLANATION_MAP
        header_banner = "【 भारतीय मानक ब्यूरो (BIS) आधिकारिक तकनीकी मार्गदर्शन 】\n\n"
        footer_banner = "\n\n*उपलब्ध अधिकृत बीआईएस स्रोतों के आधार पर यह सूचनात्मक उत्तर दिया गया है। वैधानिक अनुपालन के लिए आधिकारिक अधिसूचना का संदर्भ लें।*"
    elif target_lang == "ta":
        mapping = TAMIL_EXPLANATION_MAP
        header_banner = "【 இந்திய தரநிலைகள் பணியகம் (BIS) அதிகாரப்பூர்வ தொழில்நுட்ப வழிகாட்டல் 】\n\n"
        footer_banner = "\n\n*அங்கீகரிக்கப்பட்ட பிஐஎஸ் ஆதாரங்களின் அடிப்படையில் இந்த வழிகாட்டல் வழங்கப்பட்டுள்ளது. சட்டப்பூர்வ இணக்கத்திற்கு அதிகாரப்பூர்வ அறிவிப்பைப் பார்க்கவும்.*"
    else:
        return masked_text
    
    translated = masked_text
    for en_phrase, indic_phrase in mapping.items():
        translated = translated.replace(en_phrase, indic_phrase)
        
    # Prepend header and append footer if not already present
    if not translated.startswith("【"):
        translated = f"{header_banner}{translated}{footer_banner}"
        
    return translated


# ==============================================================================
# 5. GROUNDED RESPONSE TRANSLATION (END-TO-END)
# ==============================================================================

def translate_grounded_response(
    response: OrchestratedAIResponse,
    target_lang: str,
) -> OrchestratedAIResponse:
    """Translates an OrchestratedAIResponse to target Indian language.
    
    Strictly preserves:
    - All canonical technical tokens (IS numbers, clauses, tolerances, lab names, URLs, HUID, units)
    - Zero compliance authority: regulatory_conclusion="NONE"
    - Original citations list and verification metadata
    - GroundingStatus, confidence_score, and expert_review flags
    - Safe abstentions when source is unavailable or unverified
    """
    if target_lang == "en" or not target_lang:
        return response
    if response.answer.startswith("【"):
        return response
    
    # 1. Mask canonical technical tokens
    masked_text, token_map = CanonicalTokenEngine.mask_tokens(response.answer)
    
    # 2. Translate user-facing framing text
    translated_masked = translate_explanatory_text(masked_text, target_lang)
    
    # 3. Restore canonical tokens with 100% fidelity
    final_answer = CanonicalTokenEngine.unmask_tokens(translated_masked, token_map)
    
    # 4. Invariant audit check
    tokens_preserved = CanonicalTokenEngine.verify_token_preservation(response.answer, final_answer, token_map)
    if not tokens_preserved:
        logger.error("[MultilingualEngine] Token preservation check failed! Reverting to canonical response.")
        return response
    
    # 5. Translate disclaimer banner if needed
    if target_lang == "hi":
        disclaimer = (
            "मार्गदर्शन सिद्धांत: एआई सहायक केवल व्याख्यात्मक सहायता प्रदान करता है। "
            "सभी अनुपालन निर्णय सत्यापित प्रयोगशाला साक्ष्य के आधार पर आधिकारिक बीआईएस द्वारा निर्धारित किए जाते हैं। (एआई अनुपालन अधिकार = 0.0%)"
        )
    elif target_lang == "ta":
        disclaimer = (
            "வழிகாட்டல் கொள்கை: ஏஐ உதவியாளர் விளக்க ஆதரவை மட்டுமே வழங்குகிறது. "
            "அனைத்து இணக்க முடிவுகளும் சரிபார்க்கப்பட்ட ஆய்வக சான்றுகளின் அடிப்படையில் அதிகாரப்பூர்வ பிஐஎஸ் ஆல் மட்டுமே தீர்மானிக்கப்படுகின்றன. (ஏஐ இணக்க அதிகாரம் = 0.0%)"
        )
    else:
        disclaimer = response.disclaimer
        
    # Construct grounded response with strict preservation of citations and regulatory_conclusion
    return OrchestratedAIResponse(
        answer=final_answer,
        intent=response.intent,
        grounding_status=response.grounding_status,
        confidence_score=response.confidence_score,
        citations=list(response.citations),  # Preserved unchanged
        missing_information_notes=response.missing_information_notes,
        expert_review_recommended=response.expert_review_recommended,
        deterministic_fallback_used=response.deterministic_fallback_used,
        regulatory_conclusion="NONE",  # Invariant: LLM has ZERO compliance authority
        disclaimer=disclaimer,
    )
