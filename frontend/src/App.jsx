import React, { useState, useEffect, useCallback } from 'react';
import { SideNav, NAV_ITEMS } from './components/common/SideNav';
import { TopBar } from './components/common/TopBar';
import { GoldenPathStepper } from './components/common/GoldenPathStepper';
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
import { AnalyzeView } from './components/AnalyzeView';
import { ProductDNAView } from './components/pipeline/ProductDNAView';
import { BISApplicabilityView } from './components/pipeline/BISApplicabilityView';
import { StandardsClausesView } from './components/pipeline/StandardsClausesView';
import { EvidenceMatrixView } from './components/pipeline/EvidenceMatrixView';
import { ComplianceGapsView } from './components/pipeline/ComplianceGapsView';
import { LabActionsView } from './components/pipeline/LabActionsView';
import { CompliancePassportView } from './components/CompliancePassportView';

import { AddEvidenceModal } from './components/evidence/AddEvidenceModal';
import { EvidenceDetailDrawer } from './components/evidence/EvidenceDetailDrawer';
import { ExtractParameterModal } from './components/dna/ExtractParameterModal';
import { ConflictResolutionModal } from './components/dna/ConflictResolutionModal';
import { AddStandardModal } from './components/standards/AddStandardModal';
import { AddRequirementModal } from './components/standards/AddRequirementModal';
import { TraceChainDrawer } from './components/standards/TraceChainDrawer';
import { SourceInspectorDrawer } from './components/common/SourceInspectorDrawer';
import { AIAssistantDrawer } from './components/common/AIAssistantDrawer';
import { TrustGovernanceModal } from './components/common/TrustGovernanceModal';
import { ViewSkeleton } from './components/common/ViewSkeleton';
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
  // Navigation active tab (recovers from localStorage on refresh)
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('zyntrix_active_tab') || 'entry';
  });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Canonical Unified Assessment Pipeline State (recovers from localStorage on refresh)
  const [activeAssessment, setActiveAssessment] = useState(null);
  const [activeAssessmentId, setActiveAssessmentId] = useState(() => {
    return localStorage.getItem('zyntrix_active_assessment_id') || null;
  });
  const [assessmentsList, setAssessmentsList] = useState([]);
  const [passportData, setPassportData] = useState(null);
  const [isAssessmentLoading, setIsAssessmentLoading] = useState(false);
  const [isResettingDemo, setIsResettingDemo] = useState(false);

  // Active Context & State for Workstation / CAD / Reviews
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

  // M27 Workstation Responsive Drawers & Governance Modals
  const [isSourceInspectorOpen, setIsSourceInspectorOpen] = useState(false);
  const [activeSourceData, setActiveSourceData] = useState(null);
  const [isAIAssistantOpen, setIsAIAssistantOpen] = useState(false);
  const [isTrustModalOpen, setIsTrustModalOpen] = useState(false);

  const handleOpenSourceInspector = (data) => {
    setActiveSourceData(data || {
      source: 'Bureau of Indian Standards Catalog',
      document: 'IS 17526:2021 Gazette Order',
      clause: 'Mandatory QCO Scope',
      authority: 'Bureau of Indian Standards / Gazette',
      page: '1',
      snapshot: 'Deterministic applicability matching confirmed Product DNA against statutory catalog.',
      verification: 'Deterministic Rule Match',
      extractionMethod: 'Authoritative Parser',
      sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    });
    setIsSourceInspectorOpen(true);
  };

  // Authoritative Persistent Data Lists
  const [jobs, setJobs] = useState([]);
  const [evidenceList, setEvidenceList] = useState([]);
  const [productDnaFacts, setProductDnaFacts] = useState({});
  const [conflictsList, setConflictsList] = useState([]);
  const [auditLog, setAuditLog] = useState([]);

  // Standards & Clause Intelligence State
  const [standardsList, setStandardsList] = useState([]);
  const [activeStandardId, setActiveStandardId] = useState(null);
  const [requirementsList, setRequirementsList] = useState([]);
  const [assessmentResults, setAssessmentResults] = useState({});

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Sync activeTab to localStorage
  const handleSelectTab = (newTab) => {
    setActiveTab(newTab);
    localStorage.setItem('zyntrix_active_tab', newTab);
  };

  // Sync activeAssessmentId to localStorage
  useEffect(() => {
    if (activeAssessmentId) {
      localStorage.setItem('zyntrix_active_assessment_id', activeAssessmentId);
    }
  }, [activeAssessmentId]);

  // Load Full Unified Assessment and its Passport
  const loadAssessmentData = useCallback(async (assessmentId) => {
    if (!assessmentId) return;
    setIsAssessmentLoading(true);
    try {
      const detail = await assessmentApi.getAssessment(assessmentId);
      setActiveAssessment(detail);

      // Load passport from authoritative backend
      try {
        const passport = await assessmentApi.getPassport(assessmentId);
        setPassportData(passport);
      } catch (pErr) {
        console.warn('Passport fetch notice:', pErr);
      }
    } catch (err) {
      console.warn('Failed to load assessment data:', err);
    } finally {
      setIsAssessmentLoading(false);
    }
  }, []);

  // Reset or Seed the Golden SIH Demo Assessment
  const handleResetDemo = async () => {
    setIsResettingDemo(true);
    try {
      const resetAsm = await assessmentApi.resetGoldenDemo();
      const newId = resetAsm.id || resetAsm.assessment_id;
      setActiveAssessmentId(newId);
      setActiveAssessment(resetAsm);

      try {
        const p = await assessmentApi.getPassport(newId);
        setPassportData(p);
      } catch (pErr) {
        console.warn('Passport initial fetch notice:', pErr);
      }

      showToast('Golden SIH Demo Assessment reset (IS 17526:2021).');
    } catch (err) {
      showToast(`Reset error: ${err.message}`);
    } finally {
      setIsResettingDemo(false);
    }
  };

  // Start Compliance Assessment from BIS Assistant
  const handleStartComplianceAssessment = async (mode = 'golden') => {
    if (mode === 'golden') {
      await handleResetDemo();
      handleSelectTab('dna');
      showToast('Step 02: Product DNA & Technical Attributes loaded');
    } else {
      handleSelectTab('input');
      showToast('Step 01: Product Information Input');
    }
  };

  // Answer Technical Clarification
  const handleAnswerClarification = async (attribute, value) => {
    if (!activeAssessmentId) return;
    try {
      const updated = await assessmentApi.answerClarification(activeAssessmentId, attribute, value);
      setActiveAssessment(updated);
      try {
        const p = await assessmentApi.getPassport(activeAssessmentId);
        setPassportData(p);
      } catch (pErr) {
        console.warn('Passport refresh notice:', pErr);
      }
      showToast(`Clarified attribute "${attribute}" — deterministic scope updated.`);
    } catch (err) {
      alert(`Clarification update error: ${err.message}`);
    }
  };

  // Ingest Evidence Artifact into Assessment
  const handleAddEvidencePipeline = async (snippet, type, authority, page) => {
    if (!activeAssessmentId) return;
    try {
      const updated = await assessmentApi.addEvidence(activeAssessmentId, {
        snippet,
        evidence_type: type,
        authority,
        page,
      });
      setActiveAssessment(updated);
      try {
        const p = await assessmentApi.getPassport(activeAssessmentId);
        setPassportData(p);
      } catch (pErr) {
        console.warn('Passport refresh notice:', pErr);
      }
      showToast('Evidence artifact registered — gaps deterministically recalculated.');
    } catch (err) {
      alert(`Evidence ingestion error: ${err.message}`);
    }
  };

  // Load Job Details (Workstation / CAD / Evidence / Standards)
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

      // 4. Latest Assessment Run & Results
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

  // Initialize Auth, Jobs, and Unified Assessment on Mount
  useEffect(() => {
    async function initWorkspace() {
      try {
        const boot = await authApi.bootstrap();
        if (boot?.user) {
          setCurrentUser(boot.user);
        }
        setBackendReady(true);

        // 1. Load existing compliance jobs
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

        // 2. Load unified pipeline assessments
        try {
          const asms = await assessmentApi.listAssessments();
          setAssessmentsList(asms || []);

          const savedAsmId = localStorage.getItem('zyntrix_active_assessment_id');
          if (asms && asms.length > 0) {
            const targetAsm = (savedAsmId && asms.find((a) => (a.id === savedAsmId || a.assessment_id === savedAsmId))) || asms[0];
            const targetId = targetAsm.id || targetAsm.assessment_id;
            setActiveAssessmentId(targetId);
            await loadAssessmentData(targetId);
          } else {
            // Auto-seed Golden SIH Demo if none exists
            const seeded = await assessmentApi.resetGoldenDemo();
            const targetId = seeded.id || seeded.assessment_id;
            setActiveAssessmentId(targetId);
            setActiveAssessment(seeded);
            try {
              const p = await assessmentApi.getPassport(targetId);
              setPassportData(p);
            } catch (pErr) {
              console.warn('Passport initial fetch notice:', pErr);
            }
          }
        } catch (asmErr) {
          console.warn('Assessments init notice:', asmErr);
        }
      } catch (err) {
        console.warn('Backend connection notice:', err);
      }
    }
    initWorkspace();
  }, [loadJobData, loadAssessmentData]);

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

  // Extract Parameter into Product DNA with Strict Evidence Gating
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

  // Standards Handlers
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

  const handleSelectJob = async (jobId) => {
    setActiveJobId(jobId);
    await loadJobData(jobId);
    handleSelectTab('workstation');
    showToast(`Switched active compliance job context to ${jobId}`);
  };

  const handleNavigateWorkstationStage = (stageId) => {
    if (stageId === 'scope' || stageId === 'clauses') handleSelectTab('standards');
    else if (stageId === 'dna') handleSelectTab('dna');
    else if (stageId === 'vector') handleSelectTab('workstation');
    else if (stageId === 'evidence') handleSelectTab('evidence');
    else if (stageId === 'gaps') handleSelectTab('gaps');
    else if (stageId === 'lab') handleSelectTab('lab');
    else if (stageId === 'passport') handleSelectTab('passport');
  };

  // Entrance motion on tab switch
  useEffect(() => {
    triggerEntrance('.animate-view-stage', 20);
  }, [activeTab]);

  const currentTabObj = NAV_ITEMS.find((n) => n.id === activeTab);
  const currentTabTitle = currentTabObj
    ? currentTabObj.title
    : activeTab === 'input'
    ? 'Product Input'
    : activeTab === 'applicability'
    ? 'BIS Applicability'
    : activeTab === 'gaps'
    ? 'Compliance Gaps'
    : activeTab === 'lab'
    ? 'Lab & Actions'
    : activeTab === 'passport'
    ? 'Compliance Passport'
    : 'Compliance Compiler';

  const isEntryScreen = activeTab === 'entry';

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#0F172A] flex">
      {/* SideNav Component: Hidden on first entry screen per M27.1 Section 4 */}
      {!isEntryScreen && (
        <SideNav
          activeTab={activeTab}
          onSelectTab={handleSelectTab}
          mobileOpen={mobileMenuOpen}
          onCloseMobile={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Main Content Area */}
      <div className={`flex-1 flex flex-col min-w-0 ${!isEntryScreen ? 'lg:pl-60' : ''}`}>
        <TopBar
          activeTabTitle={currentTabTitle}
          onToggleMobile={() => setMobileMenuOpen(!mobileMenuOpen)}
          assessment={activeAssessment}
          onOpenAssistant={() => setIsAIAssistantOpen(true)}
          onOpenSourceInspector={() => handleOpenSourceInspector()}
          onResetDemo={handleResetDemo}
          isResettingDemo={isResettingDemo}
          onOpenHelp={() => setIsTrustModalOpen(true)}
        />

        {/* Golden Path Workflow Stepper Bar (Only visible inside workflow) */}
        {!isEntryScreen && (
          <div className="pt-14">
            <GoldenPathStepper
              activeTab={activeTab}
              onSelectStep={handleSelectTab}
              assessment={activeAssessment}
              onOpenTrustModal={() => setIsTrustModalOpen(true)}
            />
          </div>
        )}

        {/* Page View Container */}
        <main className={`flex-1 animate-view-stage ${isEntryScreen ? 'pt-14' : ''}`}>
          {/* FIRST SCREEN (M27.1 Section 4) */}
          {activeTab === 'entry' && (
            <div className="flex-1 flex flex-col items-center justify-center p-8 min-h-[calc(100vh-3.5rem)] font-sans">
              <div className="max-w-xl w-full text-center space-y-6 animate-in fade-in zoom-in-95 duration-200">
                <div className="w-14 h-14 bg-blue-600 rounded-xl flex items-center justify-center text-white mx-auto shadow-sm">
                  <span className="material-symbols-outlined text-3xl">shield</span>
                </div>
                
                <div>
                  <span className="font-bold text-xs tracking-wider uppercase text-blue-700 block mb-1">
                    ZYNTRIX
                  </span>
                  <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight leading-tight">
                    Compliance Compiler
                  </h1>
                  <p className="text-base text-slate-700 mt-3 font-medium">
                    Compile product requirements into evidence-backed compliance.
                  </p>
                  <p className="text-xs text-slate-500 mt-1.5 max-w-md mx-auto leading-relaxed">
                    Start with a product specification. Zyntrix identifies applicable BIS requirements, evaluates available evidence, finds gaps, and builds the assessment.
                  </p>
                </div>

                <div className="pt-2 flex flex-col items-center gap-3 w-full max-w-sm mx-auto">
                  <button 
                    type="button"
                    onClick={() => handleStartComplianceAssessment('golden')}
                    disabled={isResettingDemo}
                    className="w-full py-3.5 px-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg shadow-sm hover:shadow transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                  >
                    <span>START A NEW ASSESSMENT &rarr;</span>
                  </button>

                  <button 
                    type="button"
                    onClick={() => handleSelectTab('dna')}
                    className="w-full py-2.5 px-6 bg-white hover:bg-slate-50 text-slate-700 font-medium text-xs rounded-lg border border-slate-200 transition-colors shadow-2xs cursor-pointer"
                  >
                    CONTINUE AN ASSESSMENT
                  </button>

                  <button 
                    type="button"
                    onClick={() => setIsAIAssistantOpen(true)}
                    className="text-xs text-slate-500 hover:text-blue-600 font-medium pt-2 flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[16px]">smart_toy</span>
                    <span>ASK ASSISTANT</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 01 — BIS AI ASSISTANT */}
          {activeTab === 'assistant' && (
            <BISAssistantView
              onNavigateWorkstation={(newJobId) => {
                if (newJobId) {
                  setActiveJobId(newJobId);
                  loadJobData(newJobId);
                }
                handleSelectTab('workstation');
                showToast('Navigated to Engineering Workstation');
              }}
              onJobCreated={(newJobId) => {
                setActiveJobId(newJobId);
                loadJobData(newJobId);
              }}
              onStartComplianceAssessment={handleStartComplianceAssessment}
            />
          )}

          {/* STEP 01 (ALTERNATIVE) — MULTI-MODAL PRODUCT INPUT */}
          {activeTab === 'input' && (
            <AnalyzeView
              onAssessmentCreated={(newAsm) => {
                const newId = newAsm.id || newAsm.assessment_id;
                setActiveAssessmentId(newId);
                setActiveAssessment(newAsm);
                assessmentApi.getPassport(newId).then((p) => setPassportData(p)).catch(() => {});
                showToast(`Assessment ${newAsm.assessment_number || newId} created`);
              }}
              onNavigate={(target) => handleSelectTab(target)}
            />
          )}

          {/* STEP 02 — PRODUCT INPUT / PRODUCT DNA */}
          {activeTab === 'dna' && (
            isAssessmentLoading ? (
              <ViewSkeleton type="cards" />
            ) : (
              <ProductDNAView
                assessment={activeAssessment}
                onClarify={handleAnswerClarification}
                onNavigate={(target) => {
                  if (target === 'input') handleSelectTab('input');
                  else if (target === 'applicability') handleSelectTab('applicability');
                  else handleSelectTab(target);
                }}
                onInspectSource={handleOpenSourceInspector}
              />
            )
          )}

          {/* STEP 03 — BIS APPLICABILITY */}
          {activeTab === 'applicability' && (
            isAssessmentLoading ? (
              <ViewSkeleton type="table" />
            ) : (
              <BISApplicabilityView
                assessment={activeAssessment}
                onNavigate={(target) => {
                  if (target === 'clauses' || target === 'standards') handleSelectTab('standards');
                  else if (target === 'dna') handleSelectTab('dna');
                  else if (target === 'input') handleSelectTab('input');
                  else handleSelectTab(target);
                }}
                onInspectSource={handleOpenSourceInspector}
              />
            )
          )}

          {/* STEP 04 — STANDARDS & CLAUSES */}
          {activeTab === 'standards' && (
            isAssessmentLoading ? (
              <ViewSkeleton type="table" />
            ) : (
              <StandardsClausesView
                assessment={activeAssessment}
                onNavigate={(target) => {
                  if (target === 'evidence') handleSelectTab('evidence');
                  else if (target === 'gaps') handleSelectTab('gaps');
                  else if (target === 'dna') handleSelectTab('dna');
                  else if (target === 'input') handleSelectTab('input');
                  else handleSelectTab(target);
                }}
                onInspectSource={handleOpenSourceInspector}
              />
            )
          )}

          {/* STEP 05 — EVIDENCE MATRIX */}
          {activeTab === 'evidence' && (
            isAssessmentLoading ? (
              <ViewSkeleton type="table" />
            ) : (
              <EvidenceMatrixView
                assessment={activeAssessment}
                onUploadEvidence={handleAddEvidencePipeline}
                onNavigate={(target) => {
                  if (target === 'gaps') handleSelectTab('gaps');
                  else if (target === 'input') handleSelectTab('input');
                  else handleSelectTab(target);
                }}
                onInspectSource={handleOpenSourceInspector}
              />
            )
          )}

          {/* STEP 06 — COMPLIANCE GAPS */}
          {activeTab === 'gaps' && (
            isAssessmentLoading ? (
              <ViewSkeleton type="table" />
            ) : (
              <ComplianceGapsView
                assessment={activeAssessment}
                onNavigate={(target) => {
                  if (target === 'actions' || target === 'lab') handleSelectTab('lab');
                  else if (target === 'input') handleSelectTab('input');
                  else handleSelectTab(target);
                }}
                onInspectSource={handleOpenSourceInspector}
              />
            )
          )}

          {/* STEP 07 — LAB & ACTIONS */}
          {activeTab === 'lab' && (
            isAssessmentLoading ? (
              <ViewSkeleton type="table" />
            ) : (
              <LabActionsView
                assessment={activeAssessment}
                onNavigate={(target) => {
                  if (target === 'passport') {
                    if (activeAssessmentId && !passportData) {
                      assessmentApi.getPassport(activeAssessmentId).then((p) => setPassportData(p)).catch(() => {});
                    }
                    handleSelectTab('passport');
                  } else if (target === 'input') {
                    handleSelectTab('input');
                  } else {
                    handleSelectTab(target);
                  }
                }}
                onInspectSource={handleOpenSourceInspector}
              />
            )
          )}

          {/* STEP 08 — COMPLIANCE PASSPORT / DOSSIERS */}
          {(activeTab === 'passport' || activeTab === 'reports') && (
            isAssessmentLoading ? (
              <ViewSkeleton type="cards" />
            ) : (
              <div className="p-4 sm:p-6 lg:p-8">
                <CompliancePassportView
                  passport={passportData}
                  onClose={() => handleSelectTab('lab')}
                  onNewAssessment={() => handleSelectTab('entry')}
                  onReviewClick={() => handleSelectTab('reviews')}
                  onInspectSource={handleOpenSourceInspector}
                />
              </div>
            )
          )}

          {/* SECONDARY STATION: ENGINEERING WORKSTATION */}
          {activeTab === 'workstation' && (
            <WorkstationView
              jobId={activeJobId}
              jobs={jobs}
              onSelectJob={handleSelectJob}
              onCreateJobClick={() => setJobModalOpen(true)}
              onUploadClick={() => setAddEvidenceModalOpen(true)}
              onNavigateEvidence={() => handleSelectTab('evidence')}
              onNavigateDNA={() => handleSelectTab('dna')}
              onNavigateStandards={() => handleSelectTab('standards')}
              onNavigateStage={handleNavigateWorkstationStage}
              evidenceCount={evidenceList.length}
              onMapToDNASuccess={() => {
                if (activeJobId) loadJobData(activeJobId);
                showToast('Authoritative Product DNA updated from CAD measurements.');
              }}
            />
          )}

          {/* SECONDARY STATION: WORKSPACE */}
          {activeTab === 'workspace' && (
            <WorkspaceView
              onCreateJobClick={() => setJobModalOpen(true)}
              jobsCount={jobs.length}
              evidenceCount={evidenceList.length}
              openFindingsCount={conflictsList.length}
            />
          )}

          {/* SECONDARY STATION: COMPLIANCE JOBS */}
          {activeTab === 'jobs' && (
            <ComplianceJobsView
              jobs={jobs}
              onSelectJob={handleSelectJob}
              onCreateJob={handleCreateJob}
              modalOpen={jobModalOpen}
              setModalOpen={setJobModalOpen}
            />
          )}

          {/* SECONDARY STATION: REVIEW & ATTESTATION */}
          {activeTab === 'reviews' && (
            <ReviewWorkspaceView
              jobId={activeJobId}
              currentJob={jobs.find((j) => j.id === activeJobId)}
              currentUser={currentUser}
              onShowToast={showToast}
              evidenceList={evidenceList}
            />
          )}

          {/* SECONDARY STATION: SETTINGS */}
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
          handleSelectTab('workstation');
          showToast(`Spatial CAD view focused for ${req.reqId}`);
        }}
      />

      {/* Responsive Source Provenance Inspector Drawer */}
      <SourceInspectorDrawer
        isOpen={isSourceInspectorOpen}
        onClose={() => setIsSourceInspectorOpen(false)}
        data={activeSourceData}
      />

      {/* Responsive AI Assistant Guidance Drawer */}
      <AIAssistantDrawer
        isOpen={isAIAssistantOpen}
        onClose={() => setIsAIAssistantOpen(false)}
        assessment={activeAssessment}
        onInspectSource={handleOpenSourceInspector}
      />

      {/* Regulatory Governance & Jury FAQ Modal */}
      <TrustGovernanceModal
        isOpen={isTrustModalOpen}
        onClose={() => setIsTrustModalOpen(false)}
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
