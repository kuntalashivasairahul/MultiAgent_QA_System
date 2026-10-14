"""V2 gates with bounded hybrid search, SDK balance and section neighbours."""
import graph_v2 as v2
from retrieval import HYBRID_LIMITS, get_hybrid_context
from state import question_text

USES_RETRIEVAL = True
SUPPORTS_CHECKPOINTS = True
RETRIEVAL_K = HYBRID_LIMITS["max_chunks"]
CONTEXT_LIMITS = dict(HYBRID_LIMITS)


def retrieve(state: v2.V2State) -> v2.V2State:
    return {"documents": get_hybrid_context(question_text(state)),
            "sufficiency": None, "support": None, "draft": None}


def build_graph(*, checkpointer=None):
    return v2.build_graph(retrieve_node=retrieve, checkpointer=checkpointer)


graph = build_graph()
