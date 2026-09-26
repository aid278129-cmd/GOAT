import React, { useState } from 'react';
import {
  X,
  Search,
  ShieldCheck,
  Award,
  Cpu,
  Globe2,
  FileCheck2,
  Scale,
  Sparkles,
  ArrowRight,
} from 'lucide-react';

const BIS_STANDARDS_DATABASE = [
  {
    code: 'IS 13252 (Part 1):2010',
    title: 'Information Technology Equipment - Safety',
    category: 'Consumer Electronics & IT',
    scheme: 'Scheme-II (CRS)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'MeitY (Electronics & IT)',
    description: 'Mandatory for laptops, tablets, scanners, printers, and network adapters imported or sold in India.',
  },
  {
    code: 'IS 16046 (Part 2):2018',
    title: 'Lithium-ion Secondary Cells & Battery Systems',
    category: 'Energy Storage & Power',
    scheme: 'Scheme-II (CRS)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'MeitY (Electronics & IT)',
    description: 'Mandatory safety conformity for portable consumer power banks, phone battery packs, and EV secondary lithium modules.',
  },
  {
    code: 'IS 9873 (Part 1-9)',
    title: 'Safety Requirements for Children Toys',
    category: 'Toys & Infant Safety',
    scheme: 'Scheme-I (ISI Mark)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'DPIIT (Ministry of Commerce & Industry)',
    description: 'Covers mechanical, flammability, migration of toxic elements, and phthalate requirements. Uncertified toy import is banned at Indian customs.',
  },
  {
    code: 'IS 4151:2015',
    title: 'Protective Helmets for Two-Wheeler Riders',
    category: 'Automotive & Personal Protection',
    scheme: 'Scheme-I (ISI Mark)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'MoRTH (Road Transport & Highways)',
    description: 'Rigorous impact absorption, retention, and penetration standards. Mandatory ISI mark required for commercial sale across all Indian states.',
  },
  {
    code: 'IS 14543:2004',
    title: 'Packaged Drinking Water (Other Than Natural Mineral Water)',
    category: 'Food, Beverage & Consumables',
    scheme: 'Scheme-I (ISI Mark)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'FSSAI / Ministry of Consumer Affairs',
    description: 'Compulsory licensing scheme with mandatory laboratory bacteriological validation before any manufacturing or bottling can begin.',
  },
  {
    code: 'IS 1786:2008',
    title: 'High Strength Deformed Steel Bars (TMT Rebars)',
    category: 'Heavy Infrastructure & Metallurgy',
    scheme: 'Scheme-I (ISI Mark)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'Ministry of Steel',
    description: 'Quality control order ensures structural integrity, chemical yield strength, and seismic resistance in national construction.',
  },
  {
    code: 'IS 17526:2021',
    title: 'Stainless Steel Vacuum Flasks and Insulated Containers',
    category: 'Domestic Consumer Hardware',
    scheme: 'Scheme-I (ISI Mark)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'DPIIT / Consumer Affairs',
    description: 'Strict statutory compliance covering thermal insulation performance, leak testing, drop impact resistance, and food-grade stainless steel metallurgy.',
  },
  {
    code: 'IS 1417:2016',
    title: 'Gold and Gold Alloys, Jewellery/Artefacts - Fineness & Marking',
    category: 'Precious Metals & Hallmarking',
    scheme: 'Hallmarking',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'Ministry of Consumer Affairs',
    description: 'Mandates 6-digit alphanumeric Hallmark Unique Identification (HUID) laser-engraved onto all 14k, 18k, 20k, 22k, 23k, and 24k gold jewelry sold in India.',
  },
  {
    code: 'IS 302 (Part 2/Sec 3):2007',
    title: 'Safety of Household Electrical Appliances - Electric Irons',
    category: 'Electrical & White Goods',
    scheme: 'Scheme-I (ISI Mark)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'DPIIT (Ministry of Commerce & Industry)',
    description: 'Comprehensive insulation resistance, earth continuity, high-voltage flash test, and fire hazard prevention for all domestic pressing irons.',
  },
];

