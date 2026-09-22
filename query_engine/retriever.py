"""
retriever.py
------------
Day 4: loads the FAISS index built by build_faiss_index.py and retrieves
the top-k most similar few-shot examples for a given natural-language
question. Used by nl2sql_chain.py to build a few-shot prompt instead of
the zero-shot prompt from Day 3.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import EMBEDDING_MODEL, FAISS_TOP_K

import faiss
from sentence_transformers import SentenceTransformer

STORE_DIR = os.path.join(os.path.dirname(__file__), "..", "data_pipeline", "faiss_store")
INDEX_PATH = os.path.join(STORE_DIR, "index.faiss")
EXAMPLES_PATH = os.path.join(STORE_DIR, "examples.json")

_model = None
_index = None
_examples = None


def _load():
    """Lazy-load model/index once per process — embedding models are
    slow to load, so we don't want to reload on every single query."""
    global _model, _index, _examples
    if _model is None:
        if not os.path.exists(INDEX_PATH):
            raise RuntimeError(
                f"FAISS index not found at {INDEX_PATH}. "
                "Run `python query_engine/build_faiss_index.py` first."
            )
        _model = SentenceTransformer(EMBEDDING_MODEL)
        _index = faiss.read_index(INDEX_PATH)
        with open(EXAMPLES_PATH) as f:
            _examples = json.load(f)


def retrieve_examples(question: str, k: int = None):
    """Returns the top-k most similar {question, sql} examples for the
    given question, ranked by cosine similarity (highest first)."""
    _load()
    k = k or FAISS_TOP_K

    query_vec = _model.encode([question], normalize_embeddings=True).astype("float32")
    scores, indices = _index.search(query_vec, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        example = _examples[idx]
        results.append({**example, "similarity": float(score)})
    return results


def format_examples_for_prompt(examples: list) -> str:
    """Turns retrieved examples into a block to inject into the system prompt."""
    if not examples:
        return ""
    lines = ["Here are similar validated question -> SQL examples:\n"]
    for ex in examples:
        lines.append(f"Q: {ex['question']}\nSQL: {ex['sql']}\n")
    return "\n".join(lines)


if __name__ == "__main__":
    # Quick manual test: retrieve examples for a sample question
    import sys as _sys
    test_question = " ".join(_sys.argv[1:]) or "how many engineers work in Istanbul?"
    results = retrieve_examples(test_question)
    print(f"Query: {test_question}\n")
    for r in results:
        print(f"  [{r['similarity']:.3f}] {r['question']}")
        print(f"           -> {r['sql']}\n")
