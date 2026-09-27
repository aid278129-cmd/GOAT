import React, { useState } from 'react';

export function SettingsView({ onSaveNotification }) {
  const [settings, setSettings] = useState({
    entityName: '',
    bisRegNumber: '',
    facilityAddress: '',
    leadEngineer: '',
    manakEndpoint: 'https://manakonline.in/crs/api/v2',
    clientId: '',
    clientSecret: '',
  });

  const [saved, setSaved] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
    if (onSaveNotification) onSaveNotification('Settings saved successfully');
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6 font-sans text-slate-100">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider block mb-1">
          System Configuration
        </span>
        <h1 className="font-space-grotesk text-2xl sm:text-3xl font-bold tracking-tight text-white">
          Compliance Settings &amp; Regulatory Profile
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Configure statutory legal entity profiles, BIS ManakOnline integration, and DSC certificates.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {/* Section 1: Organization & Statutory Entity */}
        <div className="bg-[#0f1422] border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <span className="material-symbols-outlined text-cyan-400 text-lg">corporate_fare</span>
            <h2 className="text-xs font-bold uppercase tracking-wider text-white font-mono">
              Organization &amp; Statutory Entity
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono font-semibold text-slate-300 mb-1.5">
                Legal Entity Name
              </label>
              <input
                type="text"
                placeholder="e.g. Acme Technologies India Pvt Ltd"
                value={settings.entityName}
                onChange={(e) => setSettings({ ...settings, entityName: e.target.value })}
                className="w-full px-3.5 py-2.5 text-xs bg-[#080c14] border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
              />
            </div>

            <div>
              <label className="block text-xs font-mono font-semibold text-slate-300 mb-1.5">
                BIS Registration / Portal ID
              </label>
              <input
                type="text"
                placeholder="e.g. R-XXXXXXXX or Application ID"
                value={settings.bisRegNumber}
                onChange={(e) => setSettings({ ...settings, bisRegNumber: e.target.value })}
                className="w-full px-3.5 py-2.5 text-xs bg-[#080c14] border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono font-semibold text-slate-300 mb-1.5">
              Manufacturing Facility Location
            </label>
            <input
              type="text"
              placeholder="e.g. Plot No. 45, Phase II, Electronic City, Bengaluru, Karnataka"
              value={settings.facilityAddress}
              onChange={(e) => setSettings({ ...settings, facilityAddress: e.target.value })}
              className="w-full px-3.5 py-2.5 text-xs bg-[#080c14] border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
            />
          </div>

          <div>
            <label className="block text-xs font-mono font-semibold text-slate-300 mb-1.5">
              Designated Regulatory Engineer
            </label>
            <input
              type="text"
              placeholder="e.g. Enter lead compliance engineer name"
              value={settings.leadEngineer}
              onChange={(e) => setSettings({ ...settings, leadEngineer: e.target.value })}
              className="w-full px-3.5 py-2.5 text-xs bg-[#080c14] border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
            />
          </div>
        </div>

        {/* Section 2: ManakOnline Integration */}
        <div className="bg-[#0f1422] border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-cyan-400 text-lg">cloud_sync</span>
              <h2 className="text-xs font-bold uppercase tracking-wider text-white font-mono">
                BIS ManakOnline &amp; CRS Integration
              </h2>
            </div>
            <span className="font-mono text-[10px] text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-500/30">
              DISCONNECTED
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono font-semibold text-slate-300 mb-1.5">
                Portal Endpoint URL
              </label>
              <input
                type="text"
                value={settings.manakEndpoint}
                onChange={(e) => setSettings({ ...settings, manakEndpoint: e.target.value })}
                className="w-full px-3.5 py-2.5 text-xs bg-[#080c14] border border-slate-700/80 rounded-xl text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>

            <div>
              <label className="block text-xs font-mono font-semibold text-slate-300 mb-1.5">
                Client ID
              </label>
              <input
                type="text"
                placeholder="Enter client ID"
                value={settings.clientId}
                onChange={(e) => setSettings({ ...settings, clientId: e.target.value })}
                className="w-full px-3.5 py-2.5 text-xs bg-[#080c14] border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Section 3: DSC Token Status */}
        <div className="bg-[#0f1422] border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-3">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <span className="material-symbols-outlined text-cyan-400 text-lg">vpn_key</span>
            <h2 className="text-xs font-bold uppercase tracking-wider text-white font-mono">
              Digital Signature Certificate (DSC) for BIS e-Filing
            </h2>
          </div>

          <div className="p-4 bg-[#0b0f19] border border-slate-800 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400">
                <span className="material-symbols-outlined text-xl">key_off</span>
              </div>
              <div>
                <span className="text-xs font-semibold text-white block">
                  No DSC Token Connected
                </span>
                <span className="text-[11px] text-slate-400 block mt-0.5">
                  Connect USB e-Token (Class 3 Signing Certificate) or configure software PKCS#12 key.
                </span>
              </div>
            </div>

            <button
              type="button"
              className="px-3.5 py-2 bg-[#080c14] border border-slate-700 hover:border-cyan-500/40 text-cyan-300 text-xs font-mono rounded-xl transition-colors cursor-pointer"
            >
              Scan Tokens
            </button>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-end gap-3 pt-2">
          {saved && (
            <span className="text-xs text-emerald-400 font-mono font-medium flex items-center gap-1.5 animate-in fade-in duration-150">
              <span className="material-symbols-outlined text-sm">check_circle</span>
              Settings saved successfully
            </span>
          )}
          <button
            type="submit"
            className="px-6 py-3 text-xs font-bold text-slate-950 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 rounded-xl transition-all shadow-[0_0_15px_rgba(56,189,248,0.3)] cursor-pointer"
          >
            Save Regulatory Profile
          </button>
        </div>
      </form>
    </div>
  );
}
