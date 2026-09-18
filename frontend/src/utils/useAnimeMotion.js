import { useEffect, useRef } from 'react';
import { animate, stagger } from 'animejs';

/**
 * Utility hook to execute animations with fallback.
 * Adheres to engineering motion specifications:
 * - Sub-350ms restrained motions
 * - easeOutQuad or easeOutCubic (no overshoot)
 * - Micro-staggering
 */
export function useAnimeMotion(animateFn, deps = []) {
  const isMounted = useRef(false);

  useEffect(() => {
    isMounted.current = true;
    if (typeof animateFn === 'function') {
      try {
        animateFn(animate);
      } catch (err) {
        console.warn('Motion execution notice:', err);
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
  if (typeof window === 'undefined' || !document.querySelector(selector)) return;

  try {
    if (typeof animate === 'function') {
      animate(selector, {
        translateY: [6, 0],
        opacity: [0, 1],
        delay: typeof stagger === 'function' ? stagger(35, { start: delay }) : delay,
        duration: 320,
        ease: 'outQuad',
      });
    }
  } catch (e) {
    // Graceful fallback: ensure opacity is 1 if animation fails
    try {
      const els = document.querySelectorAll(selector);
      els.forEach((el) => {
        el.style.opacity = '1';
        el.style.transform = 'none';
      });
    } catch {
      // Ignored
    }
  }
}

