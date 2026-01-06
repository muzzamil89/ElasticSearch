# ElasticSearch Vector Search - Pharmacy Textsearch Bot

A production-ready hybrid vector + lexical search system built with Spring Boot, Elasticsearch, and sentence-transformers. Uses a curated pharmacy dataset to demonstrate semantic and keyword-based retrieval combined with BM25 scoring.

## Project Overview

This repository implements a **bot-based text search algorithm** that leverages vector space embeddings for semantic search combined with Elasticsearch's powerful BM25 lexical ranking. The system is designed to identify relevant pharmaceutical products based on user queries by:

1. **Semantic Search**: Using dense vector embeddings (all-MiniLM-L6-v2 model) to capture semantic meaning
2. **Lexical Search**: BM25 token-based matching for exact keyword hits
3. **Hybrid Ranking**: Script-score queries combining both signals: `cosineSimilarity + 0.01 * BM25_score`

**Target Use Case**: Pharmacy product search—helping users find medications by symptoms, dosage, category, or generic/brand names.

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | Spring Boot | 3.x |
| **Search Engine** | Elasticsearch | 8.8.2 |
| **Embedding Model** | sentence-transformers (all-MiniLM-L6-v2) | 2.1+ |
| **Deep Learning** | PyTorch, transformers | 1.12+, 4.30+ |
| **Embedding API** | FastAPI + Uvicorn | 0.128+, 0.40+ |
| **Testing** | JUnit 5, pytest | 5.x, 7.x |
| **Containerization** | Docker & Docker Compose | 24.x |
| **CI/CD** | GitHub Actions | — |

## Architecture

### System Diagram
```
┌────────────────────────────────────────────────────────────────┐
│                    Spring Boot App (Port 8081)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ElasticController                                       │  │
│  │  GET /products/search?q=<query>                          │  │
│  │  └─> Call Embedding Service → Post Script-Score Query   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                           │
                           ├─> FastAPI Embedding Service (Port 8000)
                           │   POST /embed
                           │   └─> all-MiniLM-L6-v2 (PyTorch)
                           │
                           └─> Elasticsearch (Port 9200)
                               Index: "pharmacy"
                               Mapping:
                                 - name: text
                                 - description: text
                                 - category: keyword
                                 - dose: text
                                 - embedding: dense_vector (dims=384)
                               Query Type: script_score(multi_match + cosineSimilarity)
```

### Data Flow
1. **Indexing Pipeline**:
   - Source: `src/main/resources/pharmacy_sample.jsonl` (25 synthetic products, ~1000 words)
   - Script: `scripts/embed_and_export.py` computes embeddings using sentence-transformers
   - Output: `pharmacy_index.jsonl` + `pharmacy_index.bulk.json` (ES bulk format)
   - Bulk indexing into Elasticsearch with vectors

2. **Query Pipeline**:
   - User sends query: `GET /products/search?q=aspirin for headache`
   - Spring controller extracts query, calls FastAPI `/embed` endpoint
   - FastAPI returns normalized embedding vector
   - Controller constructs Elasticsearch script_score query
   - Results ranked by `cosineSimilarity(embedding, query_vector) + 0.01 * BM25_score`

3. **Evaluation & Testing**:
   - Local evaluator (`scripts/evaluate_and_test.py`) ranks docs using hybrid scoring
   - Pytest suite validates retrieval on sample queries (Recall@1, Recall@3)
   - GitHub Actions runs Java + Python tests in CI with Elasticsearch service container

## Quick Start

### Prerequisites
- **Docker & Docker Compose** (for Elasticsearch)
- **Java 17+** (Maven wrapper included)
- **Python 3.10+** with pip
- **4GB RAM** (Docker + model + torch)

### 1. Start Elasticsearch
```powershell
# Option A: PowerShell helper (Windows)
powershell -ExecutionPolicy Bypass -File .\scripts\start_es.ps1 -TimeoutSeconds 180

# Option B: Docker Compose directly
docker compose up -d
```

Wait for health check: `curl http://localhost:9200/_cluster/health` → `"status":"green"`

