# ElasticSearch Textsearch - Local inspection

This repository contains a Spring Boot app that connects to an Elasticsearch node (configured in `src/main/resources/application.properties`).

## Where the app writes data
- The app connects to the Elasticsearch server defined by `spring.elasticsearch.uris` in `application.properties` (default: `http://localhost:9200`).
- Documents are stored in Elasticsearch indices (logical shards). The physical data lives on the Elasticsearch node(s) under the node's data path (see `elasticsearch.yml` `path.data` setting on the node).

## Useful HTTP commands (PowerShell / curl)
Replace `http://localhost:9200` with the URI configured in your `application.properties` if different.

List indices (human-readable):

```powershell
curl "http://localhost:9200/_cat/indices?v"
```

List indices as JSON (used by the app's `/products/indices` endpoint):

```powershell
curl "http://localhost:9200/_cat/indices?format=json" | ConvertFrom-Json
```

Get mappings for an index:

```powershell
curl "http://localhost:9200/<index>/_mapping?pretty"
```

Get a single document by id:

```powershell
curl "http://localhost:9200/<index>/_doc/<id>?pretty"
```

Search for documents (simple query string):

```powershell
curl "http://localhost:9200/products/_search?q=name:Widget&pretty"
```

Find node configuration (data path):

```powershell
curl "http://localhost:9200/_nodes?filter_path=**.settings.path.data" | ConvertFrom-Json
```

This will return node settings including `path.data` which points to the directory where ES stores segment files on disk.

## App endpoints added
- POST /products — save to default `products` index (existing behaviour).
- POST /products/{index} — save to a named index (creates index + mapping if missing). Index names are validated by the app (lowercase, digits, ., _, - allowed).
- GET /products/name/{name} — find by name in default index (existing repository-backed method).
- GET /products/index/{index}/name/{name} — search by name in a specific index.
- GET /products/indices — list indices visible to the configured ES node (wraps `_cat/indices?format=json`).

## Validation
The app validates dynamic index names before using them. Allowed characters: `a-z`, `0-9`, `.`, `_`, `-`. Index cannot start with `.` and max length is 255 characters.

---
If you want, I can add: index templates, custom mapping upload, or integration tests for the new endpoints.
