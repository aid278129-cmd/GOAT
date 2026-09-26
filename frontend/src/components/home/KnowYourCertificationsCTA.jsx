import React, { useState, useRef } from 'react';

export default function KnowYourCertificationsCTA({
  onClick,
  ctaTextClass = 'text-cta-blue-glow group-hover:text-cta-blue-glow-hover',
  arrowHoverColor = 'text-[#e0f2fe]',
  arrowDefaultColor = 'text-[#38bdf8]',
}) {
  const [isHovered, setIsHovered] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [tilt, setTilt] = useState({ rotateX: 0, rotateY: 0 });
  const boxRef = useRef(null);

  const handleMouseMove = (e) => {
    if (!boxRef.current) return;
    const rect = boxRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setMousePos({ x, y });

    // Calculate 3D tilt angles based on mouse position relative to center
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateY = ((x - centerX) / centerX) * 8; // max 8 deg
    const rotateX = -((y - centerY) / centerY) * 8; // max 8 deg
    setTilt({ rotateX, rotateY });
  };

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    setTilt({ rotateX: 0, rotateY: 0 });
  };

  return (
    <div className="relative group p-1 select-none">
      {/* 1. Subtle, refined ambient back-glow */}
      <div
        className={`absolute -inset-1 rounded-3xl bg-gradient-to-r from-cyan-500/15 via-blue-500/15 to-indigo-500/15 blur-lg transition-all duration-500 pointer-events-none ${
          isHovered ? 'opacity-70 scale-100' : 'opacity-25 scale-95'
        }`}
        aria-hidden="true"
      />

      {/* 2. Interactive 3D Kinetic Button Container */}
      <button
        ref={boxRef}
        onClick={onClick}
        onMouseMove={handleMouseMove}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        style={{
          transform: `perspective(1000px) rotateX(${tilt.rotateX}deg) rotateY(${tilt.rotateY}deg) scale3d(${
            isHovered ? 1.02 : 1
          }, ${isHovered ? 1.02 : 1}, 1)`,
          transition: isHovered
            ? 'transform 0.1s ease-out, box-shadow 0.3s ease'
            : 'transform 0.5s ease-out, box-shadow 0.5s ease',
        }}
        className="relative z-10 inline-flex items-center justify-between gap-6 sm:gap-8 px-8 py-5 sm:px-12 sm:py-6 rounded-2xl cursor-pointer overflow-hidden focus:outline-none focus:ring-1 focus:ring-cyan-400/50 active:scale-[0.99] border border-cyan-500/25 hover:border-cyan-400/50 transition-colors shadow-[0_8px_30px_rgba(0,0,0,0.6)]"
        aria-label="Know Your Certifications"
      >
        {/* Layer A: Subtle Luminous Border Beam Accent */}
        <div
          className="absolute -inset-[150%] animate-[spin_10s_linear_infinite] opacity-30 group-hover:opacity-60 transition-opacity pointer-events-none"
          style={{
            background:
              'conic-gradient(from 0deg at 50% 50%, transparent 0deg, rgba(56,189,248,0.4) 60deg, transparent 120deg, rgba(96,165,250,0.3) 180deg, transparent 240deg, rgba(129,140,248,0.3) 300deg, transparent 360deg)',
          }}
          aria-hidden="true"
        />

        {/* Layer B: Solid Obsidian Core Base - Prevents harsh backlight bleed */}
        <div
          className="absolute inset-[1px] rounded-[15px] bg-[#070913] transition-colors duration-300 group-hover:bg-[#0a0d1a] pointer-events-none"
          aria-hidden="true"
        />

        {/* Layer C: Gentle Interactive Cursor Spotlight */}
        <div
          className="absolute inset-0 pointer-events-none rounded-[15px] transition-opacity duration-300"
          style={{
            background: `radial-gradient(220px circle at ${mousePos.x}px ${mousePos.y}px, rgba(56, 189, 248, 0.08), transparent 70%)`,
            opacity: isHovered ? 1 : 0,
          }}
          aria-hidden="true"
        />

        {/* Layer D: Ultra-Fine Precision Grid Overlay */}
        <div
          className="absolute inset-0 opacity-[0.07] pointer-events-none rounded-[15px]"
          style={{
            backgroundImage:
              'linear-gradient(to right, rgba(56, 189, 248, 0.4) 1px, transparent 1px), linear-gradient(to bottom, rgba(56, 189, 248, 0.4) 1px, transparent 1px)',
            backgroundSize: '14px 14px',
          }}
          aria-hidden="true"
        />

        {/* Layer E: Content Pill & Headings */}
        <div className="relative flex items-center gap-3 z-10">
          <div className="flex flex-col items-start text-left">
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-block w-2 h-2 rounded-full bg-cyan-400" />
              <span className="font-footnote text-[10px] tracking-widest text-cyan-400/90 uppercase font-semibold">
                STATUTORY ENGINE
              </span>
            </div>

            {/* Main Label: Crisp, high-contrast readable styling */}
            <span
              className={`font-space-grotesk text-xl sm:text-2xl md:text-3xl font-bold tracking-tight transition-all duration-300 ${ctaTextClass}`}
            >
              Know Your Certifications
            </span>

            {/* Sub-label */}
            <span className="font-footnote text-[11px] text-slate-400 font-mono tracking-tight mt-0.5">
              Enter Platform • Deterministic Standards & QCO Compiler
            </span>
          </div>
        </div>

        {/* Layer F: Interactive Arrow Indicator without blinding bloom */}
        <div className="relative z-10 flex items-center justify-center w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-[#0e1424] border border-cyan-500/30 group-hover:border-cyan-400/70 group-hover:bg-[#121b30] transition-all duration-300 shadow-sm">
          <svg
            className={`w-6 h-6 sm:w-7 sm:h-7 transition-all duration-300 transform group-hover:translate-x-1 ${
              isHovered ? arrowHoverColor : arrowDefaultColor
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </div>
      </button>
    </div>
  );
}
