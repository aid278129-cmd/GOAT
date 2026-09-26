import React, { useState } from 'react';
import ThreeCanvas from './ThreeCanvas';
import KnowYourCertificationsCTA from './KnowYourCertificationsCTA';
import KnowYourCertificationsModal from './KnowYourCertificationsModal';

export default function LandingHomeView({ onEnterMainPage }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [paletteIndex, setPaletteIndex] = useState(0);

  // Curated color themes for user to enjoy on title click
  const themes = [
    {
      name: 'Starlight Cyan & Electric Blue',
      titleClass: 'text-title-starlight title-glow-starlight',
      ctaClass: 'text-cta-blue-glow group-hover:text-cta-blue-glow-hover',
      arrowHoverColor: 'text-[#e0f2fe]',
      arrowDefaultColor: 'text-[#38bdf8]',
      boxBorder: 'border-cyan-500/40 hover:border-cyan-300',
    },
    {
      name: 'Solar Molten Gold & Cyan Prism',
      titleClass: 'text-title-solar title-glow-solar',
      ctaClass: 'text-cta-blue-glow group-hover:text-cta-blue-glow-hover',
      arrowHoverColor: 'text-[#fef08a]',
      arrowDefaultColor: 'text-[#f59e0b]',
      boxBorder: 'border-amber-500/40 hover:border-cyan-300',
    },
    {
      name: 'Emerald Cyber & Radiant Blue',
      titleClass: 'text-title-emerald title-glow-emerald',
      ctaClass: 'text-cta-blue-glow group-hover:text-cta-blue-glow-hover',
      arrowHoverColor: 'text-[#bbf7d0]',
      arrowDefaultColor: 'text-[#34d399]',
      boxBorder: 'border-emerald-500/40 hover:border-cyan-300',
    },
  ];

  const currentTheme = themes[paletteIndex];

  const cycleTheme = () => {
    setPaletteIndex((prev) => (prev + 1) % themes.length);
  };

  const handleCtaClick = () => {
    // "after pressing 'Know your certifications' our main page should come"
    if (onEnterMainPage) {
      onEnterMainPage();
    }
  };

  return (
    <main className="relative w-screen h-screen overflow-hidden bg-[#07040a] flex flex-col items-center justify-center select-none text-stone-200">
      {/* 1. Behind That: Dynamic Responsive Three.js 3D Background */}
      <ThreeCanvas />

      {/* Atmospheric Radial Vignette & Warm Depth Gradient */}
      <div
        className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,rgba(7,4,10,0.15)_0%,rgba(7,4,10,0.72)_75%,rgba(7,4,10,0.96)_100%)] z-1"
        aria-hidden="true"
      />

      {/* Radiant Accent Orbs */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-gradient-to-tr from-cyan-600/10 via-purple-700/10 to-amber-500/10 rounded-full blur-[130px] pointer-events-none z-1 animate-flux"
        aria-hidden="true"
      />

      {/* Top Bar with Quick Explore Catalog & Status */}
      <header className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-6 py-4 pointer-events-auto">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 shadow-[0_0_12px_rgba(56,189,248,0.3)]">
            <span className="material-symbols-outlined text-[18px]">verified</span>
          </div>
          <div>
            <span className="font-space-grotesk text-xs font-bold tracking-wider text-white uppercase block">
              ZYNTRIX <span className="text-cyan-400 font-mono text-[10px]">v2.6</span>
            </span>
            <span className="font-footnote text-[10px] text-cyan-300/70 tracking-tight block">
              Statutory BIS Conformity Architecture
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/70 border border-cyan-500/30 hover:border-cyan-400/60 text-cyan-200 text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer shadow-sm"
            title="Browse Indian Standards & QCO Database"
          >
            <span className="material-symbols-outlined text-[15px] text-cyan-400">menu_book</span>
            <span className="hidden sm:inline">Standards Catalog</span>
          </button>

          <button
            type="button"
            onClick={handleCtaClick}
            className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition-all flex items-center gap-1 cursor-pointer shadow-[0_0_14px_rgba(56,189,248,0.4)]"
          >
            <span>Enter Platform</span>
            <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
          </button>
        </div>
      </header>

      {/* 2. Main Center Interface - Strictly User-Specified Content Only */}
      <div className="relative z-10 w-full max-w-4xl px-6 sm:px-10 flex flex-col items-center text-center">
        
        {/* Title: "AI Based BIS Compiler" in modern Unbounded font with new radiant color */}
        <h1
          onClick={cycleTheme}
          className={`font-unbounded text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight cursor-pointer transition-all duration-500 hover:scale-[1.015] active:scale-[0.99] text-balance leading-tight ${currentTheme.titleClass}`}
          title="Click to toggle color tone"
        >
          AI Based BIS Compiler
        </h1>

        {/* Small Footnote from the Indian Law telling about the need for BIS certification in India */}
        <div className="mt-7 sm:mt-9 max-w-2xl px-5 py-4 sm:px-7 sm:py-5 rounded-2xl footnote-glass-box text-stone-300 transition-all duration-500 hover:border-cyan-400/40 hover:shadow-[0_0_35px_rgba(56,189,248,0.15)]">
          <p className="font-footnote text-[11px] sm:text-xs leading-relaxed text-stone-300 sm:text-center text-justify tracking-normal">
            <span className="text-cyan-300 font-bold tracking-wider block sm:inline sm:mr-1.5 uppercase">
              [BIS Act, 2016 · Section 16]:
            </span>
            Under Section 16 of the Bureau of Indian Standards Act, 2016 (No. 11 of 2016), the Central Government mandates compulsory conformity to Indian Standards to safeguard public interest, health, environment, prevention of unfair trade practices, and national security — prohibiting manufacture, import, distribution, or sale without the valid Standard Mark.
          </p>
        </div>

        {/* Interactive 'Know Your Certifications' Call-To-Action Box */}
        <div className="mt-8 sm:mt-12">
          <KnowYourCertificationsCTA
            onClick={handleCtaClick}
            ctaTextClass={currentTheme.ctaClass}
            arrowHoverColor={currentTheme.arrowHoverColor}
            arrowDefaultColor={currentTheme.arrowDefaultColor}
          />
        </div>

        {/* Bottom micro-hint */}
        <p className="mt-4 text-[11px] text-slate-400/80 font-mono flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          Click <span className="text-cyan-300 font-semibold cursor-pointer underline underline-offset-2" onClick={handleCtaClick}>Know Your Certifications</span> to compile compliance or click title to toggle themes.
        </p>

      </div>

      {/* Interactive Certification Intelligence Modal */}
      <KnowYourCertificationsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onEnterPlatform={handleCtaClick}
      />
    </main>
  );
}
