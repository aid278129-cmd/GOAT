import React from 'react';

export function OverviewView({ assessmentsList = [], onNavigate, onSelectAssessment, onNewAnalysis }) {
  return (
    <div className="flex-1 p-4 md:p-6 lg:p-8 bg-[#F3F4F6] overflow-y-auto font-sans">
      <div className="max-w-[1440px] mx-auto space-y-6">
        {/* Page Header & CTA */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded font-mono">
                BIS Compliance Portal
              </span>
              <span className="text-xs text-slate-500">Bureau of Indian Standards Smart Automation</span>
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
              Zyntrix BIS Compliance Compiler
            </h1>
            <p className="text-xs md:text-sm text-slate-500 mt-0.5">
              AI-first compliance assistant translating product artifacts into clause-level BIS applicability, tests, evidence & lab actions.
            </p>
          </div>
          <button
            onClick={onNewAnalysis}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-5 py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all shadow-xs cursor-pointer self-start md:self-auto active:scale-[0.99]"
          >
            <span className="material-symbols-outlined text-[16px]">search</span>
            <span>Analyze a Product</span>
          </button>
        </div>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Overview Widgets (Left Column - 4 cols) */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            {/* Global Verification Index Card */}
            <div className="bg-indigo-600 rounded-xl p-5 text-white relative overflow-hidden shadow-xs">
              <div className="relative z-10">
                <div className="flex justify-between items-start">
                  <h3 className="text-[10px] font-bold uppercase tracking-wider opacity-85">
                    Global Verification Index
                  </h3>
                  <span className="text-[10px] font-mono bg-white/20 px-2 py-0.5 rounded">
                    100% Deterministic
                  </span>
                </div>
                <div className="text-3xl md:text-4xl font-bold mt-2 tracking-tight">94.2%</div>
                <p className="text-[11px] mt-2 leading-relaxed opacity-90">
                  Standard compliance certainty grounded on attached NABL certificates and official Gazette indices.
                </p>
                <div className="w-full bg-white/20 h-1.5 rounded-full overflow-hidden mt-3">
                  <div className="bg-white h-full w-[94%] rounded-full"></div>
                </div>
              </div>
              <div className="absolute -right-4 -bottom-4 w-28 h-28 bg-white/10 rounded-full pointer-events-none"></div>
            </div>

            {/* Quick Metrics */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <h2 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">
                Portfolio Metrics
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
                  <div className="text-2xl font-bold text-slate-900">{assessmentsList.length}</div>
                  <div className="text-[11px] font-medium text-slate-500 mt-0.5">Active Products</div>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
                  <div className="text-2xl font-bold text-indigo-600">51</div>
                  <div className="text-[11px] font-medium text-slate-500 mt-0.5">Standards Indexed</div>
                </div>
              </div>
            </div>

          </div>

          {/* Right Column (8 cols): Active Assessments */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            {/* Product Assessments Table */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex-1">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">Your Product Assessments</h2>
                  <p className="text-xs text-slate-500">Traceable compliance workspaces currently managed</p>
                </div>
                {assessmentsList.length > 0 && (
                  <button
                    onClick={onNewAnalysis}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1 cursor-pointer"
                  >
                    <span>+ Add Product</span>
                  </button>
                )}
              </div>

              {assessmentsList.length === 0 ? (
                <div className="py-12 px-4 text-center rounded-xl bg-slate-50 border border-dashed border-slate-200 space-y-3">
                  <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center mx-auto">
                    <span className="material-symbols-outlined text-[24px]">post_add</span>
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">No Assessments Created Yet</h3>
                    <p className="text-xs text-slate-500 max-w-sm mx-auto mt-0.5">
                      Start fresh by entering your product details. Zyntrix will discover applicable BIS standards and build your testing roadmap.
                    </p>
                  </div>
                  <button
                    onClick={onNewAnalysis}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-xs cursor-pointer inline-flex items-center gap-1.5"
                  >
                    <span className="material-symbols-outlined text-[16px]">add</span>
                    <span>Start First Product Assessment</span>
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
                        <th className="py-2.5 px-3">Assessment #</th>
                        <th className="py-2.5 px-3">Product Name</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {assessmentsList.map((a) => (
                        <tr key={a.assessment_id} className="hover:bg-slate-50 transition group">
                          <td className="py-3 px-3 font-mono text-slate-500 font-medium">
                            {a.assessment_number || a.assessment_id?.slice(0, 10)}
                          </td>
                          <td className="py-3 px-3 font-bold text-slate-900 group-hover:text-indigo-600 transition">
                            {a.product_name || a.title || 'Product Analysis'}
                          </td>
                          <td className="py-3 px-3 text-slate-600">
                            {a.category || 'General'}
                          </td>
                          <td className="py-3 px-3">
                            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                              {a.status || 'EVALUATING'}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right">
                            <button
                              onClick={() => {
                                onSelectAssessment(a.assessment_id);
                                onNavigate('standards');
                              }}
                              className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition cursor-pointer shadow-2xs"
                            >
                              Open
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
        </div>
      </div>
    </div>
  );
}
