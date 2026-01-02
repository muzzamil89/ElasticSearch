# TODO — Simple Vector Search Prototype

This is a small, focused project to demonstrate hybrid text + vector search using a tiny pharmacy dataset (≤ ~1000 words).

Tasks:

1. Prepare small sample dataset (done/ongoing) — `src/main/resources/pharmacy_sample.jsonl`
2. Implement preprocessing & embedding pipeline (Python)
3. Produce ES index mapping & sample bulk JSON
4. Add minimal search API scaffold in `ElasticController`
5. Write README with usage steps
6. Evaluate & iterate

Keep it minimal and easy to run locally. Use `sentence-transformers` model `all-MiniLM-L6-v2` for embeddings.
