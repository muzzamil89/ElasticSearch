"""Evaluate and simple tests for the small pharmacy dataset.

Features:
- Loads precomputed indexed JSONL with embeddings if present (src/main/resources/pharmacy_index.jsonl)
- Otherwise computes embeddings locally using the same model used by the pipeline.
- Runs a few sample queries and prints top-K results using a simple hybrid score:
      score = cosine_similarity + 0.01 * token_overlap
- Provides helpers used by pytest tests in `tests/test_search.py`.

Usage:
  python scripts/evaluate_and_test.py  # dry run, prints results
  pytest -q                          # run automated tests

Note: This script does not require Elasticsearch to run; if ES is available you can adapt it to POST the query to ES instead.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Tuple, Dict

import numpy as np
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).resolve().parents[1]
SAMPLE_INDEX_PATH = BASE / "src" / "main" / "resources" / "pharmacy_index.jsonl"
SAMPLE_SRC_PATH = BASE / "src" / "main" / "resources" / "pharmacy_sample.jsonl"

MODEL_NAME = "all-MiniLM-L6-v2"

# Define simple test queries and expected top-1 doc ids
TEST_QUERIES = [
    ("aspirin 500 mg pain", "p001"),
    ("paracetamol fever", "p002"),
    ("antibiotic for infections", "p003"),
    ("non-drowsy antihistamine", "p004"),
]


def load_indexed_docs(path: Path) -> List[dict]:
    docs = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))
    return docs


def compute_embeddings(model: SentenceTransformer, texts: List[str]) -> np.ndarray:
    arr = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return np.asarray(arr)


def build_text_for_embedding(doc: dict) -> str:
    parts = []
    if doc.get("name"):
        parts.append(doc["name"])
    if doc.get("description"):
        parts.append(doc["description"])
    if doc.get("category"):
        parts.append(doc.get("category"))
    if doc.get("dose"):
        parts.append(str(doc.get("dose")))
    return " -- ".join(parts)


def simple_token_overlap_score(query: str, doc_text: str) -> int:
    q_tokens = set(tokenize(query))
    d_tokens = set(tokenize(doc_text))
    return len(q_tokens & d_tokens)


def tokenize(s: str) -> List[str]:
    return [t for t in s.lower().split() if t]


def rank_documents(query: str, docs: List[dict], doc_embeddings: np.ndarray, model: SentenceTransformer, top_k: int = 5) -> List[Tuple[float, dict]]:
    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    # cosine with normalized vectors is dot product
    cos_sims = doc_embeddings @ q_emb
    results = []
    for i, d in enumerate(docs):
        doc_text = build_text_for_embedding(d)
        overlap = simple_token_overlap_score(query, doc_text)
        score = float(cos_sims[i]) + 0.01 * overlap
        results.append((score, d))
    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_k]


def evaluate_and_report(docs: List[dict], model: SentenceTransformer, doc_embeddings: np.ndarray):
    total = 0
    top1 = 0
    top3 = 0
    for q, expected in TEST_QUERIES:
        total += 1
        ranked = rank_documents(q, docs, doc_embeddings, model, top_k=3)
        ids = [d.get("id") for _, d in ranked]
        print("Query:", q)
        print("Top results:")
        for sco, doc in ranked:
            print(f"  {doc.get('id')} ({doc.get('name')}): score={sco:.4f}")
        if ids and ids[0] == expected:
            top1 += 1
        if expected in ids:
            top3 += 1
        print(f"Expected: {expected}; positions: {ids}\n")
    print(f"Recall@1: {top1}/{total} = {top1/total:.2f}")
    print(f"Recall@3: {top3}/{total} = {top3/total:.2f}")
    return (top1, top3, total)


if __name__ == "__main__":
    # load or compute docs and embeddings
    if SAMPLE_INDEX_PATH.exists():
        docs = load_indexed_docs(SAMPLE_INDEX_PATH)
        if "embedding" in docs[0]:
            doc_embeddings = np.asarray([np.array(d["embedding"], dtype=float) for d in docs])
            # ensure embeddings are normalized (small numerical drift may exist)
            norms = np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
            doc_embeddings = doc_embeddings / np.maximum(norms, 1e-12)
            model = SentenceTransformer(MODEL_NAME)
        else:
            model = SentenceTransformer(MODEL_NAME)
            texts = [build_text_for_embedding(d) for d in docs]
            doc_embeddings = compute_embeddings(model, texts)
    else:
        print("Indexed file not found — computing embeddings from source sample file.")
        src = load_indexed_docs(SAMPLE_SRC_PATH)
        model = SentenceTransformer(MODEL_NAME)
        docs = src
        texts = [build_text_for_embedding(d) for d in docs]
        doc_embeddings = compute_embeddings(model, texts)

    evaluate_and_report(docs, model, doc_embeddings)


def get_ranked_ids_for_query(query: str) -> List[str]:
    """Helper used in tests: returns top-3 doc ids for a query."""
    # Load docs/emb; compute model locally
    if SAMPLE_INDEX_PATH.exists():
        docs = load_indexed_docs(SAMPLE_INDEX_PATH)
        if "embedding" in docs[0]:
            doc_embeddings = np.asarray([np.array(d["embedding"], dtype=float) for d in docs])
            norms = np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
            doc_embeddings = doc_embeddings / np.maximum(norms, 1e-12)
            model = SentenceTransformer(MODEL_NAME)
        else:
            docs = load_indexed_docs(SAMPLE_INDEX_PATH)
            model = SentenceTransformer(MODEL_NAME)
            texts = [build_text_for_embedding(d) for d in docs]
            doc_embeddings = compute_embeddings(model, texts)
    else:
        docs = load_indexed_docs(SAMPLE_SRC_PATH)
        model = SentenceTransformer(MODEL_NAME)
        texts = [build_text_for_embedding(d) for d in docs]
        doc_embeddings = compute_embeddings(model, texts)

    ranked = rank_documents(query, docs, doc_embeddings, model, top_k=3)
    return [d.get("id") for _, d in ranked]
