"""V2 gates with bounded expansion of dense anchors within canonical sections."""
import graph_v2 as v2
from retrieval import SECTION_MAX_CHARS, SECTION_MAX_CHUNKS, SECTION_SEED_K, get_section_context
from state import question_text

USES_RETRIEVAL = True
RETRIEVAL_K = SECTION_MAX_CHUNKS  # Maximum returned chunks, including the original dense anchors.
CONTEXT_LIMITS = {"seed_k": SECTION_SEED_K, "max_chunks": SECTION_MAX_CHUNKS,
                  "max_document_text_characters": SECTION_MAX_CHARS}


def retrieve(state: v2.V2State) -> v2.V2State:
    return {"documents": get_section_context(question_text(state)),
            "sufficiency": None, "support": None, "draft": None}


graph = v2.build_graph(retrieve_node=retrieve)
