import React, { useState } from 'react';

const SAMPLE_STANDARDS = [
  { code: 'IS 16221-2:2015', name: 'Safety of Power Converters for use in Photovoltaic Power Systems' },
  { code: 'IS 13252-1:2010', name: 'Information Technology Equipment - Safety - General Requirements' },
  { code: 'IS 616:2017', name: 'Audio, Video and Similar Electronic Apparatus - Safety Requirements' },
  { code: 'IS 302-2-3:2017', name: 'Safety of Household and Similar Electrical Appliances' },
  { code: 'IS 10322-5:2013', name: 'Luminaires - Particular Requirements - Floodlights & General' },
];

export function ComplianceJobsView({ jobs = [], onCreateJob, modalOpen, setModalOpen }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [formData, setFormData] = useState({
    title: '',
    manufacturer: '',
    productName: '',
    standard: 'IS 16221-2:2015',
    notes: '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title.trim()) return;

    const newJob = {
      id: `JOB-${Date.now().toString().slice(-4)}`,
      title: formData.title,
      manufacturer: formData.manufacturer || 'Unassigned Manufacturer',
      productName: formData.productName || 'Unassigned Product',
      standard: formData.standard,
      status: 'AWAITING EVIDENCE',
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
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0F172A]">
            Compliance Jobs Directory
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B] mt-0.5">
            Manage, track, and execute deterministic statutory evaluations.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="px-3.5 py-2 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors flex items-center gap-1.5 self-start sm:self-auto shadow-sm"
        >
          <span className="material-symbols-outlined text-sm">add</span>
          New Compliance Job
        </button>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3 rounded-lg border border-[#E2E8F0]">
        <div className="relative w-full sm:w-80">
          <span className="material-symbols-outlined text-sm text-[#94A3B8] absolute left-2.5 top-2.5">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter jobs by ID, product, or standard..."
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white"
          />
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <span className="font-mono text-xs text-[#64748B]">
            {jobs.length} Jobs Total
          </span>
        </div>
      </div>

      {/* Jobs Table or Empty State */}
      <div className="bg-white border border-[#E2E8F0] rounded-lg overflow-hidden shadow-sm">
        {jobs.length === 0 ? (
          <div className="py-16 px-4 text-center">
            <div className="w-14 h-14 rounded-full bg-slate-100 flex items-center justify-center text-[#94A3B8] mx-auto mb-3">
              <span className="material-symbols-outlined text-3xl">folder_open</span>
            </div>
            <h3 className="text-base font-semibold text-[#0F172A] mb-1">
              No compliance jobs yet
            </h3>
            <p className="text-xs text-[#64748B] max-w-md mx-auto mb-5 leading-relaxed">
              Create your first compliance job to begin deterministic BIS statutory evaluation, multimodal technical file analysis, and evidentiary mapping.
            </p>
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="px-4 py-2 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors inline-flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              Create Your First Compliance Job
            </button>
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#F8F9FA] border-b border-[#E2E8F0] font-mono text-[11px] text-[#64748B]">
                <th className="py-3 px-4 font-semibold">JOB ID</th>
                <th className="py-3 px-4 font-semibold">TITLE</th>
                <th className="py-3 px-4 font-semibold">MANUFACTURER</th>
                <th className="py-3 px-4 font-semibold">STANDARD</th>
                <th className="py-3 px-4 font-semibold">STATUS</th>
                <th className="py-3 px-4 font-semibold text-right">DATE</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id} className="border-b border-[#E2E8F0] hover:bg-[#F8F9FA] transition-colors">
                  <td className="py-3 px-4 font-mono font-semibold text-[#1D4ED8]">{job.id}</td>
                  <td className="py-3 px-4 font-medium text-[#0F172A]">{job.title}</td>
                  <td className="py-3 px-4 text-[#64748B]">{job.manufacturer}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-[#0F172A]">{job.standard}</td>
                  <td className="py-3 px-4">
                    <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                      {job.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-[#64748B]">{job.createdAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Guided "New Compliance Job" Modal Drawer */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm"
            onClick={() => setModalOpen(false)}
          />
          <div className="relative bg-white border border-[#E2E8F0] rounded-xl max-w-lg w-full shadow-2xl z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-[#E2E8F0] flex items-center justify-between bg-[#F8F9FA]">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-600">rule_folder</span>
                <h3 className="font-bold text-sm text-[#0F172A]">Create New Compliance Job</h3>
              </div>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="text-[#64748B] hover:text-[#0F172A] p-1 rounded"
              >
                <span className="material-symbols-outlined text-base">close</span>
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4">
              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Job Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Solar PV Inverter IS 16221-2 Evaluation"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                    Manufacturer Entity
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Acme Solar Tech Pvt Ltd"
                    value={formData.manufacturer}
                    onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                    Product / SKU
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Model X-5000 / SKU-8821"
                    value={formData.productName}
                    onChange={(e) => setFormData({ ...formData, productName: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Target Statutory Standard
                </label>
                <select
                  value={formData.standard}
                  onChange={(e) => setFormData({ ...formData, standard: e.target.value })}
                  className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] focus:outline-none focus:border-[#1D4ED8] focus:bg-white font-mono"
                >
                  {SAMPLE_STANDARDS.map((s) => (
                    <option key={s.code} value={s.code}>
                      {s.code} — {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Technical Documentation Dropzone
                </label>
                <div className="border-2 border-dashed border-[#E2E8F0] rounded-lg p-5 text-center bg-[#F8F9FA] hover:bg-slate-50 transition-colors cursor-pointer">
                  <span className="material-symbols-outlined text-2xl text-[#94A3B8] block mb-1">
                    cloud_upload
                  </span>
                  <span className="text-xs font-medium text-[#0F172A] block">
                    Upload Technical Specifications, CAD &amp; BOM
                  </span>
                  <span className="text-[11px] text-[#94A3B8] block mt-0.5">
                    Supports STEP, STL, Gerber, PDF, and DOCX files
                  </span>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="mt-2 pt-4 border-t border-[#E2E8F0] flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-[#64748B] hover:text-[#0F172A] transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#1D4ED8] hover:bg-[#1E40AF] text-white rounded text-xs font-semibold transition-colors shadow-sm"
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
