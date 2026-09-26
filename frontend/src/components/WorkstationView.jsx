import React, { useState } from 'react';
import { DigitalTwinViewport } from './DigitalTwinViewport';

const WORKFLOW_STAGES = [
  { id: 'scope', step: '01', title: 'Scope & Standards' },
  { id: 'dna', step: '02', title: 'Product DNA' },
  { id: 'vector', step: '03', title: 'Vector Inspection' },
  { id: 'clauses', step: '04', title: 'Statutory Clauses' },
  { id: 'evidence', step: '05', title: 'Evidence Matrix' },
  { id: 'gaps', step: '06', title: 'Findings & Gaps' },
  { id: 'lab', step: '07', title: 'Lab Testing' },
  { id: 'passport', step: '08', title: 'Compliance Passport' },
];

export function WorkstationView({
  jobId,
  jobs = [],
  onSelectJob,
  onCreateJobClick,
  onUploadClick,
  onNavigateEvidence,
  onNavigateDNA,
  onNavigateStandards,
  onNavigateStage,
  evidenceCount = 0,
  onMapToDNASuccess,
}) {
  const [activeStage, setActiveStage] = useState('scope');
  const [cadMeasurements, setCadMeasurements] = useState([]);

  const handleStageClick = (stageId) => {
    setActiveStage(stageId);
    if (onNavigateStage) {
      onNavigateStage(stageId);
    } else if (stageId === 'evidence' && onNavigateEvidence) {
      onNavigateEvidence();
    } else if (stageId === 'dna' && onNavigateDNA) {
      onNavigateDNA();
    } else if ((stageId === 'scope' || stageId === 'clauses') && onNavigateStandards) {
      onNavigateStandards();
    }
  };

  return (
    <div className="w-full flex flex-col">
      {/* 8-Stage Workflow Sub-Navigation */}
      <div className="bg-white border-b border-[#E2E8F0] px-4 sm:px-6 lg:px-8">
        <div className="flex items-center overflow-x-auto no-scrollbar gap-1 py-1">
          {WORKFLOW_STAGES.map((s) => {
            const isActive = activeStage === s.id;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => handleStageClick(s.id)}
                className={`flex items-center gap-1.5 px-3 py-2 border-b-2 text-xs whitespace-nowrap transition-colors ${
                  isActive
                    ? 'border-[#1D4ED8] text-[#1D4ED8] font-semibold'
                    : 'border-transparent text-[#64748B] hover:text-[#0F172A] hover:border-slate-300'
                }`}
              >
                <span className="font-mono text-[11px] opacity-70">{s.step}</span>
                <span>{s.title}</span>
                {s.id === 'evidence' && evidenceCount > 0 && (
                  <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-blue-100 text-blue-800">
                    {evidenceCount}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Hero Section */}
      <section className="w-full px-4 sm:px-6 lg:px-8 py-6 bg-white border-b border-[#E2E8F0]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[11px] font-mono font-medium mb-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
              DETERMINISTIC STATUTORY COMPILER
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0F172A]">
              Compile compliance with confidence.
            </h1>
            <p className="text-xs sm:text-sm text-[#475569] mt-1 leading-relaxed">
              Automated statutory regulatory compilation against official BIS Gazette standards, multimodal technical files, and spatial CAD engineering geometry.
            </p>
          </div>

          {/* Action CTAs */}
          <div className="flex items-center gap-2.5 shrink-0">
            <button
              type="button"
              onClick={onUploadClick}
              className="px-3.5 py-2 text-xs font-medium text-[#0F172A] bg-white border border-[#E2E8F0] hover:bg-[#F8F9FA] rounded transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-sm">upload_file</span>
              Add Evidence
            </button>
            <button
              type="button"
              onClick={onCreateJobClick}
              className="px-3.5 py-2 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              Create Compliance Job
            </button>
          </div>
        </div>
      </section>

      {/* Workstation Main: 3D CAD Twin & Spatial Vector Telemetry */}
      <section className="w-full px-4 sm:px-6 lg:px-8 py-6 bg-[#F8F9FA]">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left / Center 2 Cols: Babylon.js Viewport */}
          <div className="xl:col-span-2 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-[#1D4ED8]">view_in_ar</span>
                <h2 className="text-xs font-bold uppercase tracking-wider text-[#0F172A] font-mono">
                  Compile Compliance
                </h2>
              </div>
              <span className="font-mono text-[11px] text-[#64748B]">
                Engine: Babylon.js v9.27
              </span>
            </div>

            {/* Document Specification Intake Console */}
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-3.5 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xs">
              <div className="flex items-center gap-2.5 w-full sm:w-auto">
                <div className="w-8 h-8 rounded-md bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shrink-0">
                  <span className="material-symbols-outlined text-[18px]">description</span>
                </div>
                <div className="text-xs">
                  <div className="font-semibold text-[#0F172A]">Document Technical Specifications</div>
                  <div className="text-[11px] text-[#64748B]">
                    Provide document specifications to extract Product DNA, detect applicable BIS standards, and identify compliance gaps.
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto justify-end shrink-0">
                <button
                  type="button"
                  onClick={onUploadClick}
                  className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-md flex items-center gap-1.5 cursor-pointer transition-colors"
                >
                  <span className="material-symbols-outlined text-[15px]">upload_file</span>
                  <span>Upload Document</span>
                </button>
                <button
                  type="button"
                  onClick={() => onNavigateDNA && onNavigateDNA()}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded-md flex items-center gap-1.5 shadow-2xs cursor-pointer transition-colors"
                >
                  <span>Compile Compliance &rarr;</span>
                </button>
              </div>
            </div>

            <DigitalTwinViewport
              jobId={jobId}
              onUploadClick={onUploadClick}
              onMeasurementsLoaded={(meas) => setCadMeasurements(meas || [])}
              onMapToDNASuccess={onMapToDNASuccess}
            />
          </div>

          {/* Right Col: Spatial Vector Inspection Panel */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-[#1D4ED8]">straighten</span>
                <h2 className="text-xs font-bold uppercase tracking-wider text-[#0F172A] font-mono">
                  Spatial Vector Telemetry
                </h2>
              </div>
              <span
                className={`font-mono text-[10px] px-2 py-0.5 rounded border ${
                  cadMeasurements.length > 0
                    ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
                    : 'text-amber-700 bg-amber-50 border-amber-200'
                }`}
              >
                {cadMeasurements.length > 0 ? `${cadMeasurements.length} Vectors Measured` : 'Awaiting Data'}
              </span>
            </div>

            <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 flex flex-col gap-4 shadow-sm">
              <div className="border-b border-[#E2E8F0] pb-3">
                <span className="font-mono text-[10px] uppercase tracking-wider text-[#64748B] block mb-1">
                  Active Model Geometry
                </span>
                <h3 className="font-bold text-sm text-[#0F172A]">
                  {cadMeasurements.length > 0
                    ? 'Deterministic CAD Features Established'
                    : 'No active inspection vector'}
                </h3>
                <p className="text-xs text-[#64748B] mt-1 leading-relaxed">
                  {cadMeasurements.length > 0
                    ? 'ISO 10303-21 B-Rep topology parsed. Spatial dimensions, wall profiles, and clearance vectors derived authoritatively.'
                    : 'Select or initiate a compliance job to visualize spatial creepage, clearance, and enclosure dimension verifications.'}
                </p>
              </div>

              {/* Technical Telemetry Slots */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-[#F8F9FA] p-2.5 rounded border border-[#E2E8F0]">
                  <span className="font-mono text-[10px] text-[#64748B] block">Clearance / Wall</span>
                  <span className="font-mono text-sm font-semibold text-[#0F172A] mt-0.5 block">
                    {(() => {
                      const m = cadMeasurements.find((x) => x.measurement_type === 'WALL_THICKNESS' || x.measurement_type === 'CLEARANCE');
                      return m ? `${m.value} ${m.unit}` : '-- mm';
                    })()}
                  </span>
                </div>
                <div className="bg-[#F8F9FA] p-2.5 rounded border border-[#E2E8F0]">
                  <span className="font-mono text-[10px] text-[#64748B] block">Bounding Extents (Z)</span>
                  <span className="font-mono text-sm font-semibold text-[#0F172A] mt-0.5 block">
                    {(() => {
                      const m = cadMeasurements.find((x) => x.measurement_type === 'BOUNDING_BOX_Z');
                      return m ? `${m.value} ${m.unit}` : '-- mm';
                    })()}
                  </span>
                </div>
                <div className="bg-[#F8F9FA] p-2.5 rounded border border-[#E2E8F0]">
                  <span className="font-mono text-[10px] text-[#64748B] block">Envelope Dimensions</span>
                  <span className="font-mono text-xs font-semibold text-[#0F172A] mt-0.5 block">
                    {(() => {
                      const mx = cadMeasurements.find((x) => x.measurement_type === 'BOUNDING_BOX_X');
                      const my = cadMeasurements.find((x) => x.measurement_type === 'BOUNDING_BOX_Y');
                      return mx && my ? `${mx.value} × ${my.value} mm` : '-- mm';
                    })()}
                  </span>
                </div>
                <div className="bg-[#F8F9FA] p-2.5 rounded border border-[#E2E8F0]">
                  <span className="font-mono text-[10px] text-[#64748B] block">CAD Status</span>
                  <span
                    className={`font-mono text-sm font-semibold mt-0.5 block ${
                      cadMeasurements.length > 0 ? 'text-emerald-600' : 'text-slate-400'
                    }`}
                  >
                    {cadMeasurements.length > 0 ? 'VERIFIED' : 'UNTESTED'}
                  </span>
                </div>
              </div>

              <div className="p-3 bg-blue-50/60 rounded border border-blue-100 flex items-start gap-2.5">
                <span className="material-symbols-outlined text-blue-600 text-sm mt-0.5">info</span>
                <div className="text-[11px] text-blue-900 leading-relaxed">
                  Deterministic clearance calculations follow BIS standard clause requirements and geometric contours once technical files are uploaded.
                </div>
              </div>
            </div>

            {/* Multimodal Ingestion Card */}
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 flex flex-col items-center text-center shadow-sm">
              <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-[#64748B] mb-2">
                <span className="material-symbols-outlined text-lg">drive_folder_upload</span>
              </div>
              <h4 className="text-xs font-semibold text-[#0F172A]">
                Multimodal Evidence Ingestion
              </h4>
              <p className="text-[11px] text-[#64748B] mt-1 max-w-xs">
                Supports PDF standards, acoustic recordings, visual photos, and STEP/CAD geometry.
              </p>
              <div className="flex items-center gap-2 mt-3 w-full">
                <button
                  type="button"
                  onClick={onUploadClick}
                  className="flex-1 py-1.5 bg-[#1D4ED8] hover:bg-[#1E40AF] text-white rounded text-xs font-medium transition-colors flex items-center justify-center gap-1 shadow-sm"
                >
                  <span className="material-symbols-outlined text-sm">add_circle</span>
                  Add Evidence
                </button>
                {evidenceCount > 0 && onNavigateEvidence && (
                  <button
                    type="button"
                    onClick={onNavigateEvidence}
                    className="py-1.5 px-3 bg-[#F8F9FA] hover:bg-slate-100 border border-[#E2E8F0] text-[#0F172A] rounded text-xs font-medium transition-colors"
                  >
                    View ({evidenceCount})
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Framework Architecture Cards */}
      <section className="w-full px-4 sm:px-6 lg:px-8 py-6 bg-white border-y border-[#E2E8F0]">
        <div className="mb-4">
          <span className="font-mono text-[10px] text-[#64748B] uppercase tracking-wider font-semibold">
            ENGINEERING ARCHITECTURE
          </span>
          <h2 className="text-sm font-bold text-[#0F172A]">
            The BIS Compliance Compiler Framework
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="p-4 rounded-lg bg-[#F8F9FA] border border-[#E2E8F0] flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded bg-blue-100 text-[#1D4ED8] flex items-center justify-center mb-3">
                <span className="material-symbols-outlined text-base">sync</span>
              </div>
              <h3 className="text-xs font-bold text-[#0F172A] mb-1">
                BIS Standards &amp; Gazette Sync
              </h3>
              <p className="text-xs text-[#475569] leading-relaxed">
                Direct synchronization with official BIS Gazette notifications and gazetted standard schedules for live regulatory accuracy.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#E2E8F0] flex items-center justify-between text-[11px] font-mono text-[#64748B]">
              <span>Sync Protocol</span>
              <span className="text-emerald-700 font-semibold">ACTIVE</span>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-[#F8F9FA] border border-[#E2E8F0] flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded bg-blue-100 text-[#1D4ED8] flex items-center justify-center mb-3">
                <span className="material-symbols-outlined text-base">hub</span>
              </div>
              <h3 className="text-xs font-bold text-[#0F172A] mb-1">
                Tri-Tier Evidentiary Traceability
              </h3>
              <p className="text-xs text-[#475569] leading-relaxed">
                Every clause determination links directly to spatial 3D measurements, physical laboratory reports, and engineering attestations.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#E2E8F0] flex items-center justify-between text-[11px] font-mono text-[#64748B]">
              <span>Citation Chain</span>
              <span className="text-blue-700 font-semibold">STRICT</span>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-[#F8F9FA] border border-[#E2E8F0] flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded bg-blue-100 text-[#1D4ED8] flex items-center justify-center mb-3">
                <span className="material-symbols-outlined text-base">terminal</span>
              </div>
              <h3 className="text-xs font-bold text-[#0F172A] mb-1">
                Deterministic Compliance Compiler
              </h3>
              <p className="text-xs text-[#475569] leading-relaxed">
                Eliminates LLM hallucinations through formal statutory predicate logic, gap analysis matrices, and reproducible artifact trees.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#E2E8F0] flex items-center justify-between text-[11px] font-mono text-[#64748B]">
              <span>Verification</span>
              <span className="text-purple-700 font-semibold">PROVABLE</span>
            </div>
          </div>
        </div>
      </section>

      {/* Active Compliance Register (Table with Pure Empty State) */}
      <section className="w-full px-4 sm:px-6 lg:px-8 py-6 bg-[#F8F9FA]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-[#0F172A]">
              Active Compliance Register
            </h2>
            <p className="text-xs text-[#64748B] mt-0.5">
              Live tracking of statutory audits, clause bindings, and dossier compilation progress.
            </p>
          </div>
          <button
            type="button"
            onClick={onCreateJobClick}
            className="px-3 py-1.5 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <span className="material-symbols-outlined text-sm">add</span>
            New Job
          </button>
        </div>

        {/* Table Container */}
        <div className="bg-white border border-[#E2E8F0] rounded-lg overflow-hidden shadow-sm">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#F8F9FA] border-b border-[#E2E8F0] font-mono text-[11px] text-[#64748B]">
                <th className="py-2.5 px-4 font-semibold">JOB IDENTIFIER</th>
                <th className="py-2.5 px-4 font-semibold">PRODUCT &amp; SKU</th>
                <th className="py-2.5 px-4 font-semibold">STATUTORY STANDARD</th>
                <th className="py-2.5 px-4 font-semibold">EVIDENTIARY STATUS</th>
                <th className="py-2.5 px-4 font-semibold">ATTESTATION</th>
                <th className="py-2.5 px-4 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody>
              {jobs && jobs.length > 0 ? (
                jobs.map((job) => (
                  <tr key={job.id} className="border-b border-[#E2E8F0] hover:bg-[#F8F9FA] transition-colors">
                    <td className="py-3 px-4 font-mono font-semibold text-[#1D4ED8]">
                      {job.jobNumber || job.id}
                    </td>
                    <td className="py-3 px-4 font-medium text-[#0F172A]">
                      {job.productName || job.title}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-[#0F172A]">
                      {job.standard || 'IS 17526:2021'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {job.stage || 'STAGE_EVALUATED'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                        {job.status || 'ACTIVE'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => onSelectJob?.(job.id)}
                        className="px-2.5 py-1 text-xs font-semibold text-[#1D4ED8] hover:bg-blue-50 rounded border border-blue-200 transition-colors cursor-pointer"
                      >
                        Open Job
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                /* Clean Empty State */
                <tr>
                  <td colSpan={6} className="py-12 px-4 text-center">
                    <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-[#94A3B8] mx-auto mb-3">
                      <span className="material-symbols-outlined text-2xl">rule_folder</span>
                    </div>
                    <h3 className="text-sm font-semibold text-[#0F172A] mb-1">
                      No compliance jobs registered yet
                    </h3>
                    <p className="text-xs text-[#64748B] max-w-sm mx-auto mb-4">
                      Initiate your first compliance job or upload product documentation to begin deterministic statutory evaluation.
                    </p>
                    <button
                      type="button"
                      onClick={onCreateJobClick}
                      className="px-3.5 py-2 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors inline-flex items-center gap-1.5 shadow-sm"
                    >
                      <span className="material-symbols-outlined text-sm">add</span>
                      Create Your First Compliance Job
                    </button>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
