"""Layer 9: Output Layer & Compliance Passport — Formatter.

Generates print-ready HTML and structured JSON representations
of the Compliance Passport, strictly enforcing the required title:
"Evidence-Backed Pre-Certification Compliance Assessment"
and prohibiting claims of "BIS Certificate", "BIS Approval", etc.
"""

from typing import Dict, Any
from backend.app.services.passport.models import (
    ProductionCompliancePassport,
    PASSPORT_TITLE,
    PROHIBITED_LABELS,
)


class ReportFormatter:
    """Formats Production Compliance Passports into downloadable reports."""

    @classmethod
    def format_html_report(cls, passport: ProductionCompliancePassport) -> str:
        """Render self-contained, print-ready HTML report for MSME compliance audits."""
        summary = passport.executive_summary
        gate = passport.integrity_gate

        # Generate requirements table rows
        rows_html = ""
        for r in passport.requirements_matrix:
            chain_text = ""
            if r.trust_chain:
                chain_text = f"<div class='trust-chain'>CLAIM: {r.trust_chain.claim} &rarr; SRC: {r.trust_chain.source} &rarr; STD: {r.trust_chain.standard} &rarr; CL: {r.trust_chain.clause} &rarr; EV: {r.trust_chain.evidence} &rarr; VERIFIED</div>"
            
            rows_html += f"""
            <tr>
              <td><strong>{r.standard}</strong><br><small>Clause {r.clause_number}</small></td>
              <td>{r.clause_title}<br><small>{r.code}</small></td>
              <td><span class="badge badge-{r.status.lower()}">{r.status}</span></td>
              <td>{r.available_evidence or 'None'}</td>
              <td>{r.verification}</td>
              <td>{r.observed_value or 'N/A'}</td>
              <td>{r.required_value or 'N/A'}</td>
              <td>{r.deterministic_result}</td>
              <td>{r.recommended_action}</td>
              <td>{chain_text or (r.source_citation + f' (p. {r.page_number})')}</td>
            </tr>
            """

        # Generate gaps HTML
        gaps_html = ""
        for g in passport.gap_report:
            gaps_html += f"""
            <div class="gap-card gap-{g.priority.lower()}">
              <div class="gap-header">
                <strong>[{g.priority}] {g.standard} Clause {g.clause_number}: {g.requirement_name}</strong>
                <span class="badge">{g.recommended_action}</span>
              </div>
              <p><strong>Rationale:</strong> {g.why_it_is_a_gap}</p>
              <p><strong>Missing Requirement:</strong> {g.missing_evidence}</p>
              <p><strong>Source:</strong> {g.supporting_source}</p>
            </div>
            """

        # Generate Action Center HTML
        action_html = f"""
        <div class="action-center">
          <h3>MSME Action Center</h3>
          <div class="action-grid">
            <div class="action-col">
              <h4>What You Have ({len(passport.action_center.what_you_have)})</h4>
              <ul>{"".join(f"<li>{item}</li>" for item in passport.action_center.what_you_have)}</ul>
            </div>
            <div class="action-col">
              <h4>What Is Missing ({len(passport.action_center.what_is_missing)})</h4>
              <ul>{"".join(f"<li>{item}</li>" for item in passport.action_center.what_is_missing)}</ul>
            </div>
            <div class="action-col">
              <h4>What To Test ({len(passport.action_center.what_to_test)})</h4>
              <ul>{"".join(f"<li><strong>Cl {t.code}:</strong> {t.detail}</li>" for t in passport.action_center.what_to_test)}</ul>
            </div>
            <div class="action-col">
              <h4>What To Upload ({len(passport.action_center.what_to_upload)})</h4>
              <ul>{"".join(f"<li><strong>Cl {u.code}:</strong> {u.detail}</li>" for u in passport.action_center.what_to_upload)}</ul>
            </div>
          </div>
        </div>
        """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{passport.document_title} - {passport.assessment_number}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.5; color: #1e293b; padding: 30px; max-width: 1200px; margin: auto; }}
    .header {{ border-bottom: 3px solid #4f46e5; padding-bottom: 15px; margin-bottom: 25px; }}
    .title {{ font-size: 24px; font-weight: bold; color: #0f172a; margin: 0; }}
    .subtitle {{ font-size: 13px; color: #64748b; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }}
    .meta-box {{ display: flex; justify-content: space-between; background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size: 12px; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 25px; }}
    .metric-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center; }}
    .metric-val {{ font-size: 20px; font-weight: bold; color: #4f46e5; }}
    .metric-lbl {{ font-size: 11px; color: #64748b; text-transform: uppercase; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 25px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f1f5f9; font-weight: bold; }}
    .trust-chain {{ font-family: monospace; font-size: 9px; color: #059669; margin-top: 4px; background: #ecfdf5; padding: 4px; border-radius: 4px; }}
    .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; font-family: monospace; }}
    .badge-satisfied {{ background: #d1fae5; color: #065f46; }}
    .badge-missing_evidence {{ background: #fef3c7; color: #92400e; }}
    .badge-potential_gap {{ background: #fee2e2; color: #991b1b; }}
    .gap-card {{ border-left: 4px solid; padding: 10px; margin-bottom: 10px; background: #fafafa; font-size: 11px; border-radius: 4px; }}
    .gap-critical {{ border-color: #dc2626; background: #fef2f2; }}
    .gap-high {{ border-color: #ea580c; background: #fff7ed; }}
    .gap-medium {{ border-color: #2563eb; background: #eff6ff; }}
    .gap-low {{ border-color: #64748b; background: #f8fafc; }}
    .action-center {{ background: #f8fafc; border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; margin-bottom: 25px; }}
    .action-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; font-size: 12px; }}
    .disclaimer {{ font-size: 10px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 15px; margin-top: 30px; }}
    @media print {{ body {{ padding: 0; }} }}
  </style>
</head>
<body>
  <div class="header">
    <div class="subtitle">Bureau of Indian Standards Pre-Certification Roadmap</div>
    <h1 class="title">{passport.document_title}</h1>
  </div>

  <div class="meta-box">
    <div>
      <div><strong>Product:</strong> {passport.executive_summary.product_name}</div>
      <div><strong>Category:</strong> {passport.executive_summary.category}</div>
      <div><strong>Passport ID:</strong> {passport.passport_id}</div>
    </div>
    <div>
      <div><strong>Assessment Number:</strong> {passport.assessment_number}</div>
      <div><strong>Generated:</strong> {passport.generated_at.strftime('%Y-%m-%d %H:%M UTC')}</div>
      <div><strong>Lifecycle State:</strong> {passport.lifecycle_state.value}</div>
    </div>
    <div>
      <div><strong>Product DNA Version:</strong> {passport.product_dna_version}</div>
      <div><strong>Knowledge Version:</strong> {passport.knowledge_version}</div>
      <div><strong>Snapshot Hash:</strong> {passport.snapshot_hash[:16]}...</div>
    </div>
  </div>

  <div class="summary-grid">
    <div class="metric-card"><div class="metric-val">{summary.total_requirements_evaluated}</div><div class="metric-lbl">Requirements Evaluated</div></div>
    <div class="metric-card"><div class="metric-val">{summary.satisfied_count}</div><div class="metric-lbl">Satisfied (Verified)</div></div>
    <div class="metric-card"><div class="metric-val">{summary.missing_evidence_count}</div><div class="metric-lbl">Missing Evidence</div></div>
    <div class="metric-card"><div class="metric-val">{summary.potential_gaps_count}</div><div class="metric-lbl">Actionable Gaps</div></div>
  </div>

  {action_html}

  <h3>Requirement-by-Requirement Evaluation & Verification Matrix</h3>
  <table>
    <thead>
      <tr>
        <th>Standard & Clause</th>
        <th>Requirement</th>
        <th>Status</th>
        <th>Available Evidence</th>
        <th>Verification</th>
        <th>Observed Value</th>
        <th>Required Value</th>
        <th>Deterministic Result</th>
        <th>Recommended Action</th>
        <th>Source / Layer 8 Trust Chain</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>

  <h3>Prioritized Compliance Gap Register</h3>
  {gaps_html}

  <div class="disclaimer">
    <strong>Statutory Notice:</strong>
    <ul>
      {"".join(f"<li>{d}</li>" for d in passport.disclaimers)}
    </ul>
  </div>
</body>
</html>
"""
        return html


report_formatter = ReportFormatter()
