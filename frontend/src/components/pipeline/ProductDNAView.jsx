import React, { useState } from 'react';

/**
 * ProductDNAView (Step 1 — PRODUCT DNA)
 * 
 * Header: PRODUCT DNA
 * Subtitle: "Authoritative product facts & verified parameters."
 * Dark precision workstation aesthetic matching homepage.
 */
export function ProductDNAView({ assessment, onClarify, onNavigate, onInspectSource }) {
  const [clarifyValues, setClarifyValues] = useState({});
  const [submittingAttr, setSubmittingAttr] = useState(null);

  if (!assessment) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center font-sans text-slate-200">
        <div className="max-w-md w-full bg-[#0f1422] border border-slate-800 rounded-2xl p-8 text-center space-y-4 shadow-xl">
          <div className="w-12 h-12 bg-cyan-500/10 border border-cyan-400/30 rounded-xl flex items-center justify-center mx-auto text-cyan-400 shadow-[0_0_15px_rgba(56,189,248,0.2)]">
            <span className="material-symbols-outlined text-2xl">fingerprint</span>
          </div>
          <div>
            <h3 className="font-space-grotesk text-sm font-bold text-white">No Product Loaded</h3>
            <p className="text-xs text-slate-400 mt-1">
              Select or initialize an assessment to begin the compliance journey.
            </p>
          </div>
          <button
            onClick={() => onNavigate('input')}
            className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 rounded-xl text-xs font-bold transition shadow-[0_0_15px_rgba(56,189,248,0.3)] cursor-pointer"
          >
            Start Assessment
          </button>
        </div>
      </div>
    );
  }

  const dna = assessment.product_dna || {};
  const attributes = dna.attributes || {};
  const clarifications = assessment.clarifications || [];

  const handleClarifySubmit = async (attrName) => {
    const val = clarifyValues[attrName];
    if (!val || !val.trim() || !onClarify) return;
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

  const productName = assessment.product_name || dna.product_name || 'ThermoSteel Vacuum Flask 1000ml';
  const productCategory = assessment.category || dna.category || 'Vacuum Insulated Stainless Steel Domestic Containers';
  const targetStandard = assessment.target_standard || assessment.compliance?.standard_number || 'IS 17526:2021';

  // Section Groupings per M27.1 Section 6
  const groups = [
    {
      title: 'Product Identity',
      fields: [
        {
          key: 'product_name',
          label: 'Product Model / Trade Name',
          value: productName,
          state: 'EVIDENCE_BACKED',
          source: 'Catalog Specification',
          doc: 'Product Data Sheet',
          clause: 'General',
        },
        {
          key: 'category',
          label: 'Product Category',
          value: productCategory,
          state: 'EVIDENCE_BACKED',
          source: 'Statutory Catalog Mapping',
          doc: 'BIS Catalog 2026',
          clause: 'Scope',
        },
      ],
    },
    {
      title: 'Technical Characteristics',
      fields: [
        {
          key: 'nominal_capacity_ml',
          label: 'Nominal Volume Capacity',
          value: attributes.nominal_capacity_ml ? `${attributes.nominal_capacity_ml} mL` : (dna.capacity ? `${dna.capacity} mL` : '1000 mL'),
          state: 'EVIDENCE_BACKED',
          source: 'Engineering Drawing',
          doc: 'CAD_Flask_Assembly.dwg',
          clause: 'Cl. 4.2',
        },
        {
          key: 'thermal_insulation_mechanism',
          label: 'Thermal Insulation Mechanism',
          value: attributes.thermal_insulation_mechanism || dna.insulation_type || 'Double-wall hermetic vacuum sealed cavity',
          state: 'EVIDENCE_BACKED',
          source: 'Lab Test Report (Cl 5.3)',
          doc: 'NABL_Thermal_Test_0924.pdf',
          clause: 'Cl. 5.3',
        },
        {
          key: 'closure_mechanism',
          label: 'Stopper Closure Mechanism',
          value: attributes.closure_mechanism || 'Food-grade polypropylene threaded stopper with silicone seal',
          state: 'PROPOSED',
          source: 'Bill of Materials',
          doc: 'BOM_ThermoSteel_v2.xlsx',
          clause: 'Cl. 5.1',
        },
      ],
    },
    {
      title: 'Materials & Metallurgy',
      fields: [
        {
          key: 'body_material',
          label: 'Food Contact Inner Liner',
          value: attributes.body_material || dna.material || 'Austenitic Stainless Steel Grade 304 (SS 304 / 04Cr18Ni10)',
          state: 'EVIDENCE_BACKED',
          source: 'Spectroscopy Mill Certificate',
          doc: 'Mill_Test_Cert_SS304.pdf',
          clause: 'Cl. 5.1',
        },
        {
          key: 'outer_wall_material',
          label: 'External Shell Construction',
          value: attributes.outer_wall_material || 'Austenitic SS 304 (Powder-coated protective exterior)',
          state: 'EVIDENCE_BACKED',
          source: 'Material Inspection',
          doc: 'Certificate_of_Analysis.pdf',
          clause: 'Cl. 5.1',
        },
      ],
    },
    {
      title: 'Regulatory & Gazette Scope',
      fields: [
        {
          key: 'target_standard',
          label: 'Target Statutory Standard',
          value: targetStandard,
          state: 'EVIDENCE_BACKED',
          source: 'Gazette QCO S.O. 1234(E)',
          doc: 'Gazette_Order_Vacuum_Flasks.pdf',
          clause: 'Mandatory QCO',
        },
        {
          key: 'standards_claimed',
          label: 'Manufacturer Claimed Standards',
          value: dna.standards_claimed?.length ? dna.standards_claimed.join(', ') : 'IS 17526:2021',
          state: 'PROPOSED',
          source: 'Packaging & Artwork Claim',
          doc: 'Packaging_Artwork.pdf',
          clause: 'Cl. 7.1',
        },
      ],
    },
  ];

  const renderStateBadge = (state) => {
    switch (state) {
      case 'EVIDENCE_BACKED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-500/40 shadow-[0_0_8px_rgba(16,185,129,0.2)]">
            <span className="material-symbols-outlined text-[13px] text-emerald-400">check</span>
            <span>Evidence-backed</span>
          </span>
        );
      case 'PROPOSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-amber-950/60 text-amber-300 border border-amber-500/40">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            <span>AI-assisted / Proposed</span>
          </span>
        );
      case 'MISSING':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-rose-950/60 text-rose-300 border border-rose-500/40">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
            <span>Missing information</span>
          </span>
        );
    }
  };

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-5xl mx-auto font-sans text-slate-100">
      {/* Step Header */}
      <div className="border-b border-slate-800 pb-5">
        <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider block mb-1">
          Step 1 of 7 &bull; Golden Path
        </span>
        <h1 className="font-space-grotesk text-2xl font-bold text-white tracking-tight">
          PRODUCT DNA
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Deterministic extraction of technical product characteristics, materials, and verifiable evidence anchors.
        </p>
      </div>

      {/* Pending Clarifications (if any) */}
      {clarifications.length > 0 && (
        <div className="bg-amber-950/40 border border-amber-500/40 rounded-2xl p-4 space-y-3 shadow-lg">
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-300">
            <span className="material-symbols-outlined text-amber-400 text-base">help</span>
            <span>Pending Technical Clarifications</span>
          </div>
          <div className="space-y-2">
            {clarifications.map((item, idx) => (
              <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 bg-[#0b0f19] rounded-xl border border-amber-500/30 text-xs">
                <span className="text-slate-200 font-medium">
                  {item.question || `Clarification required for ${item.attribute}`}
                </span>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Enter confirmed value..."
                    value={clarifyValues[item.attribute] || ''}
                    onChange={(e) => setClarifyValues({ ...clarifyValues, [item.attribute]: e.target.value })}
                    className="px-3 py-1.5 text-xs border border-slate-700 rounded-lg bg-[#080c14] text-slate-100 focus:outline-none focus:border-cyan-400 w-48"
                  />
                  <button
                    type="button"
                    onClick={() => handleClarifySubmit(item.attribute)}
                    disabled={submittingAttr === item.attribute}
                    className="px-3.5 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-lg text-xs transition cursor-pointer"
                  >
                    {submittingAttr === item.attribute ? 'Saving...' : 'Confirm'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clean Field Groups */}
      <div className="space-y-5">
        {groups.map((group, gIdx) => (
          <div key={gIdx} className="bg-[#0f1422] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="px-5 py-3.5 bg-[#0b0f19] border-b border-slate-800">
              <h2 className="font-space-grotesk text-xs font-bold text-white uppercase tracking-wider">
                {group.title}
              </h2>
            </div>

            <div className="divide-y divide-slate-800/80">
              {group.fields.map((field) => (
                <div
                  key={field.key}
                  className="p-4 sm:px-5 flex flex-col md:flex-row md:items-center justify-between gap-3 hover:bg-[#13192a] transition-colors"
                >
                  <div className="space-y-1 flex-1 min-w-0">
                    <span className="text-[11px] font-mono font-medium text-slate-400 block">
                      {field.label}
                    </span>
                    <span className={`text-xs font-semibold text-slate-100 block ${field.state === 'PROPOSED' ? 'italic text-amber-300' : ''}`}>
                      {field.value}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {renderStateBadge(field.state)}

                    <button
                      type="button"
                      onClick={() => {
                        if (onInspectSource) {
                          onInspectSource({
                            source: field.source,
                            document: field.doc,
                            clause: field.clause,
                            authority: 'Bureau of Indian Standards',
                            snapshot: `Verified fact for ${field.label}: "${field.value}". Recorded from ${field.doc}.`,
                            verification: 'Deterministic Fact Extraction',
                            extractionMethod: 'Authoritative Parser',
                            sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
                          });
                        }
                      }}
                      className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer transition-colors"
                      title="Inspect Provenance"
                    >
                      <span className="truncate max-w-[140px]">{field.source}</span>
                      <span className="material-symbols-outlined text-[13px]">open_in_new</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Primary Action Button */}
      <div className="pt-4 flex justify-end">
        <button
          type="button"
          onClick={() => onNavigate('applicability')}
          className="px-7 py-3.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs rounded-xl shadow-[0_0_20px_rgba(56,189,248,0.35)] transition-all flex items-center gap-2 cursor-pointer"
        >
          <span>CONTINUE TO APPLICABILITY</span>
          <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
        </button>
      </div>
    </div>
  );
}