### 2. Create Index & Bulk Index Data
```powershell
# Create index with mapping (dense_vector dims=384)
Invoke-RestMethod -Method Put -Uri 'http://localhost:9200/pharmacy' `
  -ContentType 'application/json' `
  -Body (Get-Content -Raw -Path .\es\pharmacy_mapping.json)

# Generate embeddings and bulk file
python scripts/embed_and_export.py `
  --input src/main/resources/pharmacy_sample.jsonl `
  --output src/main/resources/pharmacy_index.jsonl `
  --es-bulk --index-name pharmacy

# Bulk index (all 25 products)
Invoke-RestMethod -Method Post -Uri 'http://localhost:9200/_bulk' `
  -ContentType 'application/x-ndjson' `
  -Body (Get-Content -Raw -Path .\src\main\resources\pharmacy_index.bulk.json)
```

### 3. Start Embedding Service (Optional for local testing)
```bash
uvicorn scripts.embed_service:app --port 8000
```

Verify: `curl http://localhost:8000/docs` (interactive API)

### 4. Run Java Spring Boot App
```bash
# Option A: run directly (default port 8081)
mvn spring-boot:run
# Server: http://localhost:8081

# Option B: build fat JAR and run on an alternate port (useful if 8081 is occupied)
mvn -DskipTests package
java -Dserver.port=8082 -jar target/textsearch-0.0.1-SNAPSHOT.jar
# Server (example): http://localhost:8082
```

### 5. Test Search Endpoint
```powershell
# Search for aspirin (adjust host/port if you ran on 8082)
# Default (if mvn spring-boot:run):
curl "http://localhost:8081/products/search?q=aspirin%20for%20pain"
# If you started the JAR on 8082:
curl "http://localhost:8082/products/search?q=aspirin%20for%20pain"

# Response: JSON with top products ranked by semantic + lexical relevance
```

---

### Final Verified Run (what we executed locally)
Followed these exact commands during validation — these steps are known to work on a typical dev machine.

1. **Start Elasticsearch (PowerShell helper)**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_es.ps1 -TimeoutSeconds 180
```

2. **Create index with mapping (skip if index already exists)**
```powershell
Invoke-RestMethod -Method Put -Uri 'http://localhost:9200/pharmacy' `
  -ContentType 'application/json' `
  -Body (Get-Content -Raw -Path .\es\pharmacy_mapping.json)
```

3. **Generate embeddings and bulk file**
```bash
python scripts/embed_and_export.py \
  --input src/main/resources/pharmacy_sample.jsonl \
  --output src/main/resources/pharmacy_index.jsonl \
  --es-bulk --index-name pharmacy
```

4. **Bulk index the generated data**
```powershell
Invoke-RestMethod -Method Post -Uri 'http://localhost:9200/_bulk' `
  -ContentType 'application/x-ndjson' `
  -Body (Get-Content -Raw -Path .\src\main\resources\pharmacy_index.bulk.json)
```

5. **Start embedding service (FastAPI)**
```bash
uvicorn scripts.embed_service:app --port 8000
# Embedding endpoint: http://localhost:8000/embed
```

6. **Start Spring Boot (example: alternate port 8082)**
```bash
mvn -DskipTests package
java -Dserver.port=8082 -jar target/textsearch-0.0.1-SNAPSHOT.jar
```

7. **Query the search endpoint and inspect top-5 results**
```powershell
curl "http://localhost:8082/products/search?q=aspirin%20for%20pain"
```

Sample top-5 output (id — score — name):
```
- p001 — 0.7487 — Aspirin 500 mg
- p017 — 0.5244 — Co-codamol 8/500
- p021 — 0.5224 — Naproxen 250 mg
- p009 — 0.4852 — Ibuprofen 200 mg
- p002 — 0.4792 — Paracetamol 500 mg
```

> Note: If a port is occupied (e.g., `8081`), run the JAR with `-Dserver.port=<port>` as shown above. If the index already exists, skip the create-index step and proceed to bulk indexing.

---


## Evaluation & Testing

### Run Python Evaluator (Dry-Run)
Computes Recall@1 and Recall@3 on 4 sample queries:
```bash
python scripts/evaluate_and_test.py
```

**Expected Output**:
```
Query: aspirin 500 mg pain
Top results:
  p001 (Aspirin 500 mg): score=...
  ...
