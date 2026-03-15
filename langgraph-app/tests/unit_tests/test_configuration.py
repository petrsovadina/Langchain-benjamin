"""Tests for graph configuration and structure."""

from langgraph.pregel import Pregel

from agent.graph import graph


def test_graph_is_compiled() -> None:
    """Graph must be a compiled Pregel instance."""
    assert isinstance(graph, Pregel)


def test_graph_has_expected_nodes() -> None:
    """Graph must contain all expected agent nodes."""
    node_names = set(graph.nodes.keys())
    expected = {
        "supervisor",
        "drug_agent",
        "pubmed_agent",
        "guidelines_agent",
        "general_agent",
        "synthesizer",
    }
    missing = expected - node_names
    assert not missing, f"Missing nodes: {missing}"
