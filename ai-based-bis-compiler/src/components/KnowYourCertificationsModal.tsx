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

interface CertificationStandard {
  code: string;
  title: string;
  category: string;
  scheme: 'Scheme-I (ISI Mark)' | 'Scheme-II (CRS)' | 'Scheme-IV (FMCS)' | 'Hallmarking';
  qcoStatus: 'Mandatory (QCO Active)' | 'Compulsory Notification';
  ministry: string;
  description: string;
}

const BIS_STANDARDS_DATABASE: CertificationStandard[] = [
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
    code: 'IS 16102 (Part 1 & 2)',
    title: 'Self-Ballasted LED Lamps for General Lighting Services',
    category: 'Electrical & Illumination',
    scheme: 'Scheme-II (CRS)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'MeitY / Ministry of Power',
    description: 'Ensures luminous efficacy, electrical insulation, surge immunity, and thermal heat sink performance for retail LED lighting.',
  },
  {
    code: 'IS 1417:2016',
    title: 'Gold and Gold Alloys, Jewellery & Artefacts',
    category: 'Precious Metals & Hallmarking',
    scheme: 'Hallmarking',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'BIS Central Hallmarking Directorate',
    description: 'Mandatory 6-digit alphanumeric HUID (Hallmark Unique Identification) stamped at BIS-recognized Assaying & Hallmarking Centres (AHC).',
  },
  {
    code: 'IS 1293:2019',
    title: 'Plugs and Socket-Outlets of Rated Voltage up to 250V',
    category: 'Electrical Accessories',
    scheme: 'Scheme-I (ISI Mark)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'DPIIT / BIS',
    description: 'Prevents electrical fires, arcing hazards, and ensures child-safety shutter specifications for domestic wall receptacles.',
  },
  {
    code: 'IS 269:2015',
    title: 'Ordinary Portland Cement (33, 43, and 53 Grade)',
    category: 'Civil Materials & Concrete',
    scheme: 'Scheme-I (ISI Mark)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'Ministry of Commerce & Industry',
    description: 'Mandatory testing for compressive strength, fineness, soundness, and setting time before distribution in domestic trade.',
  },
  {
    code: 'IS 616:2017',
    title: 'Audio, Video and Similar Electronic Apparatus - Safety',
    category: 'Consumer Electronics & IT',
    scheme: 'Scheme-II (CRS)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'MeitY (Electronics & IT)',
    description: 'Safety requirements for Smart TVs, wireless display panels, amplifiers, and home theater equipment.',
  },
  {
    code: 'IS 16242:2014',
    title: 'Uninterruptible Power Systems (UPS) / Inverters',
    category: 'Energy Storage & Power',
    scheme: 'Scheme-II (CRS)',
    qcoStatus: 'Mandatory (QCO Active)',
    ministry: 'MeitY (Electronics & IT)',
    description: 'Safety compliance for home/commercial inverters, static UPS systems, and smart solar micro-inverter equipment.',
  },
];

