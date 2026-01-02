Elasticsearch usage (local)

1) Create the index with mapping:
   curl -X PUT "http://localhost:9200/pharmacy" -H 'Content-Type: application/json' -d @es/pharmacy_mapping.json

2) Generate a bulk-file with embeddings (recommended):
   python scripts/embed_and_export.py --input src/main/resources/pharmacy_sample.jsonl --output src/main/resources/pharmacy_index.jsonl --es-bulk --index-name pharmacy
   (This creates a file like src/main/resources/pharmacy_index.bulk.json)

3) Index the bulk file:
   curl -s -H "Content-Type: application/json" -XPOST "http://localhost:9200/_bulk" --data-binary @src/main/resources/pharmacy_index.bulk.json

4) Example search (replace the query_vector with the embedding produced for the query):
   POST /pharmacy/_search
   (use es/search_example.json as a template)

Embedding service
-----------------
You can run a simple local embedding service that the Java controller expects at `http://localhost:8000/embed`.

1) Start the service (after installing requirements):
   uvicorn scripts.embed_service:app --reload --port 8000

2) Example usage (single):
   curl -X POST "http://localhost:8000/embed" -H "Content-Type: application/json" -d '{"text":"aspirin 500 mg"}'
   Response: {"embedding":[...384 floats...]}

3) Batch example:
   curl -X POST "http://localhost:8000/embed/batch" -H "Content-Type: application/json" -d '{"texts":["aspirin 500 mg","paracetamol"]}'
   Response: {"embeddings":[[...],[...]]}

Notes:
- The embed script uses model `all-MiniLM-L6-v2` (dims=384). Ensure mapping dims match.
- For best results, normalize embeddings (the script does this). The search example uses `cosineSimilarity`.
- If using ES 8+, consider `knn_vector` and the kNN plugin for faster ANN search.

Evaluation & tests
------------------
You can run a local dry-run evaluation that uses the same model locally without requiring Elasticsearch:

1) Run the evaluator (prints recall & top results):
   python scripts/evaluate_and_test.py

2) Run automated tests (pytest will use the evaluator functions):
   pytest -q

These will compute embeddings locally if `src/main/resources/pharmacy_index.jsonl` is not present, or will use precomputed embeddings if that file exists.

Run Elasticsearch in Docker (Windows)
------------------------------------
1) Prereqs: Docker Desktop (or Docker Engine) and at least 2 GB available memory (4 GB recommended).

2) Start Elasticsearch (from repo root):
   # With modern Docker
   docker compose up -d
   # or legacy command
   docker-compose up -d

   Or run the included PowerShell helper (Windows PowerShell):
   # from repo root
   powershell -ExecutionPolicy Bypass -File .\scripts\start_es.ps1 -TimeoutSeconds 180

3) Wait for the healthcheck to pass and verify cluster is responding:
   curl -s http://localhost:9200 | jq .
   curl -s http://localhost:9200/_cluster/health?pretty

4) Create the index using the provided mapping:
   curl -X PUT "http://localhost:9200/pharmacy" -H "Content-Type: application/json" -d @es/pharmacy_mapping.json

   (PowerShell alternative):
   Invoke-RestMethod -Method Put -Uri http://localhost:9200/pharmacy -InFile es/pharmacy_mapping.json -ContentType 'application/json'

5) Generate embeddings and the ES bulk file (if not done yet):
   python scripts/embed_and_export.py --input src/main/resources/pharmacy_sample.jsonl --output src/main/resources/pharmacy_index.jsonl --es-bulk --index-name pharmacy

6) Index the documents (bulk):
   curl -s -H "Content-Type: application/json" -XPOST "http://localhost:9200/_bulk" --data-binary @src/main/resources/pharmacy_index.bulk.json

   (PowerShell note: bulk indexing via Invoke-RestMethod has limitations; use curl in Git Bash or WSL for reliable behavior.)

7) Run a test query (replace query vector or use the Java controller GET /products/search?q=...):
   # Example: curl to the Java app if it's running on port 8081
   curl "http://localhost:8081/products/search?q=aspirin"

Tear down:
   docker compose down -v

Notes:
- The compose file (docker-compose.yml) disables built-in security for local development (`xpack.security.enabled=false`) so the service is reachable at http://localhost:9200 without authentication. If you prefer to enable security, set `ELASTIC_PASSWORD` in the environment and update `application.properties`.
- If you are on Windows and `curl` is the PowerShell alias, use the `Invoke-RestMethod` or run the commands in Git Bash/WSL for consistent curl behavior.
