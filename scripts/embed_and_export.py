"""
Simple embedding pipeline

Reads a JSONL input file (one JSON doc per line), computes normalized embeddings
using `sentence-transformers` model `all-MiniLM-L6-v2`, and writes an output
JSONL file with an added `embedding` field (list of floats).

Optional: produce an Elasticsearch bulk file (action + source lines) suitable
for `curl -XPOST "localhost:9200/_bulk" --data-binary @bulk.json` (ensure index
mapping matches vector dims).

Usage:
  python scripts/embed_and_export.py --input src/main/resources/pharmacy_sample.jsonl \
      --output src/main/resources/pharmacy_index.jsonl

Optional flags:
  --es-bulk : emit a bulk-format file alongside the normal output
  --index-name NAME : index name to use for es-bulk actions (default: pharmacy)

Notes:
  - First run will download the model (internet required).
  - Embeddings are normalized (unit length) which works well for cosine similarity.
"""

import argparse
import json
from pathlib import Path
from typing import List

from sentence_transformers import SentenceTransformer
from tqdm import tqdm


def normalize_text(s: str) -> str:
    return " ".join(s.strip().split())


def load_docs(path: Path) -> List[dict]:
    docs = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))
    return docs


def build_text_for_embedding(doc: dict) -> str:
    parts = []
    if doc.get("name"):
        parts.append(doc["name"])
    if doc.get("description"):
        parts.append(doc["description"])
    if doc.get("category"):
        parts.append(f"Category: {doc['category']}")
    if doc.get("dose"):
        parts.append(f"Dose: {doc['dose']}")
    return " -- ".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input JSONL file")
    parser.add_argument("--output", required=True, help="Output JSONL file")
    parser.add_argument("--es-bulk", action="store_true", help="Also create ES bulk file")
    parser.add_argument("--index-name", default="pharmacy", help="Index name for ES bulk output")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for encoding")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    docs = load_docs(input_path)
    if not docs:
        print("No docs found in input file.")
        return

    model = SentenceTransformer(args.model)
    texts = [build_text_for_embedding(d) for d in docs]
    texts = [normalize_text(t) for t in texts]

    all_embeddings = []
    for i in tqdm(range(0, len(texts), args.batch_size), desc="Encoding batches"):
        batch = texts[i : i + args.batch_size]
        emb = model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
        all_embeddings.extend(emb.tolist())

    # write normal output JSONL with `embedding` field
    with output_path.open("w", encoding="utf-8") as out_f:
        for doc, embedding in zip(docs, all_embeddings):
            doc_copy = dict(doc)
            doc_copy["embedding"] = embedding
            out_f.write(json.dumps(doc_copy, ensure_ascii=False) + "\n")

    print(f"Wrote {len(docs)} docs with embeddings to {output_path}")

    if args.es_bulk:
        bulk_path = output_path.with_suffix(".bulk.json")
        with bulk_path.open("w", encoding="utf-8") as bulk_f:
            for doc, embedding in zip(docs, all_embeddings):
                action = {"index": {"_index": args.index_name, "_id": doc.get("id")}}
                src = dict(doc)
                src["embedding"] = embedding
                bulk_f.write(json.dumps(action, ensure_ascii=False) + "\n")
                bulk_f.write(json.dumps(src, ensure_ascii=False) + "\n")
        print(f"Wrote ES bulk file to {bulk_path}")


if __name__ == "__main__":
    main()
