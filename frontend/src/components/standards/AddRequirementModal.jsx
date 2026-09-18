import React, { useState, useEffect, useRef } from 'react';
import { triggerEntrance } from '../../utils/useAnimeMotion';
import {
  ComparisonType,
  COMPARISON_TYPE_LABELS,
  RequirementType,
  REQUIREMENT_TYPE_LABELS,
  VerificationMethod,
  VERIFICATION_METHOD_LABELS,
} from '../../types/standardsTypes';
import { CANONICAL_PARAMETERS } from '../../types/productDnaTypes';

export function AddRequirementModal({ isOpen, onClose, onAddRequirement, activeStandard }) {
  const modalRef = useRef(null);

  const [clauseRef, setClauseRef] = useState('');
  const [part, setPart] = useState('');
  const [section, setSection] = useState('');
  const [subClause, setSubClause] = useState('');
  const [reqText, setReqText] = useState('');
  const [reqType, setReqType] = useState(RequirementType.SAFETY);
  const [parameterKey, setParameterKey] = useState('');
  const [customParamKey, setCustomParamKey] = useState('');
  const [unit, setUnit] = useState('');
  const [comparisonType, setComparisonType] = useState(ComparisonType.GREATER_THAN_OR_EQUAL);
  const [targetValue, setTargetValue] = useState('');
  const [minValue, setMinValue] = useState('');
  const [maxValue, setMaxValue] = useState('');
  const [allowedValues, setAllowedValues] = useState('');
  const [applicabilityCondition, setApplicabilityCondition] = useState('');
  const [evidenceRequirement, setEvidenceRequirement] = useState('');
  const [verificationMethod, setVerificationMethod] = useState(VerificationMethod.TYPE_TEST);
  const [sourceReference, setSourceReference] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && modalRef.current) {
      triggerEntrance(modalRef.current);
      setClauseRef('');
      setPart('');
      setSection('');
      setSubClause('');
      setReqText('');
      setReqType(RequirementType.SAFETY);
      setParameterKey('');
      setCustomParamKey('');
      setUnit('');
      setComparisonType(ComparisonType.GREATER_THAN_OR_EQUAL);
      setTargetValue('');
      setMinValue('');
      setMaxValue('');
      setAllowedValues('');
      setApplicabilityCondition('');
      setEvidenceRequirement('');
      setVerificationMethod(VerificationMethod.TYPE_TEST);
      setSourceReference('');
      setError(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCanonicalParamChange = (e) => {
    const key = e.target.value;
    setParameterKey(key);
    if (key !== 'CUSTOM') {
      const match = CANONICAL_PARAMETERS.find((p) => p.name === key || p.id === key);
      if (match) {
        setUnit(match.defaultUnit || '');
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!clauseRef.trim()) {
      setError('Clause reference is required (e.g., Cl. 2.10.3).');
      return;
    }
    if (!reqText.trim()) {
      setError('Requirement statutory text is required.');
      return;
    }

    const effectiveParamKey =
      parameterKey === 'CUSTOM' ? customParamKey.trim() : parameterKey.trim();

    const reqId = `REQ-${Math.random().toString(36).substring(2, 7).toUpperCase()}`;

    const newReq = {
      reqId,
      standardId: activeStandard?.id || 'UNASSIGNED',
      standardIdentifier: activeStandard?.identifier || 'Statutory Standard',
      clauseRef: clauseRef.trim(),
      part: part.trim() || 'General Specifications',
      section: section.trim() || 'General Safety Requirements',
      subClause: subClause.trim() || '',
      requirementText: reqText.trim(),
      requirementType: reqType,
      requiredParameterKey: effectiveParamKey || null,
      unit: unit.trim(),
      comparisonType,
      targetValue: targetValue.trim(),
      minValue: minValue.trim(),
      maxValue: maxValue.trim(),
      allowedValues: allowedValues.trim(),
      applicabilityCondition: applicabilityCondition.trim() || 'Mandatory for all equipment within standard scope',
      evidenceRequirement: evidenceRequirement.trim() || 'Accredited laboratory test report or manufacturer certificate',
      verificationMethod,
      sourceReference: sourceReference.trim(),
      createdAt: new Date().toISOString(),
    };

    onAddRequirement(newReq);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div
        ref={modalRef}
        className="w-full max-w-2xl bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden flex flex-col font-sans max-h-[90vh]"
      >
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
              <span className="material-symbols-outlined text-lg">gavel</span>
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider font-mono">
                Define Clause Requirement
              </h2>
              <p className="text-xs text-slate-500">
                {activeStandard
                  ? `Standard: ${activeStandard.identifier} (${activeStandard.revisionYear})`
                  : 'Assigning to active statutory assessment basis'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
              <span className="material-symbols-outlined text-sm shrink-0">error</span>
              <span>{error}</span>
            </div>
          )}

          {/* Clause Hierarchy: Part -> Section -> Clause -> Sub-clause */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
            <div className="text-[11px] font-mono font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-sm text-blue-600">account_tree</span>
              Standard Statutory Hierarchy
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Part</label>
                <input
                  type="text"
                  placeholder="e.g. Part 1: General Requirements"
                  value={part}
                  onChange={(e) => setPart(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500 bg-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Section</label>
                <input
                  type="text"
                  placeholder="e.g. Section 2: Protection against hazards"
                  value={section}
                  onChange={(e) => setSection(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500 bg-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">
                  Clause Reference <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Cl. 2.10.3"
                  value={clauseRef}
                  onChange={(e) => setClauseRef(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500 bg-white font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Sub-Clause</label>
                <input
                  type="text"
                  placeholder="e.g. 2.10.3.1 Clearances in Primary Circuits"
                  value={subClause}
                  onChange={(e) => setSubClause(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500 bg-white"
                />
              </div>
            </div>
          </div>

          {/* Statutory Requirement Text */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Statutory Requirement Text <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={2}
              placeholder="Enter the verbatim or canonical requirement text from standard..."
              value={reqText}
              onChange={(e) => setReqText(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-blue-500"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Requirement Domain Classification
              </label>
              <select
                value={reqType}
                onChange={(e) => setReqType(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-blue-500 bg-white"
              >
                {Object.entries(REQUIREMENT_TYPE_LABELS).map(([k, label]) => (
                  <option key={k} value={k}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Verification Method
              </label>
              <select
                value={verificationMethod}
                onChange={(e) => setVerificationMethod(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-blue-500 bg-white"
              >
                {Object.entries(VERIFICATION_METHOD_LABELS).map(([k, label]) => (
                  <option key={k} value={k}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Product DNA Linkage */}
          <div className="p-3.5 bg-blue-50/50 border border-blue-200 rounded-lg space-y-3">
            <div className="text-[11px] font-mono font-bold text-blue-900 uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-sm text-blue-600">fingerprint</span>
              Product DNA Parameter Mapping
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                  Target Product DNA Parameter
                </label>
                <select
                  value={parameterKey}
                  onChange={handleCanonicalParamChange}
                  className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500 bg-white font-mono"
                >
                  <option value="">-- No parameter mapping (Qualitative / Visual) --</option>
                  {CANONICAL_PARAMETERS.map((p) => (
                    <option key={p.id} value={p.name}>
                      {p.name} [{p.section}] {p.defaultUnit ? `(${p.defaultUnit})` : ''}
                    </option>
                  ))}
                  <option value="CUSTOM">+ Custom Parameter Key</option>
                </select>
              </div>

              {parameterKey === 'CUSTOM' ? (
                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                    Custom Parameter Key
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. secondary_winding_temp_rise"
                    value={customParamKey}
                    onChange={(e) => setCustomParamKey(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500 bg-white font-mono"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Unit</label>
                  <input
                    type="text"
                    placeholder="e.g. mm, V, A, °C"
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500 bg-white font-mono"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Deterministic Comparison Rule */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
            <div className="text-[11px] font-mono font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-sm text-purple-600">functions</span>
              Deterministic Comparison Rule
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                Comparison Operator
              </label>
              <select
                value={comparisonType}
                onChange={(e) => setComparisonType(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-blue-500 bg-white"
              >
                {Object.entries(COMPARISON_TYPE_LABELS).map(([k, label]) => (
                  <option key={k} value={k}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Dynamic Comparison Threshold Inputs */}
            {comparisonType === ComparisonType.RANGE ? (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Min Threshold</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="e.g. 200"
                    value={minValue}
                    onChange={(e) => setMinValue(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Max Threshold</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="e.g. 240"
                    value={maxValue}
                    onChange={(e) => setMaxValue(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded font-mono"
                    required
                  />
                </div>
              </div>
            ) : comparisonType === ComparisonType.ENUMERATION ? (
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">
                  Allowed Values (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Class I, Class II"
                  value={allowedValues}
                  onChange={(e) => setAllowedValues(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded font-mono"
                  required
                />
              </div>
            ) : comparisonType === ComparisonType.BOOLEAN ? (
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">
                  Target Boolean Expected Value
                </label>
                <select
                  value={targetValue}
                  onChange={(e) => setTargetValue(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded bg-white font-mono"
                >
                  <option value="true">True / Passed</option>
                  <option value="false">False</option>
                </select>
              </div>
            ) : comparisonType === ComparisonType.TEXT_REVIEW ||
              comparisonType === ComparisonType.NOT_APPLICABLE ? null : (
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">
                  Statutory Numerical Limit / Target Value
                </label>
                <input
                  type="text"
                  placeholder="e.g. 2.5 (for >= 2.5 mm)"
                  value={targetValue}
                  onChange={(e) => setTargetValue(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded font-mono"
                  required
                />
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Applicability Condition
              </label>
              <input
                type="text"
                placeholder="e.g. Applicable if rated voltage > 50V AC"
                value={applicabilityCondition}
                onChange={(e) => setApplicabilityCondition(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Source Reference (Standard Page / Table)
              </label>
              <input
                type="text"
                placeholder="e.g. Section 2.10, Table 2H, Page 41"
                value={sourceReference}
                onChange={(e) => setSourceReference(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Required Evidence Artifact
            </label>
            <input
              type="text"
              placeholder="e.g. Laboratory Safety Test Report showing physical measurement"
              value={evidenceRequirement}
              onChange={(e) => setEvidenceRequirement(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-md"
            />
          </div>

          {/* Modal Actions */}
          <div className="pt-4 border-t border-slate-200 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-sm">add_task</span>
              Add Requirement to Catalogue
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
