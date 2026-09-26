import React from 'react';
import { MorphingInfinity } from '../loading-ui/morphing-infinity';
import { TextShimmer } from '../loading-ui/text-shimmer';

/**
 * ViewSkeleton
 * 
 * Clean workstation skeleton loader matching the product's layout.
 * Features MorphingInfinity and TextShimmer animations (loading.md & Thinking.md).
 */
export function ViewSkeleton({ type = 'table' }) {
  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Morphing Infinity Loading Indicator */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-blue-50/80 border border-blue-200/80 rounded-xl w-fit shadow-2xs">
        <MorphingInfinity className="w-5 h-5 text-blue-600 shrink-0" />
        <TextShimmer baseColor="#1d4ed8" shimmerColor="#60a5fa" duration={2} className="text-xs font-semibold">
          Synchronizing Statutory Assessment Data...
        </TextShimmer>
      </div>

      <div className="space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div className="space-y-2">
          <div className="h-6 w-48 bg-slate-200 rounded"></div>
          <div className="h-3 w-80 bg-slate-100 rounded"></div>
        </div>
        <div className="h-8 w-32 bg-slate-200 rounded-lg"></div>
      </div>

      {/* Top Banner Skeleton */}
      <div className="h-16 w-full bg-slate-100 rounded-xl border border-slate-200"></div>

      {/* Content Skeleton */}
      {type === 'table' ? (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden p-4 space-y-3">
          <div className="h-6 w-full bg-slate-100 rounded"></div>
          <div className="space-y-2 pt-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-10 w-full bg-slate-50 border border-slate-100 rounded flex items-center px-4 gap-4">
                <div className="h-3 w-16 bg-slate-200 rounded"></div>
                <div className="h-3 w-40 bg-slate-200 rounded"></div>
                <div className="h-3 w-28 bg-slate-200 rounded ml-auto"></div>
                <div className="h-3 w-20 bg-slate-200 rounded"></div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-white border border-slate-200 rounded-xl p-4 space-y-3">
              <div className="h-4 w-32 bg-slate-200 rounded"></div>
              <div className="h-3 w-48 bg-slate-100 rounded"></div>
              <div className="h-8 w-full bg-slate-50 rounded"></div>
            </div>
          ))}
        </div>
      )}
      </div>
    </div>
  );
}