Recall@1: 4/4 = 1.00
Recall@3: 4/4 = 1.00
```

### Run Unit Tests
```bash
# Java tests (requires Elasticsearch running)
mvn test

# Python tests (pytest)
pytest tests/test_search.py -v
```

### Run CI (GitHub Actions)
Push to a branch → GitHub Actions automatically:
1. Starts Elasticsearch 8.8.2 service container
2. Installs Maven & Python dependencies
3. Runs `mvn test` + `pytest`
4. Reports coverage

## API Reference

### Spring Boot Endpoints

#### Search (Hybrid Vector + Lexical)
```
GET /products/search?q=<query>&index=<index_name>
```
- **Parameters**:
  - `q` (required): Search query (e.g., "aspirin for headache")
  - `index` (optional, default: "pharmacy"): ES index to search
- **Returns**: JSON array of products ranked by hybrid score
- **Example**:
  ```bash
  curl "http://localhost:8081/products/search?q=antibiotic%20infection"
  ```

#### Legacy Endpoints
- `GET /products/name/{name}` — Find product by name (text search, no vectors)
- `POST /products` — Create product in default index
- `POST /products/{index}` — Create product in named index
- `GET /products/indices` — List all indices on ES node

### FastAPI Embedding Service (Port 8000)

#### Single Embedding
```
POST /embed
Content-Type: application/json
Body: {"text": "aspirin 500mg"}
```
Returns: `{"embedding": [float, float, ...]}`  (384 dimensions, normalized)

#### Batch Embeddings
```
POST /embed/batch
Content-Type: application/json
Body: {"texts": ["text1", "text2", ...]}
```
Returns: `{"embeddings": [[...], [...], ...]}`

## Dataset

### Pharmacy Sample (`src/main/resources/pharmacy_sample.jsonl`)
- **Size**: 25 products, ~1000 words total
- **Fields**: id, name, description, category, dose, embedding
- **Categories**: Analgesic, Antibiotic, Antihistamine, Antacid, Cough Suppressant, etc.

**Sample Product**:
```json
{
  "id": "p001",
  "name": "Aspirin 500 mg",
  "description": "Analgesic for mild pain and fever. Generic aspirin tablets.",
  "category": "Analgesic",
  "dose": "500 mg",
  "embedding": [-0.0178, 0.0326, ...]
}
```

## Configuration

### Elasticsearch (`application.properties`)
```properties
spring.elasticsearch.uris=http://localhost:9200
spring.elasticsearch.username=elastic  # default: no auth in dev mode
spring.elasticsearch.password=password
```

### Embedding Model
- **Model**: `all-MiniLM-L6-v2` (384-dim, 22M params, ~60 MB)
- **Normalized**: Yes (L2 norm = 1.0)
- **Fine-tuning**: Not required for MVP; pre-trained on 215M query-passage pairs

### Hybrid Query Scoring
```
score = cosineSimilarity(query_embedding, doc_embedding) + 0.01 * BM25_score
```
Weights can be tuned in [ElasticController.java](src/main/java/com/elastic/textsearch/controller/ElasticController.java)

## Project Files

```
ElasticSearch/
├── src/
│   ├── main/
│   │   ├── java/com/elastic/textsearch/
│   │   │   ├── TextsearchApplication.java        # Spring Boot entry point
│   │   │   ├── controller/ElasticController.java # REST endpoints + hybrid search
│   │   │   ├── entity/Product.java               # JPA entity
│   │   │   └── repository/ProductRepository.java # Spring Data Elasticsearch
│   │   └── resources/
│   │       ├── application.properties            # Config (ES URI, port)
│   │       ├── pharmacy_sample.jsonl             # Source dataset (25 products)
│   │       ├── pharmacy_index.jsonl              # With computed embeddings
│   │       └── pharmacy_index.bulk.json          # Bulk import format
│   └── test/
│       └── java/com/elastic/textsearch/
│           └── TextsearchApplicationTests.java  # Integration tests
├── scripts/
│   ├── embed_and_export.py                      # Embedding + bulk file generation
│   ├── embed_service.py                         # FastAPI embedding microservice
│   ├── evaluate_and_test.py                     # Dry-run evaluator (Recall@1/3)
│   └── start_es.ps1                             # PowerShell helper to start ES
├── es/
│   ├── pharmacy_mapping.json                    # ES index mapping (dense_vector)
│   └── USAGE.md                                 # Detailed ES setup guide
├── tests/
│   └── test_search.py                           # Pytest unit tests
├── docker-compose.yml                           # Elasticsearch single-node config
├── .github/workflows/
│   └── ci.yml                                   # GitHub Actions CI pipeline
├── requirements.txt                             # Python dependencies
├── pom.xml                                      # Maven config
├── mvnw / mvnw.cmd                              # Maven wrapper
└── README.md                                    # This file
```

## Development Workflow

### 1. Add New Products
Edit `src/main/resources/pharmacy_sample.jsonl` → re-run embed pipeline → bulk index

### 2. Tune Hybrid Score
Edit weights in [ElasticController.semanticSearch()](src/main/java/com/elastic/textsearch/controller/ElasticController.java):
```java
"cosineSimilarity(params.query_vector, 'embedding') + 0.01 * _score"
                                               ↑ tune this weight
