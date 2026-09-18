import React, { useState, useMemo } from 'react';
import {
  RequirementType,
  REQUIREMENT_TYPE_LABELS,
  ProductDnaMatchState,
  DNA_MATCH_CONFIG,
  EngineeringAssessmentState,
  ASSESSMENT_STATE_CONFIG,
  COMPARISON_TYPE_LABELS,
} from '../types/standardsTypes';
import { getDnaMatchStatus } from '../utils/deterministicEngine';

export function StandardsIntelligenceView({
  standards = [],
  activeStandardId,
  onSelectActiveStandard,
  onAddStandardClick,
  onRemoveStandard,
  requirements = [],
  onAddRequirementClick,
  productDnaFacts = {},
  conflictsList = [],
  evidenceList = [],
  assessmentResults = {},
  onEvaluateRequirement,
  onEvaluateAllRequirements,
  onInspectTraceChain,
  onNavigateDNA,
  onNavigateEvidence,
  onNavigateSpatialCAD,
}) {
  const [selectedTypeFilter, setSelectedTypeFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedHierarchy, setExpandedHierarchy] = useState({});

  // Active Standard
  const activeStandard = useMemo(() => {
    return standards.find((s) => s.id === activeStandardId) || standards[0] || null;
  }, [standards, activeStandardId]);

  // Requirements belonging to active standard
  const standardRequirements = useMemo(() => {
    if (!activeStandard) return [];
    return requirements.filter((r) => r.standardId === activeStandard.id);
  }, [requirements, activeStandard]);

  // Filtered requirements
  const filteredRequirements = useMemo(() => {
    return standardRequirements.filter((req) => {
      const matchesType =
        selectedTypeFilter === 'ALL' || req.requirementType === selectedTypeFilter;
      const q = searchQuery.toLowerCase().trim();
      const matchesQuery =
        !q ||
        req.reqId.toLowerCase().includes(q) ||
        req.clauseRef.toLowerCase().includes(q) ||
        req.requirementText.toLowerCase().includes(q) ||
        (req.requiredParameterKey && req.requiredParameterKey.toLowerCase().includes(q));
      return matchesType && matchesQuery;
    });
  }, [standardRequirements, selectedTypeFilter, searchQuery]);

  // Statistics for active standard
  const stats = useMemo(() => {
    const total = standardRequirements.length;
    let readyCount = 0;
    let missingDnaCount = 0;
    let passCount = 0;
    let gapCount = 0;
    let reviewCount = 0;

    standardRequirements.forEach((r) => {
      const matchStatus = getDnaMatchStatus(r, productDnaFacts, conflictsList);
      if (matchStatus === ProductDnaMatchState.READY_FOR_ASSESSMENT) readyCount++;
      if (matchStatus === ProductDnaMatchState.NO_MATCHING_DNA) missingDnaCount++;

      const res = assessmentResults[r.reqId] || assessmentResults[r.id];
      if (res) {
        if (res.engineeringResult === EngineeringAssessmentState.ENGINEERING_PASS) passCount++;
        if (res.engineeringResult === EngineeringAssessmentState.ENGINEERING_GAP) gapCount++;
        if (res.engineeringResult === EngineeringAssessmentState.HUMAN_REVIEW_REQUIRED) reviewCount++;
      }
    });

    return { total, readyCount, missingDnaCount, passCount, gapCount, reviewCount };
  }, [standardRequirements, productDnaFacts, conflictsList, assessmentResults]);

  // Empty state if no standards assigned
  if (standards.length === 0) {
    return (
      <div className="w-full flex-1 p-6 md:p-8 bg-[#F8F9FA] flex flex-col font-sans">
        <div className="max-w-3xl mx-auto w-full space-y-6">
          {/* Regulatory Mandate Firewall Banner */}
          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <div className="flex items-center gap-2.5">
              <span className="material-symbols-outlined text-blue-600 text-xl">gavel</span>
              <div>
                <h1 className="text-sm font-bold text-slate-900 uppercase tracking-wider font-mono">
                  Stage 03: Standards & Clause Intelligence
                </h1>
                <p className="text-xs text-slate-500">
                  Deterministic compilation against official statutory standards and clause catalogues
                </p>
              </div>
            </div>
          </div>

          {/* Clean Zero State */}
          <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-xs flex flex-col items-center">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 mb-4">
              <span className="material-symbols-outlined text-3xl">menu_book</span>
            </div>
            <h2 className="text-base font-bold text-slate-900 mb-1">
              No standards assigned to this compliance job.
            </h2>
            <p className="text-xs text-slate-500 max-w-md leading-relaxed mb-6">
              Assign an official Indian Standard (IS) or statutory technical regulation to establish the active clause catalogue and deterministic assessment rules.
            </p>
            <button
              type="button"
              onClick={onAddStandardClick}
              className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition flex items-center gap-2 shadow-sm cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              Assign First Standard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full flex-1 p-4 sm:p-6 lg:p-8 bg-[#F8F9FA] flex flex-col gap-6 font-sans">
      {/* Top Banner: Statutory Firewall & Regulatory Separation Notice */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-mono font-bold">
              STAGE 03 • DETERMINISTIC COMPILER
            </span>
            <span className="px-2 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-800 text-[10px] font-mono font-semibold">
              ENGINEERING ASSESSMENT ONLY
            </span>
          </div>
          <h1 className="text-lg font-bold text-slate-900 mt-1">
            Standards & Clause Intelligence Workspace
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Deterministic statutory assessment: Accepted Evidence &rarr; Verified Product DNA &rarr; Applicable Requirement
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            type="button"
            onClick={onAddRequirementClick}
            className="px-3.5 py-2 text-xs font-medium text-slate-800 bg-white border border-slate-300 hover:bg-slate-50 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer shadow-xs"
          >
            <span className="material-symbols-outlined text-sm">add_task</span>
            Add Requirement
          </button>
          <button
            type="button"
            onClick={onAddStandardClick}
            className="px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer shadow-xs"
          >
            <span className="material-symbols-outlined text-sm">add</span>
            Add Standard
          </button>
        </div>
      </div>

      {/* Standards Selection Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-mono font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <span className="material-symbols-outlined text-sm text-blue-600">bookmark</span>
            Assigned Statutory Standards ({standards.length})
          </div>
          {activeStandard && (
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-slate-500 font-mono">
                Active Assessment Basis:
              </span>
              <span className="px-2 py-0.5 bg-blue-100 text-blue-800 border border-blue-300 rounded font-mono font-bold text-xs">
                {activeStandard.identifier}
              </span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {standards.map((std) => {
            const isActive = std.id === activeStandard?.id;
            return (
              <div
                key={std.id}
                onClick={() => onSelectActiveStandard(std.id)}
                className={`p-3.5 rounded-lg border transition-all cursor-pointer flex flex-col justify-between gap-2 ${
                  isActive
                    ? 'border-blue-600 bg-blue-50/40 ring-1 ring-blue-500 shadow-xs'
                    : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-slate-900">
                      {std.identifier}
                    </span>
                    {isActive ? (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-blue-600 text-white">
                        ACTIVE BASIS
                      </span>
                    ) : (
                      <span className="text-[10px] font-mono text-slate-400">ASSIGNED</span>
                    )}
                  </div>
                  <div className="text-[11px] font-medium text-slate-700 mt-1 line-clamp-1">
                    {std.title}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                    Rev: {std.revisionYear}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[10px]">
                  <span className="text-slate-500 truncate max-w-[180px]">
                    {std.gazetteRef || 'Statutory Gazette'}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveStandard(std.id);
                    }}
                    className="text-slate-400 hover:text-red-600 transition p-0.5"
                    title="Remove standard"
                  >
                    <span className="material-symbols-outlined text-sm">delete</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* KPI Metrics Summary for Active Standard */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[10px] font-mono text-slate-500 uppercase font-semibold">Total Requirements</div>
          <div className="text-xl font-bold font-mono text-slate-900 mt-0.5">{stats.total}</div>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[10px] font-mono text-purple-600 uppercase font-semibold">Ready for Assessment</div>
          <div className="text-xl font-bold font-mono text-purple-700 mt-0.5">{stats.readyCount}</div>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[10px] font-mono text-amber-600 uppercase font-semibold">Data Required (DNA)</div>
          <div className="text-xl font-bold font-mono text-amber-700 mt-0.5">{stats.missingDnaCount}</div>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[10px] font-mono text-emerald-600 uppercase font-semibold">Engineering Pass</div>
          <div className="text-xl font-bold font-mono text-emerald-700 mt-0.5">{stats.passCount}</div>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[10px] font-mono text-rose-600 uppercase font-semibold">Engineering Gaps</div>
          <div className="text-xl font-bold font-mono text-rose-700 mt-0.5">{stats.gapCount}</div>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[10px] font-mono text-indigo-600 uppercase font-semibold">Human Review</div>
          <div className="text-xl font-bold font-mono text-indigo-700 mt-0.5">{stats.reviewCount}</div>
        </div>
      </div>

      {/* Clause Catalogue & Requirements Section */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden flex flex-col">
        {/* Controls Bar */}
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono font-bold text-slate-700 uppercase mr-1">Domain:</span>
            <button
              type="button"
              onClick={() => setSelectedTypeFilter('ALL')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition cursor-pointer ${
                selectedTypeFilter === 'ALL'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
              }`}
            >
              All Domains
            </button>
            {Object.entries(REQUIREMENT_TYPE_LABELS).map(([k, label]) => (
              <button
                key={k}
                type="button"
                onClick={() => setSelectedTypeFilter(k)}
                className={`px-2 py-1 rounded text-[11px] font-medium transition cursor-pointer whitespace-nowrap ${
                  selectedTypeFilter === k
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                {label.split(' ')[0]}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2.5">
            <div className="relative">
              <input
                type="text"
                placeholder="Search clause or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-7 pr-3 py-1.5 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-blue-500 bg-white"
              />
              <span className="material-symbols-outlined text-sm text-slate-400 absolute left-2 top-2">
                search
              </span>
            </div>

            <button
              type="button"
              onClick={() => onEvaluateAllRequirements(activeStandard)}
              disabled={standardRequirements.length === 0}
              className="px-3 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 disabled:opacity-50 rounded-md transition flex items-center gap-1.5 cursor-pointer shadow-xs"
            >
              <span className="material-symbols-outlined text-sm text-emerald-400">play_arrow</span>
              Run Deterministic Compilation
            </button>
          </div>
        </div>

        {/* Requirements List */}
        {filteredRequirements.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center">
            <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
              <span className="material-symbols-outlined text-2xl">rule</span>
            </div>
            <h3 className="text-sm font-bold text-slate-800 mb-1">
              No requirements defined in this catalogue yet.
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mb-4">
              Add clauses and structured deterministic requirements to begin matching against verified Product DNA.
            </p>
            <button
              type="button"
              onClick={onAddRequirementClick}
              className="px-3.5 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md transition cursor-pointer"
            >
              + Add Clause Requirement
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {filteredRequirements.map((req) => {
              const matchStatus = getDnaMatchStatus(req, productDnaFacts, conflictsList);
              const matchConfig = DNA_MATCH_CONFIG[matchStatus];
              const result = assessmentResults[req.reqId] || assessmentResults[req.id];
              const resultConfig = result
                ? ASSESSMENT_STATE_CONFIG[result.engineeringResult]
                : ASSESSMENT_STATE_CONFIG[EngineeringAssessmentState.NOT_ASSESSED];

              const isSpatialApplicable =
                req.requiredParameterKey?.includes('creepage') ||
                req.requiredParameterKey?.includes('clearance') ||
                req.requiredParameterKey?.includes('dimension') ||
                req.requirementType === RequirementType.MECHANICAL;

              return (
                <div key={req.reqId} className="p-4 sm:p-5 hover:bg-slate-50/50 transition flex flex-col gap-3">
                  {/* Top Bar: IDs, Clause, Domain, Verification Method */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">
                        {req.reqId}
                      </span>
                      <span className="font-mono text-xs font-semibold text-slate-900 bg-slate-100 border border-slate-300 px-2 py-0.5 rounded">
                        {req.clauseRef}
                      </span>
                      <span className="text-[11px] text-slate-500 font-mono">
                        {req.part} &gt; {req.section}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                        {req.verificationMethod}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                        {REQUIREMENT_TYPE_LABELS[req.requirementType] || req.requirementType}
                      </span>
                    </div>
                  </div>

                  {/* Requirement Text */}
                  <div className="text-xs text-slate-800 leading-relaxed font-medium">
                    {req.requirementText}
                  </div>

                  {/* Rule & Mapping Specification */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                    <div>
                      <div className="text-[10px] font-mono uppercase text-slate-400 font-semibold mb-0.5">
                        Deterministic Rule Operator
                      </div>
                      <div className="font-mono text-slate-800 text-[11px]">
                        <span className="font-bold text-purple-700">{req.comparisonType}</span>
                        {req.targetValue && ` (Target: ${req.targetValue} ${req.unit || ''})`}
                        {req.minValue && ` (Range: [${req.minValue} - ${req.maxValue} ${req.unit || ''}])`}
                        {req.allowedValues && ` (Allowed: {${req.allowedValues}})`}
                      </div>
                    </div>

                    <div>
                      <div className="text-[10px] font-mono uppercase text-slate-400 font-semibold mb-0.5">
                        Required Product DNA Parameter
                      </div>
                      <div className="font-mono text-slate-800 text-[11px] flex items-center justify-between">
                        <span>{req.requiredParameterKey || '— (No parameter linked)'}</span>
                        {req.requiredParameterKey && productDnaFacts[req.requiredParameterKey] && (
                          <span className="font-bold text-emerald-700">
                            Current Value: {productDnaFacts[req.requiredParameterKey].value} {productDnaFacts[req.requiredParameterKey].unit || ''}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Deterministic Evaluation Breakdown if evaluated */}
                  {result && (result.observed_value !== null || result.evaluation_expression) && (
                    <div className="p-3 bg-white rounded-lg border border-slate-200 text-xs font-mono grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">Observed Value</span>
                        <span className="font-semibold text-slate-800">
                          {result.observed_value !== null && result.observed_value !== undefined
                            ? `${result.observed_value} ${result.observed_unit || ''}`
                            : '— (No DNA)'}
                        </span>
                        {result.normalized_value !== null &&
                          result.normalized_value !== undefined &&
                          result.normalized_unit &&
                          result.normalized_unit !== result.observed_unit && (
                            <span className="text-blue-600 text-[10px] block font-semibold">
                              Normalized: {result.normalized_value} {result.normalized_unit}
                            </span>
                          )}
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">Expected / Rule</span>
                        <span className="font-semibold text-slate-800">
                          {result.expected_value
                            ? `${result.comparison_operator || '=='} ${result.expected_value} ${result.expected_unit || ''}`
                            : result.threshold_min !== null && result.threshold_min !== undefined && result.threshold_max !== null && result.threshold_max !== undefined
                            ? `[${result.threshold_min} - ${result.threshold_max} ${result.expected_unit || ''}]`
                            : result.threshold_max !== null && result.threshold_max !== undefined
                            ? `≤ ${result.threshold_max} ${result.expected_unit || ''}`
                            : result.threshold_min !== null && result.threshold_min !== undefined
                            ? `≥ ${result.threshold_min} ${result.expected_unit || ''}`
                            : '—'}
                        </span>
                      </div>
                      <div className="truncate">
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">Compiler Expression</span>
                        <span className="font-semibold text-slate-700 truncate block" title={result.evaluation_expression}>
                          {result.evaluation_expression || result.explanation || '—'}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Traceability Status & Assessment Output */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-100">
                    <div className="flex flex-wrap items-center gap-2">
                      {/* Product DNA Match State Pill (Invariant: Never called PASS or COMPLIANT) */}
                      <div
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${matchConfig.bg}`}
                        title={matchConfig.description}
                      >
                        <span className="material-symbols-outlined text-sm">{matchConfig.icon}</span>
                        <span>{matchConfig.label}</span>
                      </div>

                      {/* Engineering Assessment State Badge */}
                      <div
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${resultConfig.badge}`}
                      >
                        <span className="material-symbols-outlined text-sm">{resultConfig.icon}</span>
                        <span>ENGINEERING ASSESSMENT: {resultConfig.label}</span>
                      </div>
                    </div>

                    {/* Action Controls */}
                    <div className="flex items-center gap-2 shrink-0">
                      {isSpatialApplicable && onNavigateSpatialCAD && (
                        <button
                          type="button"
                          onClick={() => onNavigateSpatialCAD(req)}
                          className="px-2.5 py-1 text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded transition flex items-center gap-1 cursor-pointer"
                          title="View 3D CAD Twin Coordinates"
                        >
                          <span className="material-symbols-outlined text-xs">view_in_ar</span>
                          CAD Twin
                        </button>
                      )}

                      {result && (
                        <button
                          type="button"
                          onClick={() => onInspectTraceChain(result, req)}
                          className="px-2.5 py-1 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded transition flex items-center gap-1 cursor-pointer"
                        >
                          <span className="material-symbols-outlined text-xs">timeline</span>
                          Trace Chain
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => onEvaluateRequirement(activeStandard, req)}
                        className="px-3 py-1 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded transition flex items-center gap-1 cursor-pointer shadow-2xs"
                      >
                        <span className="material-symbols-outlined text-xs">play_arrow</span>
                        Evaluate
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
