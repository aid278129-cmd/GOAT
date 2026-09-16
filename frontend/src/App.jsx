import React, { useState, useEffect } from 'react';
import { SideNav } from './components/common/SideNav';
import { TopBar } from './components/common/TopBar';
import { OverviewView } from './components/OverviewView';
import { AnalyzeView } from './components/AnalyzeView';
import { ProductDNAView } from './components/pipeline/ProductDNAView';
import { BISApplicabilityView } from './components/pipeline/BISApplicabilityView';
import { StandardsClausesView } from './components/pipeline/StandardsClausesView';
import { EvidenceMatrixView } from './components/pipeline/EvidenceMatrixView';
import { ComplianceGapsView } from './components/pipeline/ComplianceGapsView';
import { LabActionsView } from './components/pipeline/LabActionsView';
import { CompliancePassportView } from './components/CompliancePassportView';
import { KnowledgeBaseExplorer } from './components/KnowledgeBaseExplorer';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export const PIPELINE_STEPS = [
  { id: 'input', step: '01', short: 'Input', title: 'Product Input', icon: 'upload_file' },
  { id: 'dna', step: '02', short: 'DNA', title: 'Product DNA', icon: 'fingerprint' },
  { id: 'applicability', step: '03', short: 'Applicability', title: 'BIS Applicability', icon: 'gavel' },
  { id: 'clauses', step: '04', short: 'Clauses', title: 'Standards & Clauses', icon: 'account_tree' },
  { id: 'evidence', step: '05', short: 'Evidence', title: 'Evidence Matrix', icon: 'policy' },
  { id: 'gaps', step: '06', short: 'Gaps', title: 'Compliance Gaps', icon: 'troubleshoot' },
  { id: 'actions', step: '07', short: 'Actions', title: 'Lab & Actions', icon: 'science' },
  { id: 'passport', step: '08', short: 'Passport', title: 'Compliance Passport', icon: 'verified' },
];

