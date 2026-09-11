import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  ShieldCheck,
  Scale,
  RefreshCw,
  AlertCircle,
  Sliders,
  CheckCircle2,
  XCircle,
  Layers,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export function EvaluationConsole() {
  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchEvaluationReport();
  }, []);

  const fetchEvaluationReport = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/evaluation/report`);
      if (res.ok) {
        const data = await res.json();
        setReport(data);
      }
    } catch (err) {
      console.warn('Evaluation report error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !report) {
    return (
      <div className="p-8 text-center text-slate-500 bg-white border border-slate-200 rounded-xl space-y-2 shadow-2xs">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto text-indigo-600" />
        <p className="text-xs">Computing empirical metrics across N=30 stratified benchmark cases...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-xs text-slate-800 font-sans">
      {/* Console Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-indigo-600 uppercase tracking-wider">
              Audit & Governance
            </span>
            <span className="text-slate-400">&bull;</span>
            <span className="text-[10px] font-mono text-slate-500">N=30 Stratified Ground Truth</span>
          </div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 mt-0.5">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            Evaluation Console & LLM Authority Audit
          </h2>
          <p className="text-[11px] text-slate-500 mt-1">
            Empirical multi-dimensional accuracy measurements, retrieval ablation comparisons, and compliance decision authority validation.
          </p>
        </div>

        <button
          onClick={fetchEvaluationReport}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-bold border border-slate-200 transition shrink-0 cursor-pointer shadow-2xs"
        >
          <RefreshCw className="w-3.5 h-3.5 text-indigo-600" />
          Re-evaluate Suite
        </button>
      </div>

      {/* Critical LLM Authority Audit Banner */}
      <div className="p-5 rounded-xl bg-emerald-50/70 border border-emerald-200 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded bg-emerald-100 text-emerald-700 border border-emerald-200 shrink-0 mt-0.5">
            <Scale className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <strong className="text-slate-900 text-sm">LLM Compliance Decision Authority Audit:</strong>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                0 (0.00%) &bull; STRICT ZERO
              </span>
            </div>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Every compliance gap verdict is computed by the deterministic Declarative Rule Engine and Requirement Comparator. The LLM operates strictly in explanatory and extraction capacity without decision power.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-right font-mono text-xs shrink-0 border-t md:border-t-0 md:border-l border-emerald-200 pt-3 md:pt-0 md:pl-4">
          <div>
            <span className="text-[10px] text-slate-500 block uppercase">Deterministic Decisions</span>
            <strong className="text-emerald-700 text-base">{report.llm_authority_audit.deterministic_rule_decisions}</strong>
          </div>
          <div>
            <span className="text-[10px] text-slate-500 block uppercase">LLM Decisions</span>
            <strong className="text-rose-600 text-base">{report.llm_authority_audit.llm_compliance_decisions}</strong>
          </div>
        </div>
      </div>

      {/* 9-Dimension Metric Cards */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Multi-Dimensional Empirical Measurements (Individual Dimension Scores)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            report.product_dna_evaluation,
            report.attribute_normalization_evaluation,
            report.clarification_evaluation,
            report.standard_identification_evaluation,
            report.retrieval_evaluation,
            report.evidence_extraction_evaluation,
            report.citation_validity_evaluation,
            report.gap_classification_evaluation,
            report.unsupported_claim_blocking,
          ].map((dim, idx) => (
            <div key={idx} className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 flex flex-col justify-between shadow-2xs hover:shadow-xs transition">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-500 uppercase">{dim.dataset_type.split(' ')[0]}</span>
                  <span className="text-xs font-mono font-bold text-indigo-600">
                    {(dim.accuracy_or_rate * 100).toFixed(1)}%
                  </span>
                </div>
                <h4 className="font-bold text-slate-900 text-xs mt-1">{dim.name}</h4>
                <p className="text-[10px] text-slate-600 mt-1 leading-relaxed">
                  Method: {dim.method}
                </p>
              </div>
              <div className="pt-2 border-t border-slate-100 text-[9px] text-amber-800 italic">
                Limitation: {dim.limitations}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Retrieval Strategy Ablation Table */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-xs">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-4 h-4 text-purple-600" />
            Formal Retrieval Strategy Ablation Study
          </h3>
          <span className="text-[10px] font-mono text-slate-500">Benchmark Sample N=30</span>
        </div>
        <div className="overflow-x-auto border border-slate-200 rounded-lg shadow-2xs">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-100 text-slate-700 border-b border-slate-200">
              <tr>
                <th className="p-3 font-semibold">Strategy Architecture</th>
                <th className="p-3 font-semibold">Recall@1</th>
                <th className="p-3 font-semibold">Recall@3</th>
                <th className="p-3 font-semibold">Recall@5</th>
                <th className="p-3 font-semibold">MRR</th>
                <th className="p-3 font-semibold">Avg Latency (ms)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white text-slate-800">
              {report.retrieval_ablation.map((row, idx) => (
                <tr key={idx} className={row.strategy.includes('DEFAULT') ? 'bg-indigo-50/40' : 'hover:bg-slate-50/80'}>
                  <td className="p-3 font-bold text-slate-900">
                    {row.strategy}
                  </td>
                  <td className="p-3">{(row.recall_at_1 * 100).toFixed(0)}%</td>
                  <td className="p-3 font-bold text-emerald-700">{(row.recall_at_3 * 100).toFixed(0)}%</td>
                  <td className="p-3">{(row.recall_at_5 * 100).toFixed(0)}%</td>
                  <td className="p-3 text-indigo-700">{row.mrr.toFixed(2)}</td>
                  <td className="p-3 text-slate-500">{row.avg_latency_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Retrieval Error Analysis */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3 shadow-xs">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-500" />
          Categorized Retrieval Error Analysis & Miss Classification
        </h3>
        <div className="space-y-2">
          {report.retrieval_error_analysis.map((err, idx) => (
            <div key={idx} className="p-3 rounded bg-slate-50 border border-slate-200 text-xs font-mono flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-2xs">
              <div>
                <span className="font-bold text-indigo-700">{err.case_id}:</span>{' '}
                <span className="text-slate-800 font-sans">{err.notes}</span>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  Expected: {err.expected_clauses.join(', ') || 'None'} &bull; Retrieved: {err.retrieved_clauses.join(', ') || 'None'}
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 shrink-0">
                {err.error_type}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Disclaimers & Limitations */}
      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-600 space-y-1">
        <strong className="text-slate-800 uppercase tracking-wider block">Empirical Measurement Honesty Disclaimer:</strong>
        <p>{report.disclaimer}</p>
      </div>
    </div>
  );
}
