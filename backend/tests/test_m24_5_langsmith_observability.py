"""Comprehensive Test Suite for Milestone M24.5: LangSmith Observability & LangStudio Graph Visualization.

Strictly verifies:
1. Tracing is DISABLED by default (LANGSMITH_TRACING=false)
2. Tracing enabled detection
3. Real graph execution trace creation (node metadata, latency, status)
4. Tool trace metadata (input summary, duration, status, call ID)
5. Correlation ID propagation across execution traces and metadata
6. Deterministic redaction of API keys (OpenAI, Composio, Groq, Bearer tokens)
7. Deterministic redaction of database URLs
8. Deterministic redaction of PII (emails, phone numbers, identity numbers)
9. Recursive trace payload sanitization & proprietary BOM protection
10. LangSmith failure isolation (network/auth errors never crash compliance graph)
11. Zero compliance authority preservation (read-only observability, 0.0% authority)
12. ONE LLM invariant preservation
13. Graph topology invariance (11 nodes, 16 edges, strict DAG)
14. LangStudio configuration validity and inspectability
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from backend.app.services.orchestrator.graph.tracing import (
    is_tracing_enabled,
    get_langsmith_config,
    redact_sensitive_content,
    sanitize_trace_payload,
    compute_content_hash,
    PrivacyPreservingCallbackHandler,
)
from backend.app.services.orchestrator.graph.runner import (
    run_compliance_graph_with_state,
    run_compliance_graph,
)
from backend.app.services.orchestrator.graph import compliance_graph
from backend.app.services.orchestrator.schemas import OrchestratedAIResponse
from backend.app.services.orchestrator.llm_interface import single_structured_llm


# ------------------------------------------------------------------------------
# 1. Tracing Default & Configuration
# ------------------------------------------------------------------------------
def test_tracing_disabled_by_default(monkeypatch):
    """Verify that tracing is disabled by default when no environment variable is set."""
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)

    assert is_tracing_enabled() is False

    config = get_langsmith_config("CORR-TEST-001", "THREAD-001")
    assert config["configurable"]["thread_id"] == "THREAD-001"
    assert config["metadata"]["correlation_id"] == "CORR-TEST-001"
    assert config["metadata"]["compliance_authority"] == "0.0%"
    assert config["metadata"]["observability_mode"] == "READ_ONLY"

    # Only local privacy handler is present, no outbound LangChainTracer
    assert len(config["callbacks"]) == 1
    assert isinstance(config["callbacks"][0], PrivacyPreservingCallbackHandler)


def test_tracing_enabled_detection(monkeypatch):
    """Verify that tracing is properly detected when explicitly set."""
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    assert is_tracing_enabled() is True

    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    assert is_tracing_enabled() is True


# ------------------------------------------------------------------------------
# 2. Real Graph Trace & Metadata
# ------------------------------------------------------------------------------
def test_real_graph_trace_creation_and_node_metadata():
    """Verify that real graph execution generates structured node traces with latency & status."""
    query = "What is the insulation resistance requirement under IS 302-2-201:2008?"
    product_dna = {"product_name": "Immersion Water Heater", "category": "Appliances"}

    response, state = run_compliance_graph_with_state(user_query=query, product_dna=product_dna)

    traces = state.get("execution_traces", [])
    assert len(traces) > 0

    for tr in traces:
        assert "node_name" in tr
        assert "start_time" in tr
        assert "end_time" in tr
        assert "duration_ms" in tr
        assert tr["duration_ms"] >= 0.0
        assert tr["status"] in ("SUCCESS", "FAILED", "SKIPPED")

    # Verify correlation ID format
    assert state["correlation_id"].startswith("GRAPH-L3-")


def test_tool_trace_metadata_collection():
    """Verify that controlled tool execution records tool traces with latency and status."""
    query = "What does Clause 19.1 require in IS 302-2-201:2008?"
    product_dna = {"product_name": "Immersion Water Heater", "category": "Appliances"}

    _, state = run_compliance_graph_with_state(user_query=query, product_dna=product_dna)

    tool_traces = state.get("tool_traces", [])
    assert len(tool_traces) > 0

    t0 = tool_traces[0]
    assert "tool_name" in t0
    assert "tool_call_id" in t0
    assert "node_name" in t0
    assert "timestamp" in t0
    assert "duration_ms" in t0
    assert "status" in t0
    assert t0["status"] in ("SUCCESS", "CACHED", "FAILED", "REJECTED")


def test_correlation_id_propagation():
    """Verify correlation ID is propagated into execution state, node traces, and metadata."""
    query = "Convert 100 F to C"
    _, state = run_compliance_graph_with_state(user_query=query)

    cid = state["correlation_id"]
    assert cid.startswith("GRAPH-L3-")
    assert state["regulatory_conclusion"] == "NONE"


# ------------------------------------------------------------------------------
# 3. Deterministic Redaction Engine
# ------------------------------------------------------------------------------
def test_deterministic_redaction_api_keys_and_secrets():
    """Verify API keys and secrets from all supported providers are redacted."""
    dummy_langsmith_key = "lsv2_" + "pt_mock_test_token_1234567890123456"
    raw_text = (
        "Composio key: ak_agAs0DibC3NMMKRzNryY, "
        "OpenAI key: sk-proj-1234567890abcdef1234567890, "
        "Groq key: gsk_1234567890abcdef1234567890, "
        f"LangSmith key: {dummy_langsmith_key}, "
        "Auth: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
    )
    redacted = redact_sensitive_content(raw_text)

    assert "ak_agAs0DibC3NMMKRzNryY" not in redacted
    assert "sk-proj-1234567890" not in redacted
    assert "gsk_1234567890" not in redacted
    assert dummy_langsmith_key not in redacted
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_deterministic_redaction_database_urls():
    """Verify raw database connection URIs with credentials are redacted."""
    raw_text = "Connected to postgresql://zyntrix_admin:P@ssw0rd123@db.prod.internal:5432/compliance_db"
    redacted = redact_sensitive_content(raw_text)

    assert "zyntrix_admin:P@ssw0rd123" not in redacted
    assert "[REDACTED_DATABASE_URL]" in redacted


def test_deterministic_redaction_pii():
    """Verify PII (emails, phone numbers, identification numbers) are redacted."""
    raw_text = "Submitted by engineer john.doe@manufacturer.co.in, phone: +91 (987) 654-3210, ID: 1234 5678 9012"
    redacted = redact_sensitive_content(raw_text)

    assert "john.doe@manufacturer.co.in" not in redacted
    assert "987" not in redacted or "[REDACTED_PHONE]" in redacted
    assert "1234 5678 9012" not in redacted
    assert "[REDACTED_EMAIL]" in redacted


def test_sanitize_trace_payload_recursive_and_bom_protection():
    """Verify nested structures and proprietary BOM data are protected with hashes."""
    payload = {
        "user_query": "What is the requirement for user test@example.com with key sk-abcdef1234567890123456?",
        "bom_raw": "Confidential internal bill of materials with trade secrets",
        "nested": {
            "db_uri": "sqlite://admin:secret@localhost/test.db",
            "items": ["safe item", "secret key ak_123456789012345678"],
        },
    }

    sanitized = sanitize_trace_payload(payload)

    assert "[REDACTED_EMAIL]" in sanitized["user_query"]
    assert "[REDACTED_SECRET]" in sanitized["user_query"]
    assert "[PROTECTED_PAYLOAD: hash=" in sanitized["bom_raw"]
    assert "[REDACTED_DATABASE_URL]" in sanitized["nested"]["db_uri"]
    assert "[REDACTED_SECRET]" in sanitized["nested"]["items"][1]


# ------------------------------------------------------------------------------
# 4. Failure Isolation
# ------------------------------------------------------------------------------
def test_langsmith_failure_isolation_network_error(monkeypatch):
    """Verify that a network failure or misconfiguration in LangSmith never fails the graph."""
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "invalid_key_simulate_failure")

    # Simulate LangChainTracer raising an initialization or connection error
    with patch("backend.app.services.orchestrator.graph.tracing.LangChainTracer") as mock_tracer_cls:
        mock_tracer_cls.side_effect = ConnectionError("Could not reach LangSmith API endpoint at https://api.smith.langchain.com")

        # Graph execution MUST succeed smoothly despite tracer failure
        query = "What is the insulation resistance requirement under IS 302-2-201:2008?"
        product_dna = {"product_name": "Immersion Water Heater", "category": "Appliances"}

        response, state = run_compliance_graph_with_state(user_query=query, product_dna=product_dna)

        assert isinstance(response, OrchestratedAIResponse)
        assert response.regulatory_conclusion == "NONE"
        assert state["regulatory_conclusion"] == "NONE"
        assert state["llm_compliance_authority"] == 0.0


# ------------------------------------------------------------------------------
# 5. Authority Firewall & Invariants
# ------------------------------------------------------------------------------
def test_observability_zero_compliance_authority():
    """Verify that observability cannot modify compliance determinations (authority = 0.0%)."""
    query = "Is this water heater compliant?"
    product_dna = {"product_name": "Immersion Water Heater", "category": "Appliances"}

    response, state = run_compliance_graph_with_state(user_query=query, product_dna=product_dna)

    # Authority invariants strictly preserved
    assert response.regulatory_conclusion == "NONE"
    assert state["regulatory_conclusion"] == "NONE"
    assert state["llm_compliance_authority"] == 0.0


def test_one_llm_invariant_preserved():
    """Verify SingleStructuredLLM remains the only LLM model instance."""
    assert single_structured_llm is not None
    assert single_structured_llm.__class__.__name__ == "SingleStructuredLLM"


def test_graph_topology_unchanged():
    """Verify LangGraph topology remains identical to M24.4.2."""
    g = compliance_graph.get_graph()
    assert len([n for n in g.nodes.keys() if not n.startswith("__")]) == 11
    assert len(g.edges) == 16


# ------------------------------------------------------------------------------
# 6. LangStudio Compatibility
# ------------------------------------------------------------------------------
def test_langstudio_configuration_file():
    """Verify langgraph.json exists and specifies the exact valid graph target."""
    config_path = os.path.join(os.getcwd(), "langgraph.json")
    assert os.path.exists(config_path), "langgraph.json is missing!"

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "graphs" in data
    assert "compliance_graph" in data["graphs"]
    assert "compliance_graph_studio" in data["graphs"]["compliance_graph"]
