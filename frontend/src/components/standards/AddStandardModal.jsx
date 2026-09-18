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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div
        ref={modalRef}
        className="w-full max-w-xl bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden flex flex-col font-sans"
      >
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
              <span className="material-symbols-outlined text-lg">menu_book</span>
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider font-mono">
                Assign Statutory Standard
              </h2>
              <p className="text-xs text-slate-500">
                Define the applicable statutory standard and revision for this compliance job
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
              <span className="material-symbols-outlined text-sm shrink-0">error</span>
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Standard Identifier <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                placeholder="e.g. IS 13252 (Part 1)"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 font-mono"
                required
              />
              <p className="text-[10px] text-slate-400 mt-1">Official Indian Standard code or harmonized standard</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Revision / Year / Amendment
              </label>
              <input
                type="text"
                placeholder="e.g. 2010 / A2:2015"
                value={revisionYear}
                onChange={(e) => setRevisionYear(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 font-mono"
              />
              <p className="text-[10px] text-slate-400 mt-1">Applicable revision year and amendment cycle</p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Standard Title / Specification Name
            </label>
            <input
              type="text"
              placeholder="e.g. Information Technology Equipment - Safety - General Requirements"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Gazette Order / Statutory Notification Reference
            </label>
            <input
              type="text"
              placeholder="e.g. S.O. 2357(E) Electronics & IT Goods (Compulsory Registration) Order"
              value={gazetteRef}
              onChange={(e) => setGazetteRef(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Applicability Scope & Category
            </label>
            <textarea
              rows={2}
              placeholder="Define operational envelope or product category conditions under which this standard governs..."
              value={applicabilityScope}
              onChange={(e) => setApplicabilityScope(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isActiveBasis}
                onChange={(e) => setIsActiveBasis(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
              />
              <span className="text-xs font-medium text-slate-700">
                Mark as Active Assessment Basis for this Compliance Job
              </span>
            </label>
          </div>

          {/* Modal Actions */}
          <div className="pt-4 border-t border-slate-200 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              Add Standard to Job
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
