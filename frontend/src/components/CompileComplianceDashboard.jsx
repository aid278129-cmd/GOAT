import React, { useState } from 'react';
import { extractTextFromPDF, parseProductInfoFromText } from '../utils/pdfParser';
import { MorphingInfinity } from './loading-ui/morphing-infinity';
import { TextShimmer } from './loading-ui/text-shimmer';

/**
 * CompileComplianceDashboard
 * 
 * The primary dashboard landing view for Zyntrix.
 * Centers around "Compile Compliance":
 * 1. User inputs or uploads product specifications / document
 * 2. Compiles deterministically through:
 *    Product DNA -> BIS Applicability -> Requirements -> Evidence -> Gaps -> Actions -> Assessment Passport
 * 3. Shows exactly what BIS requirements apply, open gaps, and compliance verdict.
 */
export function CompileComplianceDashboard({
  onCompileCompliance,
  onResetGoldenDemo,
  isResettingDemo = false,
  onOpenAssistant,
  onInspectSource,
}) {
  const [intakeMode, setIntakeMode] = useState('upload'); // 'upload' | 'manual' | 'preset'

  // Manual & Extracted Specification State
  const [productName, setProductName] = useState('ThermoSteel Vacuum Flask 1000ml');
  const [category, setCategory] = useState('Domestic Vacuum Ware & Food-Contact Containers');
  const [targetStandard, setTargetStandard] = useState('IS 17526:2021');
  const [capacity, setCapacity] = useState('1000');
  const [material, setMaterial] = useState('Austenitic Stainless Steel 304 (SS 304)');
  const [insulationType, setInsulationType] = useState('Double-wall hermetic vacuum sealed');
  const [intendedUse, setIntendedUse] = useState('Domestic beverage storage (hot & cold fluid retention)');
  const [description, setDescription] = useState(
    '1000 mL cylindrical vacuum insulated flask fabricated with food-contact grade SS 304 inner and outer walls. Equipped with polypropylene threaded stopper and silicone hermetic seal.'
  );

  // File Upload State
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isParsing, setIsParsing] = useState(false);
  const [fileSha256, setFileSha256] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  // Pre-configured Statutory Presets
  const presets = [
    {
      id: 'is17526',
      standard: 'IS 17526:2021',
      title: 'Stainless Steel Vacuum Flasks (1000ml)',
      category: 'Domestic Containers & Kitchenware',
      qco: 'Mandatory QCO (Scheme I - ISI Mark)',
      desc: 'Double-wall stainless steel vacuum insulated flask up to 2000 ml. Mandatory Gazette Quality Control Order.',
      data: {
        productName: 'ThermoSteel Vacuum Flask 1000ml',
        category: 'Domestic Vacuum Ware & Food-Contact Containers',
        targetStandard: 'IS 17526:2021',
        capacity: '1000',
        material: 'Austenitic Stainless Steel 304 (SS 304)',
        insulationType: 'Double-wall hermetic vacuum sealed',
        intendedUse: 'Domestic beverage storage (hot & cold fluid retention)',
        description: '1000 mL cylindrical vacuum insulated flask with food-grade SS 304 inner liner, threaded polypropylene stopper, and silicone hermetic gasket.',
      },
    },
    {
      id: 'is16221',
      standard: 'IS 16221 (Part 2):2015',
      title: '5 kW Hybrid Solar Inverter',
      category: 'Power Electronics & Renewable Energy',
      qco: 'Mandatory CRS (Scheme II)',
      desc: 'Grid-connected and hybrid photovoltaic power converters. Compulsory Registration Scheme under MNRE/MeitY.',
      data: {
        productName: 'SolarMax 5kW Hybrid PV Inverter',
        category: 'Power Electronics & Converters',
        targetStandard: 'IS 16221 (Part 2):2015',
        capacity: '5000',
        material: 'Die-cast aluminum IP65 enclosure',
        insulationType: 'Galvanic isolation / Class I insulation',
        intendedUse: 'Grid synchronization and residential solar storage',
        description: '5000 W hybrid solar inverter with anti-islanding protection (IS 16169), dual MPPT inputs, and 230V AC output.',
      },
    },
    {
      id: 'is13252',
      standard: 'IS 13252 (Part 1):2010',
      title: '65W USB-C GaN Power Adapter',
      category: 'Information Technology Equipment (ITE)',
      qco: 'Mandatory CRS (Scheme II)',
      desc: 'Mains-operated power adapters and battery chargers for IT equipment. Mandatory under MeitY CRO.',
      data: {
        productName: 'VoltCharge 65W GaN Fast Charger',
        category: 'IT Equipment & Power Adapters',
        targetStandard: 'IS 13252 (Part 1):2010',
        capacity: '65',
        material: 'V-0 flame-retardant polycarbonate',
        insulationType: 'Class II reinforced insulation',
        intendedUse: 'Powering laptops and mobile smart devices',
        description: '65W GaN power adapter with 100-240V AC input, Type-C PD 3.0 output, and creepage/clearance distance compliance.',
      },
    },
  ];

  // Handle File Selection and Parsing
  const handleFileChange = async (file) => {
    if (!file) return;
    setUploadedFile(file);
    setIsParsing(true);

    try {
      // Calculate a local SHA-256 for integrity preview
      const buffer = await file.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
      setFileSha256(hashHex);

      // If PDF, extract text
      if (file.name.toLowerCase().endsWith('.pdf')) {
        const text = await extractTextFromPDF(file);
        if (text) {
          const parsed = parseProductInfoFromText(text, file.name);
          if (parsed.productName) setProductName(parsed.productName);
          if (parsed.category) setCategory(parsed.category);
          if (parsed.description) setDescription(parsed.description);
        }
      } else {
        // Plain text / JSON parsing
        const reader = new FileReader();
        reader.onload = (e) => {
          const content = e.target?.result;
          if (typeof content === 'string') {
            const parsed = parseProductInfoFromText(content, file.name);
            if (parsed.productName) setProductName(parsed.productName);
            if (parsed.description) setDescription(parsed.description);
          }
        };
        reader.readAsText(file);
      }
    } catch (err) {
      console.warn('File inspection notice:', err);
    } finally {
      setIsParsing(false);
    }
  };

  const handleApplyPreset = (preset) => {
    setProductName(preset.data.productName);
    setCategory(preset.data.category);
    setTargetStandard(preset.data.targetStandard);
    setCapacity(preset.data.capacity);
    setMaterial(preset.data.material);
    setInsulationType(preset.data.insulationType);
    setIntendedUse(preset.data.intendedUse);
    setDescription(preset.data.description);
    setIntakeMode('manual');
  };

  const handleCompile = () => {
    const payload = {
      productName,
      category,
      targetStandard,
      capacity,
      material,
      insulationType,
      intendedUse,
      description,
      uploadedFileName: uploadedFile?.name || null,
      sha256: fileSha256 || null,
    };

    if (onCompileCompliance) {
      onCompileCompliance(payload);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 font-sans">
      {/* ------------------------------------------------------------- */}
      {/* 1. Header: Enterprise Statutory Compiler Identity             */}
      {/* ------------------------------------------------------------- */}
      <div className="border-b border-slate-200 pb-6 mb-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full bg-blue-600"></span>
              <span className="text-[11px] font-bold uppercase tracking-wider text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">
                Bureau of Indian Standards Statutory Compiler
              </span>
              <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">
                SIH Problem Statement 26107
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Compile Compliance
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
              Input technical product specifications or upload documentation to deterministically evaluate applicable Indian Standards, extract Product DNA, audit evidence, detect gaps, and compile a compliance passport.
            </p>
          </div>

          {/* Quick Benchmark Load */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => onResetGoldenDemo && onResetGoldenDemo()}
              disabled={isResettingDemo}
              className="px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:border-slate-400 rounded-lg transition-colors shadow-2xs flex items-center gap-2 cursor-pointer disabled:opacity-50"
              title="Load IS 17526:2021 Stainless Steel Vacuum Flask Golden Demo"
            >
              {isResettingDemo ? (
                <>
                  <MorphingInfinity className="w-4 h-4 text-blue-600" />
                  <TextShimmer baseColor="#3b82f6" shimmerColor="#1e3a8a" duration={1.5} className="font-semibold text-xs">
                    Loading Golden Demo...
                  </TextShimmer>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[16px] text-blue-600">
                    auto_awesome
                  </span>
                  <span>Load Golden Demo (IS 17526)</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 2. Main Console: "Compile Compliance" Specification Intake    */}
      {/* ------------------------------------------------------------- */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden mb-8">
        {/* Mode Selector Navigation */}
        <div className="flex items-center justify-between border-b border-slate-200 px-4 sm:px-6 bg-slate-50/70">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5 py-3">
              <span className="material-symbols-outlined text-blue-600 text-lg">fact_check</span>
              <span>Specification Intake</span>
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setIntakeMode('upload')}
              className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors cursor-pointer ${
                intakeMode === 'upload'
                  ? 'border-blue-600 text-blue-700 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-900'
              }`}
            >
              Upload Document / Datasheet
            </button>
            <button
              type="button"
              onClick={() => setIntakeMode('manual')}
              className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors cursor-pointer ${
                intakeMode === 'manual'
                  ? 'border-blue-600 text-blue-700 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-900'
              }`}
            >
              Manual Specification Form
            </button>
            <button
              type="button"
              onClick={() => setIntakeMode('preset')}
              className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors cursor-pointer ${
                intakeMode === 'preset'
                  ? 'border-blue-600 text-blue-700 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-900'
              }`}
            >
              Statutory Presets
            </button>
          </div>
        </div>

        {/* Console Body */}
        <div className="p-5 sm:p-7">
          {/* TAB 1: Document Upload */}
          {intakeMode === 'upload' && (
            <div className="space-y-5">
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragActive(false);
                  if (e.dataTransfer.files?.[0]) {
                    handleFileChange(e.dataTransfer.files[0]);
                  }
                }}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50/50'
                    : 'border-slate-300 hover:border-blue-400 bg-slate-50/50'
                }`}
                onClick={() => document.getElementById('spec-file-input')?.click()}
              >
                <input
                  id="spec-file-input"
                  type="file"
                  accept=".pdf,.json,.txt,.csv,.doc,.docx"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      handleFileChange(e.target.files[0]);
                    }
                  }}
                  className="hidden"
                />

                <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center mx-auto mb-3">
                  <span className="material-symbols-outlined text-2xl">upload_file</span>
                </div>

                <div className="text-sm font-bold text-slate-900">
                  {uploadedFile ? uploadedFile.name : 'Upload Product Specification Document'}
                </div>

                <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                  Drag and drop technical specification sheet, test report, product manual, or Bill of Materials (PDF, JSON, TXT).
                </p>

                <div className="flex items-center justify-center gap-2 mt-4 text-[11px] text-slate-400 font-mono">
                  <span>Accepted: PDF &bull; JSON &bull; CSV &bull; TXT</span>
                  <span>&bull;</span>
                  <span>Max 25 MB</span>
                </div>
              </div>

              {/* Uploaded File Integrity Card */}
              {uploadedFile && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-emerald-600 text-sm">check_circle</span>
                      <span>Document Received & Parsed</span>
                    </span>
                    <span className="font-mono text-[11px] text-slate-500">
                      {(uploadedFile.size / 1024).toFixed(1)} KB
                    </span>
                  </div>

                  {fileSha256 && (
                    <div className="font-mono text-[10px] text-slate-500 break-all bg-white p-2 rounded border border-slate-200">
                      SHA-256: {fileSha256}
                    </div>
                  )}

                  <div className="pt-2 text-slate-600 text-xs">
                    Target detected: <strong>{productName}</strong> ({category})
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Manual Specification Form */}
          {intakeMode === 'manual' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
                  Product Commercial Name / Model
                </label>
                <input
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
                  placeholder="e.g. ThermoSteel Vacuum Flask 1000ml"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
                  Product Category
                </label>
                <input
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
                  placeholder="e.g. Domestic Vacuum Ware & Food-Contact Containers"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
                  Applicable Indian Standard (or Auto-Detect)
                </label>
                <input
                  type="text"
                  value={targetStandard}
                  onChange={(e) => setTargetStandard(e.target.value)}
                  className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-mono focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
                  placeholder="e.g. IS 17526:2021"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
                  Capacity / Rating
                </label>
                <input
                  type="text"
                  value={capacity}
                  onChange={(e) => setCapacity(e.target.value)}
                  className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
                  placeholder="e.g. 1000 mL or 5000 W"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
                  Materials & Construction
                </label>
                <input
                  type="text"
                  value={material}
                  onChange={(e) => setMaterial(e.target.value)}
                  className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
                  placeholder="e.g. Austenitic Stainless Steel 304 (SS 304) for food-contact inner/outer walls"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
                  Technical Description & Insulation Mechanism
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors leading-relaxed"
                  placeholder="Describe dimensions, wall thickness, thermal performance claim, closures, and test parameters..."
                />
              </div>
            </div>
          )}

          {/* TAB 3: Statutory Presets */}
          {intakeMode === 'preset' && (
            <div className="space-y-3">
              <div className="text-xs text-slate-500 mb-2">
                Select an official statutory benchmark to immediately load verified product characteristics and Quality Control Order requirements:
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {presets.map((p) => (
                  <div
                    key={p.id}
                    className="p-4 bg-slate-50 hover:bg-blue-50/50 border border-slate-200 hover:border-blue-300 rounded-xl transition-all cursor-pointer flex flex-col justify-between"
                    onClick={() => handleApplyPreset(p)}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-1 mb-2">
                        <span className="font-mono text-xs font-bold text-blue-700 bg-white px-2 py-0.5 rounded border border-blue-200">
                          {p.standard}
                        </span>
                        <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
                          {p.qco.split(' ')[0]}
                        </span>
                      </div>
                      <h4 className="font-bold text-slate-900 text-xs mb-1">{p.title}</h4>
                      <p className="text-[11px] text-slate-600 leading-relaxed">{p.desc}</p>
                    </div>

                    <div className="mt-3 pt-2 border-t border-slate-200 flex items-center justify-between text-[11px] font-semibold text-blue-700">
                      <span>Load Specification</span>
                      <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compilation Execution Action Bar */}
          <div className="mt-6 pt-5 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-[11px] text-slate-500 leading-relaxed text-center sm:text-left">
              Deterministic evaluation executes: <strong>Product DNA &rarr; Applicability &rarr; Requirements &rarr; Evidence &rarr; Gaps &rarr; Actions &rarr; Passport</strong>.
            </div>

            <button
              type="button"
              onClick={handleCompile}
              className="w-full sm:w-auto px-7 py-3 bg-blue-600 hover:bg-blue-700 active:scale-[0.99] text-white font-semibold text-xs rounded-lg shadow-sm hover:shadow transition-all flex items-center justify-center gap-2 cursor-pointer shrink-0"
            >
              <span>COMPILE COMPLIANCE</span>
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 3. Statutory Standards Scoping Matrix (Authentic Engineering) */}
      {/* ------------------------------------------------------------- */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 font-mono">
            Mandatory Statutory Quality Control Orders (QCO)
          </h2>
          <span className="text-[11px] text-slate-400 font-mono">
            Gazette of India Published Orders
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            {
              standard: 'IS 17526:2021',
              title: 'Vacuum Insulated Flasks & Containers',
              scope: 'Double-wall stainless steel domestic containers up to 2000 ml',
              scheme: 'Scheme I (ISI Mark)',
              status: 'Mandatory QCO',
            },
            {
              standard: 'IS 16221 (Part 2):2015',
              title: 'Solar Photovoltaic Inverters',
              scope: 'Power converters & grid-tied inverters for PV power systems',
              scheme: 'Scheme II (CRS)',
              status: 'Mandatory CRO',
            },
            {
              standard: 'IS 13252 (Part 1):2010',
              title: 'Information Technology Equipment',
              scope: 'Mains-powered and battery-operated office & IT devices',
              scheme: 'Scheme II (CRS)',
              status: 'Mandatory CRO',
            },
            {
              standard: 'IS 302 (Part 1):2024',
              title: 'Household Electrical Appliances Safety',
              scope: 'General safety requirements for electric domestic appliances',
              scheme: 'Scheme I (ISI Mark)',
              status: 'Statutory Safety',
            },
          ].map((item, idx) => (
            <div
              key={idx}
              className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-2 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                    {item.standard}
                  </span>
                  <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
                    {item.status}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-900 mt-2">{item.title}</h4>
                <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">{item.scope}</p>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                <span className="text-slate-500 font-medium">{item.scheme}</span>
                <button
                  type="button"
                  onClick={() => {
                    setTargetStandard(item.standard);
                    setIntakeMode('manual');
                  }}
                  className="text-blue-600 hover:text-blue-800 font-semibold cursor-pointer"
                >
                  Select &rarr;
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 4. The 7-Stage Compliance Pipeline Overview                   */}
      {/* ------------------------------------------------------------- */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 shadow-2xs">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-3">
          Zyntrix Deterministic Regulatory Execution Pipeline
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 text-xs font-sans">
          {[
            { step: '01', title: 'Product DNA', desc: 'Facts & attributes extraction' },
            { step: '02', title: 'Applicability', desc: 'Statutory standard & QCO scoping' },
            { step: '03', title: 'Requirements', desc: 'Clause parameters & limits' },
            { step: '04', title: 'Evidence Matrix', desc: 'Lab test artifacts & SHA-256' },
            { step: '05', title: 'Compliance Gaps', desc: 'Missing tests & deviations' },
            { step: '06', title: 'Lab Actions', desc: 'Testing orders & dispatch' },
            { step: '07', title: 'Passport', desc: 'Cryptographic compliance attestation' },
          ].map((st) => (
            <div key={st.step} className="bg-white p-2.5 rounded-lg border border-slate-200">
              <span className="font-mono text-[10px] font-bold text-blue-700 block">
                {st.step}
              </span>
              <div className="font-semibold text-slate-900 mt-0.5">{st.title}</div>
              <div className="text-[10px] text-slate-500 mt-0.5 leading-tight">{st.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
