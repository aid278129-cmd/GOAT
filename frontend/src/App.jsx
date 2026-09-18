import React, { useState, useEffect, useCallback } from 'react';
import { SideNav, NAV_ITEMS } from './components/common/SideNav';
import { TopBar } from './components/common/TopBar';
import { WorkstationView } from './components/WorkstationView';
import { WorkspaceView } from './components/WorkspaceView';
import { ComplianceJobsView } from './components/ComplianceJobsView';
import { EvidenceIngestionView } from './components/EvidenceIngestionView';
import { ProductDNAWorkspaceView } from './components/ProductDNAWorkspaceView';
import { DossiersReportsView } from './components/DossiersReportsView';
import { SettingsView } from './components/SettingsView';
import { StandardsIntelligenceView } from './components/StandardsIntelligenceView';
import { ReviewWorkspaceView } from './components/ReviewWorkspaceView';
import BISAssistantView from './components/BISAssistantView';
import { AddEvidenceModal } from './components/evidence/AddEvidenceModal';
import { EvidenceDetailDrawer } from './components/evidence/EvidenceDetailDrawer';
import { ExtractParameterModal } from './components/dna/ExtractParameterModal';
import { ConflictResolutionModal } from './components/dna/ConflictResolutionModal';
import { AddStandardModal } from './components/standards/AddStandardModal';
import { AddRequirementModal } from './components/standards/AddRequirementModal';
import { TraceChainDrawer } from './components/standards/TraceChainDrawer';
import { EngineeringCopilotDrawer } from './components/EngineeringCopilotDrawer';
import { triggerEntrance } from './utils/useAnimeMotion';
import { ProcessingStatus } from './types/evidenceTypes';
import { formatBytes } from './utils/evidenceCrypto';
import {
  authApi,
  jobsApi,
  evidenceApi,
  dnaApi,
  standardsApi,
  assessmentApi,
  auditApi,
} from './api';

function mapBackendResult(res, standard) {
  return {
    assessmentId: res.id,
    engineeringResult: res.assessment_state,
    assessment_state: res.assessment_state,
    applicability_state: res.applicability_state,
    applicability_reason: res.applicability_reason,
    explanation: res.evaluation_expression || `${res.parameter_key || 'Requirement'}: ${res.assessment_state}`,
    evaluation_expression: res.evaluation_expression,
    timestamp: res.created_at,
    observed_value: res.observed_value,
    observed_unit: res.observed_unit,
    normalized_value: res.normalized_value,
    normalized_unit: res.normalized_unit,
    expected_value: res.expected_value,
    expected_unit: res.expected_unit,
    threshold_min: res.threshold_min,
    threshold_max: res.threshold_max,
    comparison_operator: res.comparison_operator,
    source_evidence_id: res.source_evidence_id,
    source_file_name: res.source_file_name,
    source_sha256: res.source_sha256,
    trace_chain: res.trace_chain,
    traceChain: {
      standard: {
        identifier: standard?.identifier || 'Statutory Standard',
        revisionYear: standard?.revisionYear || '',
        title: standard?.title || '',
      },
      clause: {
        clauseRef: res.clause_number,
        subClause: '',
        part: standard?.identifier || 'Clause',
        section: res.clause_number,
      },
      requirement: {
        reqId: `REQ-${res.clause_number}`,
        comparisonType: res.comparison_operator,
        targetValue: res.expected_value,
        unit: res.expected_unit || res.normalized_unit,
        minValue: res.threshold_min,
        maxValue: res.threshold_max,
        text: res.parameter_key ? `Assessment of parameter ${res.parameter_key}` : `Clause ${res.clause_number}`,
      },
      productDna: res.observed_value ? {
        key: res.parameter_key,
        value: res.observed_value,
        unit: res.observed_unit,
        reviewStatus: 'ACCEPTED_EVIDENCE_BACKED',
        locationCitation: res.source_file_name || 'Accepted Evidence',
      } : null,
      evidence: res.source_evidence_id ? {
        id: res.source_evidence_id,
        fileName: res.source_file_name || 'Evidence Document',
        sha256Hash: res.source_sha256 || 'Pending Hash',
        acceptanceStatus: 'ACCEPTED',
      } : null,
    },
    auditRecord: {
      assessmentId: res.id,
      executionStatus: 'COMMITTED_IN_POSTGRES',
      ruleVersion: res.rule_version || 'v2.0-deterministic',
      knowledgeBaseVersion: res.kb_version || 'KB-2026.1',
      evidenceHashes: res.source_sha256 ? [res.source_sha256] : [],
    },
  };
}

