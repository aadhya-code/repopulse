import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from app.search import build_index, search
from app.risk_model import score_all

app = FastAPI(
    title="RepoPulse AI Service",
    description="LangChain/Hugging Face semantic search + PR risk scoring for RepoPulse.",
)

NODE_SERVICE_URL = os.getenv("NODE_SERVICE_URL", "http://node-service:4000")


class IndexRequest(BaseModel):
    repo: str  # "owner/name"


class SearchRequest(BaseModel):
    repo: str
    query: str
    k: int = 5


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/index")
def index_repo(req: IndexRequest):
    """Build/refresh the semantic search index for a repo from stored commits."""
    count = build_index(req.repo)
    if count == 0:
        raise HTTPException(
            status_code=404,
            detail="No commits found for this repo. Ingest it via the Node service first.",
        )
    return {"repo": req.repo, "commitsIndexed": count}


@app.post("/search")
def search_repo(req: SearchRequest):
    """Semantic search over a repo's commit history."""
    results = search(req.repo, req.query, k=req.k)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="No index found for this repo. Call /index first.",
        )
    return {"repo": req.repo, "query": req.query, "results": results}


@app.post("/risk/{owner}/{repo}")
async def score_repo_risk(owner: str, repo: str):
    """
    Train the risk classifier on this repo's PRs, score every PR, and
    write the scores back to MongoDB via the Node service's PATCH endpoint.
    """
    full_repo = f"{owner}/{repo}"
    scores = score_all(full_repo)
    if not scores:
        raise HTTPException(
            status_code=404,
            detail="Not enough PR data to train a risk model yet (need at least ~10 PRs).",
        )

    async with httpx.AsyncClient() as client:
        for item in scores:
            url = f"{NODE_SERVICE_URL}/repos/{owner}/{repo}/pulls/{item['number']}/risk"
            await client.patch(url, json={"riskScore": item["riskScore"]})

    return {"repo": full_repo, "scored": len(scores)}