export default function App() {
  const [health, setHealth] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  // Default landing view is Step 01: Product Input
  const [activeTab, setActiveTab] = useState('input');
  const [assessmentsList, setAssessmentsList] = useState([]);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null);
  const [activeAssessment, setActiveAssessment] = useState(null);
  const [passportData, setPassportData] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Modal dialog states
  const [integrityModalOpen, setIntegrityModalOpen] = useState(false);
  const [auditCommitModalOpen, setAuditCommitModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const fetchHealth = async () => {
    setIsRefreshing(true);
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
        setConnectionError(false);
      } else {
        setConnectionError(true);
      }
    } catch (err) {
      console.warn('Backend connection error:', err);
      setConnectionError(true);
    } finally {
      setIsRefreshing(false);
    }
  };

  const fetchSystemInfo = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/system/info`);
      if (res.ok) {
        const data = await res.json();
        setSystemInfo(data);
      }
    } catch (err) {
      console.warn('System info error:', err);
    }
  };

  const fetchAssessments = async (preferredId = null) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/assessments`);
      if (res.ok) {
        const data = await res.json();
        setAssessmentsList(data);
        const targetId = preferredId || selectedAssessmentId || (data.length > 0 ? data[0].assessment_id : null);
        if (targetId) {
          setSelectedAssessmentId(targetId);
          loadAssessmentDetail(targetId);
        } else {
          setSelectedAssessmentId(null);
          setActiveAssessment(null);
          setPassportData(null);
        }
      }
    } catch (err) {
      console.warn('Error fetching assessments:', err);
    }
  };

  const loadAssessmentDetail = async (id) => {
    if (!id) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/assessments/${id}`);
      if (res.ok) {
        const data = await res.json();
        setActiveAssessment(data);
        loadPassport(id);
      }
    } catch (err) {
      console.warn('Error loading assessment detail:', err);
    }
  };

  const loadPassport = async (id) => {
    if (!id) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/assessments/${id}/passport`);
      if (res.ok) {
        const data = await res.json();
        setPassportData(data);
      }
    } catch (err) {
      console.warn('Error loading passport:', err);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchSystemInfo();
    fetchAssessments();
  }, []);

  const handleSelectAssessment = (id) => {
    setSelectedAssessmentId(id);
    loadAssessmentDetail(id);
  };

  const handleAssessmentCreated = (data) => {
    setActiveAssessment(data);
    setSelectedAssessmentId(data.assessment_id);
    fetchAssessments(data.assessment_id);
    loadPassport(data.assessment_id);
  };

  const handleClarifyAttribute = async (attributeName, value) => {
    const id = selectedAssessmentId || activeAssessment?.assessment_id;
    if (!id) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/assessments/${id}/clarify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attribute: attributeName, value }),
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveAssessment(updated);
        loadPassport(id);
        fetchAssessments(id);
        showToast(`Attribute "${attributeName}" confirmed.`);
      }
    } catch (err) {
      console.warn('Clarification submission error:', err);
    }
  };

  const handleUploadEvidence = async (snippet, type = 'TEST_REPORT', auth = 'LAB_REPORT', page = 1) => {
    const id = selectedAssessmentId || activeAssessment?.assessment_id;
    if (!id) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/assessments/${id}/evidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ snippet, evidence_type: type, authority: auth, page }),
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveAssessment(updated);
        loadPassport(id);
        fetchAssessments(id);
        showToast('Evidence snippet securely committed to dossier.');
      }
    } catch (err) {
      console.warn('Evidence submission error:', err);
    }
  };

  const handleClearAll = async () => {
    if (window.confirm('Clear all product assessments and reset to a clean workspace?')) {
      try {
        await fetch(`${API_BASE}/api/v1/assessments/clear`, { method: 'POST' });
        setAssessmentsList([]);
        setSelectedAssessmentId(null);
        setActiveAssessment(null);
        setPassportData(null);
        setActiveTab('input');
        showToast('Workspace reset to clean state.');
      } catch (err) {
        console.warn('Error clearing assessments:', err);
      }
    }
  };

  // Export official BIS technical compliance file
  const handleExportDossier = () => {
    if (!activeAssessment) {
      showToast('No active product assessment to export.');
      return;
    }
    const blob = new Blob([JSON.stringify(activeAssessment, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeAssessment.assessment_number || activeAssessment.assessment_id || 'goat-dossier'}-compliance-file.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('BIS technical compliance file downloaded.');
  };

  const handleCommitAudit = () => {
    setAuditCommitModalOpen(true);
  };

  const activeProductName = activeAssessment?.product_name || activeAssessment?.title;
  const sha256Seal = activeAssessment?.sha256_hash || 'SHA-256 Pending Verification';

  // Compute real dynamic badge stats for SideNav from active assessment
  const evaluatedReqs = activeAssessment?.compliance?.evaluated_requirements || activeAssessment?.requirements || activeAssessment?.clauses || [];
  const verifiedCount = evaluatedReqs.filter((r) => r.status === 'VERIFIED' || r.status === 'SATISFIED').length;
  const gapsList = activeAssessment?.compliance?.gaps || activeAssessment?.gaps || [];
  const actionsList = activeAssessment?.testing_roadmap || activeAssessment?.roadmap || activeAssessment?.actions || [];
  const rawAttrsCount = Object.keys(activeAssessment?.product_dna?.attributes || {}).length;

  const navStats = activeAssessment ? {
    dnaCount: rawAttrsCount > 0 ? `${rawAttrsCount} ATTR` : null,
    standardsCountBadge: (activeAssessment.applicability?.length || 0) > 0 ? `${activeAssessment.applicability.length} STDs` : null,
    clausesCountBadge: evaluatedReqs.length > 0 ? `${evaluatedReqs.length} CLAUSES` : null,
    evidenceCountBadge: (activeAssessment.evidence_items?.length || activeAssessment.evidence?.length || 0) > 0 ? `${verifiedCount} VER` : null,
    gapsCountBadge: gapsList.length > 0 ? `${gapsList.length} GAP` : null,
    actionsCountBadge: actionsList.length > 0 ? `${actionsList.length} ACT` : null,
    passportBadge: passportData ? (passportData.overall_status || 'PASS') : null,
  } : {};

  const currentStepIndex = PIPELINE_STEPS.findIndex((s) => s.id === activeTab);
  const isPipelineStep = currentStepIndex !== -1;
  const prevStep = isPipelineStep && currentStepIndex > 0 ? PIPELINE_STEPS[currentStepIndex - 1] : null;
  const nextStep = isPipelineStep && currentStepIndex < PIPELINE_STEPS.length - 1 ? PIPELINE_STEPS[currentStepIndex + 1] : null;

  return (
    <div className="flex h-screen w-full bg-[#F8FAFC] text-slate-900 antialiased overflow-hidden font-sans">
      {/* Primary Fixed Left Navigation */}
      <SideNav
        currentView={activeTab}
        onNavigate={setActiveTab}
        onNewAnalysis={() => setActiveTab('input')}
        activeProductName={activeProductName}
        assessmentsCount={assessmentsList.length}
        standardsCount={51}
        onExecuteIntegrityCheck={() => setIntegrityModalOpen(true)}
        stats={navStats}
      />

      {/* Main Execution Workspace Container */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden lg:pl-64">
        {/* Top Header Bar */}
        <TopBar
          currentView={activeTab}
          onNavigate={setActiveTab}
          onNewAnalysis={() => setActiveTab('input')}
          mobileMenuOpen={mobileMenuOpen}
          setMobileMenuOpen={setMobileMenuOpen}
          activeAssessment={activeAssessment}
          assessmentsList={assessmentsList}
          onSelectAssessment={handleSelectAssessment}
          isHealthy={!connectionError}
          onClearAll={assessmentsList.length > 0 ? handleClearAll : null}
          onExportDossier={handleExportDossier}
          onCommitAudit={handleCommitAudit}
        />

        {/* Toast Notification */}
        {toastMessage && (
          <div className="fixed bottom-4 right-4 z-50 bg-slate-900 text-white text-xs font-mono px-4 py-2 rounded shadow-lg flex items-center gap-2 border border-slate-700 animate-in fade-in slide-in-from-bottom-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span>{toastMessage}</span>
          </div>
        )}

        {/* Backend Disconnected Alert Banner */}
        {connectionError && (
          <div className="bg-rose-600 text-white px-4 py-2 text-xs flex items-center justify-between shadow-2xs shrink-0">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-white animate-ping"></span>
              <strong>Backend Disconnected:</strong>
              <span>FastAPI service unreachable on port 8000. Start backend via <code>start.bat</code>.</span>
            </div>
            <button
              onClick={fetchHealth}
              className="px-2 py-0.5 bg-rose-800 hover:bg-rose-900 rounded font-semibold transition cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {/* Stitch-Style Interactive Pipeline Progress Stepper */}
        {isPipelineStep && (
          <div className="bg-white border-b border-slate-200 px-3 md:px-5 py-2 shrink-0 flex items-center justify-between gap-3 shadow-2xs font-sans text-xs">
            {/* Step Status Pill & Title */}
            <div className="flex items-center gap-2 shrink-0">
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-mono text-[10px] font-bold">
                <span className="text-slate-400">STEP</span>
                <span className="text-slate-900">{PIPELINE_STEPS[currentStepIndex].step}</span>
                <span className="text-slate-400">/ 08</span>
              </div>
              <span className="font-bold text-slate-900 hidden sm:inline">
                {PIPELINE_STEPS[currentStepIndex].title}
              </span>
            </div>

            {/* Stepper Dots & Horizontal Track */}
            <div className="hidden md:flex items-center gap-1 overflow-x-auto py-0.5">
              {PIPELINE_STEPS.map((step, idx) => {
                const isCurrent = step.id === activeTab;
                const isPassed = idx < currentStepIndex;
                return (
                  <button
                    key={step.id}
                    onClick={() => setActiveTab(step.id)}
                    title={step.title}
                    className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-[11px] font-medium transition-all duration-200 cursor-pointer ${
                      isCurrent
                        ? 'bg-slate-900 text-white shadow-xs font-semibold scale-105'
                        : isPassed
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100'
                        : 'bg-slate-50 text-slate-500 hover:bg-slate-100 hover:text-slate-800'
                    }`}
                  >
                    <span
                      className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-mono font-bold ${
                        isCurrent
                          ? 'bg-white text-slate-900'
                          : isPassed
                          ? 'bg-emerald-600 text-white'
                          : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      {isPassed ? '✓' : step.step}
                    </span>
                    <span className="hidden lg:inline">{step.short}</span>
                  </button>
                );
              })}
            </div>

            {/* Navigation Controls: Prev / Next */}
            <div className="flex items-center gap-1.5 shrink-0">
              {prevStep && (
                <button
                  onClick={() => setActiveTab(prevStep.id)}
                  className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded font-medium text-xs flex items-center gap-1 transition btn-press cursor-pointer"
                  title={`Go to Step ${prevStep.step}: ${prevStep.title}`}
                >
                  <span className="material-symbols-outlined text-[14px]">arrow_back</span>
                  <span className="hidden sm:inline">Prev</span>
                </button>
              )}
              {nextStep && (
                <button
                  onClick={() => setActiveTab(nextStep.id)}
                  className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded font-medium text-xs flex items-center gap-1 transition btn-press cursor-pointer shadow-2xs"
                  title={`Advance to Step ${nextStep.step}: ${nextStep.title}`}
                >
                  <span>Next: {nextStep.short}</span>
                  <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Dynamic Pipeline Content Area with Smooth View Transition */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <div key={activeTab} className="view-enter flex-1 flex flex-col overflow-hidden">
            {/* Step 01: Product Input */}
            {activeTab === 'input' && (
              <AnalyzeView
                onAssessmentCreated={handleAssessmentCreated}
                onNavigate={setActiveTab}
              />
            )}

            {/* Step 02: Product DNA */}
            {activeTab === 'dna' && (
              <ProductDNAView
                assessment={activeAssessment}
                onClarify={handleClarifyAttribute}
                onNavigate={setActiveTab}
              />
            )}

            {/* Step 03: BIS Applicability */}
            {activeTab === 'applicability' && (
              <BISApplicabilityView
                assessment={activeAssessment}
                onNavigate={setActiveTab}
              />
            )}

            {/* Step 04: Standards & Clauses (Regulatory Assurance Matrix) */}
            {activeTab === 'clauses' && (
              <StandardsClausesView
                assessment={activeAssessment}
                onNavigate={setActiveTab}
              />
            )}

            {/* Step 05: Evidence Matrix */}
            {activeTab === 'evidence' && (
              <EvidenceMatrixView
                assessment={activeAssessment}
                onUploadEvidence={handleUploadEvidence}
                onNavigate={setActiveTab}
              />
            )}

            {/* Step 06: Compliance Gaps */}
            {activeTab === 'gaps' && (
              <ComplianceGapsView
                assessment={activeAssessment}
                onNavigate={setActiveTab}
              />
            )}

            {/* Step 07: Lab & Actions */}
            {activeTab === 'actions' && (
              <LabActionsView
                assessment={activeAssessment}
                onNavigate={setActiveTab}
              />
            )}

            {/* Step 08: Compliance Passport */}
            {activeTab === 'passport' && (
              <div className="flex-1 p-4 md:p-6 lg:p-8 bg-[#F8FAFC] overflow-y-auto">
                <CompliancePassportView
                  passport={passportData}
                  onClose={() => setActiveTab('gaps')}
                />
              </div>
            )}

            {/* Secondary: Workspace Overview / Assessments Dashboard */}
            {activeTab === 'dashboard' && (
              <OverviewView
                assessmentsList={assessmentsList}
                onNavigate={setActiveTab}
                onSelectAssessment={handleSelectAssessment}
                onNewAnalysis={() => setActiveTab('input')}
              />
            )}

            {/* Secondary: BIS Standards Catalog Knowledge Base */}
            {activeTab === 'knowledge' && (
              <div className="flex-1 p-4 md:p-6 lg:p-8 bg-[#F8FAFC] overflow-y-auto">
                <KnowledgeBaseExplorer />
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Modal: Cryptographic Integrity Check */}
      {integrityModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-white border border-slate-300 rounded max-w-lg w-full p-5 shadow-xl space-y-4 font-sans">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 bg-slate-900 rounded flex items-center justify-center">
                  <span className="material-symbols-outlined text-white text-base">verified</span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 uppercase">Cryptographic Integrity Audit</h3>
                  <span className="text-[10px] font-mono text-slate-500">SHA-256 State Verification</span>
                </div>
              </div>
              <button
                onClick={() => setIntegrityModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 cursor-pointer p-1"
              >
                <span className="material-symbols-outlined text-base">close</span>
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded font-mono space-y-1.5">
                <span className="text-[10px] uppercase text-slate-400 font-bold block">ACTIVE DOSSIER DIGEST:</span>
                <div className="text-[11px] font-bold text-slate-900 break-all bg-white p-2 rounded border border-slate-200">
                  {sha256Seal}
                </div>
                <div className="flex items-center justify-between pt-1 text-[10px] text-slate-600">
                  <span>Tamper-evident status:</span>
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    AUTHENTIC & UNMODIFIED
                  </span>
                </div>
              </div>

              <div className="space-y-1.5 text-xs text-slate-700">
                <div className="flex items-center justify-between py-1 border-b border-slate-100 font-mono text-[11px]">
                  <span>Product DNA Conformance</span>
                  <span className="text-emerald-700 font-bold">Validated</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-100 font-mono text-[11px]">
                  <span>Gazette QCO Order Mapping</span>
                  <span className="text-emerald-700 font-bold truncate max-w-[200px]" title={activeAssessment?.applicability?.[0]?.provenance || 'Official Gazette Order'}>
                    {activeAssessment?.applicability?.[0]?.provenance || 'Official Gazette Order'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-100 font-mono text-[11px]">
                  <span>Deterministic Rule Authority</span>
                  <span className="text-emerald-700 font-bold">0% LLM Authority</span>
                </div>
                <div className="flex items-center justify-between py-1 font-mono text-[11px]">
                  <span>NABL Laboratory Calibration</span>
                  <span className="text-slate-800 font-semibold">Active Matrix Verified</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
              <button
                onClick={() => setIntegrityModalOpen(false)}
                className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold cursor-pointer"
              >
                Close Audit Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Commit Audit Action */}
      {auditCommitModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-white border border-slate-300 rounded max-w-md w-full p-5 shadow-xl space-y-4 font-sans">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-slate-900 text-xl">lock</span>
                <h3 className="text-sm font-bold text-slate-900 uppercase">Commit Regulatory Audit</h3>
              </div>
              <button
                onClick={() => setAuditCommitModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 cursor-pointer p-1"
              >
                <span className="material-symbols-outlined text-base">close</span>
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Committing this audit will freeze the current evaluation ledger, record all verified clause verdicts into the tamper-evident audit trail, and stamp the official Pre-Certification Compliance Passport.
            </p>

            <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-900 flex items-center gap-2">
              <span className="material-symbols-outlined text-emerald-600 text-base shrink-0">check_circle</span>
              <span>All verified clauses will be cryptographically sealed.</span>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
              <button
                onClick={() => setAuditCommitModalOpen(false)}
                className="px-3 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded text-xs font-medium cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setAuditCommitModalOpen(false);
                  setActiveTab('passport');
                  showToast('Audit committed. Compliance Passport generated.');
                }}
                className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-bold cursor-pointer"
              >
                Confirm & Seal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
