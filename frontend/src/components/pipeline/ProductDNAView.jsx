import React, { useState } from 'react';
import { StatusBadge } from '../StatusBadge';

export function ProductDNAView({ assessment, onClarify, onNavigate }) {
  const [clarifyValues, setClarifyValues] = useState({});
  const [submittingAttr, setSubmittingAttr] = useState(null);
  const [inspectingParam, setInspectingParam] = useState(null);

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
              No active product assessment is currently selected. Start by providing technical product information in Step 1.
            </p>
          </div>
          <div className="flex justify-center pt-2">
            <button
              onClick={() => onNavigate('input')}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold transition cursor-pointer"
            >
              Step 1: Product Input
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
    { key: 'product_name', label: 'Product Model / Trade Name', defaultVal: assessment.product_name || dna.product_name, impact: 'Catalog Identification' },
    { key: 'category', label: 'Product Category', defaultVal: assessment.category || dna.category, impact: 'Primary Standard Category Scope' },
    { key: 'intended_use', label: 'Intended Use & Environment', defaultVal: dna.intended_use, impact: 'Statutory Safety Envelope' },
    { key: 'material', label: 'Primary Materials & Grades', defaultVal: Array.isArray(dna.materials) ? dna.materials.join(', ') : (dna.material || attributes.material), impact: 'Material Conformance (Cl. 4.1)' },
    { key: 'capacity_ml', label: 'Nominal Capacity / Volume', defaultVal: dna.capacity_ml || attributes.capacity_ml ? `${dna.capacity_ml || attributes.capacity_ml} mL` : (attributes.capacity || attributes.volume || null), impact: 'Test Volume Tolerance (Cl. 5.1)' },
    { key: 'construction', label: 'Construction & Wall Type', defaultVal: dna.construction || attributes.construction, impact: 'Double Wall Requirement (Cl. 5.2)' },
    { key: 'insulation', label: 'Thermal / Electrical Insulation', defaultVal: dna.insulated !== undefined ? (dna.insulated ? 'Vacuum Double Wall Insulation' : 'Non-Insulated') : (dna.insulation || attributes.insulation), impact: 'Thermal Performance Test (Cl. 5.3)' },
    { key: 'food_contact', label: 'Food Contact Surface', defaultVal: dna.food_contact !== undefined ? (dna.food_contact ? 'Yes (SS 304 / Grade 304S1)' : 'No') : null, impact: 'Leaching & Toxicity (Cl. 4.2)' },
    { key: 'rated_voltage', label: 'Rated Voltage (AC/DC)', defaultVal: dna.rated_voltage || attributes.rated_voltage ? `${dna.rated_voltage || attributes.rated_voltage} V` : null, impact: 'Electrical Safety Envelope' },
    { key: 'rated_power_w', label: 'Rated Power / Wattage', defaultVal: dna.rated_power_w || attributes.rated_power_w ? `${dna.rated_power_w || attributes.rated_power_w} W` : null, impact: 'Power Rating Verification' },
    { key: 'standards_claimed', label: 'Manufacturer Claimed Standards', defaultVal: dna.standards_claimed?.length ? dna.standards_claimed.join(', ') : null, impact: 'Self-Declaration vs Statutory Scope' },
  ];

  return (
    <div className="flex-1 p-6 md:p-8 space-y-6 overflow-y-auto font-sans bg-[#F8FAFC]">
      {/* Step Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded">
              Step 02 / 08 &bull; Product DNA & Fact Ledger
            </span>
            <span className="text-xs text-slate-500 font-mono">0% LLM Compliance Authority</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Product DNA Fact Ledger</span>
            <span className="text-xs font-mono font-normal text-slate-500">[{assessment.assessment_number || assessment.assessment_id?.slice(0, 8)}]</span>
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            This is the structured representation of the product that drives applicability and requirement evaluation.
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

      {/* Primary Concept Callout Banner */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 to-indigo-950 text-white shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-300 font-bold block">
            Core Compiler Principle
          </span>
          <div className="text-sm font-semibold text-white">
            This structured DNA drives deterministic BIS applicability and clause evaluation.
          </div>
          <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
            Deterministic rule engines match these empirical facts against Gazette QCO schedules. A proposed AI parameter must never visually or legally substitute for accepted evidence-backed facts.
          </p>
        </div>
        <div className="flex sm:flex-col gap-2 shrink-0 text-[10px] font-mono">
          <div className="flex items-center gap-1.5 bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span>ACCEPTED_EVIDENCE_BACKED</span>
          </div>
          <div className="flex items-center gap-1.5 bg-amber-500/20 text-amber-300 px-2 py-1 rounded border border-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
            <span>AI_ASSISTED / PROPOSED</span>
          </div>
          <div className="flex items-center gap-1.5 bg-slate-500/20 text-slate-300 px-2 py-1 rounded border border-slate-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
            <span>MISSING_EVIDENCE</span>
          </div>
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
            {Object.keys(attributes).length + 4} Parameters Inspected &bull; Click parameter to view provenance
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-100/70 text-slate-600 font-mono text-[10px] uppercase tracking-wider">
                <th className="py-2.5 px-4">Parameter Name</th>
                <th className="py-2.5 px-4">Value & Visual State</th>
                <th className="py-2.5 px-4">Trust Boundary</th>
                <th className="py-2.5 px-4">Provenance Source</th>
                <th className="py-2.5 px-4 text-right">Regulatory Impact</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {canonicalFields.map((field) => {
                const val = field.defaultVal;
                const isPresent = val !== null && val !== undefined && val !== '';
                const isClarified = !clarifications.some((c) => (c.attribute_name || c.attribute) === field.key);
                const state = isPresent ? (isClarified ? 'ACCEPTED_EVIDENCE_BACKED' : 'AI_ASSISTED / PROPOSED') : 'MISSING_EVIDENCE';

                return (
                  <tr
                    key={field.key}
                    onClick={() => setInspectingParam({ ...field, state })}
                    className="hover:bg-slate-50/80 transition cursor-pointer"
                  >
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      <div className="flex items-center gap-1.5">
                        <span>{field.label}</span>
                        <span className="material-symbols-outlined text-slate-400 text-xs hover:text-slate-700">info</span>
                      </div>
                      <span className="block text-[10px] font-mono font-normal text-slate-400">{field.key}</span>
                    </td>

                    {/* Value rendered according to trust tier */}
                    <td className="py-3 px-4 font-mono">
                      {state === 'ACCEPTED_EVIDENCE_BACKED' && (
                        <div className="p-1.5 rounded bg-emerald-50/60 border border-emerald-200 text-emerald-950 font-bold inline-block">
                          <span>{val}</span>
                        </div>
                      )}
                      {state === 'AI_ASSISTED / PROPOSED' && (
                        <div className="p-1.5 rounded bg-amber-50/60 border border-dashed border-amber-300 text-amber-900 italic inline-block">
                          <span>{val}</span>
                          <span className="text-[10px] font-normal not-italic text-amber-700 block font-sans">
                            [AI Candidate &bull; Requires Engineer Attestation]
                          </span>
                        </div>
                      )}
                      {state === 'MISSING_EVIDENCE' && (
                        <span className="text-slate-400 italic font-sans text-[11px] block">
                          [MISSING EVIDENCE &bull; Upload Spec or Test Report]
                        </span>
                      )}
                    </td>

                    {/* Trust Boundary State Badge */}
                    <td className="py-3 px-4">
                      {state === 'ACCEPTED_EVIDENCE_BACKED' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          ACCEPTED_EVIDENCE_BACKED
                        </span>
                      )}
                      {state === 'AI_ASSISTED / PROPOSED' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-800 border border-amber-200" title="Proposed AI value — not an accepted statutory value">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                          AI_ASSISTED / PROPOSED
                        </span>
                      )}
                      {state === 'MISSING_EVIDENCE' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-100 text-slate-500 border border-slate-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                          MISSING_EVIDENCE
                        </span>
                      )}
                    </td>

                    {/* Provenance Source */}
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                      {isPresent ? (
                        <div className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-[13px] text-slate-400">description</span>
                          <span className="truncate max-w-[160px]">{dna.source_type || 'DOCUMENT_INGESTION'}</span>
                        </div>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>

                    {/* Regulatory Impact */}
                    <td className="py-3 px-4 text-right font-mono text-[11px]">
                      {isPresent ? (
                        <span className="text-indigo-700 font-medium">{field.impact || 'Determines Scope'}</span>
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

      {/* Parameter Provenance Inspection Drawer */}
      {inspectingParam && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block">
                  Product DNA Provenance Inspector
                </span>
                <h3 className="text-sm font-bold text-slate-900">{inspectingParam.label}</h3>
                <span className="text-xs font-mono text-slate-400">{inspectingParam.key}</span>
              </div>
              <button
                type="button"
                onClick={() => setInspectingParam(null)}
                className="p-1 text-slate-400 hover:text-slate-700 rounded transition cursor-pointer"
              >
                <span className="material-symbols-outlined text-base">close</span>
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Confirmed Value:</span>
                <div className="font-mono font-bold text-slate-900 text-sm">
                  {inspectingParam.defaultVal || 'Not specified'}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                <div className="p-2.5 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[9px] uppercase text-slate-400 block font-bold">Trust Classification</span>
                  <span className="font-bold text-indigo-700">{inspectingParam.state}</span>
                </div>
                <div className="p-2.5 rounded bg-slate-50 border border-slate-100">
                  <span className="text-[9px] uppercase text-slate-400 block font-bold">Source Provenance</span>
                  <span className="text-slate-800">{dna.source_type || 'DOCUMENT_INGESTION'}</span>
                </div>
              </div>

              <div className="p-3 rounded bg-indigo-50/50 border border-indigo-100 space-y-1">
                <span className="text-[10px] font-mono uppercase text-indigo-900 font-bold">Statutory Regulatory Impact:</span>
                <p className="text-indigo-950 leading-relaxed font-sans">
                  {inspectingParam.impact}. Matches standard applicability rule parameters and clause limits under Indian Standard specifications.
                </p>
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="button"
                onClick={() => setInspectingParam(null)}
                className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

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
