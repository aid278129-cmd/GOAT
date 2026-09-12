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
import { ControlledDemoView } from './components/pipeline/ControlledDemoView';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

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
      } catch (err) {
        console.warn('Error clearing assessments:', err);
      }
    }
  };

  const activeProductName = activeAssessment?.product_name || activeAssessment?.title;

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
        />

        {/* Backend Disconnected Alert Banner */}
        {connectionError && (
          <div className="bg-rose-600 text-white px-4 py-2 text-xs flex items-center justify-between shadow-2xs">
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

        {/* Dynamic Pipeline Content Area */}
        <main className="flex-1 flex flex-col overflow-hidden">
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

          {/* Step 04: Standards & Clauses */}
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

          {/* Secondary: Controlled Demonstration / SIH Evaluation */}
          {activeTab === 'evaluation' && (
            <ControlledDemoView
              onLoadDemoAssessment={handleAssessmentCreated}
              onNavigate={setActiveTab}
            />
          )}
        </main>
      </div>
    </div>
  );
}
