import React, { useState } from 'react';
import { extractTextFromPDF, parseProductInfoFromText } from '../utils/pdfParser';
import { MorphingInfinity } from './loading-ui/morphing-infinity';
import { TextShimmer } from './loading-ui/text-shimmer';
import GlideSelect from './loading-ui/GlideSelect';

/**
 * CompileComplianceDashboard
 * 
 * The primary dashboard landing view for GOAT BIS Compliance Compiler.
 * Dark precision engineering workstation aesthetic matching 3D Homepage.
 * Integrates GlideSelect for standards selection.
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

  const standardOptions = [
    { value: 'IS 17526:2021', label: 'IS 17526:2021 (Vacuum Flasks)', tag: 'Scheme I' },
    { value: 'IS 16221 (Part 2):2015', label: 'IS 16221:2015 (Solar PV Inverter)', tag: 'CRS' },
    { value: 'IS 13252 (Part 1):2010', label: 'IS 13252:2010 (IT Equipment)', tag: 'CRS' },
    { value: 'IS 302 (Part 1):2024', label: 'IS 302:2024 (Electric Appliances)', tag: 'Scheme I' },
  ];

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
          if (parsed.targetStandard) setTargetStandard(parsed.targetStandard);
          if (parsed.capacity) setCapacity(parsed.capacity);
          if (parsed.material) setMaterial(parsed.material);
          if (parsed.insulationType) setInsulationType(parsed.insulationType);
          if (parsed.intendedUse) setIntendedUse(parsed.intendedUse);
          if (parsed.description) setDescription(parsed.description);
        }
      }
    } catch (err) {
      console.warn('File processing notice:', err);
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
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 font-sans text-slate-100">
      {/* ------------------------------------------------------------- */}
      {/* 1. Header: Enterprise Statutory Compiler Identity             */}
      {/* ------------------------------------------------------------- */}
      <div className="border-b border-slate-800 pb-6 mb-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-cyan-300 bg-cyan-950/60 border border-cyan-500/30 px-2.5 py-0.5 rounded shadow-[0_0_10px_rgba(56,189,248,0.2)]">
                Bureau of Indian Standards Statutory Compiler
              </span>
              <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">
                SIH Problem Statement 26107
              </span>
            </div>
            <h1 className="font-space-grotesk text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Compile Compliance
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Input technical product specifications or upload documentation to deterministically evaluate applicable Indian Standards, extract Product DNA, audit evidence, detect gaps, and compile a certified compliance passport.
            </p>
          </div>

          {/* Quick Benchmark Load */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => onResetGoldenDemo && onResetGoldenDemo()}
              disabled={isResettingDemo}
              className="px-4 py-2.5 text-xs font-semibold text-cyan-200 bg-cyan-950/50 border border-cyan-500/40 hover:border-cyan-400 hover:bg-cyan-900/60 rounded-xl transition-all shadow-[0_0_15px_rgba(56,189,248,0.15)] flex items-center gap-2 cursor-pointer disabled:opacity-50"
              title="Load IS 17526:2021 Stainless Steel Vacuum Flask Golden Demo"
            >
              {isResettingDemo ? (
                <>
                  <MorphingInfinity className="w-4 h-4 text-cyan-400" />
                  <TextShimmer baseColor="#38bdf8" shimmerColor="#a5f3fc" duration={1.5} className="font-semibold text-xs">
                    Loading Golden Demo...
                  </TextShimmer>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[16px] text-cyan-400">
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
      <div className="bg-[#0f1422]/90 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl overflow-hidden mb-8">
        {/* Mode Selector Navigation */}
        <div className="flex items-center justify-between border-b border-slate-800 px-4 sm:px-6 bg-[#0a0d16]">
          <div className="flex items-center gap-2">
            <span className="text-xs font-space-grotesk font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5 py-3.5">
              <span className="material-symbols-outlined text-cyan-400 text-lg">fact_check</span>
              <span>Specification Intake</span>
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setIntakeMode('upload')}
              className={`px-3.5 py-3 text-xs font-medium border-b-2 transition-all cursor-pointer ${
                intakeMode === 'upload'
                  ? 'border-cyan-400 text-cyan-300 font-semibold bg-cyan-950/20'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Upload Document / Datasheet
            </button>
            <button
              type="button"
              onClick={() => setIntakeMode('manual')}
              className={`px-3.5 py-3 text-xs font-medium border-b-2 transition-all cursor-pointer ${
                intakeMode === 'manual'
                  ? 'border-cyan-400 text-cyan-300 font-semibold bg-cyan-950/20'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Manual Specification Form
            </button>
            <button
              type="button"
              onClick={() => setIntakeMode('preset')}
              className={`px-3.5 py-3 text-xs font-medium border-b-2 transition-all cursor-pointer ${
                intakeMode === 'preset'
                  ? 'border-cyan-400 text-cyan-300 font-semibold bg-cyan-950/20'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
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
                className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
                  dragActive
                    ? 'border-cyan-400 bg-cyan-950/30'
                    : 'border-slate-700/80 hover:border-cyan-500/50 bg-[#0b0f19]/70'
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

                <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 flex items-center justify-center mx-auto mb-3 shadow-[0_0_15px_rgba(56,189,248,0.2)]">
                  <span className="material-symbols-outlined text-3xl">upload_file</span>
                </div>

                <div className="font-space-grotesk text-sm font-bold text-white">
                  {uploadedFile ? uploadedFile.name : 'Upload Product Specification Document'}
                </div>

                <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                  Drag and drop technical specification sheet, test report, product manual, or Bill of Materials (PDF, JSON, TXT).
                </p>

                <div className="flex items-center justify-center gap-2 mt-4 text-[11px] text-slate-500 font-mono">
                  <span>Accepted: PDF &bull; JSON &bull; CSV &bull; TXT</span>
                  <span>&bull;</span>
                  <span>Max 25 MB</span>
                </div>
              </div>

              {/* Uploaded File Integrity Card */}
              {uploadedFile && (
                <div className="p-4 bg-[#0b0f19] border border-slate-800 rounded-xl text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-emerald-400 text-sm">check_circle</span>
                      <span>Document Received & Parsed</span>
                    </span>
                    <span className="font-mono text-[11px] text-slate-400">
                      {(uploadedFile.size / 1024).toFixed(1)} KB
                    </span>
                  </div>

                  {fileSha256 && (
                    <div className="font-mono text-[10px] text-cyan-300/80 break-all bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
                      SHA-256: {fileSha256}
                    </div>
                  )}

                  <div className="pt-2 text-slate-300 text-xs">
                    Target detected: <strong className="text-white">{productName}</strong> ({category})
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Manual Specification Form */}
          {intakeMode === 'manual' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Product Commercial Name / Model
                </label>
                <input
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  className="w-full text-xs bg-[#0b0f19] border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30 transition-colors"
                  placeholder="e.g. ThermoSteel Vacuum Flask 1000ml"
                />
              </div>

              <div>
                <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Product Category
                </label>
                <input
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full text-xs bg-[#0b0f19] border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30 transition-colors"
                  placeholder="e.g. Domestic Vacuum Ware & Food-Contact Containers"
                />
              </div>

              <div>
                <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Target Statutory Standard
                </label>
                <div className="w-full">
                  <GlideSelect
                    options={standardOptions}
                    value={targetStandard}
                    onChange={(val) => setTargetStandard(val)}
                    size="md"
                    menuWidth={280}
                    surfaceColor="#0b0f19"
                    highlightColor="#1e293b"
                    accentColor="#38bdf8"
                    textColor="#f1f5f9"
                    radius={10}
                    className="w-full"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Capacity / Rating
                </label>
                <input
                  type="text"
                  value={capacity}
                  onChange={(e) => setCapacity(e.target.value)}
                  className="w-full text-xs bg-[#0b0f19] border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30 transition-colors"
                  placeholder="e.g. 1000 mL or 5000 W"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Materials & Construction
                </label>
                <input
                  type="text"
                  value={material}
                  onChange={(e) => setMaterial(e.target.value)}
                  className="w-full text-xs bg-[#0b0f19] border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30 transition-colors"
                  placeholder="e.g. Austenitic Stainless Steel 304 (SS 304) for food-contact inner/outer walls"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Technical Description & Insulation Mechanism
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full text-xs bg-[#0b0f19] border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30 transition-colors leading-relaxed"
                  placeholder="Describe dimensions, wall thickness, thermal performance claim, closures, and test parameters..."
                />
              </div>
            </div>
          )}

          {/* TAB 3: Statutory Presets */}
          {intakeMode === 'preset' && (
            <div className="space-y-3">
              <div className="text-xs text-slate-400 mb-2">
                Select an official statutory benchmark to immediately load verified product characteristics and Quality Control Order requirements:
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {presets.map((p) => (
                  <div
                    key={p.id}
                    className="p-4 bg-[#0b0f19] hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/50 rounded-xl transition-all cursor-pointer flex flex-col justify-between group shadow-md"
                    onClick={() => handleApplyPreset(p)}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-1 mb-2">
                        <span className="font-mono text-xs font-bold text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/30">
                          {p.standard}
                        </span>
                        <span className="text-[10px] font-medium text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-500/30">
                          {p.qco.split(' ')[0]}
                        </span>
                      </div>
                      <h4 className="font-space-grotesk font-bold text-white text-xs mb-1 group-hover:text-cyan-200 transition-colors">{p.title}</h4>
                      <p className="text-[11px] text-slate-400 leading-relaxed">{p.desc}</p>
                    </div>

                    <div className="mt-3 pt-2.5 border-t border-slate-800 flex items-center justify-between text-[11px] font-semibold text-cyan-400 group-hover:text-cyan-300">
                      <span>Load Specification</span>
                      <span className="material-symbols-outlined text-[15px] group-hover:translate-x-1 transition-transform">arrow_forward</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compilation Execution Action Bar */}
          <div className="mt-6 pt-5 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-[11px] text-slate-400 leading-relaxed text-center sm:text-left">
              Deterministic evaluation executes: <strong className="text-slate-200">Product DNA &rarr; Applicability &rarr; Requirements &rarr; Evidence &rarr; Gaps &rarr; Actions &rarr; Passport</strong>.
            </div>

            <button
              type="button"
              onClick={handleCompile}
              className="w-full sm:w-auto px-8 py-3.5 bg-gradient-to-r from-cyan-500 via-sky-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 active:scale-[0.99] text-slate-950 font-bold text-xs rounded-xl shadow-[0_0_20px_rgba(56,189,248,0.35)] transition-all flex items-center justify-center gap-2 cursor-pointer shrink-0"
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
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
            Mandatory Statutory Quality Control Orders (QCO)
          </h2>
          <span className="text-[11px] text-slate-500 font-mono">
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
              className="bg-[#0f1422] border border-slate-800 hover:border-slate-700 rounded-xl p-4 shadow-md space-y-2 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-xs font-bold text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/30">
                    {item.standard}
                  </span>
                  <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-500/30">
                    {item.status}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-white mt-2 font-space-grotesk">{item.title}</h4>
                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{item.scope}</p>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                <span className="text-slate-400 font-medium">{item.scheme}</span>
                <button
                  type="button"
                  onClick={() => {
                    setTargetStandard(item.standard);
                    setIntakeMode('manual');
                  }}
                  className="text-cyan-400 hover:text-cyan-300 font-semibold cursor-pointer"
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
      <div className="bg-[#0b0f19] border border-slate-800 rounded-2xl p-5 shadow-lg">
        <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-500 mb-3">
          GOAT Deterministic Regulatory Execution Pipeline
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 text-xs font-sans">
          {[
            { step: '01', title: 'Product DNA', desc: 'Facts & attributes extraction' },
            { step: '02', title: 'Applicability', desc: 'Statutory standard & QCO scoping' },
            { step: '03', title: 'Requirements', desc: 'Clause parameters & limits' },
            { step: '04', title: 'Evidence Matrix', desc: 'Lab test artifacts & SHA-256' },
            { step: '05', title: 'Compliance Gaps', desc: 'Missing tests & deviations' },
            { step: '06', title: 'Lab Actions', desc: 'Testing orders & dispatch' },
            { step: '07', title: 'Passport', desc: 'Cryptographic compliance attestation' },
          ].map((st) => (
            <div key={st.step} className="bg-[#0f1422] p-3 rounded-xl border border-slate-800 hover:border-cyan-500/30 transition-colors">
              <span className="font-mono text-[10px] font-bold text-cyan-400 block">
                {st.step}
              </span>
              <div className="font-space-grotesk font-semibold text-slate-100 mt-1">{st.title}</div>
              <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">{st.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
