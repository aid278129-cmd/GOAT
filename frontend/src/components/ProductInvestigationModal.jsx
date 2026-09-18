import React, { useState } from 'react';
import { assistantApi } from '../api/assistant';

export default function ProductInvestigationModal({ isOpen, onClose, onStartWorkstationJob }) {
  const [productName, setProductName] = useState('');
  const [category, setCategory] = useState('SOLAR_INVERTERS');
  const [powerKw, setPowerKw] = useState('5.0');
  const [voltageV, setVoltageV] = useState('230');
  const [description, setDescription] = useState('5 kW hybrid solar inverter with grid-tie and lithium battery storage interface for residential rooftop installation.');
  const [loading, setLoading] = useState(false);
  const [recommendationResult, setRecommendationResult] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleRunInvestigation = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const fullDesc = `${productName} (${category}). Power: ${powerKw} kW, Voltage: ${voltageV} V. ${description}`;
      const res = await assistantApi.recommendStandard(fullDesc, 4);
      setRecommendationResult(res);
    } catch (err) {
      setError(err.message || 'Failed to retrieve standard recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleHandoff = async (standardNumber) => {
    setLoading(true);
    try {
      const payload = {
        title: `${productName || 'Product'} Compliance Job - ${standardNumber}`,
        product_name: productName || 'Generic Product',
        target_standard_number: standardNumber,
        product_context: {
          category,
          power_kw: parseFloat(powerKw) || 0,
          voltage_v: parseFloat(voltageV) || 0,
          description,
        },
      };
      const res = await assistantApi.startWorkstationJob(payload);
      if (onStartWorkstationJob) {
        onStartWorkstationJob(res.job_id);
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to initiate workstation job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-900 to-indigo-950 p-6 text-white flex justify-between items-start">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-2 border border-indigo-400/30">
              SIH PS 26107 · Product Standards Explorer
            </div>
            <h2 className="text-xl font-bold tracking-tight">Investigate Applicable Indian Standards</h2>
            <p className="text-xs text-slate-300 mt-1">
              Provide product specifications to discover potentially applicable Indian Standards, BIS schemes, and testing considerations.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {/* Form */}
          <form onSubmit={handleRunInvestigation} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Product Name / Model
                </label>
                <input
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="e.g. Solarix-5000 Hybrid Inverter"
                  required
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Product Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="SOLAR_INVERTERS">Solar Inverters & Power Converters</option>
                  <option value="IT_ELECTRONICS">Information Technology & Power Adapters</option>
                  <option value="HOUSEHOLD_APPLIANCES">Household Electrical Appliances</option>
                  <option value="BATTERIES">Secondary Lithium Batteries</option>
                  <option value="ELECTRICAL_ACCESSORIES">Plugs, Sockets & Accessories</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Rated Capacity / Power (kW)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={powerKw}
                  onChange={(e) => setPowerKw(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Nominal Voltage (V)
                </label>
                <input
                  type="number"
                  value={voltageV}
                  onChange={(e) => setVoltageV(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Detailed Product Description & Functional Context
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="Describe intended application, grid interface, environmental rating, materials, etc."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 border border-slate-300 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? 'Evaluating Knowledge...' : '🔍 Retrieve Standards & Schemes'}
              </button>
            </div>
          </form>

          {error && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Results Display */}
          {recommendationResult && (
            <div className="space-y-4 pt-4 border-t border-slate-200">
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
                ⚠️ <strong>Statutory Notice</strong>: {recommendationResult.disclaimer}
              </div>

              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                Potentially Relevant Standards ({recommendationResult.potentially_relevant_standards.length})
              </h3>

              <div className="space-y-3">
                {recommendationResult.potentially_relevant_standards.map((std, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-slate-50 border border-slate-200 rounded-xl hover:border-indigo-300 transition-colors"
                  >
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-indigo-900 text-sm">{std.standard_number}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${std.is_mandatory ? 'bg-red-100 text-red-700' : 'bg-slate-200 text-slate-700'}`}>
                            {std.is_mandatory ? 'MANDATORY QCO' : 'VOLUNTARY'}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full font-semibold">
                            {std.confidence_basis}
                          </span>
                        </div>
                        <h4 className="font-semibold text-slate-900 text-sm mt-1">{std.title}</h4>
                        <p className="text-xs text-slate-600 mt-1">
                          <strong>Why Retrieved:</strong> {std.why_retrieved}
                        </p>
                        {std.key_clauses && std.key_clauses.length > 0 && (
                          <div className="mt-2 text-xs text-slate-500">
                            <strong>Key Clauses:</strong>{' '}
                            {std.key_clauses.map((c) => `Clause ${c.clause_number} (${c.clause_title})`).join(', ')}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => handleHandoff(std.standard_number)}
                        className="px-3 py-1.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg whitespace-nowrap shadow-sm"
                      >
                        ⚡ Open in Workstation
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {recommendationResult.applicable_bis_scheme && (
                <div className="p-4 bg-indigo-50/50 border border-indigo-200 rounded-xl">
                  <div className="text-xs font-bold text-indigo-800 uppercase tracking-wider mb-1">
                    Applicable Conformity Scheme
                  </div>
                  <div className="text-sm font-semibold text-slate-900">
                    {recommendationResult.applicable_bis_scheme.scheme_name}
                  </div>
                  <div className="text-xs text-slate-600 mt-1">
                    {recommendationResult.applicable_bis_scheme.description}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
