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
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6 max-w-4xl">
      {/* Header */}
      <div className="pb-4 border-b border-[#E2E8F0]">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0F172A]">
          Compliance Settings &amp; Regulatory Profile
        </h1>
        <p className="text-xs sm:text-sm text-[#64748B] mt-0.5">
          Configure statutory legal entity profiles, BIS ManakOnline integration, and DSC certificates.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {/* Section 1: Organization & Statutory Entity */}
        <div className="bg-white border border-[#E2E8F0] rounded-lg p-6 shadow-sm flex flex-col gap-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[#E2E8F0]">
            <span className="material-symbols-outlined text-[#1D4ED8] text-base">corporate_fare</span>
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0F172A] font-mono">
              Organization &amp; Statutory Entity
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                Legal Entity Name
              </label>
              <input
                type="text"
                placeholder="e.g. Acme Technologies India Pvt Ltd"
                value={settings.entityName}
                onChange={(e) => setSettings({ ...settings, entityName: e.target.value })}
                className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                BIS Registration / Portal ID
              </label>
              <input
                type="text"
                placeholder="e.g. R-XXXXXXXX or Application ID"
                value={settings.bisRegNumber}
                onChange={(e) => setSettings({ ...settings, bisRegNumber: e.target.value })}
                className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#0F172A] mb-1">
              Manufacturing Facility Location
            </label>
            <input
              type="text"
              placeholder="e.g. Plot No. 45, Phase II, Electronic City, Bengaluru, Karnataka"
              value={settings.facilityAddress}
              onChange={(e) => setSettings({ ...settings, facilityAddress: e.target.value })}
              className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#0F172A] mb-1">
              Designated Regulatory Engineer
            </label>
            <input
              type="text"
              placeholder="e.g. Enter lead compliance engineer name"
              value={settings.leadEngineer}
              onChange={(e) => setSettings({ ...settings, leadEngineer: e.target.value })}
              className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white"
            />
          </div>
        </div>

        {/* Section 2: ManakOnline Integration */}
        <div className="bg-white border border-[#E2E8F0] rounded-lg p-6 shadow-sm flex flex-col gap-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#1D4ED8] text-base">cloud_sync</span>
              <h2 className="text-xs font-bold uppercase tracking-wider text-[#0F172A] font-mono">
                BIS ManakOnline &amp; CRS Integration
              </h2>
            </div>
            <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              DISCONNECTED
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                Portal Endpoint URL
              </label>
              <input
                type="text"
                value={settings.manakEndpoint}
                onChange={(e) => setSettings({ ...settings, manakEndpoint: e.target.value })}
                className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] font-mono focus:outline-none focus:border-[#1D4ED8] focus:bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                Client ID
              </label>
              <input
                type="text"
                placeholder="Enter client ID"
                value={settings.clientId}
                onChange={(e) => setSettings({ ...settings, clientId: e.target.value })}
                className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white font-mono"
              />
            </div>
          </div>
        </div>

        {/* Section 3: DSC Token Status */}
        <div className="bg-white border border-[#E2E8F0] rounded-lg p-6 shadow-sm flex flex-col gap-3">
          <div className="flex items-center gap-2 pb-3 border-b border-[#E2E8F0]">
            <span className="material-symbols-outlined text-[#1D4ED8] text-base">vpn_key</span>
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0F172A] font-mono">
              Digital Signature Certificate (DSC) for BIS e-Filing
            </h2>
          </div>

          <div className="p-4 bg-[#F8F9FA] border border-[#E2E8F0] rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-slate-200 flex items-center justify-center text-slate-500">
                <span className="material-symbols-outlined text-lg">key_off</span>
              </div>
              <div>
                <span className="text-xs font-semibold text-[#0F172A] block">
                  No DSC Token Connected
                </span>
                <span className="text-[11px] text-[#64748B] block">
                  Connect USB e-Token (Class 3 Signing Certificate) or configure software PKCS#12 key.
                </span>
              </div>
            </div>

            <button
              type="button"
              className="px-3 py-1.5 bg-white border border-[#E2E8F0] hover:bg-slate-50 text-[#0F172A] text-xs font-medium rounded transition-colors"
            >
              Scan Tokens
            </button>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-end gap-3">
          {saved && (
            <span className="text-xs text-emerald-600 font-medium flex items-center gap-1 animate-in fade-in duration-150">
              <span className="material-symbols-outlined text-sm">check_circle</span>
              Settings saved successfully
            </span>
          )}
          <button
            type="submit"
            className="px-5 py-2 text-xs font-semibold text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors shadow-sm"
          >
            Save Regulatory Profile
          </button>
        </div>
      </form>
    </div>
  );
}
