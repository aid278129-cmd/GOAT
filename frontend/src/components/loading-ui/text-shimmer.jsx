import React, { useMemo } from 'react';

/**
 * TextShimmer
 * 
 * Based on @loading-ui/text-shimmer (Thinking.md)
 * Sweeps a subtle, high-polish highlight across a line of text.
 * Perfect for AI thinking states, generative summaries, and scanning labels.
 */
export function TextShimmer({
  children,
  as: Component = 'p',
  className = '',
  duration = 2,
  spread = 2,
  baseColor,
  shimmerColor,
  style = {},
}) {
  const textContent = typeof children === 'string' ? children : String(children ?? '');

  const dynamicSpread = useMemo(() => {
    return (textContent.length || 10) * spread;
  }, [textContent, spread]);

  const effectiveBaseColor = baseColor ?? 'rgba(100, 116, 139, 0.45)';
  const effectiveShimmerColor = shimmerColor ?? 'currentColor';

  return (
    <Component
      className={`text-shimmer-root relative inline-block select-none ${className}`}
      style={{
        ...style,
        '--spread': `${dynamicSpread}px`,
        '--base-color': effectiveBaseColor,
        '--base-gradient-color': effectiveShimmerColor,
        backgroundSize: '250% 100%, auto',
        WebkitBackgroundClip: 'text',
        backgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        color: 'transparent',
        backgroundRepeat: 'no-repeat, padding-box',
        backgroundImage: `linear-gradient(90deg, transparent calc(50% - var(--spread)), var(--base-gradient-color), transparent calc(50% + var(--spread))), linear-gradient(var(--base-color), var(--base-color))`,
        animation: `textShimmerSweep ${duration}s linear infinite`,
      }}
    >
      {children}
    </Component>
  );
}

export default TextShimmer;
