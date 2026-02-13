from langgraph.pregel import Pregel

from agent.graph import graph


def test_general_agent() -> None:
    # TODO: You can add actual unit tests
    # for your graph and other logic here.
    assert isinstance(graph, Pregel)