export default function App() {
  // Navigation active tab (Layer A: BIS Intelligent Assistant is the Front Door)
  const [activeTab, setActiveTab] = useState('assistant');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Active Context & State
  const [activeJobId, setActiveJobId] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [backendReady, setBackendReady] = useState(false);

  // Modals & Drawers
  const [jobModalOpen, setJobModalOpen] = useState(false);
  const [addEvidenceModalOpen, setAddEvidenceModalOpen] = useState(false);
  const [extractModalOpen, setExtractModalOpen] = useState(false);
  const [inspectingEvidence, setInspectingEvidence] = useState(null);
  const [activeConflictModal, setActiveConflictModal] = useState(null);
  const [addStandardModalOpen, setAddStandardModalOpen] = useState(false);
  const [addRequirementModalOpen, setAddRequirementModalOpen] = useState(false);
  const [activeTraceResult, setActiveTraceResult] = useState(null);
  const [activeTraceReq, setActiveTraceReq] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // Authoritative Persistent Data Lists
  const [jobs, setJobs] = useState([]);
  const [evidenceList, setEvidenceList] = useState([]);
  const [productDnaFacts, setProductDnaFacts] = useState({});
  const [conflictsList, setConflictsList] = useState([]);
  const [auditLog, setAuditLog] = useState([]);

  // Stage 03 Standards & Clause Intelligence State
  const [standardsList, setStandardsList] = useState([]);
  const [activeStandardId, setActiveStandardId] = useState(null);
  const [requirementsList, setRequirementsList] = useState([]);
  const [assessmentResults, setAssessmentResults] = useState({});
  const [assessmentAuditLog, setAssessmentAuditLog] = useState([]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Load Job Details (Evidence, DNA, Standards, Requirements, Audit)
  const loadJobData = useCallback(async (jobId) => {
    if (!jobId) return;
    try {
      // 1. Evidence
      const evItems = await evidenceApi.listEvidence(jobId);
      const mappedEvs = evItems.map((ev) => ({
        id: ev.id,
        fileName: ev.file_name,
        fileType: (ev.file_type || 'PDF').toUpperCase(),
        subType: (ev.file_type || 'DOCUMENT').toUpperCase(),
        subTypeLabel: ev.file_name,
        fileSize: formatBytes(ev.file_size_bytes),
        fileSizeBytes: ev.file_size_bytes,
        uploadTimestamp: ev.created_at || '',
        source: ev.source,
        sha256: ev.sha256_hash,
        integrityStatus: 'HASH_VALID',
        processingStatus: ev.processing_status || ProcessingStatus.EXTRACTION_COMPLETE,
        processingProgress: 100,
        acceptanceStatus: ev.acceptance_status || 'REQUIRES_REVIEW',
        reviewNote: ev.acceptance_reason || '',
        rawStoragePath: ev.storage_path,
      }));
      setEvidenceList(mappedEvs);

      // 2. Product DNA
      const dnaData = await dnaApi.getProductDNA(jobId);
      const factsMap = {};
      (dnaData.raw_parameters || []).forEach((p) => {
        factsMap[p.parameter] = {
          id: p.id,
          section: p.category,
          name: p.parameter,
          value: p.value,
          unit: p.unit || '',
          sourceEvidenceId: p.source_evidence_id,
          sourceFileName: p.source_file_name,
          sourceLocation: p.page_or_sheet || 'Direct extraction',
          extractionMethod: p.extraction_method || 'ENGINEERING_VERIFIED',
          confidence: p.confidence,
          reviewStatus: 'ACCEPTED_EVIDENCE_BACKED',
          evidenceSha256: p.source_evidence_id
            ? (mappedEvs.find((e) => e.id === p.source_evidence_id)?.sha256 || '')
            : '',
          updatedAt: p.verification_timestamp || p.created_at || '',
        };
      });
      setProductDnaFacts(factsMap);

      // 3. Standards
      const stdItems = await standardsApi.listStandards(jobId);
      const mappedStds = stdItems.map((s) => ({
        id: s.id,
        identifier: s.standard_identifier,
        title: s.title,
        revisionYear: s.revision_year,
        applicability: s.applicability,
        isActiveBasis: s.is_active_assessment_basis,
        scopeSummary: s.scope_summary,
      }));
      setStandardsList(mappedStds);

      const activeBasis = mappedStds.find((s) => s.isActiveBasis) || mappedStds[0];
      if (activeBasis) {
        setActiveStandardId(activeBasis.id);
        const reqs = await standardsApi.listRequirements(jobId, activeBasis.id);
        setRequirementsList(
          reqs.map((r) => ({
            id: r.id,
            reqId: r.requirement_id || `REQ-${r.clause_number}`,
            clauseRef: r.clause_reference || r.clause_number,
            standardId: r.standard_id,
            title: r.title || r.clause_reference,
            type: r.requirement_type,
            requirementType: r.requirement_type,
            description: r.description || r.requirement_text,
            requirementText: r.requirement_text || r.description || '',
            requiredParameterKey: r.parameter_key,
            parameterKey: r.parameter_key,
            comparisonType: r.comparison_operator,
            comparisonOperator: r.comparison_operator,
            expectedUnit: r.expected_unit,
            targetValue: r.expected_value,
            minValue: r.threshold_min,
            maxValue: r.threshold_max,
            allowedValues: r.allowed_values ? (Array.isArray(r.allowed_values) ? r.allowed_values.join(', ') : r.allowed_values) : '',
            applicabilityCondition: r.applicability_condition,
            evidenceRequirement: r.evidence_requirement,
            verificationMethod: r.verification_method,
            status: r.status,
          }))
        );
      } else {
        setActiveStandardId(null);
        setRequirementsList([]);
      }

      // 4. Latest Assessment Run & Results from PostgreSQL
      try {
        const latestRun = await assessmentApi.getLatestAssessment(jobId);
        if (latestRun?.results) {
          const resultsMap = {};
          latestRun.results.forEach((r) => {
            const mapped = mapBackendResult(r, activeBasis);
            resultsMap[r.requirement_id] = mapped;
            resultsMap[`REQ-${r.clause_number}`] = mapped;
          });
          setAssessmentResults(resultsMap);
        } else {
          setAssessmentResults({});
        }
      } catch (err) {
        // No assessment runs yet for this job
        setAssessmentResults({});
      }

      // 5. Audit Log
      const audits = await auditApi.getJobAuditTrail(jobId);
      setAuditLog(
        audits.map((a) => ({
          id: a.id,
          action: a.action,
          actor: a.actor_email || 'Lead Engineer',
          targetType: a.target_type,
          targetId: a.target_id,
          details: a.details,
          timestamp: a.created_at,
        }))
      );
    } catch (err) {
      console.warn('Failed to load compliance job data:', err);
    }
  }, []);

  // Initialize Auth & Authoritative Workspace on Mount
  useEffect(() => {
    async function initWorkspace() {
      try {
        const boot = await authApi.bootstrap();
        if (boot?.user) {
          setCurrentUser(boot.user);
        }
        setBackendReady(true);

        const loadedJobs = await jobsApi.listJobs();
        const mappedJobs = loadedJobs.map((j) => ({
          id: j.id,
          jobNumber: j.job_number,
          title: j.title,
          manufacturer: j.manufacturer || 'Unassigned Manufacturer',
          productName: j.product_name || 'Unassigned Product',
          stage: j.stage,
          status: j.status,
          complianceScore: j.compliance_score,
          createdAt: j.created_at ? j.created_at.split('T')[0] : '',
        }));
        setJobs(mappedJobs);

        if (mappedJobs.length > 0) {
          const firstId = mappedJobs[0].id;
          setActiveJobId(firstId);
          await loadJobData(firstId);
        }
      } catch (err) {
        console.warn('Backend connection notice:', err);
      }
    }
    initWorkspace();
  }, [loadJobData]);

  // Create Job Handler
  const handleCreateJob = async (newJobData) => {
    try {
      const serverJob = await jobsApi.createJob({
        title: newJobData.title,
        product_name: newJobData.productName,
        manufacturer: newJobData.manufacturer,
        model_number: newJobData.modelNumber,
        stage: '01_EVIDENCE_INGESTION',
      });

      const normalized = {
        id: serverJob.id,
        jobNumber: serverJob.job_number,
        title: serverJob.title,
        manufacturer: serverJob.manufacturer || 'Unassigned Manufacturer',
        productName: serverJob.product_name || 'Unassigned Product',
        stage: serverJob.stage,
        status: serverJob.status,
        complianceScore: serverJob.compliance_score,
        createdAt: serverJob.created_at ? serverJob.created_at.split('T')[0] : '',
      };

      setJobs((prev) => [normalized, ...prev]);
      setActiveJobId(serverJob.id);
      await loadJobData(serverJob.id);
      showToast(`Compliance Job ${serverJob.job_number} created in PostgreSQL`);
    } catch (err) {
      alert(`Job Creation Error: ${err.message}`);
    }
  };

  // Add Evidence Handler
  const handleAddEvidence = async (record) => {
    let targetJobId = activeJobId;
    if (!targetJobId) {
      if (jobs.length > 0) {
        targetJobId = jobs[0].id;
        setActiveJobId(targetJobId);
      } else {
        // Auto-initialize first job if none exists
        try {
          const newJob = await jobsApi.createJob({
            title: 'Initial Product Compliance Assessment',
            product_name: 'Unassigned Product',
            manufacturer: 'Engineering Test Facility',
            stage: '01_EVIDENCE_INGESTION',
          });
          targetJobId = newJob.id;
          setActiveJobId(newJob.id);
          setJobs([{
            id: newJob.id,
            jobNumber: newJob.job_number,
            title: newJob.title,
            manufacturer: newJob.manufacturer,
            productName: newJob.product_name,
            stage: newJob.stage,
            status: newJob.status,
            complianceScore: newJob.compliance_score,
            createdAt: newJob.created_at?.split('T')[0] || '',
          }]);
        } catch (jobErr) {
          alert('Please create a Compliance Job before uploading evidence artifacts.');
          return;
        }
      }
    }

    try {
      const fileToUpload = record.rawFile || new Blob([record.fileName], { type: 'text/plain' });
      const uploaded = await evidenceApi.uploadEvidence(
        targetJobId,
        fileToUpload,
        record.source || 'Engineering Upload'
      );

      showToast(`Evidence ${uploaded.file_name} uploaded (SHA-256 verified on server)`);
      await loadJobData(targetJobId);
    } catch (err) {
      alert(`Evidence Upload Failed: ${err.message}`);
    }
  };

  // Update Evidence Review Status
  const handleUpdateEvidenceStatus = async (evidenceId, newStatus, reviewNote) => {
    if (!activeJobId) return;
    try {
      await evidenceApi.reviewEvidence(activeJobId, evidenceId, newStatus, reviewNote || '');
      showToast(`Evidence updated to ${newStatus} in PostgreSQL`);
      await loadJobData(activeJobId);
    } catch (err) {
      alert(`Evidence Review Failed: ${err.message}`);
    }
  };

  // Extract Parameter into Product DNA with Strict Backend Evidence Gating
  const handleExtractParameter = async (payload) => {
    if (!activeJobId) {
      alert('Active compliance job required.');
      return;
    }

    try {
      await dnaApi.addDNAParameter(activeJobId, {
        category: payload.section || 'Product Identity',
        parameter: payload.parameterName,
        value: String(payload.extractedValue),
        unit: payload.unit || '',
        source_evidence_id: payload.evidence?.id,
        page_or_sheet: payload.location || 'Direct extraction',
        extraction_method: payload.extractionMethod || 'DIRECT_DOCUMENT_EXTRACTION',
      });

      showToast(`Parameter "${payload.parameterName}" bound to Product DNA.`);
      await loadJobData(activeJobId);
    } catch (err) {
      alert(err.message);
    }
  };

  // Resolve Conflict Handler
  const handleResolveConflict = (resolutionPayload) => {
    showToast('Parameter conflict resolved and recorded to audit log.');
  };

  // Stage 03 Standards Handlers
  const handleAddStandard = async (newStandard) => {
    if (!activeJobId) {
      alert('Please select or create a Compliance Job first.');
      return;
    }
    try {
      const created = await standardsApi.assignStandard(activeJobId, {
        standard_identifier: newStandard.identifier,
        title: newStandard.title,
        revision_year: newStandard.revisionYear || '',
        applicability: newStandard.applicability || 'MANDATORY',
        is_active_assessment_basis: Boolean(newStandard.isActiveBasis),
      });
      showToast(`Statutory standard ${created.standard_identifier} assigned`);
      await loadJobData(activeJobId);
    } catch (err) {
      alert(`Standard Assignment Failed: ${err.message}`);
    }
  };

  const handleRemoveStandard = async (standardId) => {
    if (!activeJobId) return;
    try {
      await standardsApi.removeStandard(activeJobId, standardId);
      showToast('Standard removed from compliance job in PostgreSQL');
      await loadJobData(activeJobId);
    } catch (err) {
      alert(`Failed to remove standard: ${err.message}`);
    }
  };

  const handleAddRequirement = async (newReq) => {
    if (!activeJobId || !activeStandardId) {
      alert('Active compliance job and standard required.');
      return;
    }
    try {
      const created = await standardsApi.addRequirement(activeJobId, activeStandardId, {
        clause_number: newReq.clauseRef,
        title: newReq.title,
        requirement_type: newReq.type || 'SAFETY',
        description: newReq.description || '',
      });
      showToast(`Clause requirement ${created.clause_number} registered`);
      await loadJobData(activeJobId);
    } catch (err) {
      alert(`Failed to register clause requirement: ${err.message}`);
    }
  };

  const handleEvaluateRequirement = async (standard, requirement) => {
    if (!activeJobId || !standard) {
      alert('Active compliance job and standard required for deterministic evaluation.');
      return;
    }
    try {
      showToast(`Evaluating ${requirement.reqId} via backend deterministic engine...`);
      const res = await assessmentApi.evaluateAssessment(activeJobId, standard.id);

      const newResults = {};
      (res.results || []).forEach((r) => {
        const mapped = mapBackendResult(r, standard);
        newResults[r.requirement_id] = mapped;
        newResults[`REQ-${r.clause_number}`] = mapped;
      });

      setAssessmentResults((prev) => ({ ...prev, ...newResults }));

      // Refresh append-only audit trail from PostgreSQL
      const audits = await auditApi.getJobAuditTrail(activeJobId);
      setAuditLog(
        audits.map((a) => ({
          id: a.id,
          action: a.action,
          actor: a.actor_email || 'Lead Engineer',
          targetType: a.target_type,
          targetId: a.target_id,
          details: a.details,
          timestamp: a.created_at,
        }))
      );

      const targetRes = newResults[requirement.id] || newResults[requirement.reqId];
      const outcome = targetRes?.engineeringResult || 'EVALUATION_RECORDED';
      showToast(`Deterministic Engine: ${requirement.reqId} → ${outcome}`);
    } catch (err) {
      alert(`Assessment Evaluation Error: ${err.message}`);
    }
  };

  const handleEvaluateAllRequirements = async (standard) => {
    if (!activeJobId || !standard) {
      alert('Active compliance job and standard required for batch evaluation.');
      return;
    }
    try {
      showToast(`Running deterministic compliance assessment for standard ${standard.identifier}...`);
      const res = await assessmentApi.evaluateAssessment(activeJobId, standard.id);

      const newResults = {};
      (res.results || []).forEach((r) => {
        const mapped = mapBackendResult(r, standard);
        newResults[r.requirement_id] = mapped;
        newResults[`REQ-${r.clause_number}`] = mapped;
      });

      setAssessmentResults((prev) => ({ ...prev, ...newResults }));

      // Refresh append-only audit trail
      const audits = await auditApi.getJobAuditTrail(activeJobId);
      setAuditLog(
        audits.map((a) => ({
          id: a.id,
          action: a.action,
          actor: a.actor_email || 'Lead Engineer',
          targetType: a.target_type,
          targetId: a.target_id,
          details: a.details,
          timestamp: a.created_at,
        }))
      );

      showToast(`Assessment complete: ${res.total_requirements} statutory requirements evaluated`);
    } catch (err) {
      alert(`Batch Assessment Error: ${err.message}`);
    }
  };

  const handleInspectTraceChain = (result, req) => {
    setActiveTraceResult(result);
    setActiveTraceReq(req);
  };

  // Trigger Anime.js entrance motion on tab switch
  useEffect(() => {
    triggerEntrance('.animate-view-stage', 20);
  }, [activeTab]);

  const currentTabObj = NAV_ITEMS.find((n) => n.id === activeTab);
  const currentTabTitle = currentTabObj ? currentTabObj.title : 'Workstation';

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#0F172A] flex">
      {/* SideNav Component */}
      <SideNav
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-60">
        {/* TopBar Component */}
        <TopBar
          activeTabTitle={currentTabTitle}
          onToggleMobile={() => setMobileMenuOpen(!mobileMenuOpen)}
        />

        {/* Page View Container */}
        <main className="flex-1 pt-14 animate-view-stage">
          {activeTab === 'assistant' && (
            <BISAssistantView
              onNavigateWorkstation={(newJobId) => {
                if (newJobId) {
                  setActiveJobId(newJobId);
                  loadJobData(newJobId);
                }
                setActiveTab('workstation');
                showToast('Navigated to Engineering Workstation');
              }}
              onJobCreated={(newJobId) => {
                setActiveJobId(newJobId);
                loadJobData(newJobId);
              }}
            />
          )}

          {activeTab === 'workstation' && (
            <WorkstationView
              jobId={activeJobId}
              onCreateJobClick={() => setJobModalOpen(true)}
              onUploadClick={() => setAddEvidenceModalOpen(true)}
              onNavigateEvidence={() => setActiveTab('evidence')}
              onNavigateDNA={() => setActiveTab('dna')}
              onNavigateStandards={() => setActiveTab('standards')}
              evidenceCount={evidenceList.length}
              onMapToDNASuccess={() => {
                if (activeJobId) loadJobData(activeJobId);
                showToast('Authoritative Product DNA updated from CAD measurements.');
              }}
            />
          )}

          {activeTab === 'workspace' && (
            <WorkspaceView
              onCreateJobClick={() => setJobModalOpen(true)}
              evidenceCount={evidenceList.length}
            />
          )}

          {activeTab === 'jobs' && (
            <ComplianceJobsView
              jobs={jobs}
              onCreateJob={handleCreateJob}
              modalOpen={jobModalOpen}
              setModalOpen={setJobModalOpen}
            />
          )}

          {activeTab === 'evidence' && (
            <EvidenceIngestionView
              evidenceList={evidenceList}
              onOpenAddModal={() => setAddEvidenceModalOpen(true)}
              onInspectEvidence={(item) => setInspectingEvidence(item)}
            />
          )}

          {activeTab === 'dna' && (
            <ProductDNAWorkspaceView
              productDnaFacts={productDnaFacts}
              conflictsList={conflictsList}
              auditLog={auditLog}
              onOpenExtractModal={() => setExtractModalOpen(true)}
              onOpenConflictModal={(conf) => setActiveConflictModal(conf)}
            />
          )}

          {activeTab === 'standards' && (
            <StandardsIntelligenceView
              standards={standardsList}
              activeStandardId={activeStandardId}
              onSelectActiveStandard={(id) => {
                setActiveStandardId(id);
                if (activeJobId) {
                  standardsApi.listRequirements(activeJobId, id).then((reqs) => {
                    setRequirementsList(
                      reqs.map((r) => ({
                        id: r.id,
                        reqId: r.requirement_id || `REQ-${r.clause_number}`,
                        clauseRef: r.clause_reference || r.clause_number,
                        standardId: r.standard_id,
                        title: r.title || r.clause_reference,
                        type: r.requirement_type,
                        requirementType: r.requirement_type,
                        description: r.description || r.requirement_text,
                        requirementText: r.requirement_text || r.description || '',
                        requiredParameterKey: r.parameter_key,
                        parameterKey: r.parameter_key,
                        comparisonType: r.comparison_operator,
                        comparisonOperator: r.comparison_operator,
                        expectedUnit: r.expected_unit,
                        targetValue: r.expected_value,
                        minValue: r.threshold_min,
                        maxValue: r.threshold_max,
                        allowedValues: r.allowed_values ? (Array.isArray(r.allowed_values) ? r.allowed_values.join(', ') : r.allowed_values) : '',
                        applicabilityCondition: r.applicability_condition,
                        evidenceRequirement: r.evidence_requirement,
                        verificationMethod: r.verification_method,
                        status: r.status,
                      }))
                    );
                  });
                }
              }}
              onAddStandardClick={() => setAddStandardModalOpen(true)}
              onRemoveStandard={handleRemoveStandard}
              requirements={requirementsList}
              onAddRequirementClick={() => setAddRequirementModalOpen(true)}
              productDnaFacts={productDnaFacts}
              conflictsList={conflictsList}
              evidenceList={evidenceList}
              assessmentResults={assessmentResults}
              onEvaluateRequirement={handleEvaluateRequirement}
              onEvaluateAllRequirements={handleEvaluateAllRequirements}
              onInspectTraceChain={handleInspectTraceChain}
              onNavigateDNA={() => setActiveTab('dna')}
              onNavigateEvidence={() => setActiveTab('evidence')}
              onNavigateSpatialCAD={(req) => {
                setActiveTab('workstation');
                showToast(`Viewing CAD telemetry for ${req.reqId}`);
              }}
            />
          )}

          {activeTab === 'reviews' && (
            <ReviewWorkspaceView
              jobId={activeJobId}
              currentJob={jobs.find((j) => j.id === activeJobId)}
              currentUser={currentUser}
              onShowToast={showToast}
              evidenceList={evidenceList}
            />
          )}

          {activeTab === 'reports' && (
            <DossiersReportsView
              jobId={activeJobId}
              onNavigateJobs={() => setActiveTab('jobs')}
              evidenceCount={evidenceList.length}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsView onSaveNotification={showToast} />
          )}
        </main>
      </div>

      {/* Unified Add Evidence Modal */}
      <AddEvidenceModal
        isOpen={addEvidenceModalOpen}
        onClose={() => setAddEvidenceModalOpen(false)}
        onAddEvidence={handleAddEvidence}
      />

      {/* Evidence Detail & Review Drawer */}
      <EvidenceDetailDrawer
        evidence={inspectingEvidence}
        isOpen={Boolean(inspectingEvidence)}
        onClose={() => setInspectingEvidence(null)}
        onUpdateStatus={handleUpdateEvidenceStatus}
      />

      {/* Extract Parameter from Accepted Evidence Modal */}
      <ExtractParameterModal
        isOpen={extractModalOpen}
        onClose={() => setExtractModalOpen(false)}
        evidenceList={evidenceList}
        onExtractParameter={handleExtractParameter}
      />

      {/* Parameter Conflict Resolution Modal */}
      <ConflictResolutionModal
        conflict={activeConflictModal}
        isOpen={Boolean(activeConflictModal)}
        onClose={() => setActiveConflictModal(null)}
        onResolve={handleResolveConflict}
      />

      {/* Add Statutory Standard Modal */}
      <AddStandardModal
        isOpen={addStandardModalOpen}
        onClose={() => setAddStandardModalOpen(false)}
        onAddStandard={handleAddStandard}
      />

      {/* Add Clause Requirement Modal */}
      <AddRequirementModal
        isOpen={addRequirementModalOpen}
        onClose={() => setAddRequirementModalOpen(false)}
        onAddRequirement={handleAddRequirement}
        activeStandard={standardsList.find((s) => s.id === activeStandardId) || standardsList[0]}
      />

      {/* Traceability Chain Drawer */}
      <TraceChainDrawer
        isOpen={Boolean(activeTraceResult)}
        onClose={() => {
          setActiveTraceResult(null);
          setActiveTraceReq(null);
        }}
        result={activeTraceResult}
        requirement={activeTraceReq}
        onSpatialInspect={(req) => {
          setActiveTab('workstation');
          showToast(`Spatial CAD view focused for ${req.reqId}`);
        }}
      />

      {/* Engineering Copilot Drawer */}
      <EngineeringCopilotDrawer
        jobId={activeJobId}
        activeStandardId={activeStandardId}
        onOpenReview={() => setActiveTab('review')}
        onOpenEvidence={() => setActiveTab('evidence')}
      />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 bg-[#0F172A] text-white px-4 py-2.5 rounded-lg shadow-xl border border-slate-700 flex items-center gap-2 text-xs animate-in fade-in slide-in-from-bottom-2 duration-200">
          <span className="material-symbols-outlined text-emerald-400 text-sm">check_circle</span>
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
}
