"""Small, inspectable RAG pipeline with metadata-first citations."""
import json
import os
import re
from pathlib import Path
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def load_documents(path: Path) -> List[Dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    docs = []
    for item in raw:
        required = {"doc_id", "title", "source_url", "text"}
        if not required.issubset(item):
            raise ValueError(f"Document missing required metadata: {required - set(item)}")
        docs.append({**item, "text": str(item["text"]).strip()})
    return docs

def chunk_text(text: str, chunk_size: int = 850, overlap: int = 120) -> List[str]:
    """Chunk by words, preserving a configurable overlap."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap
    return chunks

class PlantRAG:
    def __init__(self, documents: List[Dict], top_k: int = 4):
        self.documents = documents
        self.top_k = top_k
        self.chunks = []
        for doc in documents:
            for i, chunk in enumerate(chunk_text(doc["text"])):
                self.chunks.append({
                    "doc_id": doc["doc_id"], "title": doc["title"],
                    "source_url": doc["source_url"], "section": doc.get("section", "general"),
                    "chunk_id": f"{doc['doc_id']}#chunk-{i+1}", "text": chunk
                })
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        corpus = [c["text"] for c in self.chunks]
        self.matrix = self.vectorizer.fit_transform(corpus) if corpus else None

    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        if not query.strip() or self.matrix is None:
            return []
        qv = self.vectorizer.transform([query])
        scores = cosine_similarity(qv, self.matrix).ravel()
        ranked = scores.argsort()[::-1]
        results = []
        for idx in ranked:
            score = float(scores[idx])
            if score <= 0:
                continue
            item = dict(self.chunks[idx])
            item["score"] = score
            item["excerpt"] = item["text"][:900]
            results.append(item)
            if len(results) >= (top_k or self.top_k):
                break
        return results

    def answer(self, question: str, audience: str = "Deep dive") -> Dict:
        retrieved = self.retrieve(question)
        if not retrieved:
            return {"answer": "I couldn't find relevant evidence in the current plant library, so I won't guess. Try naming a plant or asking about its climate, range, uses, or research.", "sources": [], "mode": "abstain"}
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            answer = self._generate(question, retrieved, audience, api_key)
            mode = "llm_rag"
        else:
            answer = self._evidence_only(question, retrieved, audience)
            mode = "evidence_only"
        # Citations are always built from retrieved metadata, never from model-created URLs.
        sources = [{
            "doc_id": r["doc_id"], "title": r["title"], "source_url": r["source_url"],
            "section": r["section"], "score": r["score"], "excerpt": r["excerpt"]
        } for r in retrieved]
        return {"answer": answer, "sources": sources, "mode": mode}

    def _evidence_only(self, question, retrieved, audience):
        lead = ("A quick plant explorer note: " if audience == "Curious kid" else "Evidence summary: ")
        excerpts = [r["text"].strip() for r in retrieved[:2]]
        joined = " ".join(excerpts)
        if len(joined) > 1500:
            joined = joined[:1500].rsplit(" ", 1)[0] + "…"
        return lead + joined + "\n\nThis is a source excerpt, not a complete answer. Check the linked references for context."

    def _generate(self, question, retrieved, audience, api_key):
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        context = "\n\n".join(
            f"[{r['doc_id']} | {r['title']} | {r['source_url']}]\n{r['text']}"
            for r in retrieved
        )
        style = "Explain simply for a curious child, without talking down." if audience == "Curious kid" else "Give a concise scientific explanation with caveats."
        system = (
            "You are Know Your Plant, a botanical learning assistant. Answer only from the supplied context. "
            "If context is insufficient, say so and ask a useful follow-up. Distinguish native range from introduced "
            "range, traditional use from clinical evidence, and laboratory research from proven real-world effects. "
            "Never give medical treatment advice or tell users to ingest/apply a plant. Do not invent citations or URLs. "
            "Do not claim a paper is recent unless its publication date is supplied. " + style
        )
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.1,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": f"Question: {question}\n\nRetrieved evidence:\n{context}"}]
        )
        return response.choices[0].message.content.strip()
