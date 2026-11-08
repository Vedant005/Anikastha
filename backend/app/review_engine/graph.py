import logging

from langgraph.graph import END, START, StateGraph

from app.review_engine.nodes.code_specialist import code_specialist_node
from app.review_engine.nodes.dep_specialist import dep_specialist_node
from app.review_engine.nodes.synthesizer import synthesizer_node
from app.review_engine.nodes.verdict import verdict_node
from app.review_engine.nodes.verifier import verifier_node
from app.review_engine.state import ReviewState

logger = logging.getLogger("pr_sentinel.review_graph")


def build_review_graph():
    """
    Constructs the LangGraph multi-agent security review pipeline:
    START
      ├──> code_specialist  ──┐
      └──> dep_specialist   ──┴──> synthesizer ──> verifier ──> verdict ──> END
    """
    builder = StateGraph(ReviewState)

    # Register specialist and gatekeeper nodes
    builder.add_node("code_specialist", code_specialist_node)
    builder.add_node("dep_specialist", dep_specialist_node)
    builder.add_node("synthesizer", synthesizer_node)
    builder.add_node("verifier", verifier_node)
    builder.add_node("verdict", verdict_node)

    # Wire execution graph
    builder.add_edge(START, "code_specialist")
    builder.add_edge(START, "dep_specialist")
    builder.add_edge("code_specialist", "synthesizer")
    builder.add_edge("dep_specialist", "synthesizer")
    builder.add_edge("synthesizer", "verifier")
    builder.add_edge("verifier", "verdict")
    builder.add_edge("verdict", END)

    review_graph = builder.compile()
    return review_graph


# Pre-compiled graph instance
review_engine_graph = build_review_graph()
