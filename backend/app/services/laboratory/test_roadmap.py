from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TestRoadmapItem(BaseModel):
    requirement_code: str
    clause_number: str
    test_name: str
    test_method_standard: str
    required_apparatus: str
    evidence_required: str
    pass_criteria: str
    bis_sampling_guideline: Optional[str] = None


class RecognizedLaboratory(BaseModel):
    name: str
    location: str
    state: str
    is_nabl_accredited: bool = True
    is_bis_recognized: bool = True
    accredited_standards: List[str] = Field(default_factory=list)
    verification_status: str = "VERIFIED"
    authority: str = "BIS_OFFICIAL_CATALOG"


def compile_testing_roadmap(standard_number: str) -> List[TestRoadmapItem]:
    """Compile structured testing roadmap for applicable requirements without claiming physical scheduling."""
    if "17526" in standard_number:
        return [
            TestRoadmapItem(
                requirement_code="REQ-PERF-THERM",
                clause_number="5.4",
                test_name="Thermal Performance (Heat Retention) Test",
                test_method_standard="IS 17526:2021 Clause 5.4",
                required_apparatus="Calibrated Thermocouple / Digital Precision Thermometer, Constant Temp Water Bath",
                evidence_required="NABL Accredited Laboratory Test Report",
                pass_criteria="Water temperature shall be >= 60°C after 6 hours from initial 95°C",
                bis_sampling_guideline="8 sample flasks selected at random across production batch (PM/IS 17526/1)",
            ),
            TestRoadmapItem(
                requirement_code="REQ-PERF-LEAK",
                clause_number="5.2",
                test_name="Inversion Leakage Test",
                test_method_standard="IS 17526:2021 Clause 5.2",
                required_apparatus="Testing Rig / Clean Absorbent Filter Paper",
                evidence_required="Laboratory Inspection Certificate",
                pass_criteria="Zero liquid droplet leakage or moisture seepage after 10-minute continuous inversion",
                bis_sampling_guideline="Sample size: 8 units per lot (BIS Product Manual Guidelines)",
            ),
            TestRoadmapItem(
                requirement_code="REQ-MAT-304",
                clause_number="4.2.1",
                test_name="Chemical Composition Analysis of Stainless Steel",
                test_method_standard="IS 6911 / Optical Emission Spectrometer (OES)",
                required_apparatus="Optical Emission Spectrometer / Wet Chemical Analysis Kit",
                evidence_required="Mill Test Certificate (MTC) or Raw Material Test Report",
                pass_criteria="Minimum 17.5-19.5% Cr, 8.0-10.5% Ni (Grade 304 food contact compliance)",
                bis_sampling_guideline="1 test coupon per raw material coil batch",
            ),
        ]
    return []


def get_verified_laboratories(standard_number: str) -> List[RecognizedLaboratory]:
    """Return verified BIS-recognized / NABL-accredited laboratories for the standard."""
    if "17526" in standard_number:
        return [
            RecognizedLaboratory(
                name="Central Laboratory, Bureau of Indian Standards (CLD)",
                location="Sahibabad, Ghaziabad",
                state="Uttar Pradesh",
                is_nabl_accredited=True,
                is_bis_recognized=True,
                accredited_standards=["IS 17526:2021", "IS 302-2-15", "IS 9845"],
                verification_status="VERIFIED",
                authority="BIS_OFFICIAL_CATALOG",
            ),
            RecognizedLaboratory(
                name="National Test House (NTH), Northern Region",
                location="Kamla Nehru Nagar, Ghaziabad",
                state="Uttar Pradesh",
                is_nabl_accredited=True,
                is_bis_recognized=True,
                accredited_standards=["IS 17526:2021", "IS 6911"],
                verification_status="VERIFIED",
                authority="BIS_OFFICIAL_CATALOG",
            ),
        ]
    return []
