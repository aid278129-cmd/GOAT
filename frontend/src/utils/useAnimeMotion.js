import { useEffect, useRef } from 'react';

/**
 * Utility hook to execute Anime.js animations with fallback.
 * Adheres to Stitch engineering motion specifications:
 * - Sub-350ms restrained motions
 * - easeOutQuad or easeOutCubic (no overshoot)
 * - Micro-staggering
 */
export function useAnimeMotion(animateFn, deps = []) {
  const isMounted = useRef(false);

  useEffect(() => {
    isMounted.current = true;
    
    // Check if anime is available globally or via window
    const anime = window.anime || (typeof window !== 'undefined' ? window.anime : null);

    if (anime && typeof animateFn === 'function') {
      try {
        animateFn(anime);
      } catch (err) {
        console.warn('Anime.js motion execution error:', err);
      }
    }

    return () => {
      isMounted.current = false;
    };
  }, deps);
}

/**
 * Standard entrance animation for page containers and elements
 */
export function triggerEntrance(selector = '.animate-entrance', delay = 0) {
  const anime = window.anime || (typeof window !== 'undefined' ? window.anime : null);
  if (!anime) return;

  try {
    anime({
      targets: selector,
      translateY: [6, 0],
      opacity: [0, 1],
      delay: anime.stagger ? anime.stagger(35, { start: delay }) : delay,
      duration: 320,
      easing: 'easeOutQuad'
    });
  } catch (e) {
    // Graceful fallback
  }
}
