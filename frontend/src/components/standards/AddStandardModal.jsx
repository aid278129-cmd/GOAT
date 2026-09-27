import React, { useState, useEffect, useRef } from 'react';
import { triggerEntrance } from '../../utils/useAnimeMotion';

export function AddStandardModal({ isOpen, onClose, onAddStandard }) {
  const modalRef = useRef(null);

  const [identifier, setIdentifier] = useState('');
  const [revisionYear, setRevisionYear] = useState('');
  const [title, setTitle] = useState('');
  const [gazetteRef, setGazetteRef] = useState('');
  const [applicabilityScope, setApplicabilityScope] = useState('');
  const [isActiveBasis, setIsActiveBasis] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && modalRef.current) {
      triggerEntrance(modalRef.current);
      setIdentifier('');
      setRevisionYear('');
      setTitle('');
      setGazetteRef('');
      setApplicabilityScope('');
      setIsActiveBasis(true);
      setError(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!identifier.trim()) {
      setError('Standard identifier is required (e.g., IS 13252 (Part 1)).');
      return;
    }

    const standard = {
      id: `STD-${Math.random().toString(36).substring(2, 7).toUpperCase()}`,
      identifier: identifier.trim(),
      revisionYear: revisionYear.trim() || 'Current Gazette Revision',
      title: title.trim() || 'Statutory Indian Standard Specification',
      gazetteRef: gazetteRef.trim() || 'Official Gazette Order',
      applicabilityScope: applicabilityScope.trim() || 'Statutory product category applicability defined by engineer',
      isActiveBasis: Boolean(isActiveBasis),
      createdAt: new Date().toISOString(),
    };

    onAddStandard(standard);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div
        ref={modalRef}
        className="w-full max-w-xl bg-[#0d121f] text-slate-100 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col font-sans"
      >
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-900/60 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
              <span className="material-symbols-outlined text-lg">menu_book</span>
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider font-mono">
                Assign Statutory Standard
              </h2>
              <p className="text-xs text-slate-400">
                Define the applicable statutory standard and revision for this compliance job
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-xl flex items-center gap-2 text-xs text-rose-300">
              <span className="material-symbols-outlined text-sm shrink-0">error</span>
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Standard Identifier <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                placeholder="e.g. IS 13252 (Part 1)"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
                required
              />
              <p className="text-[10px] text-slate-500 mt-1">Official Indian Standard code or harmonized standard</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Revision / Year / Amendment
              </label>
              <input
                type="text"
                placeholder="e.g. 2010 / A2:2015"
                value={revisionYear}
                onChange={(e) => setRevisionYear(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
              />
              <p className="text-[10px] text-slate-500 mt-1">Applicable revision year and amendment cycle</p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Standard Title / Specification Name
            </label>
            <input
              type="text"
              placeholder="e.g. Information Technology Equipment - Safety - General Requirements"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Gazette Order / Statutory Notification Reference
            </label>
            <input
              type="text"
              placeholder="e.g. S.O. 2357(E) Electronics &amp; IT Goods (Compulsory Registration) Order"
              value={gazetteRef}
              onChange={(e) => setGazetteRef(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Applicability Scope &amp; Category
            </label>
            <textarea
              rows={2}
              placeholder="Define operational envelope or product category conditions under which this standard governs..."
              value={applicabilityScope}
              onChange={(e) => setApplicabilityScope(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isActiveBasis}
                onChange={(e) => setIsActiveBasis(e.target.checked)}
                className="w-4 h-4 text-cyan-500 rounded border-slate-700 bg-slate-900 focus:ring-cyan-500"
              />
              <span className="text-xs font-medium text-slate-300">
                Mark as Active Assessment Basis for this Compliance Job
              </span>
            </label>
          </div>

          {/* Modal Actions */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all flex items-center gap-1.5 shadow-md shadow-cyan-500/20 cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm font-bold">add</span>
              Add Standard to Job
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