interface KnowYourCertificationsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function KnowYourCertificationsModal({
  isOpen,
  onClose,
}: KnowYourCertificationsModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedScheme, setSelectedScheme] = useState<string>('All');

  if (!isOpen) return null;

  const schemes = [
    'All',
    'Scheme-I (ISI Mark)',
    'Scheme-II (CRS)',
    'Scheme-IV (FMCS)',
    'Hallmarking',
  ];

  const filteredStandards = BIS_STANDARDS_DATABASE.filter((std) => {
    const matchesSearch =
      std.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      std.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      std.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      std.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesScheme =
      selectedScheme === 'All' || std.scheme === selectedScheme;

    return matchesSearch && matchesScheme;
  });

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 overflow-y-auto bg-black/85 backdrop-blur-2xl transition-all duration-300 animate-in fade-in"
    >
      <div className="relative w-full max-w-5xl max-h-[90vh] flex flex-col rounded-2xl bg-[#091122] border border-amber-500/30 shadow-[0_0_80px_rgba(0,0,0,0.85)] overflow-hidden text-slate-100 font-cta">
        
        {/* Top Header Strip */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-amber-500/20 bg-[#0d1830]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold font-title tracking-tight text-white">
                  Know Your Certifications
                </h2>
                <span className="text-[11px] font-mono-code px-2.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 tracking-wider">
                  BIS ACT 2016 COMPILER
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 font-cta">
                Statutory Conformity Assessment & Compulsory Indian Standards (IS Codes)
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-amber-200/60 hover:text-white hover:bg-amber-500/10 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-400/50 cursor-pointer"
            aria-label="Close dialog"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          
          {/* Legal Statutory Notice Banner */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/15 via-[#1a0c28] to-emerald-500/15 border border-amber-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <Scale className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-amber-200 font-display">
                  Section 16 Statutory Mandate & Enforcement
                </h3>
                <p className="text-xs text-stone-300 mt-0.5 leading-relaxed font-body">
                  Products notified under Quality Control Orders (QCOs) by Central Ministries must bear the valid Standard Mark. Non-compliant commercialization attracts penal action under Section 29 of the BIS Act.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs font-footnote text-emerald-300 shrink-0 bg-emerald-950/40 px-3 py-1.5 rounded-lg border border-emerald-500/30">
              <span>Section 16 / 29 Enforcement</span>
            </div>
          </div>

          {/* Scheme Badges Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-[#140a20] border border-amber-500/20 hover:border-amber-400/50 transition-all">
              <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold uppercase tracking-wider mb-1 font-display">
                <Award className="w-4 h-4" />
                <span>Scheme-I (ISI Mark)</span>
              </div>
              <p className="text-xs text-stone-400 leading-normal font-body">
                Product certification with initial factory audit, quality surveillance, and on-site testing for 450+ goods.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#140a20] border border-emerald-500/20 hover:border-emerald-400/50 transition-all">
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-1 font-display">
                <Cpu className="w-4 h-4" />
                <span>Scheme-II (CRS)</span>
              </div>
              <p className="text-xs text-stone-400 leading-normal font-body">
                Compulsory Registration Scheme for electronics, smart devices, power supplies & IT equipment under MeitY.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#140a20] border border-purple-500/20 hover:border-purple-400/50 transition-all">
              <div className="flex items-center gap-2 text-purple-300 text-xs font-semibold uppercase tracking-wider mb-1 font-display">
                <Globe2 className="w-4 h-4" />
                <span>Scheme-IV (FMCS)</span>
              </div>
              <p className="text-xs text-stone-400 leading-normal font-body">
                Foreign Manufacturers Certification Scheme granting standard mark licenses to offshore manufacturing hubs.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#140a20] border border-amber-300/20 hover:border-amber-300/50 transition-all">
              <div className="flex items-center gap-2 text-amber-300 text-xs font-semibold uppercase tracking-wider mb-1 font-display">
                <Sparkles className="w-4 h-4" />
                <span>Hallmarking (HUID)</span>
              </div>
              <p className="text-xs text-stone-400 leading-normal font-body">
                Mandatory 6-character alphanumeric tracing for precious gold and silver jewelry articles across India.
              </p>
            </div>
          </div>

          {/* Interactive Search & Filter Bar */}
          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-amber-400/60 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by IS Code, product keyword (e.g., Laptop, Battery, Toys, Helmet, Steel)..."
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#13091e] border border-amber-500/25 text-sm text-white placeholder-stone-500 focus:outline-none focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400 transition-all font-body"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-stone-400 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Scheme Filter Buttons */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
              {schemes.map((scheme) => (
                <button
                  key={scheme}
                  onClick={() => setSelectedScheme(scheme)}
                  className={`px-3 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-all cursor-pointer ${
                    selectedScheme === scheme
                      ? 'bg-amber-500 text-stone-950 font-bold shadow-lg shadow-amber-500/25'
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
                className="p-4 rounded-xl bg-[#13081e]/80 border border-amber-500/20 hover:border-emerald-400/40 transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="text-xs font-footnote font-semibold text-amber-300 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
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

                  <h4 className="text-sm font-semibold text-white group-hover:text-amber-200 transition-colors font-body">
                    {std.title}
                  </h4>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed font-cta">
                    {std.description}
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400 font-mono-code">
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
          <div className="p-4 rounded-xl bg-[#060c1c] border border-amber-500/20 text-xs text-slate-300 space-y-1.5 font-editorial">
            <div className="flex items-center gap-2 text-amber-300 font-semibold text-xs font-mono-code not-italic">
              <Scale className="w-4 h-4" />
              <span>THE BUREAU OF INDIAN STANDARDS ACT, 2016 (NO. 11 OF 2016)</span>
            </div>
            <p className="leading-relaxed text-[12px] text-slate-200 italic">
              "16. (1) If the Central Government is of the opinion that it is necessary or expedient so to do in the public interest or for the protection of human, animal or plant health, safety of the environment, or prevention of unfair trade practices, or national security, that any goods, article, process, system or service of any scheduled industry shall conform to an Indian Standard, it may, by order, published in the Official Gazette, direct that conformity of such goods, article, process, system or service to the Indian Standard shall be compulsory."
            </p>
          </div>
        </div>

        {/* Modal Bottom Bar */}
        <div className="px-6 py-4 border-t border-amber-500/20 bg-[#0d1830] flex items-center justify-between text-xs text-slate-400 font-cta">
          <span>AI-Powered BIS Conformity Intelligence</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold transition-all flex items-center gap-1.5 cursor-pointer font-cta"
          >
            <span>Return to Homepage</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
