import React, { useState, useEffect } from 'react';
import {
  FileCheck2,
  Dna,
  ShieldCheck,
  AlertTriangle,
  FileSearch,
  UploadCloud,
  FlaskConical,
  Building2,
  Layers,
  History,
  CheckCircle2,
  HelpCircle,
  Award,
  ChevronDown,
  ChevronUp,
  Plus,
  ArrowRight,
  Sparkles,
  Scale,
  Eye,
  X,
  FileText,
  AlertCircle,
  ExternalLink,
  RotateCcw,
  CheckSquare,
  Camera,
  ShieldAlert,
} from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { EvidenceGraphCanvas } from './EvidenceGraphCanvas';
import { CompliancePassportView } from './CompliancePassportView';
import { AssessmentChatDrawer } from './AssessmentChatDrawer';
import { extractTextFromPDF, parseProductInfoFromText } from '../utils/pdfParser';

export function AssessmentWorkspace() {
  const [assessmentsList, setAssessmentsList] = useState([]);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeSection, setActiveSection] = useState('overview'); // overview | dna | applicability | requirements | evidence | evaluation | roadmap | graph | passport | history
  const [passportData, setPassportData] = useState(null);
  const [snapshots, setSnapshots] = useState([]);

  // Selected Evidence for Modal Preview
  const [selectedEvidenceModal, setSelectedEvidenceModal] = useState(null);

  // New Assessment Creation State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProdName, setNewProdName] = useState('');
  const [newCategory, setNewCategory] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [uploadedPdfName, setUploadedPdfName] = useState('');
  const [isAuthoritative, setIsAuthoritative] = useState(false);

  // Evidence Upload State
  const [evidenceSnippet, setEvidenceSnippet] = useState('');
  const [evidenceType, setEvidenceType] = useState('TEST_REPORT');
  const [evidenceAuthority, setEvidenceAuthority] = useState('LAB_REPORT');
  const [evidencePage, setEvidencePage] = useState(2);
  const [isSubmittingEvidence, setIsSubmittingEvidence] = useState(false);
  const [expandedTraceIdx, setExpandedTraceIdx] = useState(null);

  useEffect(() => {
    fetchAssessments();
  }, []);

  const fetchAssessments = async () => {
    try {
      const res = await fetch('/api/v1/assessments');
      if (res.ok) {
        const data = await res.json();
        setAssessmentsList(data);
        if (data.length > 0 && !selectedAssessmentId) {
          loadAssessment(data[0].assessment_id);
        } else if (data.length === 0) {
          setAssessment(null);
          setSelectedAssessmentId(null);
        }
      }
    } catch (err) {
      console.warn('Error fetching assessments:', err);
    }
  };

  const loadAssessment = async (id) => {
    setIsLoading(true);
    setSelectedAssessmentId(id);
    try {
      const res = await fetch(`/api/v1/assessments/${id}`);
      if (res.ok) {
        const data = await res.json();
        setAssessment(data);
      }
    } catch (err) {
      console.warn('Error loading assessment:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateAssessment = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/assessments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_name: newProdName,
          category: newCategory,
          description: newDesc,
          authoritative_mode: isAuthoritative,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setShowCreateModal(false);
        setAssessment(data);
        setSelectedAssessmentId(data.assessment_id);
        fetchAssessments();
      }
    } catch (err) {
      console.warn('Error creating assessment:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadWaterHeaterSample = () => {
    setUploadedPdfName('Electric_Immersion_Water_Heater_Lab_Report.pdf');
    setNewProdName('Electric Immersion Water Heater (EWH-1500)');
    setNewCategory('Kitchen & Domestic Appliances');
    setNewDesc(
      `The tested product is an electric immersion water heater intended for heating water in domestic applications. The appliance consists of a heating element, insulated handle, power cord, plug, and indicator lamp.\n\n` +
      `Electrical & Operating Ratings: Voltage: 230 V AC, Power: 1500 W, Frequency: 50 Hz.\n\n` +
      `Materials & Construction: Heating element: Stainless steel; Handle: Heat-resistant polymer; Power cord: PVC insulated; Plug: 3-pin, 6 A; Body: Corrosion-resistant metal; Indicator: LED.\n\n` +
      `Verified Laboratory Test Parameters: Rated power test: 1492 W (Pass); Insulation resistance: 25 MΩ (Pass); Electric strength test: No breakdown (Pass); Leakage current test: 0.32 mA (Pass); Earthing continuity: 0.08 Ω (Pass); Temperature-rise test: Within limit (Pass); Mechanical strength: No damage (Pass); Marking and labeling: Compliant (Pass).\n\n` +
      `Laboratory Evidence: Report #ABC/EWH/2026/0902/001 issued by ABC Product Testing Laboratory. Overall Result: PASS.`
    );
  };

  const handleFileProcessForNewAssessment = async (file) => {
    if (!file) return;
    setUploadedPdfName(file.name);
    try {
      let extractedText = '';
      if (file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf') {
        extractedText = await extractTextFromPDF(file);
      } else if (file.type.startsWith('text/') || file.name.endsWith('.json') || file.name.endsWith('.csv') || file.name.endsWith('.txt')) {
        extractedText = await file.text();
      }
      if (extractedText) {
        const parsed = parseProductInfoFromText(extractedText, file.name);
        if (parsed.productName) setNewProdName(parsed.productName);
        if (parsed.category) setNewCategory(parsed.category);
        if (parsed.description) setNewDesc(parsed.description);
      } else {
        const fallbackName = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
        if (!newProdName) setNewProdName(fallbackName);
      }
    } catch (err) {
      console.warn('PDF extraction error in AssessmentWorkspace:', err);
    }
  };

  const handleAnswerClarification = async (attributeName, value) => {
    if (!assessment) return;
    try {
      const res = await fetch(`/api/v1/assessments/${assessment.assessment_id}/clarify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attribute: attributeName, value }),
      });
      if (res.ok) {
        const data = await res.json();
        setAssessment(data);
      }
    } catch (err) {
      console.warn('Clarification submission error:', err);
    }
  };

  const handleUploadEvidenceSnippet = async (snippet, type = 'TEST_REPORT', auth = 'LAB_REPORT', page = 2) => {
    if (!assessment || !snippet.trim()) return;
    setIsSubmittingEvidence(true);
    try {
      const res = await fetch(`/api/v1/assessments/${assessment.assessment_id}/evidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          snippet,
          evidence_type: type,
          authority: auth,
          page: Number(page) || 1,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setAssessment(data);
        setEvidenceSnippet('');
      }
    } catch (err) {
      console.warn('Evidence submission error:', err);
    } finally {
      setIsSubmittingEvidence(false);
    }
  };

  const handleUploadEvidence = async (e) => {
    e.preventDefault();
    await handleUploadEvidenceSnippet(evidenceSnippet, evidenceType, evidenceAuthority, evidencePage);
  };

  const handleLoadPassport = async () => {
    if (!assessment) return;
    try {
      const res = await fetch(`/api/v1/assessments/${assessment.assessment_id}/passport`);
      if (res.ok) {
        const data = await res.json();
        setPassportData(data);
        setActiveSection('passport');
      }
    } catch (err) {
      console.warn('Passport error:', err);
    }
  };

  const handleLoadSnapshots = async () => {
    if (!assessment) return;
    try {
      const res = await fetch(`/api/v1/assessments/${assessment.assessment_id}/snapshots`);
      if (res.ok) {
        const data = await res.json();
        setSnapshots(data);
      }
    } catch (err) {
      console.warn('Snapshots error:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Bar: Selector & Start Assessment Button */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-600/20 text-indigo-600 border border-blue-600/30">
            <FileCheck2 className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-slate-500 uppercase tracking-wider">
              MSME Compliance Operations
            </span>
            <h2 className="text-base font-bold text-slate-900">Evidence-First Compliance Assessment Workspace</h2>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {assessmentsList.length > 0 && (
            <select
              value={selectedAssessmentId || ''}
              onChange={(e) => loadAssessment(e.target.value)}
              className="bg-slate-50 border border-slate-300 text-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-800"
            >
              {assessmentsList.map((a) => (
                <option key={a.assessment_id} value={a.assessment_id}>
                  {a.assessment_number} &bull; {a.status}
                </option>
              ))}
            </select>
          )}

          {assessmentsList.length > 0 && (
            <button
              onClick={async () => {
                if (window.confirm('Clear all assessments and start fresh?')) {
                  setIsLoading(true);
                  try {
                    await fetch('/api/v1/assessments/clear', { method: 'POST' });
                    setAssessment(null);
                    setSelectedAssessmentId(null);
                    setAssessmentsList([]);
                  } catch (err) {
                    console.warn('Clear error:', err);
                  } finally {
                    setIsLoading(false);
                  }
                }
              }}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-100 hover:bg-red-50 text-slate-700 hover:text-red-700 border border-slate-200 hover:border-red-200 text-xs font-semibold transition shrink-0 cursor-pointer"
              title="Clear all assessments and start with a fresh product"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Clear All
            </button>
          )}

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs text-xs font-bold transition shadow-lg shrink-0"
          >
            <Plus className="w-3.5 h-3.5" />
            New Assessment
          </button>
        </div>
      </div>

      {/* Modal: New Assessment */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-white/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs max-w-lg w-full p-6 space-y-4 text-xs">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Plus className="w-4 h-4 text-indigo-600" />
                Initialize New Product Assessment
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-500 hover:text-white"
              >
                &times;
              </button>
            </div>

            <div className="p-3 rounded-lg bg-indigo-50/70 border border-indigo-100 text-[11px] text-blue-200">
              <strong className="block font-bold mb-0.5">Invariant: PRODUCT FACT ≠ COMPLIANCE EVIDENCE</strong>
              Entering product details describes your product specifications. No requirements will be marked SATISFIED until verified laboratory or documentary evidence is provided.
            </div>

            <form onSubmit={handleCreateAssessment} className="space-y-4">
              <div>
                <label className="text-slate-700 font-semibold block mb-1">Product Trade Name:</label>
                <input
                  type="text"
                  value={newProdName}
                  onChange={(e) => setNewProdName(e.target.value)}
                  placeholder="e.g. Stainless Steel Thermal Bottle 1000ml, Immersion Water Heater 1500W"
                  className="w-full bg-slate-50 border border-slate-200 rounded px-3 py-2 text-white font-mono placeholder:text-slate-600"
                  required
                />
              </div>

              <div>
                <label className="text-slate-700 font-semibold block mb-1">Product Category:</label>
                <input
                  type="text"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  placeholder="e.g. Drinkware & Food Contact, Domestic Electrical Appliances, Toys"
                  className="w-full bg-slate-50 border border-slate-200 rounded px-3 py-2 text-white font-mono placeholder:text-slate-600"
                  required
                />
              </div>

              <div>
                <label className="text-slate-700 font-semibold block mb-1">Product Description / Technical Specifications:</label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  rows={3}
                  placeholder="Describe materials (e.g. SS 304, silicone gasket), capacity, wattage, intended usage..."
                  className="w-full bg-slate-50 border border-slate-200 rounded px-3 py-2 text-white font-mono leading-relaxed placeholder:text-slate-600"
                  required
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="authMode"
                  checked={isAuthoritative}
                  onChange={(e) => setIsAuthoritative(e.target.checked)}
                  className="rounded bg-slate-50 border-slate-200 text-blue-600 focus:ring-0"
                />
                <label htmlFor="authMode" className="text-slate-700">
                  Strict Authoritative Mode (Only verified standard clauses)
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs font-bold transition disabled:opacity-50"
                >
                  {isLoading ? 'Creating...' : 'Initialize Assessment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Main Assessment Container */}
      {assessment ? (
        <div className="space-y-6">
          {/* Section A: Assessment Header */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-200 pb-3">
              <div>
                <div className="flex items-center gap-2 text-[11px] font-mono">
                  <span className="text-slate-500">{assessment.assessment_number}</span>
                  <span className="text-slate-600">&bull;</span>
                  <span className="text-indigo-600 font-bold">Version {assessment.current_version}</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mt-0.5">{assessment.title}</h3>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className={`px-2.5 py-1 rounded text-xs font-mono font-bold border ${
                  assessment.mode === 'AUTHORITATIVE_MODE'
                    ? 'bg-blue-950 text-blue-300 border-blue-800'
                    : 'bg-amber-950 text-amber-300 border-amber-800'
                }`}>
                  {assessment.mode === 'AUTHORITATIVE_MODE' ? 'AUTHORITATIVE MODE (Verified Only)' : 'DEVELOPMENT MODE (Evidence-First Gating)'}
                </span>

                <span className="px-2.5 py-1 rounded text-xs font-mono font-bold bg-slate-50 text-slate-700 border border-slate-300">
                  Status: {assessment.status}
                </span>

                <button
                  onClick={handleLoadPassport}
                  className="px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs text-xs font-bold transition flex items-center gap-1.5 cursor-pointer"
                >
                  <Award className="w-3.5 h-3.5" />
                  Compliance Passport
                </button>
              </div>
            </div>

            {/* Structured Requirement Overview Counters (No Fake Percentages) */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 text-xs">
              <div className="p-3 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-500 text-[10px] uppercase">Requirements</span>
                <div className="text-base font-bold text-slate-900 font-mono">
                  {assessment.summary.total_requirements}
                </div>
              </div>
              <div className="p-3 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-500 text-[10px] uppercase">Satisfied (Evidence)</span>
                <div className="text-base font-bold text-emerald-700 font-mono">
                  {assessment.summary.satisfied_count}
                </div>
              </div>
              <div className="p-3 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-500 text-[10px] uppercase">Potentially Satisfied</span>
                <div className="text-base font-bold text-indigo-600 font-mono">
                  {assessment.summary.potentially_satisfied_count}
                </div>
              </div>
              <div className="p-3 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-500 text-[10px] uppercase">Missing Evidence</span>
                <div className="text-base font-bold text-amber-700 font-mono">
                  {assessment.summary.missing_evidence_count}
                </div>
              </div>
              <div className="p-3 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-500 text-[10px] uppercase">Testing Required</span>
                <div className="text-base font-bold text-purple-400 font-mono">
                  {assessment.summary.recommended_actions?.REQUIRES_TESTING || 0}
                </div>
              </div>
              <div className="p-3 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-500 text-[10px] uppercase">Conflicts / Review</span>
                <div className="text-base font-bold text-rose-700 font-mono">
                  {assessment.summary.conflicting_evidence_count + (assessment.evidence_conflicts?.length || 0)}
                </div>
              </div>
              <div className="p-3 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-500 text-[10px] uppercase">Overall Verdict</span>
                <div className="text-xs font-bold text-slate-900 font-mono mt-1">
                  <StatusBadge status={assessment.summary.summary_verdict} />
                </div>
              </div>
            </div>

            {/* Active Evidence Conflicts Alert Banner */}
            {assessment.evidence_conflicts && assessment.evidence_conflicts.length > 0 && (
              <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/80 flex items-start gap-3 text-xs text-rose-200">
                <AlertTriangle className="w-5 h-5 text-rose-700 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <strong className="text-rose-300 font-bold block text-sm">
                    CONTRADICTORY EVIDENCE DETECTED ({assessment.evidence_conflicts.length} Attribute Conflict{assessment.evidence_conflicts.length > 1 ? 's' : ''})
                  </strong>
                  <p className="leading-relaxed">
                    Independent documents present contradictory values for: {assessment.evidence_conflicts.map(c => `'${c.attribute}'`).join(', ')}.
                    The compliance engine strictly prohibits silent resolution by LLM guessing.
                    Recommended Action: <strong>EXPERT_REVIEW</strong>.
                  </p>
                </div>
              </div>
            )}

            {/* Active Clarification Questions Banner */}
            {assessment.clarifications && assessment.clarifications.length > 0 && (
              <div className="p-4 rounded-lg bg-amber-950/40 border border-amber-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-amber-200">
                <div className="flex items-start gap-3">
                  <HelpCircle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
                  <div className="space-y-0.5">
                    <strong className="text-amber-300 font-bold block text-sm">
                      CLARIFICATION REQUIRED ({assessment.clarifications.length} Missing Product Fact{assessment.clarifications.length > 1 ? 's' : ''})
                    </strong>
                    <p className="leading-relaxed text-[11px]">
                      Essential attributes ({assessment.clarifications.map(c => `'${c.attribute_name}'`).join(', ')}) are unstated.
                      The system refuses to guess missing specifications.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setActiveSection('dna')}
                  className="px-3 py-1.5 rounded bg-amber-600 hover:bg-amber-500 text-white font-bold transition shrink-0 text-xs"
                >
                  Answer Questions
                </button>
              </div>
            )}

            {/* Navigation Stepper (8-Step Workflow) */}
            <div className="flex border-b border-slate-200 gap-1 overflow-x-auto pt-2 pb-px text-xs font-semibold">
              {[
                { id: 'overview', label: '1. Overview' },
                { id: 'dna', label: '2. Product DNA & Claims' },
                { id: 'applicability', label: '3. Standards Applicability' },
                { id: 'requirements', label: '4. Requirements & Evidence' },
                { id: 'evidence', label: '5. Evidence Workspace' },
                { id: 'evaluation', label: '6. Deterministic Evaluation' },
                { id: 'roadmap', label: '7. Testing & Laboratories' },
                { id: 'graph', label: '8. Evidence Graph' },
                { id: 'history', label: '9. Audit Snapshots' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveSection(tab.id);
                    if (tab.id === 'history') handleLoadSnapshots();
                  }}
                  className={`px-3 py-2 rounded-t-lg transition whitespace-nowrap border-t border-x ${
                    activeSection === tab.id
                      ? 'bg-slate-50 text-indigo-600 border-slate-200 border-b-slate-950 -mb-px font-bold'
                      : 'text-slate-500 hover:text-slate-800 border-transparent hover:bg-slate-50'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Section: Overview */}
          {activeSection === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <FileSearch className="w-4 h-4 text-indigo-600" />
                    Applicable Indian Standards & QCO Orders
                  </h4>
                  <div className="space-y-3">
                    {assessment.applicability.map((app, idx) => (
                      <div key={idx} className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3 text-xs">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono font-bold text-indigo-600 text-sm">{app.standard_number}</span>
                            {app.is_primary && (
                              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">
                                Primary Standard
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <StatusBadge status={app.applicability_status || app.technical_relevance} />
                            {app.scope_status && (
                              <StatusBadge status={app.scope_status} />
                            )}
                            {app.qco_status && (
                              <StatusBadge status={app.qco_status} />
                            )}
                          </div>
                        </div>

                        <div className="font-bold text-slate-900 text-sm">{app.standard_title}</div>
                        <p className="text-slate-700 text-xs leading-relaxed">{app.explanation}</p>

                        {/* Clarification prompt if missing facts */}
                        {app.clarification_question && (
                          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 space-y-1">
                            <div className="font-bold text-xs flex items-center gap-1.5 text-amber-800">
                              <HelpCircle className="w-3.5 h-3.5" />
                              Clarification Required to Confirm Applicability Scope
                            </div>
                            <div className="text-[11px] leading-relaxed">{app.clarification_question}</div>
                          </div>
                        )}

                        {/* Expandable Deterministic Decision Trace */}
                        <div className="pt-2 border-t border-slate-200">
                          <button
                            type="button"
                            onClick={() => setExpandedTraceIdx(expandedTraceIdx === idx ? null : idx)}
                            className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 transition-colors"
                          >
                            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                            {expandedTraceIdx === idx ? "Hide Deterministic Decision Trace" : "View Deterministic Trace (8-Step Audit Trail)"}
                            {expandedTraceIdx === idx ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>

                          {expandedTraceIdx === idx && (
                            <div className="mt-3 p-3 rounded-lg bg-white border border-slate-200 space-y-2 text-[11px] font-mono">
                              <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                                <span className="text-slate-500">Pipeline Stage:</span>
                                <span className="font-bold text-indigo-700">Layer 5 — Applicability Engine</span>
                              </div>
                              <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                                <span className="text-slate-500">Matched Rule:</span>
                                <span className="font-bold text-slate-800">{app.matched_rule_id} ({app.rule_verification_status})</span>
                              </div>
                              <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                                <span className="text-slate-500">Scope Evaluation:</span>
                                <span className="font-bold text-slate-800">{app.scope_status}</span>
                              </div>
                              <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                                <span className="text-slate-500">QCO Statutory Mandate:</span>
                                <span className="font-bold text-slate-800">{app.qco_status}</span>
                              </div>
                              <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                                <span className="text-slate-500">LLM Decision Authority:</span>
                                <span className="font-bold text-emerald-700">0.0% (Zero LLM Regulatory Authority • Evidence-Grounded)</span>
                              </div>
                              {app.decision_trace?.product_facts && app.decision_trace.product_facts.length > 0 && (
                                <div className="pt-1">
                                  <span className="text-slate-500 block">Facts Evaluated:</span>
                                  <div className="text-[10px] text-slate-700 bg-slate-50 p-2 rounded mt-1 overflow-x-auto">
                                    {app.decision_trace.product_facts.join(" | ")}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Evidence Gaps & Next Steps */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4 text-xs">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-700" />
                    Requirements Status & Operational Actions
                  </h4>
                  <div className="space-y-2">
                    {assessment.compliance && assessment.compliance.evaluations.map((ev, idx) => (
                      <div key={idx} className="p-3.5 rounded bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                          <div className="font-bold text-slate-900">Clause {ev.clause_number}: {ev.clause_title}</div>
                          <div className="text-[11px] text-slate-500 mt-0.5">{ev.explanation}</div>
                        </div>
                        <div className="flex sm:flex-col items-end gap-1.5 shrink-0">
                          <StatusBadge status={ev.status} />
                          {ev.recommended_action && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-rose-50 text-rose-700 border border-rose-200">
                              {ev.recommended_action}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Col: Trust Governance Card */}
              <div className="space-y-6">
                <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-3 text-xs">
                  <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">
                    Regulatory Trust & Gating Card
                  </h4>
                  <div className="p-3 rounded bg-slate-50 border border-slate-200 space-y-2">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Hard Satisfied Gate:</span>
                      <strong className="text-emerald-700 font-mono">ACTIVE (No Claims Allowed)</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Official QCO Order:</span>
                      <strong className="text-emerald-700">DPIIT 2023 VERIFIED</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Evidence Requirement Matrix:</span>
                      <strong className="text-indigo-600">ENFORCED</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Rule Engine Authority:</span>
                      <strong className="text-slate-800 font-mono">DETERMINISTIC ONLY</strong>
                    </div>
                  </div>
                  <button
                    onClick={handleLoadPassport}
                    className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs font-bold transition flex items-center justify-center gap-2"
                  >
                    <Award className="w-4 h-4" />
                    Open Compliance Passport
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Section: Product DNA & Clarifications */}
          {activeSection === 'dna' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Dna className="w-4 h-4 text-indigo-600" />
                    Extracted Product DNA Attributes
                  </h4>
                  <span className="text-[10px] font-mono text-slate-500">Provenance Monitored</span>
                </div>
                <div className="space-y-2 text-xs">
                  {assessment.product_dna.attributes.map((attr, idx) => {
                    const provType = attr.provenance?.provenance_type || 'USER_CLAIM';
                    return (
                      <div key={idx} className="p-3 rounded bg-slate-50 border border-slate-200 flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-slate-500 text-[10px] block uppercase">{attr.name}</span>
                            <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold border ${
                              provType === 'USER_CLAIM'
                                ? 'bg-amber-950/60 text-amber-300 border-amber-800'
                                : provType === 'USER_CLARIFICATION'
                                ? 'bg-blue-950/60 text-blue-300 border-blue-800'
                                : 'bg-emerald-950/60 text-emerald-300 border-emerald-800'
                            }`}>
                              {provType}
                            </span>
                          </div>
                          <strong className="text-slate-900 text-sm mt-0.5 block">
                            {String(attr.value)} {attr.unit || ''}
                          </strong>
                          <div className="text-[10px] text-slate-500 mt-0.5">
                            Source: {attr.provenance?.source_text ? `"${attr.provenance.source_text.slice(0, 80)}..."` : 'User Input'}
                          </div>
                        </div>
                        <div className="text-right font-mono text-[10px]">
                          <span className="text-indigo-600 block">
                            Confidence: {(attr.provenance?.confidence || 0.95).toFixed(2)}
                          </span>
                          <span className="text-slate-500">{attr.provenance?.extraction_method || 'parser'}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Clarifications */}
              <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4">
                <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-amber-700" />
                  Missing Critical Attributes & Clarifications
                </h4>
                {assessment.clarifications.length === 0 ? (
                  <div className="p-6 rounded-lg bg-slate-50 border border-slate-200 text-center text-xs text-slate-500 space-y-1">
                    <CheckCircle2 className="w-6 h-6 text-emerald-700 mx-auto" />
                    <p className="font-bold text-slate-900">All required product attributes clarified.</p>
                    <p className="text-[11px]">No missing parameters blocking deterministic rule mapping.</p>
                  </div>
                ) : (
                  <div className="space-y-3 text-xs">
                    {assessment.clarifications.map((cl, idx) => (
                      <div key={idx} className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
                        <div className="flex items-center justify-between">
                          <strong className="text-white">{cl.attribute_name}</strong>
                          <span className="text-[10px] font-mono font-bold text-amber-700">{cl.criticality}</span>
                        </div>
                        <p className="text-slate-700 text-[11px] leading-relaxed">{cl.reason}</p>
                        {cl.options && (
                          <div className="flex flex-wrap gap-2 pt-1">
                            {cl.options.map((opt, oIdx) => (
                              <button
                                key={oIdx}
                                onClick={() => handleAnswerClarification(cl.attribute_name, opt)}
                                className="px-3 py-1 rounded bg-white hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 border border-slate-200 font-semibold transition cursor-pointer shadow-2xs"
                              >
                                {opt}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Section: Requirements & Evidence Traceability */}
          {activeSection === 'requirements' && (
            <div className="space-y-6">
              {/* Layer 7: Honest Compliance Coverage Summary (No Score Gaming) */}
              <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-3 text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-3">
                  <div className="flex items-center gap-2">
                    <CheckSquare className="w-4 h-4 text-indigo-600" />
                    <h4 className="text-sm font-bold text-slate-900">Compliance Coverage Summary</h4>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                      Layer 7 Gap Engine
                    </span>
                  </div>
                  <span className="text-[11px] font-mono font-semibold text-emerald-700 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Honest Counts Only &bull; 0% LLM Compliance Authority
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 font-mono text-center">
                  <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                    <span className="text-slate-500 text-[10px] block">TOTAL REQS</span>
                    <strong className="text-slate-900 text-sm">{assessment.compliance?.total_requirements || assessment.compliance?.evaluations?.length || 0}</strong>
                  </div>
                  <div className="p-2.5 rounded bg-emerald-50 border border-emerald-200">
                    <span className="text-emerald-700 text-[10px] block font-bold">SATISFIED</span>
                    <strong className="text-emerald-800 text-sm">{assessment.compliance?.satisfied_count || 0}</strong>
                  </div>
                  <div className="p-2.5 rounded bg-blue-50 border border-blue-200">
                    <span className="text-blue-700 text-[10px] block font-bold">POTENTIALLY SAT</span>
                    <strong className="text-blue-800 text-sm">{assessment.compliance?.potentially_satisfied_count || 0}</strong>
                  </div>
                  <div className="p-2.5 rounded bg-amber-50 border border-amber-200">
                    <span className="text-amber-700 text-[10px] block font-bold">MISSING EVIDENCE</span>
                    <strong className="text-amber-800 text-sm">{assessment.compliance?.missing_evidence_count || 0}</strong>
                  </div>
                  <div className="p-2.5 rounded bg-orange-50 border border-orange-200">
                    <span className="text-orange-700 text-[10px] block font-bold">MORE INFO REQ</span>
                    <strong className="text-orange-800 text-sm">{assessment.summary?.more_information_required_count || 0}</strong>
                  </div>
                  <div className="p-2.5 rounded bg-rose-50 border border-rose-200">
                    <span className="text-rose-700 text-[10px] block font-bold">POTENTIAL GAPS</span>
                    <strong className="text-rose-800 text-sm">{assessment.compliance?.gaps_count || 0}</strong>
                  </div>
                  <div className="p-2.5 rounded bg-red-50 border border-red-200">
                    <span className="text-red-700 text-[10px] block font-bold">CONFLICTING</span>
                    <strong className="text-red-800 text-sm">{assessment.compliance?.conflicting_count || 0}</strong>
                  </div>
                  <div className="p-2.5 rounded bg-purple-50 border border-purple-200">
                    <span className="text-purple-700 text-[10px] block font-bold">EXPERT REVIEW</span>
                    <strong className="text-purple-800 text-sm">{assessment.compliance?.expert_review_count || 0}</strong>
                  </div>
                </div>
              </div>

              {/* Requirement Cards with 13-Field Verification Matrix */}
              <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">Requirement-by-Requirement Deterministic Assessment</h4>
                    <p className="text-slate-500 text-xs mt-0.5">
                      Standard &bull; Clause &bull; Requirement &bull; Evidence &bull; Observed &bull; Required &bull; Deterministic Rule &bull; Result &bull; Action
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-slate-50 text-slate-700 border border-slate-200 font-mono text-xs">
                    {assessment.compliance?.evaluations?.length || 0} Clauses
                  </span>
                </div>

                <div className="space-y-4">
                  {assessment.compliance && assessment.compliance.evaluations.map((ev, idx) => {
                    const isSatisfied = ev.status === 'SATISFIED';
                    const isMissing = ev.status === 'MISSING_EVIDENCE' || ev.status === 'POTENTIALLY_SATISFIED';
                    const chain = ev.audit_chain;
                    const prio = ev.gap_priority || (['8.1', '13.2', '4.4'].includes(ev.clause_number) ? 'CRITICAL' : (['5.4', '5.3', '4.2.1'].includes(ev.clause_number) ? 'HIGH' : 'MEDIUM'));

                    return (
                      <div key={idx} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-3">
                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-mono font-bold text-indigo-600">{ev.requirement_code}</span>
                              <span className="text-slate-500">&bull;</span>
                              <span className="font-bold text-slate-900">Clause {ev.clause_number}: {ev.clause_title}</span>
                              <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase tracking-wider ${
                                prio === 'CRITICAL' ? 'bg-red-100 text-red-800 border border-red-300' :
                                prio === 'HIGH' ? 'bg-amber-100 text-amber-800 border border-amber-300' :
                                prio === 'MEDIUM' ? 'bg-blue-100 text-blue-800 border border-blue-300' :
                                'bg-slate-100 text-slate-700 border border-slate-300'
                              }`}>
                                Priority: {prio}
                              </span>
                            </div>
                            <p className="text-slate-500 text-[11px] mt-0.5">{ev.description}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <StatusBadge status={ev.status} />
                            {ev.recommended_action && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-rose-50 text-rose-700 border border-rose-200">
                                {ev.recommended_action}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* 13-Field Verification Matrix */}
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 text-[10px] font-mono">
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">1. Standard</span>
                            <strong className="text-slate-800">{ev.applicable_standard || 'IS 17526:2021'}</strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">2. Clause</span>
                            <strong className="text-slate-800">Clause {ev.clause_number}</strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">3. Req Type</span>
                            <strong className="text-indigo-600">{ev.requirement_type || 'PERFORMANCE'}</strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">4. Req Evidence</span>
                            <strong className="text-slate-800 truncate block">{(ev.required_evidence_types || ['LAB_REPORT'])[0]}</strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">5. Current Evidence</span>
                            <strong className={ev.evidence_ids?.length ? 'text-emerald-700' : 'text-slate-500'}>
                              {ev.evidence_ids?.length ? ev.evidence_ids[0] : 'None'}
                            </strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">6. Evidence Status</span>
                            <strong className={isSatisfied ? 'text-emerald-700' : 'text-amber-700'}>
                              {ev.evidence_status || (isSatisfied ? 'VERIFIED' : 'PENDING')}
                            </strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">7. Observed Value</span>
                            <strong className="text-slate-800 truncate block">{ev.evidence_provenance?.source_excerpt ? ev.evidence_provenance.source_excerpt.slice(0, 25) : (isSatisfied ? 'Conforming' : 'None')}</strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">8. Required Value</span>
                            <strong className="text-slate-800 truncate block">{ev.measurable_condition || 'Standard Pass'}</strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">9. Deterministic Rule</span>
                            <strong className="text-indigo-600 truncate block">{ev.comparison_rule || 'Formula / Gate Check'}</strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">10. Result</span>
                            <strong className={isSatisfied ? 'text-emerald-700' : (ev.status === 'POTENTIAL_GAP' ? 'text-rose-700' : 'text-amber-700')}>
                              {isSatisfied ? 'PASS' : (ev.status === 'POTENTIAL_GAP' ? 'FAIL' : 'PENDING')}
                            </strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">11. Gap State</span>
                            <strong className={isSatisfied ? 'text-emerald-700' : 'text-rose-700'}>
                              {isSatisfied ? 'NO GAP' : 'GAP ACTIVE'}
                            </strong>
                          </div>
                          <div className="p-2 rounded bg-white border border-slate-200">
                            <span className="text-slate-500 block uppercase">12. Action</span>
                            <strong className="text-rose-700 truncate block">{ev.recommended_action || 'NONE'}</strong>
                          </div>
                        </div>

                        {/* Satisfied Audit Chain Banner */}
                        {isSatisfied && chain && (
                          <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-300 space-y-2 text-[11px]">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-emerald-900 flex items-center gap-1.5 font-mono">
                                <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                                DETERMINISTIC EVIDENCE CHAIN (AUDIT PASS)
                              </span>
                              <button
                                onClick={() => setSelectedEvidenceModal(ev)}
                                className="px-2.5 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-white text-[10px] font-bold transition flex items-center gap-1"
                              >
                                <Eye className="w-3 h-3" />
                                View Supporting Evidence
                              </button>
                            </div>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-slate-700 font-mono text-[10px]">
                              <div><span className="text-emerald-700 font-bold">Evidence ID:</span> {chain.evidence_id}</div>
                              <div><span className="text-emerald-700 font-bold">Source Authority:</span> {chain.source_authority}</div>
                              <div><span className="text-emerald-700 font-bold">Page:</span> {chain.page_number}</div>
                              <div><span className="text-emerald-700 font-bold">Rule Verdict:</span> <strong className="text-emerald-800 font-bold">{chain.rule_result}</strong></div>
                            </div>
                            <div className="text-slate-700 text-[11px] pt-1">
                              <strong>Explanation:</strong> {ev.explanation}
                            </div>
                          </div>
                        )}

                        {/* Missing Evidence Action Box */}
                        {isMissing && (
                          <div className="p-3 rounded-lg bg-white border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-[11px]">
                            <div className="text-slate-600">
                              <strong>Status:</strong> {ev.explanation}
                            </div>
                            <button
                              onClick={() => {
                                setActiveSection('evidence');
                                setEvidenceType(ev.required_evidence_types?.[0] || 'TEST_REPORT');
                              }}
                              className="px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs font-bold transition shrink-0 flex items-center gap-1.5"
                            >
                              <UploadCloud className="w-3.5 h-3.5" />
                              Upload Supporting Evidence
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Section: Evidence Workspace */}
          {activeSection === 'evidence' && (
            <div className="space-y-6">
              {/* Quick Action: Golden Demo Evidence Fixtures */}
              <div className="bg-white border border-amber-800/60 rounded-xl p-5 space-y-3 text-xs">
                <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                  <h4 className="font-bold text-amber-300 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-700" />
                    Golden Demonstration Evidence Presets
                  </h4>
                  <span className="text-slate-500 text-[10px] font-mono">Click to test deterministic engine</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                  <button
                    onClick={() => handleUploadEvidenceSnippet(
                      "National Test House Accredited Laboratory Report NTH/2026/044: Product subjected to Clause 5.2 leakage test. Flask filled to nominal capacity and inverted for 10 minutes: zero leakage or moisture weeping observed. Clause 5.2 passed.",
                      "TEST_REPORT",
                      "LAB_REPORT",
                      2,
                    )}
                    className="p-3 rounded-lg bg-slate-50 hover:bg-indigo-50 hover:border-indigo-200 border border-slate-200 text-left space-y-1 transition group"
                  >
                    <strong className="text-emerald-700 block group-hover:text-emerald-300">
                      1. NABL Lab Report (Leakage PASS)
                    </strong>
                    <p className="text-[10px] text-slate-500">
                      Clause 5.2 Inversion test: zero leakage. Satisfies REQ-PERF-LEAK.
                    </p>
                  </button>

                  <button
                    onClick={() => handleUploadEvidenceSnippet(
                      "SAIL Raw Material Chemical Test Certificate MTC-2026-304: Material grade certified as Grade 304 austenitic stainless steel conforming to IS 6911.",
                      "MATERIAL_CERTIFICATE",
                      "MILL_TEST_CERTIFICATE",
                      1,
                    )}
                    className="p-3 rounded-lg bg-slate-50 hover:bg-indigo-50 hover:border-indigo-200 border border-slate-200 text-left space-y-1 transition group"
                  >
                    <strong className="text-emerald-700 block group-hover:text-emerald-300">
                      2. Mill Test Certificate (Grade 304)
                    </strong>
                    <p className="text-[10px] text-slate-500">
                      Material chemical composition. Satisfies REQ-MAT-304.
                    </p>
                  </button>

                  <button
                    onClick={() => handleUploadEvidenceSnippet(
                      "Competitor Catalog / Conflicting Spec: Nominal capacity 750 ml.",
                      "PRODUCT_SPECIFICATION",
                      "MANUFACTURER_DECLARATION",
                      1,
                    )}
                    className="p-3 rounded-lg bg-slate-50 hover:bg-indigo-50 hover:border-indigo-200 border border-slate-200 text-left space-y-1 transition group"
                  >
                    <strong className="text-rose-700 block group-hover:text-rose-300">
                      3. Conflicting Capacity Spec
                    </strong>
                    <p className="text-[10px] text-slate-500">
                      Declares 750 ml against 1000 ml claim. Triggers CONFLICTING_EVIDENCE.
                    </p>
                  </button>
                </div>
              </div>

              {/* Upload Form & Registry */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4 text-xs">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <UploadCloud className="w-4 h-4 text-indigo-600" />
                    Submit Custom Evidence (Test Reports / Certificates)
                  </h4>
                  <form onSubmit={handleUploadEvidence} className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="text-slate-500 text-[11px] block mb-1">Evidence Type:</label>
                        <select
                          value={evidenceType}
                          onChange={(e) => setEvidenceType(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-white font-mono"
                        >
                          <option value="TEST_REPORT">TEST_REPORT</option>
                          <option value="LAB_REPORT">LAB_REPORT</option>
                          <option value="MATERIAL_CERTIFICATE">MATERIAL_CERTIFICATE</option>
                          <option value="LABEL_PHOTO">LABEL_PHOTO</option>
                          <option value="TECHNICAL_DRAWING">TECHNICAL_DRAWING</option>
                          <option value="PRODUCT_SPECIFICATION">PRODUCT_SPECIFICATION</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-slate-500 text-[11px] block mb-1">Authority Level:</label>
                        <select
                          value={evidenceAuthority}
                          onChange={(e) => setEvidenceAuthority(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-white font-mono"
                        >
                          <option value="LAB_REPORT">LAB_REPORT (Accredited Lab)</option>
                          <option value="MILL_TEST_CERTIFICATE">MILL_TEST_CERTIFICATE</option>
                          <option value="BIS_OFFICIAL">BIS_OFFICIAL</option>
                          <option value="MANUFACTURER_DECLARATION">MANUFACTURER_DECLARATION</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-slate-500 text-[11px] block mb-1">Document Page #:</label>
                        <input
                          type="number"
                          min="1"
                          value={evidencePage}
                          onChange={(e) => setEvidencePage(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-white font-mono"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-slate-500 text-[11px] block mb-1">Evidence Text Excerpt / Report Findings:</label>
                      <textarea
                        value={evidenceSnippet}
                        onChange={(e) => setEvidenceSnippet(e.target.value)}
                        rows={4}
                        placeholder="Paste official test excerpt (e.g. Clause 5.2 inverted 10 mins: zero leakage observed)..."
                        className="w-full bg-slate-50 border border-slate-200 rounded p-3 text-white font-mono leading-relaxed"
                        required
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={isSubmittingEvidence || !evidenceSnippet.trim()}
                      className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs font-bold transition disabled:opacity-50"
                    >
                      {isSubmittingEvidence ? 'Extracting & Gating...' : 'Upload & Recalculate Gaps'}
                    </button>
                  </form>
                </div>

                {/* Evidence Registry */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-3 text-xs">
                  <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">
                    Extracted Evidence Items ({assessment.evidence_items?.length || 0})
                  </h4>
                  {(!assessment.evidence_items || assessment.evidence_items.length === 0) ? (
                    <div className="text-slate-500 text-center py-8">
                      No physical evidence uploaded yet. Submit a test report to resolve gaps.
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                      {assessment.evidence_items.map((ev, idx) => (
                        <div key={idx} className="p-3 rounded bg-slate-50 border border-slate-200 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-bold text-indigo-600">{ev.evidence_id}</span>
                            <span className="text-[10px] font-mono text-emerald-700">{ev.verification_status}</span>
                          </div>
                          <div className="text-white font-semibold">{ev.attribute}: {String(ev.normalized_value)} {ev.normalized_unit || ''}</div>
                          <div className="text-[10px] text-slate-500">
                            Source: {ev.source_authority} &bull; Page {ev.page_number || ev.page || 1}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Section: Deterministic Evaluation Gate & Complete Gap Register */}
          {activeSection === 'evaluation' && (
            <div className="space-y-6">
              <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4 text-xs">
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Scale className="w-4 h-4 text-indigo-600" />
                    Deterministic Hard SATISFIED Gate Architecture
                  </h4>
                  <span className="text-[11px] font-mono text-emerald-700 font-bold">
                    Zero LLM Compliance Authority Guaranteed
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                    <strong className="text-emerald-700 block font-bold">Gate Invariant Rules</strong>
                    <ul className="list-disc list-inside space-y-1 text-slate-700 text-[11px]">
                      <li><strong>No User Claim Authority:</strong> Product descriptions describe claims, never compliance.</li>
                      <li><strong>Traceable Evidence Mandate:</strong> SATISFIED requires linked, verified documentary evidence.</li>
                      <li><strong>No Silent LLM Resolution:</strong> Conflicting values automatically route to EXPERT_REVIEW.</li>
                      <li><strong>Zero Guessing Policy:</strong> Physical testing requirements remain REQUIRES_TESTING until laboratory reports are provided.</li>
                    </ul>
                  </div>

                  <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                    <strong className="text-indigo-600 block font-bold">Rule Engine Version & Protocol</strong>
                    <div className="space-y-1.5 font-mono text-[11px] text-slate-700">
                      <div>Engine: <strong>DETERMINISTIC_RULE_ENGINE v2.0 (Layer 7 Production)</strong></div>
                      <div>Primary Standard: <strong>{assessment.applicability?.[0]?.standard_number || 'IS 17526:2021'}</strong></div>
                      <div>Hard Gate: <strong>VERIFIED REQ + VERIFIED EVIDENCE + LINK + PASS + NO CONFLICT = SATISFIED</strong></div>
                      <div>Discrepancy Policy: <strong>Discrepant reports strictly trigger EXPERT_REVIEW</strong></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Complete Compliance Gap Register */}
              <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4 text-xs">
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      Complete Compliance Gap Register
                    </h4>
                    <p className="text-slate-500 text-xs mt-0.5">
                      Deterministic Prioritization: CRITICAL &bull; HIGH &bull; MEDIUM &bull; LOW
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-amber-50 text-amber-800 border border-amber-200 font-mono text-xs font-bold">
                    {assessment.compliance?.evaluations?.filter(e => e.status !== 'SATISFIED').length || 0} Actionable Gaps
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 font-mono text-[10px] uppercase">
                        <th className="p-2">Priority</th>
                        <th className="p-2">Clause / Code</th>
                        <th className="p-2">Requirement</th>
                        <th className="p-2">Status</th>
                        <th className="p-2">Gap Rationale / Missing</th>
                        <th className="p-2">Action</th>
                        <th className="p-2">Source</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {assessment.compliance?.evaluations?.filter(e => e.status !== 'SATISFIED').map((ev, idx) => {
                        const prio = ev.gap_priority || (['8.1', '13.2', '4.4'].includes(ev.clause_number) ? 'CRITICAL' : (['5.4', '5.3', '4.2.1'].includes(ev.clause_number) ? 'HIGH' : 'MEDIUM'));
                        return (
                          <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                            <td className="p-2 whitespace-nowrap">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold ${
                                prio === 'CRITICAL' ? 'bg-red-100 text-red-800 border border-red-300' :
                                prio === 'HIGH' ? 'bg-amber-100 text-amber-800 border border-amber-300' :
                                prio === 'MEDIUM' ? 'bg-blue-100 text-blue-800 border border-blue-300' :
                                'bg-slate-100 text-slate-700 border border-slate-300'
                              }`}>
                                {prio}
                              </span>
                            </td>
                            <td className="p-2 whitespace-nowrap font-mono">
                              <strong className="text-slate-800 block">Cl {ev.clause_number}</strong>
                              <span className="text-[10px] text-slate-500">{ev.requirement_code}</span>
                            </td>
                            <td className="p-2 max-w-xs">
                              <div className="font-semibold text-slate-800">{ev.clause_title}</div>
                              <div className="text-[11px] text-slate-500 truncate">{ev.description}</div>
                            </td>
                            <td className="p-2 whitespace-nowrap">
                              <StatusBadge status={ev.status} />
                            </td>
                            <td className="p-2 max-w-sm text-[11px] text-slate-600">
                              {ev.explanation}
                            </td>
                            <td className="p-2 whitespace-nowrap font-mono">
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                                {ev.recommended_action || 'PROVIDE_EVIDENCE'}
                              </span>
                            </td>
                            <td className="p-2 whitespace-nowrap text-[10px] font-mono text-slate-500">
                              {ev.applicable_standard || 'IS 17526:2021'} Cl {ev.clause_number}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Section: Testing Roadmap (5 Categorized Buckets) */}
          {activeSection === 'roadmap' && (
            <div className="space-y-6">
              <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4 text-xs">
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <FlaskConical className="w-4 h-4 text-indigo-600" />
                      Categorized Testing & Remediation Roadmap
                    </h4>
                    <p className="text-slate-500 text-xs mt-0.5">
                      Requirements grouped deterministically by the exact operational category of action needed.
                    </p>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">
                    Protocol: {assessment.applicability?.[0]?.standard_number || 'IS 17526:2021'}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {/* Category 1: Physical Lab Testing Required */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <strong className="text-purple-700 font-mono font-bold flex items-center gap-1.5">
                        <FlaskConical className="w-3.5 h-3.5" />
                        1. LAB TEST REQUIRED
                      </strong>
                      <span className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-800 font-mono text-[10px] font-bold">
                        {assessment.compliance?.evaluations?.filter(e => e.status !== 'SATISFIED' && (e.recommended_action === 'REQUIRES_TESTING' || ['5.2', '5.3', '5.4'].includes(e.clause_number))).length || 0}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {assessment.compliance?.evaluations?.filter(e => e.status !== 'SATISFIED' && (e.recommended_action === 'REQUIRES_TESTING' || ['5.2', '5.3', '5.4'].includes(e.clause_number))).map((ev, i) => (
                        <div key={i} className="p-2.5 rounded bg-white border border-slate-200 text-[11px] space-y-1">
                          <strong className="text-slate-800 block">Clause {ev.clause_number}: {ev.clause_title}</strong>
                          <p className="text-slate-500 text-[10px]">{ev.measurable_condition || 'Laboratory testing required'}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Category 2: Document / Test Certificate Required */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <strong className="text-blue-700 font-mono font-bold flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5" />
                        2. DOCUMENT REQUIRED
                      </strong>
                      <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 font-mono text-[10px] font-bold">
                        {assessment.compliance?.evaluations?.filter(e => e.status !== 'SATISFIED' && e.recommended_action === 'UPLOAD_EVIDENCE' && !['5.2', '5.3', '5.4', '7.1'].includes(e.clause_number)).length || 0}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {assessment.compliance?.evaluations?.filter(e => e.status !== 'SATISFIED' && e.recommended_action === 'UPLOAD_EVIDENCE' && !['5.2', '5.3', '5.4', '7.1'].includes(e.clause_number)).map((ev, i) => (
                        <div key={i} className="p-2.5 rounded bg-white border border-slate-200 text-[11px] space-y-1">
                          <strong className="text-slate-800 block">Clause {ev.clause_number}: {ev.clause_title}</strong>
                          <p className="text-slate-500 text-[10px]">{ev.measurable_condition || 'Official test certificate'}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Category 3: Manufacturer Specification Required */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <strong className="text-amber-700 font-mono font-bold flex items-center gap-1.5">
                        <HelpCircle className="w-3.5 h-3.5" />
                        3. SPECIFICATION REQUIRED
                      </strong>
                      <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-mono text-[10px] font-bold">
                        {assessment.compliance?.evaluations?.filter(e => e.status !== 'SATISFIED' && e.recommended_action === 'PROVIDE_SPECIFICATION').length || 0}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {assessment.compliance?.evaluations?.filter(e => e.status !== 'SATISFIED' && e.recommended_action === 'PROVIDE_SPECIFICATION').map((ev, i) => (
                        <div key={i} className="p-2.5 rounded bg-white border border-slate-200 text-[11px] space-y-1">
                          <strong className="text-slate-800 block">Clause {ev.clause_number}: {ev.clause_title}</strong>
                          <p className="text-slate-500 text-[10px]">{ev.explanation}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Category 4: Photo / Marking Artwork Required */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <strong className="text-emerald-700 font-mono font-bold flex items-center gap-1.5">
                        <Camera className="w-3.5 h-3.5" />
                        4. PHOTO / ARTWORK REQUIRED
                      </strong>
                      <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-mono text-[10px] font-bold">
                        {assessment.compliance?.evaluations?.filter(e => e.status !== 'SATISFIED' && (e.requirement_type === 'MARKING' || e.clause_number === '7.1')).length || 0}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {assessment.compliance?.evaluations?.filter(e => e.status !== 'SATISFIED' && (e.requirement_type === 'MARKING' || e.clause_number === '7.1')).map((ev, i) => (
                        <div key={i} className="p-2.5 rounded bg-white border border-slate-200 text-[11px] space-y-1">
                          <strong className="text-slate-800 block">Clause {ev.clause_number}: {ev.clause_title}</strong>
                          <p className="text-slate-500 text-[10px]">ISI Mark artwork and label packaging verification</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Category 5: Expert Review Required */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <strong className="text-rose-700 font-mono font-bold flex items-center gap-1.5">
                        <ShieldAlert className="w-3.5 h-3.5" />
                        5. EXPERT REVIEW REQUIRED
                      </strong>
                      <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 font-mono text-[10px] font-bold">
                        {assessment.compliance?.evaluations?.filter(e => e.status === 'CONFLICTING_EVIDENCE' || e.recommended_action === 'EXPERT_REVIEW').length || 0}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {assessment.compliance?.evaluations?.filter(e => e.status === 'CONFLICTING_EVIDENCE' || e.recommended_action === 'EXPERT_REVIEW').map((ev, i) => (
                        <div key={i} className="p-2.5 rounded bg-white border border-slate-200 text-[11px] space-y-1">
                          <strong className="text-slate-800 block">Clause {ev.clause_number}: {ev.clause_title}</strong>
                          <p className="text-slate-500 text-[10px]">Contradictory records detected. Manual legal/technical review needed.</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Verified BIS & NABL Laboratories */}
              <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4 text-xs">
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <h4 className="font-bold text-slate-900 flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-indigo-600" />
                    Verified BIS & NABL Laboratories
                  </h4>
                  <span className="text-[10px] font-mono text-emerald-700">Accredited Testing Centers</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {assessment.laboratories && assessment.laboratories.map((l, idx) => (
                    <div key={idx} className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                      <div className="flex items-center justify-between">
                        <strong className="text-slate-900 font-bold">{l.name}</strong>
                        <span className="text-[10px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          NABL ACCREDITED
                        </span>
                      </div>
                      <div className="text-slate-500 text-[11px]">{l.location}, {l.state}</div>
                      <div className="text-[10px] text-slate-600 font-mono pt-1">
                        Scope: {l.accredited_standards.join(', ')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Section: Evidence Graph */}
          {activeSection === 'graph' && (
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-600" />
                Auditable React Flow Evidence Graph
              </h4>
              <EvidenceGraphCanvas graphData={assessment.evidence_graph} />
            </div>
          )}

          {/* Section: Compliance Passport */}
          {activeSection === 'passport' && passportData && (
            <CompliancePassportView passport={passportData} onClose={() => setActiveSection('overview')} />
          )}

          {/* Section: Snapshots History */}
          {activeSection === 'history' && (
            <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-5 space-y-4 text-xs">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <History className="w-4 h-4 text-indigo-600" />
                Assessment Snapshots & Reproducibility Audit Log
              </h4>
              <div className="space-y-2">
                {snapshots.map((s, idx) => (
                  <div key={idx} className="p-3.5 rounded bg-slate-50 border border-slate-200 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-indigo-600">v{s.version}</span>
                        <strong className="text-white">{s.trigger_event}</strong>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        Knowledge Version: {s.knowledge_version} &bull; {new Date(s.created_at).toUTCString()}
                      </div>
                    </div>
                    <span className="text-slate-500 font-mono text-[11px]">
                      Snapshot ID: {s.snapshot_id}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evidence Details Modal */}
          {selectedEvidenceModal && (
            <div className="fixed inset-0 bg-white/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
              <div className="bg-white border border-slate-200 rounded-xl shadow-xs max-w-lg w-full p-6 space-y-4 text-xs">
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-emerald-700" />
                    Supporting Evidence Verification Detail
                  </h3>
                  <button
                    onClick={() => setSelectedEvidenceModal(null)}
                    className="text-slate-500 hover:text-white"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-3 font-mono">
                  <div className="p-3 rounded bg-slate-50 border border-slate-200 space-y-1.5">
                    <div><span className="text-slate-500">Requirement:</span> <strong className="text-white">{selectedEvidenceModal.requirement_code} (Clause {selectedEvidenceModal.clause_number})</strong></div>
                    <div><span className="text-slate-500">Evidence ID:</span> <strong className="text-indigo-600">{selectedEvidenceModal.audit_chain?.evidence_id}</strong></div>
                    <div><span className="text-slate-500">Source Document:</span> <strong className="text-white">{selectedEvidenceModal.audit_chain?.document_id}</strong></div>
                    <div><span className="text-slate-500">Source Authority:</span> <strong className="text-emerald-700">{selectedEvidenceModal.audit_chain?.source_authority}</strong></div>
                    <div><span className="text-slate-500">Page Number:</span> <strong className="text-white">{selectedEvidenceModal.audit_chain?.page_number}</strong></div>
                    <div><span className="text-slate-500">Evaluation Rule:</span> <strong className="text-white">{selectedEvidenceModal.audit_chain?.evaluation_rule}</strong></div>
                    <div><span className="text-slate-500">Rule Verdict:</span> <strong className="text-emerald-700 font-bold">{selectedEvidenceModal.audit_chain?.rule_result}</strong></div>
                  </div>

                  <div className="p-3 rounded bg-slate-50 border border-slate-200 space-y-1">
                    <span className="text-slate-500 text-[10px] uppercase block">Audit Finding Excerpt:</span>
                    <p className="text-slate-800 text-[11px] leading-relaxed italic">
                      "{selectedEvidenceModal.explanation}"
                    </p>
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => setSelectedEvidenceModal(null)}
                    className="px-4 py-2 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold border border-slate-200"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Floating Context-Aware Assessment Chat Drawer */}
          <AssessmentChatDrawer
            assessmentId={assessment.assessment_id}
            assessmentNumber={assessment.assessment_number}
          />
        </div>
      ) : (
        <div className="max-w-2xl mx-auto my-6 bg-white border border-slate-200 shadow-xs rounded-2xl p-8 shadow-2xl space-y-6">
          <div className="text-center space-y-2 border-b border-slate-200 pb-6">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 text-indigo-600 mb-1">
              <Plus className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-slate-900">Start New Product Compliance Assessment</h3>
            <p className="text-xs text-slate-500 max-w-lg mx-auto">
              Enter your product specifications below. Zyntrix will dynamically determine applicable Indian Standards (BIS), Quality Control Orders (QCOs), and generate a requirement-by-requirement evidence roadmap.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-indigo-50/70 border border-indigo-100 text-xs text-blue-200 flex items-start gap-2.5">
            <ShieldCheck className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
            <div>
              <strong className="block font-bold text-blue-100 mb-0.5">Strict Zero-Hallucination Regulatory Gate</strong>
              Product inputs capture your technical facts. Compliance status will remain <span className="font-mono text-amber-300 font-semibold">MISSING_EVIDENCE</span> until verified test reports or accredited laboratory certificates are uploaded.
            </div>
          </div>

          {/* PDF Report Quick Fill Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center gap-2 text-xs text-slate-700">
              <UploadCloud className="w-4 h-4 text-indigo-600 shrink-0" />
              <span>Upload lab report to auto-fill specifications:</span>
              {uploadedPdfName && (
                <span className="text-emerald-700 font-mono text-[11px] font-semibold">
                  ({uploadedPdfName})
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <label className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs text-xs font-semibold cursor-pointer transition">
                Upload PDF Report
                <input
                  type="file"
                  className="hidden"
                  accept=".pdf,.json,.txt,.csv"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileProcessForNewAssessment(e.target.files[0]);
                    }
                  }}
                />
              </label>
              <button
                type="button"
                onClick={handleLoadWaterHeaterSample}
                className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-medium border border-slate-300 transition cursor-pointer"
              >
                Fill from Water Heater Lab Report
              </button>
            </div>
          </div>

          <form onSubmit={handleCreateAssessment} className="space-y-5">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1.5">
                Product Trade Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={newProdName}
                onChange={(e) => setNewProdName(e.target.value)}
                placeholder="e.g. Stainless Steel Thermal Bottle 1000ml, Immersion Water Heater 1500W, Plastic Toy Car"
                className="w-full bg-slate-50 border border-slate-200 focus:border-blue-500 rounded-lg px-3.5 py-2.5 text-sm text-white font-mono placeholder:text-slate-600 transition outline-none"
                required
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1.5">
                Product Category / Industry Sector <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                placeholder="e.g. Drinkware & Food Contact, Domestic Electrical Appliances, Toys, Steel & Civil"
                className="w-full bg-slate-50 border border-slate-200 focus:border-blue-500 rounded-lg px-3.5 py-2.5 text-sm text-white font-mono placeholder:text-slate-600 transition outline-none"
                required
              />
              <div className="flex flex-wrap gap-1.5 mt-2">
                {[
                  'Drinkware & Food Contact Containers',
                  'Kitchen & Domestic Appliances',
                  'Electronics & IT (CRS)',
                  'Toys & Children Products',
                  'Automotive & Helmets',
                  'Civil, Steel & Cement',
                ].map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setNewCategory(cat)}
                    className="text-[11px] px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition"
                  >
                    + {cat}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1.5">
                Technical Specifications & Materials <span className="text-red-400">*</span>
              </label>
              <textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                rows={3}
                placeholder="Describe product materials (e.g. SS 304, food grade silicone, ABS plastic), capacity, voltage/wattage, insulation type, intended usage..."
                className="w-full bg-slate-50 border border-slate-200 focus:border-blue-500 rounded-lg px-3.5 py-2.5 text-sm text-white font-mono placeholder:text-slate-600 transition outline-none"
                required
              />
            </div>

            <div className="flex items-center gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200/80">
              <input
                type="checkbox"
                id="inPlaceAuthMode"
                checked={isAuthoritative}
                onChange={(e) => setIsAuthoritative(e.target.checked)}
                className="rounded bg-slate-50 border-slate-200 text-blue-600 focus:ring-0"
              />
              <label htmlFor="inPlaceAuthMode" className="text-xs text-slate-700">
                <strong>Strict Authoritative Mode</strong> &mdash; Evaluate exclusively against verified official BIS Gazette Quality Control Orders.
              </label>
            </div>

            <button
              type="submit"
              disabled={isLoading || !newProdName.trim() || !newCategory.trim() || !newDesc.trim()}
              className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs font-bold text-sm transition shadow-lg shadow-blue-600/20 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Analyzing Product DNA & BIS Applicability...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  Start BIS Compliance Assessment
                </>
              )}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
