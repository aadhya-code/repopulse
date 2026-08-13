"""
Semantic search over a repo's commit history.

Pipeline:
  1. Pull commit messages from MongoDB (populated by the Node service).
  2. Embed them with a local Hugging Face sentence-transformer model
     (no external API key required for embeddings).
  3. Index the embeddings in a LangChain FAISS vector store.
  4. Answer natural-language questions by retrieving the most relevant
     commits ("what changed in the auth module last week?").

This module deliberately keeps the LLM-generation step swappable: by
default it returns the retrieved commits directly (no generation API key
needed), but if LLM_API_KEY is set it can be wired to a LangChain
RetrievalQA chain for a generated natural-language answer instead of a
raw list of matches.
"""

from typing import List, Dict
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

from app.db import commits_collection

_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_embeddings = HuggingFaceEmbeddings(model_name=_EMBEDDING_MODEL)

# Simple in-memory cache: one FAISS index per repo, rebuilt on ingest.
_indexes: Dict[str, FAISS] = {}


def build_index(repo: str) -> int:
    """(Re)build the vector index for a repo from its stored commits."""
    docs: List[Document] = []
    for c in commits_collection.find({"repo": repo}):
        message = c.get("message", "").strip()
        if not message:
            continue
        docs.append(
            Document(
                page_content=message,
                metadata={
                    "sha": c.get("sha"),
                    "author": c.get("author"),
                    "committedAt": str(c.get("committedAt")),
                },
            )
        )

    if not docs:
        return 0

    _indexes[repo] = FAISS.from_documents(docs, _embeddings)
    return len(docs)


def search(repo: str, query: str, k: int = 5) -> List[Dict]:
    """Return the top-k commits most semantically similar to the query."""
    index = _indexes.get(repo)
    if index is None:
        build_index(repo)
        index = _indexes.get(repo)

    if index is None:
        return []

    results = index.similarity_search_with_score(query, k=k)
    return [
        {
            "message": doc.page_content,
            "sha": doc.metadata.get("sha"),
            "author": doc.metadata.get("author"),
            "committedAt": doc.metadata.get("committedAt"),
            "score": float(score),
        }
        for doc, score in results
    ]
