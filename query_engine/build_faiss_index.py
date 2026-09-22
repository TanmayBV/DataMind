"""
build_faiss_index.py
---------------------
Day 4: embeds the curated few-shot examples (data/few_shot_examples.jsonl)
using a local sentence-transformers model and builds a FAISS index for
fast similarity search at query time.

Run once (or whenever you add/edit examples):
    python query_engine/build_faiss_index.py

Produces:
    data_pipeline/faiss_store/index.faiss   -- the vector index
    data_pipeline/faiss_store/examples.json -- the examples, same order as index
"""

import json
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
from config import DATA_DIR, EMBEDDING_MODEL

import faiss
from sentence_transformers import SentenceTransformer

STORE_DIR = os.path.join(os.path.dirname(__file__), "..", "data_pipeline", "faiss_store")
EXAMPLES_PATH = os.path.join(DATA_DIR, "few_shot_examples.jsonl")


def load_examples(path):
    examples = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def main():
    os.makedirs(STORE_DIR, exist_ok=True)

    examples = load_examples(EXAMPLES_PATH)
    print(f"Loaded {len(examples)} few-shot examples from {EXAMPLES_PATH}")

    print(f"Loading embedding model: {EMBEDDING_MODEL} (first run downloads ~90MB, cached after)")
    model = SentenceTransformer(EMBEDDING_MODEL)

    questions = [ex["question"] for ex in examples]
    embeddings = model.encode(questions, show_progress_bar=True, normalize_embeddings=True)
    embeddings = embeddings.astype("float32")

    dimension = embeddings.shape[1]
    # Inner product on normalized vectors == cosine similarity
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    faiss.write_index(index, os.path.join(STORE_DIR, "index.faiss"))
    with open(os.path.join(STORE_DIR, "examples.json"), "w") as f:
        json.dump(examples, f, indent=2)

    print(f"\nIndex built: {index.ntotal} vectors, dimension {dimension}")
    print(f"Saved to {STORE_DIR}/index.faiss and {STORE_DIR}/examples.json")


if __name__ == "__main__":
    main()