```

### 3. Evaluate on New Queries
Add queries to `TEST_QUERIES` in `scripts/evaluate_and_test.py`, run evaluator

### 4. Fine-tune Embedding Model
Download a stronger model (e.g., `all-mpnet-base-v2`) → update `MODEL_NAME` in scripts

## Troubleshooting

### Elasticsearch Connection Refused
```
Error: java.net.ConnectException: Connection refused
```
**Solution**: Start Elasticsearch first
```powershell
docker compose up -d
```

### Port Already in Use (9200 / 8081 / 8000)
```
Error: Bind address already in use
```
**Solutions**:
- Stop Docker container: `docker compose down`
- Kill process on port: `netstat -ano | findstr :9200` → `taskkill /PID <PID>`
- Change port in `application.properties` or `docker-compose.yml`

### Model Download Slow
First run of embedding service downloads ~60MB model. Use a faster internet or pre-cache:
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Tests Fail with "No Mapping for Method"
Ensure Spring Data Elasticsearch repository matches field names in ES mapping exactly.

## Performance Notes

- **Index Size**: 25 products = ~1 MB (uncompressed)
- **Query Latency**: ~100-200ms (ES + embedding service round-trip)
- **Memory**: ~2GB Docker + ~1.5GB PyTorch model + buffer
- **Model Inference**: ~10ms per query (GPU optional, CPU fine for MVP)

## Next Steps / Roadmap

- [ ] Fine-tune embedding model on pharmacy-specific data
- [ ] Add MRR / nDCG evaluation metrics
- [ ] Implement user feedback loop (relevance labels)
- [ ] Add caching layer (Redis) for popular queries
- [ ] Expand dataset to 10K+ products
- [ ] Deploy to cloud (AWS, GCP, Azure)
- [ ] Add admin UI for index management & re-indexing

## Testing & CI/CD

All tests run in GitHub Actions:
- **Java**: Spring Boot integration tests (creates test index, inserts products, asserts retrieval)
- **Python**: Pytest with sample queries (Recall@1, Recall@3 > 80%)
- **Workflow**: [.github/workflows/ci.yml](.github/workflows/ci.yml)

## License

MIT License — feel free to use and modify for your projects.

## References

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- [sentence-transformers](https://www.sbert.net/)
- [Spring Data Elasticsearch](https://spring.io/projects/spring-data-elasticsearch)
- [FastAPI](https://fastapi.tiangolo.com/)

---

**Author**: Developed as a hybrid vector + lexical search proof-of-concept for pharmacy product discovery.
**Last Updated**: January 2, 2026
