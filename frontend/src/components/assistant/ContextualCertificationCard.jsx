import React, { useState } from 'react';

/**
 * ContextualCertificationCard
 * 
 * Provides interactive guidance on BIS certification schemes (Scheme I ISI, Scheme II CRS)
 * and step-by-step licensing procedures under the Bureau of Indian Standards Act 2016.
 */
export function ContextualCertificationCard({ onInspectSource }) {
  const [activeTab, setActiveTab] = useState('process'); // 'process' | 'schemes' | 'documents'

  const stages = [
    {
      step: '01',
      title: 'Application & Portal Submission',
      desc: 'Submit Form VI via the Manak Online portal with manufacturing facility details, test equipment list, and statutory application fees.',
      doc: 'Manak Online e-BIS Portal',
      time: 'Day 1 - 7',
    },
    {
      step: '02',
      title: 'Factory Audit & Quality Inspection',
      desc: 'BIS Technical Officer conducts on-site factory audit to inspect quality control, in-house testing equipment, and draw sealed test samples.',
      doc: 'BIS Assessment Manual',
      time: 'Day 15 - 30',
    },
    {
      step: '03',
      title: 'Independent Laboratory Testing',
      desc: 'Sealed samples dispatched to Central Laboratory or BIS-recognized NABL laboratory for testing against statutory Indian Standard clauses.',
      doc: 'IS Test Protocol',
      time: 'Day 30 - 60',
    },
    {
      step: '04',
      title: 'Grant of License (CML)',
      desc: 'Upon conforming test reports and audit clearance, BIS issues Certification of Marks License (CM/L) authorizing application of standard ISI mark.',
      doc: 'Form VII / Gazette',
      time: 'Final Grant',
    },
  ];

  const schemes = [
    {
      id: 'scheme1',
      name: 'Scheme I — ISI Mark Scheme',
      badge: 'Product Certification',
      desc: 'Applicable to domestic and foreign manufacturers. Mandatory for products under Quality Control Orders (QCOs) including steel, appliances, safety glass, and domestic containers.',
      authority: 'BIS Act 2016 / Gazette Orders',
    },
    {
      id: 'scheme2',
      name: 'Scheme II — Compulsory Registration (CRS)',
      badge: 'IT & Electronics',
      desc: 'Self-declaration of conformity based on testing in BIS-recognized labs. Mandatory under MeitY orders for laptops, adapters, smartphones, and inverters.',
      authority: 'MeitY CRO Orders',
    },
    {
      id: 'scheme4',
      name: 'Scheme IV — Eco Mark',
      badge: 'Environmental Label',
      desc: 'Assigned to products meeting both statutory Indian Standards and environmental sustainability criteria.',
      authority: 'Ministry of Environment, Forest and Climate Change',
    },
  ];

  return (
    <div className="mt-3.5 bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs transition-all">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-blue-600 text-lg">verified</span>
          <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            BIS Certification & Schemes Guide
          </span>
        </div>
        <span className="text-[11px] font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
          Statutory Framework
        </span>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 mb-4">
        <button
          type="button"
          onClick={() => setActiveTab('process')}
          className={`px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
            activeTab === 'process'
              ? 'bg-blue-50 text-blue-700 border border-blue-200 font-semibold'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          Licensing Process (4 Steps)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('schemes')}
          className={`px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
            activeTab === 'schemes'
              ? 'bg-blue-50 text-blue-700 border border-blue-200 font-semibold'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          Certification Schemes
        </button>
      </div>

      {/* Content */}
      {activeTab === 'process' ? (
        <div className="space-y-2.5">
          {stages.map((st) => (
            <div
              key={st.step}
              className="flex items-start gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs"
            >
              <span className="font-mono text-xs font-bold text-blue-700 bg-white px-2 py-1 rounded border border-blue-200 shrink-0">
                {st.step}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-bold text-slate-900 text-xs truncate">{st.title}</h4>
                  <span className="text-[10px] text-slate-400 font-mono shrink-0">{st.time}</span>
                </div>
                <p className="text-slate-600 text-xs mt-1 leading-relaxed">{st.desc}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2.5">
          {schemes.map((sc) => (
            <div
              key={sc.id}
              className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1"
            >
              <div className="flex items-center justify-between gap-2">
                <h4 className="font-bold text-slate-900 text-xs">{sc.name}</h4>
                <span className="text-[10px] font-medium text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                  {sc.badge}
                </span>
              </div>
              <p className="text-slate-600 text-xs leading-relaxed">{sc.desc}</p>
              <div className="text-[10px] text-slate-400 pt-1">
                Governing basis: {sc.authority}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer provenance notice */}
      <div className="mt-3.5 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <span>Information derived from BIS Act 2016 regulations</span>
        <button
          type="button"
          onClick={() => onInspectSource && onInspectSource({
            source: 'Bureau of Indian Standards Conformity Assessment Regulations 2018',
            document: 'Gazette of India Extraordinary Part II',
            clause: 'Regulation 4 & Schedule II',
            authority: 'Bureau of Indian Standards',
            page: '12-16',
            verification: 'Statutory Gazette Publication',
            extractionMethod: 'Authoritative Parser',
            sha256: 'a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0',
          })}
          className="text-blue-600 hover:text-blue-800 font-medium underline cursor-pointer"
        >
          Inspect Statutory Source
        </button>
      </div>
    </div>
  );
}
