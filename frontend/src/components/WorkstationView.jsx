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
    <div className="w-full flex flex-col bg-[#090d16] text-slate-100 min-h-screen">
      {/* 8-Stage Workflow Sub-Navigation */}
      <div className="bg-[#0b0f19] border-b border-slate-800/80 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center overflow-x-auto no-scrollbar gap-1 py-1 max-w-7xl mx-auto">
          {WORKFLOW_STAGES.map((s) => {
            const isActive = activeStage === s.id;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => handleStageClick(s.id)}
                className={`flex items-center gap-1.5 px-3 py-2 border-b-2 text-xs whitespace-nowrap transition-all cursor-pointer ${
                  isActive
                    ? 'border-cyan-400 text-cyan-400 font-semibold bg-cyan-950/20'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <span className="font-mono text-[11px] opacity-70">{s.step}</span>
                <span>{s.title}</span>
                {s.id === 'evidence' && evidenceCount > 0 && (
                  <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800/60">
                    {evidenceCount}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Hero Section */}
      <section className="w-full px-4 sm:px-6 lg:px-8 py-6 bg-[#0b0f19]/60 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-[11px] font-mono font-medium mb-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
              DETERMINISTIC STATUTORY COMPILER
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 font-['Space_Grotesk']">
              Compile compliance with confidence.
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 leading-relaxed">
              Automated statutory regulatory compilation against official BIS Gazette standards, multimodal technical files, and spatial CAD engineering geometry.
            </p>
          </div>

          {/* Action CTAs */}
          <div className="flex items-center gap-2.5 shrink-0">
            <button
              type="button"
              onClick={onUploadClick}
              className="px-3.5 py-2 text-xs font-medium text-slate-300 bg-slate-900/90 border border-slate-700/80 hover:bg-slate-800 hover:text-slate-100 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm">upload_file</span>
              Add Evidence
            </button>
            <button
              type="button"
              onClick={onCreateJobClick}
              className="px-4 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all flex items-center gap-1.5 shadow-lg shadow-cyan-500/10 cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm font-bold">add</span>
              Create Compliance Job
            </button>
          </div>
        </div>
      </section>

      {/* Workstation Main: 3D CAD Twin & Spatial Vector Telemetry */}
      <section className="w-full px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left / Center 2 Cols: Babylon.js Viewport */}
          <div className="xl:col-span-2 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-cyan-400">view_in_ar</span>
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
                  Spatial CAD Workstation
                </h2>
              </div>
              <span className="font-mono text-[11px] text-slate-500">
                Engine: Babylon.js v9.27
              </span>
            </div>

            {/* Document Specification Intake Console */}
            <div className="bg-[#0f1422]/90 backdrop-blur-md border border-slate-800/80 rounded-xl p-3.5 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-lg">
              <div className="flex items-center gap-3 w-full sm:w-auto">
                <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 shrink-0">
                  <span className="material-symbols-outlined text-[18px]">description</span>
                </div>
                <div className="text-xs">
                  <div className="font-semibold text-slate-200 font-['Space_Grotesk']">Document Technical Specifications</div>
                  <div className="text-[11px] text-slate-400">
                    Provide document specifications to extract Product DNA, detect applicable BIS standards, and identify compliance gaps.
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto justify-end shrink-0">
                <button
                  type="button"
                  onClick={onUploadClick}
                  className="px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg flex items-center gap-1.5 cursor-pointer transition-colors"
                >
                  <span className="material-symbols-outlined text-[15px]">upload_file</span>
                  <span>Upload Document</span>
                </button>
                <button
                  type="button"
                  onClick={() => onNavigateDNA && onNavigateDNA()}
                  className="px-3.5 py-1.5 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg flex items-center gap-1.5 shadow-md shadow-cyan-500/20 cursor-pointer transition-all"
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
                <span className="material-symbols-outlined text-base text-cyan-400">straighten</span>
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
                  Spatial Vector Telemetry
                </h2>
              </div>
              <span
                className={`font-mono text-[10px] px-2.5 py-0.5 rounded-full border ${
                  cadMeasurements.length > 0
                    ? 'text-emerald-300 bg-emerald-950/60 border-emerald-800/60'
                    : 'text-amber-300 bg-amber-950/60 border-amber-800/60'
                }`}
              >
                {cadMeasurements.length > 0 ? `${cadMeasurements.length} Vectors Measured` : 'Awaiting Data'}
              </span>
            </div>

            <div className="bg-[#0f1422]/90 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 flex flex-col gap-4 shadow-xl">
              <div className="border-b border-slate-800 pb-3">
                <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
                  Active Model Geometry
                </span>
                <h3 className="font-bold text-sm text-slate-100 font-['Space_Grotesk']">
                  {cadMeasurements.length > 0
                    ? 'Deterministic CAD Features Established'
                    : 'No active inspection vector'}
                </h3>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  {cadMeasurements.length > 0
                    ? 'ISO 10303-21 B-Rep topology parsed. Spatial dimensions, wall profiles, and clearance vectors derived authoritatively.'
                    : 'Select or initiate a compliance job to visualize spatial creepage, clearance, and enclosure dimension verifications.'}
                </p>
              </div>

              {/* Technical Telemetry Slots */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                  <span className="font-mono text-[10px] text-slate-400 block">Clearance / Wall</span>
                  <span className="font-mono text-sm font-semibold text-cyan-400 mt-0.5 block">
                    {(() => {
                      const m = cadMeasurements.find((x) => x.measurement_type === 'WALL_THICKNESS' || x.measurement_type === 'CLEARANCE');
                      return m ? `${m.value} ${m.unit}` : '-- mm';
                    })()}
                  </span>
                </div>
                <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                  <span className="font-mono text-[10px] text-slate-400 block">Bounding Extents (Z)</span>
                  <span className="font-mono text-sm font-semibold text-cyan-400 mt-0.5 block">
                    {(() => {
                      const m = cadMeasurements.find((x) => x.measurement_type === 'BOUNDING_BOX_Z');
                      return m ? `${m.value} ${m.unit}` : '-- mm';
                    })()}
                  </span>
                </div>
                <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                  <span className="font-mono text-[10px] text-slate-400 block">Envelope Dimensions</span>
                  <span className="font-mono text-xs font-semibold text-slate-200 mt-0.5 block">
                    {(() => {
                      const mx = cadMeasurements.find((x) => x.measurement_type === 'BOUNDING_BOX_X');
                      const my = cadMeasurements.find((x) => x.measurement_type === 'BOUNDING_BOX_Y');
                      return mx && my ? `${mx.value} × ${my.value} mm` : '-- mm';
                    })()}
                  </span>
                </div>
                <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                  <span className="font-mono text-[10px] text-slate-400 block">CAD Status</span>
                  <span
                    className={`font-mono text-xs font-semibold mt-1 inline-block px-1.5 py-0.5 rounded border ${
                      cadMeasurements.length > 0
                        ? 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60'
                        : 'text-slate-500 bg-slate-800/50 border-slate-700/50'
                    }`}
                  >
                    {cadMeasurements.length > 0 ? 'VERIFIED' : 'UNTESTED'}
                  </span>
                </div>
              </div>

              <div className="p-3 bg-cyan-950/40 rounded-lg border border-cyan-800/50 flex items-start gap-2.5">
                <span className="material-symbols-outlined text-cyan-400 text-sm mt-0.5">info</span>
                <div className="text-[11px] text-cyan-200 leading-relaxed">
                  Deterministic clearance calculations follow BIS standard clause requirements and geometric contours once technical files are uploaded.
                </div>
              </div>
            </div>

            {/* Multimodal Ingestion Card */}
            <div className="bg-[#0f1422]/90 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 flex flex-col items-center text-center shadow-xl">
              <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 mb-2">
                <span className="material-symbols-outlined text-lg">drive_folder_upload</span>
              </div>
              <h4 className="text-xs font-semibold text-slate-100 font-['Space_Grotesk']">
                Multimodal Evidence Ingestion
              </h4>
              <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
                Supports PDF standards, acoustic recordings, visual photos, and STEP/CAD geometry.
              </p>
              <div className="flex items-center gap-2 mt-4 w-full">
                <button
                  type="button"
                  onClick={onUploadClick}
                  className="flex-1 py-2 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 text-slate-950 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 shadow-md shadow-cyan-500/20 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-sm font-bold">add_circle</span>
                  Add Evidence
                </button>
                {evidenceCount > 0 && onNavigateEvidence && (
                  <button
                    type="button"
                    onClick={onNavigateEvidence}
                    className="py-2 px-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors cursor-pointer"
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
      <section className="w-full px-4 sm:px-6 lg:px-8 py-8 bg-[#0b0f19]/60 border-y border-slate-800/80">
        <div className="max-w-7xl mx-auto">
          <div className="mb-4">
            <span className="font-mono text-[10px] text-cyan-400 uppercase tracking-widest font-semibold">
              ENGINEERING ARCHITECTURE
            </span>
            <h2 className="text-sm font-bold text-slate-100 font-['Space_Grotesk'] mt-0.5">
              The BIS Compliance Compiler Framework
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="p-5 rounded-xl bg-[#0f1422]/90 border border-slate-800 flex flex-col justify-between hover:border-cyan-500/40 transition-colors shadow-lg">
              <div>
                <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyan-400 flex items-center justify-center mb-3">
                  <span className="material-symbols-outlined text-base">sync</span>
                </div>
                <h3 className="text-xs font-bold text-slate-100 font-['Space_Grotesk'] mb-1">
                  BIS Standards &amp; Gazette Sync
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Direct synchronization with official BIS Gazette notifications and gazetted standard schedules for live regulatory accuracy.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Sync Protocol</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  ACTIVE
                </span>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-[#0f1422]/90 border border-slate-800 flex flex-col justify-between hover:border-cyan-500/40 transition-colors shadow-lg">
              <div>
                <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyan-400 flex items-center justify-center mb-3">
                  <span className="material-symbols-outlined text-base">hub</span>
                </div>
                <h3 className="text-xs font-bold text-slate-100 font-['Space_Grotesk'] mb-1">
                  Tri-Tier Evidentiary Traceability
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Every clause determination links directly to spatial 3D measurements, physical laboratory reports, and engineering attestations.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Citation Chain</span>
                <span className="text-cyan-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                  STRICT
                </span>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-[#0f1422]/90 border border-slate-800 flex flex-col justify-between hover:border-cyan-500/40 transition-colors shadow-lg">
              <div>
                <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyan-400 flex items-center justify-center mb-3">
                  <span className="material-symbols-outlined text-base">terminal</span>
                </div>
                <h3 className="text-xs font-bold text-slate-100 font-['Space_Grotesk'] mb-1">
                  Deterministic Compliance Compiler
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Eliminates LLM hallucinations through formal statutory predicate logic, gap analysis matrices, and reproducible artifact trees.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Verification</span>
                <span className="text-purple-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                  PROVABLE
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Active Compliance Register (Table with Pure Empty State) */}
      <section className="w-full px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-100 font-['Space_Grotesk']">
                Active Compliance Register
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Live tracking of statutory audits, clause bindings, and dossier compilation progress.
              </p>
            </div>
            <button
              type="button"
              onClick={onCreateJobClick}
              className="px-3.5 py-1.5 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all flex items-center gap-1.5 shadow-md shadow-cyan-500/20 cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm font-bold">add</span>
              New Job
            </button>
          </div>

          {/* Table Container */}
          <div className="bg-[#0f1422]/90 backdrop-blur-md border border-slate-800/80 rounded-xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-900/60 border-b border-slate-800 font-mono text-[11px] text-slate-400 uppercase tracking-wider">
                    <th className="py-3 px-4 font-semibold">JOB IDENTIFIER</th>
                    <th className="py-3 px-4 font-semibold">PRODUCT &amp; SKU</th>
                    <th className="py-3 px-4 font-semibold">STATUTORY STANDARD</th>
                    <th className="py-3 px-4 font-semibold">EVIDENTIARY STATUS</th>
                    <th className="py-3 px-4 font-semibold">ATTESTATION</th>
                    <th className="py-3 px-4 font-semibold text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {jobs && jobs.length > 0 ? (
                    jobs.map((job) => (
                      <tr key={job.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-semibold text-cyan-400">
                          {job.jobNumber || job.id}
                        </td>
                        <td className="py-3.5 px-4 font-medium text-slate-200">
                          {job.productName || job.title}
                        </td>
                        <td className="py-3.5 px-4 font-mono text-[11px] text-slate-300">
                          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-300">
                            {job.standard || 'IS 16221-2:2015'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-800/60">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                            {job.stage || 'STAGE_EVALUATED'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="inline-block px-2.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                            {job.status || 'ACTIVE'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            type="button"
                            onClick={() => onSelectJob?.(job.id)}
                            className="px-2.5 py-1 text-xs font-medium text-cyan-300 hover:text-cyan-200 bg-cyan-950/60 hover:bg-cyan-900/60 rounded-md border border-cyan-800/60 transition-colors cursor-pointer"
                          >
                            Open Job
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    /* Clean Empty State */
                    <tr>
                      <td colSpan={6} className="py-16 px-4 text-center">
                        <div className="w-12 h-12 rounded-xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 mx-auto mb-3">
                          <span className="material-symbols-outlined text-2xl">rule_folder</span>
                        </div>
                        <h3 className="text-sm font-semibold text-slate-200 font-['Space_Grotesk'] mb-1">
                          No compliance jobs registered yet
                        </h3>
                        <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
                          Initiate your first compliance job or upload product documentation to begin deterministic statutory evaluation.
                        </p>
                        <button
                          type="button"
                          onClick={onCreateJobClick}
                          className="px-3.5 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all inline-flex items-center gap-1.5 shadow-md shadow-cyan-500/20 cursor-pointer"
                        >
                          <span className="material-symbols-outlined text-sm font-bold">add</span>
                          Create Your First Compliance Job
                        </button>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
