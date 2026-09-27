import React, { useState } from 'react';
import { GlideSelect } from './loading-ui';

const SAMPLE_STANDARDS = [
  { value: 'IS 16221-2:2015', label: 'IS 16221-2:2015 — PV Power Converters' },
  { value: 'IS 13252-1:2010', label: 'IS 13252-1:2010 — IT Equipment Safety' },
  { value: 'IS 616:2017', label: 'IS 616:2017 — Audio & Video Apparatus' },
  { value: 'IS 302-2-3:2017', label: 'IS 302-2-3:2017 — Household Appliances' },
  { value: 'IS 10322-5:2013', label: 'IS 10322-5:2013 — Luminaires & Floodlights' },
];

export function ComplianceJobsView({ jobs = [], onSelectJob, onCreateJob, modalOpen, setModalOpen }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [formData, setFormData] = useState({
    title: '',
    manufacturer: '',
    productName: '',
    standard: 'IS 16221-2:2015',
    notes: '',
  });

  const filteredJobs = jobs.filter((job) => {
    const q = searchQuery.toLowerCase();
    const id = (job.jobNumber || job.id || '').toLowerCase();
    const title = (job.productName || job.title || '').toLowerCase();
    const mfg = (job.manufacturer || '').toLowerCase();
    const std = (job.standard || '').toLowerCase();
    return id.includes(q) || title.includes(q) || mfg.includes(q) || std.includes(q);
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title.trim()) return;

    const newJob = {
      id: `JOB-${Date.now().toString().slice(-4)}`,
      jobNumber: `ZY-JOB-${Date.now().toString().slice(-4)}`,
      title: formData.title,
      manufacturer: formData.manufacturer || 'Unassigned Manufacturer',
      productName: formData.productName || formData.title,
      standard: formData.standard,
      status: 'AWAITING EVIDENCE',
      stage: 'AWAITING EVIDENCE',
      createdAt: new Date().toISOString().split('T')[0],
    };

    if (onCreateJob) {
      onCreateJob(newJob);
    }
    setModalOpen(false);
    setFormData({
      title: '',
      manufacturer: '',
      productName: '',
      standard: 'IS 16221-2:2015',
      notes: '',
    });
  };

  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-[10px] font-mono tracking-widest uppercase text-cyan-400 font-semibold">
              Deterministic Job Ledger
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 font-['Space_Grotesk']">
            Compliance Jobs Directory
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Manage, track, and execute deterministic statutory evaluations with tamper-evident audit trails.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="px-4 py-2.5 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all flex items-center gap-2 self-start sm:self-auto shadow-lg shadow-cyan-500/10 cursor-pointer active:scale-95"
        >
          <span className="material-symbols-outlined text-sm font-bold">add</span>
          New Compliance Job
        </button>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-[#0f1422]/90 backdrop-blur-md p-3 rounded-xl border border-slate-800/80 shadow-inner">
        <div className="relative w-full sm:w-88">
          <span className="material-symbols-outlined text-sm text-slate-500 absolute left-3 top-2.5">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter jobs by ID, product, standard, or entity..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900/80 border border-slate-700/60 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20 font-['Plus_Jakarta_Sans']"
          />
        </div>

        <div className="flex items-center gap-3 self-end sm:self-auto px-2">
          <span className="font-mono text-xs text-slate-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <strong className="text-slate-200 font-semibold">{filteredJobs.length}</strong> {filteredJobs.length === 1 ? 'Job' : 'Jobs'} Found
          </span>
        </div>
      </div>

      {/* Jobs Table or Empty State */}
      <div className="bg-[#0f1422]/90 backdrop-blur-md border border-slate-800/80 rounded-xl overflow-hidden shadow-2xl">
        {filteredJobs.length === 0 ? (
          <div className="py-20 px-4 text-center">
            <div className="w-14 h-14 rounded-2xl bg-cyan-950/40 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mx-auto mb-3 shadow-inner">
              <span className="material-symbols-outlined text-3xl">folder_open</span>
            </div>
            <h3 className="text-base font-semibold text-slate-100 mb-1 font-['Space_Grotesk']">
              {jobs.length === 0 ? 'No compliance jobs yet' : 'No matching jobs found'}
            </h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mb-6 leading-relaxed">
              {jobs.length === 0
                ? 'Create your first compliance job to begin deterministic BIS statutory evaluation, multimodal technical file analysis, and evidentiary mapping.'
                : 'Try adjusting your search query to locate active statutory compliance tasks.'}
            </p>
            {jobs.length === 0 && (
              <button
                type="button"
                onClick={() => setModalOpen(true)}
                className="px-4 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all inline-flex items-center gap-1.5 shadow-lg shadow-cyan-500/10 cursor-pointer"
              >
                <span className="material-symbols-outlined text-sm font-bold">add</span>
                Create Your First Compliance Job
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-900/60 border-b border-slate-800 font-mono text-[11px] text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4 font-semibold">JOB ID</th>
                  <th className="py-3 px-4 font-semibold">TITLE / SKU</th>
                  <th className="py-3 px-4 font-semibold">MANUFACTURER</th>
                  <th className="py-3 px-4 font-semibold">STANDARD</th>
                  <th className="py-3 px-4 font-semibold">STATUS</th>
                  <th className="py-3 px-4 font-semibold text-right">DATE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredJobs.map((job) => (
                  <tr
                    key={job.id}
                    onClick={() => onSelectJob?.(job.id)}
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                    title="Click to activate compliance job"
                  >
                    <td className="py-3.5 px-4 font-mono font-semibold text-cyan-400 group-hover:text-cyan-300 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-xs text-slate-500 group-hover:text-cyan-400 transition-colors">
                        terminal
                      </span>
                      {job.jobNumber || job.id}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-200">
                      {job.productName || job.title}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">
                      {job.manufacturer}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-300">
                      <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-300">
                        {job.standard || 'IS 16221-2:2015'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-mono font-medium bg-cyan-950/60 text-cyan-300 border border-cyan-800/60">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                        {job.stage || job.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono text-slate-400 text-[11px]">
                      {job.createdAt}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Guided "New Compliance Job" Modal Drawer */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
            onClick={() => setModalOpen(false)}
          />
          <div className="relative bg-[#0d121f] border border-slate-800 rounded-2xl max-w-lg w-full shadow-2xl z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
                  <span className="material-symbols-outlined text-[16px]">rule_folder</span>
                </div>
                <h3 className="font-bold text-sm text-slate-100 font-['Space_Grotesk']">
                  Create New Compliance Job
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <span className="material-symbols-outlined text-base">close</span>
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Job Title <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Solar PV Inverter IS 16221-2 Evaluation"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 text-xs bg-slate-900/90 border border-slate-700/80 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Manufacturer Entity
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Acme Solar Tech Pvt Ltd"
                    value={formData.manufacturer}
                    onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-slate-900/90 border border-slate-700/80 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Product / SKU
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Model X-5000 / SKU-8821"
                    value={formData.productName}
                    onChange={(e) => setFormData({ ...formData, productName: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-slate-900/90 border border-slate-700/80 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Target Statutory Standard
                </label>
                <GlideSelect
                  items={SAMPLE_STANDARDS}
                  value={formData.standard}
                  onChange={(val) => setFormData({ ...formData, standard: val })}
                  placeholder="Select BIS Standard"
                  width="100%"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Technical Documentation Dropzone
                </label>
                <div className="border border-dashed border-slate-700 hover:border-cyan-500/60 rounded-xl p-5 text-center bg-slate-900/50 hover:bg-slate-900/80 transition-colors cursor-pointer group">
                  <span className="material-symbols-outlined text-2xl text-slate-400 group-hover:text-cyan-400 block mb-1 transition-colors">
                    cloud_upload
                  </span>
                  <span className="text-xs font-medium text-slate-200 block">
                    Upload Technical Specifications, CAD &amp; BOM
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5 font-mono">
                    Supports STEP, STL, Gerber, PDF, and DOCX files
                  </span>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="mt-2 pt-4 border-t border-slate-800 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 text-slate-950 rounded-lg text-xs font-semibold transition-all shadow-md shadow-cyan-500/20 cursor-pointer"
                >
                  Initialize Compliance Job
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
