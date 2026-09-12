import React, { useState } from 'react';
import { StatusBadge } from '../StatusBadge';

export function ProductDNAView({ assessment, onClarify, onNavigate }) {
  const [clarifyValues, setClarifyValues] = useState({});
  const [submittingAttr, setSubmittingAttr] = useState(null);

  if (!assessment) {
    return (
      <div className="flex-1 p-6 md:p-8 flex items-center justify-center font-sans">
        <div className="max-w-md w-full bg-white border border-slate-200 rounded-lg p-8 text-center space-y-4 shadow-2xs">
          <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto text-slate-500">
            <span className="material-symbols-outlined text-2xl">fingerprint</span>
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">No Product DNA Loaded</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              No active product assessment is currently selected. Start by providing technical product information in Step 1 or load a controlled demo case.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-2 justify-center pt-2">
            <button
              onClick={() => onNavigate('input')}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold transition cursor-pointer"
            >
              Step 1: Product Input
            </button>
            <button
              onClick={() => onNavigate('evaluation')}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold border border-slate-200 transition cursor-pointer"
            >
              Load Demo Case
            </button>
          </div>
        </div>
      </div>
    );
  }

  const dna = assessment.product_dna || {};
  const attributes = dna.attributes || {};
  const clarifications = assessment.clarifications || [];

  const handleClarifySubmit = async (attrName) => {
    const val = clarifyValues[attrName];
    if (!val || !val.trim()) return;
    setSubmittingAttr(attrName);
    try {
      await onClarify(attrName, val.trim());
      setClarifyValues((prev) => ({ ...prev, [attrName]: '' }));
    } catch (err) {
      console.error('Failed to submit clarification:', err);
    } finally {
      setSubmittingAttr(null);
    }
  };

  const canonicalFields = [
    { key: 'product_name', label: 'Product Model / Trade Name', defaultVal: assessment.product_name || dna.product_name },
    { key: 'category', label: 'Product Category', defaultVal: assessment.category || dna.category },
    { key: 'intended_use', label: 'Intended Use & Environment', defaultVal: dna.intended_use },
    { key: 'material', label: 'Primary Materials & Grades', defaultVal: dna.material || attributes.material },
    { key: 'capacity_ml', label: 'Nominal Capacity / Volume', defaultVal: dna.capacity_ml || attributes.capacity_ml ? `${dna.capacity_ml || attributes.capacity_ml} mL` : null },
    { key: 'rated_voltage', label: 'Rated Voltage (AC/DC)', defaultVal: dna.rated_voltage || attributes.rated_voltage ? `${dna.rated_voltage || attributes.rated_voltage} V` : null },
    { key: 'rated_power_w', label: 'Rated Power / Wattage', defaultVal: dna.rated_power_w || attributes.rated_power_w ? `${dna.rated_power_w || attributes.rated_power_w} W` : null },
    { key: 'construction', label: 'Construction & Wall Type', defaultVal: dna.construction || attributes.construction },
    { key: 'insulation', label: 'Thermal / Electrical Insulation', defaultVal: dna.insulation || attributes.insulation },
    { key: 'food_contact', label: 'Food Contact Surface', defaultVal: dna.food_contact !== undefined ? (dna.food_contact ? 'Yes' : 'No') : null },
    { key: 'standards_claimed', label: 'Manufacturer Claimed Standards', defaultVal: dna.standards_claimed?.length ? dna.standards_claimed.join(', ') : null },
  ];

  return (
    <div className="flex-1 p-6 md:p-8 space-y-6 overflow-y-auto font-sans bg-[#F8FAFC]">
      {/* Step Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded">
              Step 02 / 08 &bull; Layer 2 Fact Engine
            </span>
            <span className="text-xs text-slate-500">Structured Technical Representation</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Product DNA & Technical Attributes</span>
            <span className="text-xs font-mono font-normal text-slate-500">[{assessment.assessment_number || assessment.assessment_id?.slice(0, 8)}]</span>
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            Verified technical facts extracted from product artifacts. Inferred values are flagged and require confirmation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('applicability')}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
          >
            <span>Proceed to BIS Applicability</span>
            <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
          </button>
        </div>
      </div>

      {/* Actionable Missing Attributes / Clarification Banner */}
      {clarifications.length > 0 && (
        <div className="p-4 rounded-lg bg-amber-50 border border-amber-200 space-y-3">
          <div className="flex items-start gap-2.5">
            <span className="material-symbols-outlined text-amber-700 text-lg shrink-0 mt-0.5">warning</span>
            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between">
                <h2 className="text-xs font-bold text-amber-900 uppercase tracking-wide">
                  Clarification Required ({clarifications.length} Missing Factor{clarifications.length > 1 ? 's' : ''})
                </h2>
                <span className="text-[10px] font-mono bg-amber-200/70 text-amber-900 px-2 py-0.5 rounded font-semibold">
                  Required for Deterministic Scoping
                </span>
              </div>
              <p className="text-xs text-amber-800 leading-relaxed">
                Essential discriminators are unstated in the provided documentation. Layer 5 BIS Applicability requires these values to deterministically confirm standard scope and QCO status without speculation.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            {clarifications.map((item, idx) => {
              const attrKey = item.attribute_name || item.attribute;
              const isSubmitting = submittingAttr === attrKey;
              return (
                <div key={idx} className="p-3 rounded bg-white border border-amber-200 shadow-2xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-slate-800">{attrKey}</span>
                    <span className="text-[10px] font-mono text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">
                      REQUIRED
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-tight">
                    {item.question || item.reason || `Provide exact specification for ${attrKey}.`}
                  </p>
                  <div className="flex gap-1.5">
                    <input
                      type="text"
                      placeholder={`Enter ${attrKey} value...`}
                      value={clarifyValues[attrKey] || ''}
                      onChange={(e) => setClarifyValues({ ...clarifyValues, [attrKey]: e.target.value })}
                      onKeyDown={(e) => e.key === 'Enter' && handleClarifySubmit(attrKey)}
                      className="flex-1 px-2.5 py-1 text-xs border border-slate-300 rounded focus:border-slate-900 focus:outline-none bg-slate-50"
                    />
                    <button
                      onClick={() => handleClarifySubmit(attrKey)}
                      disabled={isSubmitting || !clarifyValues[attrKey]?.trim()}
                      className="px-3 py-1 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white rounded text-xs font-semibold transition cursor-pointer"
                    >
                      {isSubmitting ? 'Saving...' : 'Confirm'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Primary Technical DNA Matrix */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-slate-600 text-sm">tune</span>
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              Product Technical Fact Ledger
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-500">
            {Object.keys(attributes).length + 4} Parameters Inspected
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-100/70 text-slate-600 font-mono text-[10px] uppercase tracking-wider">
                <th className="py-2.5 px-4">Parameter</th>
                <th className="py-2.5 px-4">Confirmed Technical Value</th>
                <th className="py-2.5 px-4">Verification State</th>
                <th className="py-2.5 px-4">Provenance Source</th>
                <th className="py-2.5 px-4 text-right">Regulatory Impact</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {canonicalFields.map((field) => {
                const val = field.defaultVal;
                const isPresent = val !== null && val !== undefined && val !== '';
                const isClarified = !clarifications.some((c) => (c.attribute_name || c.attribute) === field.key);
                const state = isPresent ? (isClarified ? 'USER_CONFIRMED' : 'EXTRACTED') : 'MISSING';

                return (
                  <tr key={field.key} className="hover:bg-slate-50 transition">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      {field.label}
                      <span className="block text-[10px] font-mono font-normal text-slate-400">{field.key}</span>
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {isPresent ? (
                        <span className="text-slate-800 font-medium">{val}</span>
                      ) : (
                        <span className="text-slate-400 italic">Not specified in uploaded documents</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {state === 'USER_CONFIRMED' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          CONFIRMED
                        </span>
                      )}
                      {state === 'EXTRACTED' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-sky-50 text-sky-700 border border-sky-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-sky-500"></span>
                          EXTRACTED
                        </span>
                      )}
                      {state === 'MISSING' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-100 text-slate-500 border border-slate-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                          MISSING
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                      {isPresent ? (dna.source_type || 'DOCUMENT_INGESTION') : '—'}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-[11px]">
                      {isPresent ? (
                        <span className="text-emerald-700 font-medium">Determines Scope</span>
                      ) : (
                        <span className="text-amber-700">Scope Pending</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Technical Raw Fact Audit Card */}
      <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2 text-xs">
        <h3 className="font-bold text-slate-900 text-xs uppercase tracking-wide flex items-center gap-1.5">
          <span className="material-symbols-outlined text-sm text-slate-500">description</span>
          <span>Technical Ingestion Spec Digest</span>
        </h3>
        <p className="text-slate-600 text-xs leading-relaxed font-mono bg-slate-50 p-3 rounded border border-slate-200">
          {assessment.description || 'No raw technical specification recorded for this assessment.'}
        </p>
      </div>
    </div>
  );
}
