import React, { useState, useEffect } from 'react';
import { SideNav } from './components/common/SideNav';
import { TopBar } from './components/common/TopBar';
import { OverviewView } from './components/OverviewView';
import { AnalyzeView } from './components/AnalyzeView';
import { AssessmentWorkspace } from './components/AssessmentWorkspace';
import { ProductWorkspace } from './components/ProductWorkspace';
import { KnowledgeBaseExplorer } from './components/KnowledgeBaseExplorer';
import { ComplianceAssistantPage } from './components/ComplianceAssistantPage';
import { TemplateGeneratorView } from './components/TemplateGeneratorView';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export default function App() {
  const [health, setHealth] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // overview | analyze | workspace | standards | assistant | passport | knowledge | evaluation | diagnostics
  const [assessmentsList, setAssessmentsList] = useState([]);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null);
  const [activeAssessment, setActiveAssessment] = useState(null);
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

  const fetchAssessments = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/assessments`);
      if (res.ok) {
        const data = await res.json();
        setAssessmentsList(data);
        if (data.length > 0 && !selectedAssessmentId) {
          setSelectedAssessmentId(data[0].assessment_id);
          loadAssessmentDetail(data[0].assessment_id);
        } else if (data.length === 0) {
          setSelectedAssessmentId(null);
          setActiveAssessment(null);
        }
      }
    } catch (err) {
      console.warn('Error fetching assessments:', err);
    }
  };

  const loadAssessmentDetail = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/assessments/${id}`);
      if (res.ok) {
        const data = await res.json();
        setActiveAssessment(data);
      }
    } catch (err) {
      console.warn('Error loading assessment detail:', err);
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
    fetchAssessments();
  };

  const handleClearAll = async () => {
    if (window.confirm('Clear all product assessments and start with a fresh slate?')) {
      try {
        await fetch(`${API_BASE}/api/v1/assessments/clear`, { method: 'POST' });
        setAssessmentsList([]);
        setSelectedAssessmentId(null);
        setActiveAssessment(null);
        setActiveTab('overview');
      } catch (err) {
        console.warn('Error clearing assessments:', err);
      }
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#F3F4F6] text-slate-900 antialiased overflow-hidden font-sans">
      {/* Fixed Left Navigation */}
      <SideNav
        currentView={activeTab}
        onNavigate={setActiveTab}
        onNewAnalysis={() => setActiveTab('analyze')}
        assessmentsCount={assessmentsList.length}
        standardsCount={51}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden lg:pl-64">
        {/* Top Header Bar */}
        <TopBar
          currentView={activeTab}
          onNavigate={setActiveTab}
          onNewAnalysis={() => setActiveTab('analyze')}
          mobileMenuOpen={mobileMenuOpen}
          setMobileMenuOpen={setMobileMenuOpen}
          productName={activeAssessment?.title || activeAssessment?.product_name}
          isHealthy={!connectionError}
          healthDetails={health}
          onClearAll={assessmentsList.length > 0 ? handleClearAll : null}
        />

        {/* Backend Disconnection Banner */}
        {connectionError && (
          <div className="bg-rose-600 text-white px-4 py-2.5 text-xs flex items-center justify-between shadow-xs">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-white animate-ping"></span>
              <strong>Backend Disconnected:</strong>
              <span>FastAPI backend unreachable on port 8000. Start server via <code>start.bat</code>.</span>
            </div>
            <button
              onClick={fetchHealth}
              className="px-2.5 py-1 bg-rose-800 hover:bg-rose-900 rounded font-semibold transition"
            >
              Retry
            </button>
          </div>
        )}

        {/* Dynamic Main Workspace Container */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {activeTab === 'overview' && (
            <OverviewView
              assessmentsList={assessmentsList}
              onNavigate={setActiveTab}
              onSelectAssessment={handleSelectAssessment}
              onNewAnalysis={() => setActiveTab('analyze')}
            />
          )}

          {activeTab === 'analyze' && (
            <AnalyzeView
              onAssessmentCreated={handleAssessmentCreated}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === 'standards' && (
            <div className="flex-1 p-4 md:p-6 lg:p-8 bg-[#F3F4F6] overflow-y-auto">
              <AssessmentWorkspace />
            </div>
          )}

          {activeTab === 'assistant' && (
            <ComplianceAssistantPage activeAssessment={activeAssessment} />
          )}

          {activeTab === 'knowledge' && (
            <div className="flex-1 p-4 md:p-6 lg:p-8 bg-[#F3F4F6] overflow-y-auto">
              <KnowledgeBaseExplorer />
            </div>
          )}



          {activeTab === 'templates' && (
            <TemplateGeneratorView onNavigate={setActiveTab} />
          )}
        </main>
      </div>
    </div>
  );
}
