from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn

app = FastAPI(title="Embedding Service")

class EmbedRequest(BaseModel):
    text: str

class EmbedResponse(BaseModel):
    embedding: List[float]

class BatchEmbedRequest(BaseModel):
    texts: List[str]

class BatchEmbedResponse(BaseModel):
    embeddings: List[List[float]]

# Load model once on startup
model = SentenceTransformer("all-MiniLM-L6-v2")

@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="'text' must not be empty")
    emb = model.encode(req.text, normalize_embeddings=True)
    return EmbedResponse(embedding=[float(x) for x in emb.tolist()])

@app.post("/embed/batch", response_model=BatchEmbedResponse)
def embed_batch(req: BatchEmbedRequest):
    if not req.texts:
        raise HTTPException(status_code=400, detail="'texts' must be a non-empty list")
    emb = model.encode(req.texts, normalize_embeddings=True)
    return BatchEmbedResponse(embeddings=[[float(x) for x in row.tolist()] for row in emb])

if __name__ == "__main__":
    # Run with: python scripts/embed_service.py  OR
    #    uvicorn scripts.embed_service:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
