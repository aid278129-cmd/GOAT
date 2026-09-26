import React, { useState, useRef } from 'react';

interface KnowYourCertificationsCTAProps {
  onClick: () => void;
  ctaTextClass?: string;
  arrowHoverColor?: string;
  arrowDefaultColor?: string;
}

export default function KnowYourCertificationsCTA({
  onClick,
  ctaTextClass = 'text-cta-blue-glow group-hover:text-cta-blue-glow-hover',
  arrowHoverColor = 'text-[#e0f2fe]',
  arrowDefaultColor = 'text-[#38bdf8]',
}: KnowYourCertificationsCTAProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [tilt, setTilt] = useState({ rotateX: 0, rotateY: 0 });
  const boxRef = useRef<HTMLButtonElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
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
      {/* 1. Outer Holographic Ambient Back-Glow (Reactive to Hover) in Radiant Cyan-Blue */}
      <div
        className={`absolute -inset-2 rounded-3xl bg-gradient-to-r from-cyan-500/30 via-sky-500/40 to-indigo-500/30 blur-xl transition-all duration-700 pointer-events-none ${
          isHovered
            ? 'opacity-100 scale-105 blur-2xl'
            : 'opacity-40 scale-95 blur-lg'
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
            isHovered ? 1.03 : 1
          }, ${isHovered ? 1.03 : 1}, 1)`,
          transition: isHovered
            ? 'transform 0.1s ease-out, box-shadow 0.3s ease'
            : 'transform 0.5s ease-out, box-shadow 0.5s ease',
        }}
        className="relative z-10 inline-flex items-center justify-between gap-6 sm:gap-8 px-8 py-5 sm:px-12 sm:py-6 rounded-2xl cursor-pointer overflow-hidden focus:outline-none focus:ring-2 focus:ring-cyan-400/70 active:scale-[0.98]"
        aria-label="Know Your Certifications"
      >
        {/* Layer A: Rotating Conic Laser Border Effect in Cyan & Starlight Blue */}
        <div
          className="absolute -inset-[200%] animate-[spin_6s_linear_infinite] opacity-60 group-hover:opacity-100 transition-opacity pointer-events-none"
          style={{
            background:
              'conic-gradient(from 0deg at 50% 50%, transparent 0deg, #38bdf8 60deg, transparent 120deg, #60a5fa 180deg, transparent 240deg, #818cf8 300deg, transparent 360deg)',
          }}
          aria-hidden="true"
        />

        {/* Layer B: Dark Crystalline Obsidian Core Base */}
        <div
          className="absolute inset-[1.5px] rounded-[15px] bg-[#090b16]/92 backdrop-blur-2xl transition-colors duration-300 group-hover:bg-[#0c1020]/90 pointer-events-none"
          aria-hidden="true"
        />

        {/* Layer C: Interactive Dynamic Spotlight that tracks cursor inside the box */}
        <div
          className="absolute inset-0 pointer-events-none rounded-[15px] transition-opacity duration-300"
          style={{
            background: `radial-gradient(280px circle at ${mousePos.x}px ${mousePos.y}px, rgba(56, 189, 248, 0.25), rgba(96, 165, 250, 0.12) 40%, transparent 80%)`,
            opacity: isHovered ? 1 : 0,
          }}
          aria-hidden="true"
        />

        {/* Layer D: Horizontal Security Laser Scanner Line Sweep in Electric Blue */}
        <div
          className={`absolute inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent pointer-events-none transition-opacity duration-500 ${
            isHovered ? 'opacity-90 animate-scanline' : 'opacity-0'
          }`}
          aria-hidden="true"
        />

        {/* Layer E: Micro Fine Cyber Grid Pattern */}
        <div
          className="absolute inset-0 opacity-[0.08] group-hover:opacity-[0.16] transition-opacity pointer-events-none rounded-[15px]"
          style={{
            backgroundImage: `linear-gradient(to right, #38bdf8 1px, transparent 1px), linear-gradient(to bottom, #38bdf8 1px, transparent 1px)`,
            backgroundSize: '16px 16px',
          }}
          aria-hidden="true"
        />

        {/* Layer F: Precision Corner Reticles / Tactical Brackets (┌ ┐ └ ┘) in Cyan */}
        <div className="absolute top-2 left-2 w-2.5 h-2.5 border-t-2 border-l-2 border-cyan-400/60 group-hover:border-cyan-300 group-hover:scale-110 transition-all pointer-events-none" />
        <div className="absolute top-2 right-2 w-2.5 h-2.5 border-t-2 border-r-2 border-cyan-400/60 group-hover:border-cyan-300 group-hover:scale-110 transition-all pointer-events-none" />
        <div className="absolute bottom-2 left-2 w-2.5 h-2.5 border-b-2 border-l-2 border-cyan-400/60 group-hover:border-cyan-300 group-hover:scale-110 transition-all pointer-events-none" />
        <div className="absolute bottom-2 right-2 w-2.5 h-2.5 border-b-2 border-r-2 border-cyan-400/60 group-hover:border-cyan-300 group-hover:scale-110 transition-all pointer-events-none" />

        {/* Left Side Status Diode Indicator in Blue/Cyan */}
        <div className="relative z-20 flex items-center gap-3">
          <div className="relative flex items-center justify-center w-2.5 h-2.5">
            <span
              className={`absolute inline-flex h-full w-full rounded-full transition-colors duration-300 ${
                isHovered
                  ? 'bg-cyan-300 animate-ping opacity-75'
                  : 'bg-cyan-400/60'
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-1.5 w-1.5 transition-colors duration-300 ${
                isHovered ? 'bg-white shadow-[0_0_10px_#38bdf8]' : 'bg-cyan-400'
              }`}
            />
          </div>

          {/* Option Text: "Know Your Certifications" in Space Grotesk with the signature blue */}
          <span
            className={`font-space-grotesk font-extrabold text-base sm:text-xl tracking-wider uppercase transition-all duration-300 ${ctaTextClass}`}
          >
            Know Your Certifications
          </span>
        </div>

        {/* Right Side: Kinetic Articulated Arrow (->) */}
        <div className="relative z-20 flex items-center pl-2">
          {/* Animated trailing chevrons on hover */}
          <div
            className={`flex items-center -space-x-1.5 transition-all duration-300 mr-1 ${
              isHovered
                ? 'opacity-100 translate-x-0'
                : 'opacity-0 -translate-x-2 pointer-events-none'
            }`}
          >
            <span className="font-footnote text-xs text-cyan-400/50 animate-pulse">&gt;</span>
            <span className="font-footnote text-xs text-cyan-300/80 animate-pulse delay-75">&gt;</span>
          </div>

          {/* Kinetic Prominent Arrow glyph with energy glow */}
          <span
            className={`font-footnote font-extrabold text-xl sm:text-2xl transition-all duration-300 ease-out flex items-center ${
              isHovered
                ? `translate-x-2 scale-110 ${arrowHoverColor} drop-shadow-[0_0_16px_rgba(56,189,248,1)]`
                : `${arrowDefaultColor} drop-shadow-[0_0_8px_rgba(56,189,248,0.7)]`
            }`}
            aria-hidden="true"
          >
            -&gt;
          </span>
        </div>
      </button>
    </div>
  );
}