export default function KnowYourCertificationsModal({ isOpen, onClose, onEnterPlatform }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedScheme, setSelectedScheme] = useState('ALL');

  if (!isOpen) return null;

  const filteredStandards = BIS_STANDARDS_DATABASE.filter((item) => {
    const matchesSearch =
      item.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.ministry.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesScheme =
      selectedScheme === 'ALL' || item.scheme.toLowerCase().includes(selectedScheme.toLowerCase());

    return matchesSearch && matchesScheme;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
      <div
        className="relative w-full max-w-4xl max-h-[90vh] bg-[#0c0614] border border-cyan-500/30 rounded-2xl shadow-[0_0_60px_rgba(56,189,248,0.25)] flex flex-col overflow-hidden text-stone-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Top Header */}
        <div className="px-6 py-4 border-b border-cyan-500/20 bg-[#12091f]/90 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-space-grotesk text-base sm:text-lg font-bold text-white tracking-wide">
                Mandatory Indian BIS Certifications Catalog
              </h3>
              <p className="text-xs text-cyan-300/80 font-footnote">
                Statutory Quality Control Orders (QCO) & BIS Act 2016 Conformity
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-stone-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
          {/* Search Bar & Scheme Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-cyan-400/70" />
              <input
                type="text"
                placeholder="Search standard code (IS 17526, IS 16046), product, ministry..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#140822] border border-cyan-500/25 focus:border-cyan-400 text-xs sm:text-sm text-white placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
              />
            </div>
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
              {['ALL', 'Scheme-I', 'Scheme-II', 'Hallmarking'].map((scheme) => (
                <button
                  key={scheme}
                  onClick={() => setSelectedScheme(scheme)}
                  className={`px-3 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-all cursor-pointer ${
                    selectedScheme === scheme
                      ? 'bg-cyan-500 text-stone-950 font-bold shadow-lg shadow-cyan-500/25'
                      : 'bg-[#150a22] text-stone-400 hover:text-white hover:bg-[#1f1032]'
                  }`}
                >
                  {scheme}
                </button>
              ))}
            </div>
          </div>

          {/* Standards Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {filteredStandards.map((std) => (
              <div
                key={std.code}
                className="p-4 rounded-xl bg-[#13081e]/80 border border-cyan-500/20 hover:border-emerald-400/40 transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="text-xs font-mono font-semibold text-cyan-300 px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
                      {std.code}
                    </span>
                    <span
                      className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                        std.scheme === 'Scheme-II (CRS)'
                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                          : std.scheme === 'Hallmarking'
                          ? 'bg-amber-400/10 text-amber-300 border-amber-400/30'
                          : 'bg-purple-500/10 text-purple-300 border-purple-500/30'
                      }`}
                    >
                      {std.scheme}
                    </span>
                  </div>

                  <h4 className="text-sm font-semibold text-white group-hover:text-cyan-200 transition-colors">
                    {std.title}
                  </h4>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                    {std.description}
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                  <span>{std.ministry}</span>
                  <span className="text-emerald-400 font-medium flex items-center gap-1">
                    <FileCheck2 className="w-3.5 h-3.5" />
                    {std.qcoStatus}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Legal Citation Footnote in Modal */}
          <div className="p-4 rounded-xl bg-[#060c1c] border border-cyan-500/20 text-xs text-slate-300 space-y-1.5">
            <div className="flex items-center gap-2 text-cyan-300 font-semibold text-xs font-mono not-italic">
              <Scale className="w-4 h-4" />
              <span>THE BUREAU OF INDIAN STANDARDS ACT, 2016 (NO. 11 OF 2016)</span>
            </div>
            <p className="leading-relaxed text-[12px] text-slate-200 italic">
              "16. (1) If the Central Government is of the opinion that it is necessary or expedient so to do in the public interest or for the protection of human, animal or plant health, safety of the environment, or prevention of unfair trade practices, or national security, that any goods, article, process, system or service of any scheduled industry shall conform to an Indian Standard, it may, by order, published in the Official Gazette, direct that conformity of such goods, article, process, system or service to the Indian Standard shall be compulsory."
            </p>
          </div>
        </div>

        {/* Modal Bottom Bar */}
        <div className="px-6 py-4 border-t border-cyan-500/20 bg-[#0d1830] flex items-center justify-between text-xs text-slate-400">
          <span>AI-Powered BIS Conformity Intelligence</span>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium transition-all cursor-pointer"
            >
              Close
            </button>
            {onEnterPlatform && (
              <button
                onClick={onEnterPlatform}
                className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <span>Launch Main Platform</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
