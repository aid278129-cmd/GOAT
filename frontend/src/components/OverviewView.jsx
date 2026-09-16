import React from 'react';

export function OverviewView({ assessmentsList = [], onNavigate, onSelectAssessment, onNewAnalysis }) {
  // Compute genuine aggregate metrics from active assessments
  const totalAssessments = assessmentsList.length;
  const standardsCount = 51; // Authoritative BIS Gazette Standards in catalog
  const evaluatingCount = assessmentsList.filter((a) => (a.status || 'EVALUATING') === 'EVALUATING').length;

  return (
    <div className="flex-1 p-6 md:p-8 space-y-6 overflow-y-auto font-sans bg-[#F8FAFC]">
      {/* Header & Quick Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded">
              GOAT Workspace Overview
            </span>
            <span className="text-xs text-slate-500">Bureau of Indian Standards Smart Pre-Certification</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Compliance Dossier Workspace
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            Active product assessments, standards scoping, and evidence audit trails.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onNewAnalysis}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-2xs"
          >
            <span className="material-symbols-outlined text-[15px]">add</span>
            <span>New Product Assessment</span>
          </button>
        </div>
      </div>

      {/* Operational Summary Metrics (Strictly Real Data) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-slate-400 font-bold block">
            Active Assessments
          </span>
          <div className="text-2xl font-mono font-bold text-slate-900 mt-1">{totalAssessments}</div>
          <span className="text-[11px] text-slate-500">Product Dossiers in Session</span>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-indigo-600 font-bold block">
            BIS Standards Catalog
          </span>
          <div className="text-2xl font-mono font-bold text-indigo-700 mt-1">{standardsCount}</div>
          <span className="text-[11px] text-slate-500">Gazetted IS Specifications</span>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-amber-600 font-bold block">
            Under Evaluation
          </span>
          <div className="text-2xl font-mono font-bold text-amber-700 mt-1">{evaluatingCount}</div>
          <span className="text-[11px] text-slate-500">Active Pipeline Compilations</span>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-emerald-600 font-bold block">
            Compliance Engine
          </span>
          <div className="text-2xl font-mono font-bold text-emerald-700 mt-1">DETERMINISTIC</div>
          <span className="text-[11px] text-slate-500">0% LLM Compliance Authority</span>
        </div>
      </div>

      {/* Active Assessments Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-slate-600 text-sm">inventory_2</span>
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              Product Assessment Registry
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-500">
            {totalAssessments} Registered Product{totalAssessments === 1 ? '' : 's'}
          </span>
        </div>

        {totalAssessments === 0 ? (
          <div className="p-10 text-center space-y-3">
            <div className="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
              <span className="material-symbols-outlined text-2xl">post_add</span>
            </div>
            <div className="space-y-1 max-w-sm mx-auto">
              <h3 className="text-sm font-bold text-slate-800">No compliance assessments yet</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Provide technical product information via PDF, OCR, Voice, or BOM to begin compliance compilation.
              </p>
            </div>
            <div className="flex justify-center gap-2 pt-2">
              <button
                onClick={onNewAnalysis}
                className="px-4 py-2 rounded bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition cursor-pointer"
              >
                Step 1: Product Input
              </button>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-100/70 text-slate-600 font-mono text-[10px] uppercase tracking-wider">
                  <th className="py-2.5 px-4">Dossier #</th>
                  <th className="py-2.5 px-4">Product Name</th>
                  <th className="py-2.5 px-4">Category</th>
                  <th className="py-2.5 px-4">Standard Scoped</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {assessmentsList.map((a) => (
                  <tr key={a.assessment_id} className="hover:bg-slate-50 transition group">
                    <td className="py-3 px-4 font-mono font-medium text-slate-600">
                      {a.assessment_number || a.assessment_id?.slice(0, 8)}
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-900 group-hover:text-indigo-600 transition">
                      {a.product_name || a.title || 'Product Analysis'}
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {a.category || 'General'}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-700 font-medium">
                      {a.target_standard || 'IS 17526:2021'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {a.status || 'EVALUATING'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => {
                          onSelectAssessment(a.assessment_id);
                          onNavigate('dna');
                        }}
                        className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold transition cursor-pointer"
                      >
                        Open Dossier
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
