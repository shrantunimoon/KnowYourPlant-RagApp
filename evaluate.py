"""Small repeatable RAG evaluation harness.

The included set is a starter test set, not a scientific benchmark.
Expand it with reviewed expected evidence and domain-expert judgments.
"""
import json
from pathlib import Path
from rag import PlantRAG, load_documents

ROOT = Path(__file__).parent
docs = load_documents(ROOT / "data" / "plant_knowledge.json")
rag = PlantRAG(docs, top_k=4)
cases = json.loads((ROOT / "data" / "eval_cases.json").read_text(encoding="utf-8"))

def recall_at_k(retrieved_ids, relevant_ids):
    relevant = set(relevant_ids)
    return len(set(retrieved_ids) & relevant) / len(relevant) if relevant else None

def reciprocal_rank(retrieved_ids, relevant_ids):
    relevant = set(relevant_ids)
    for rank, doc_id in enumerate(retrieved_ids, 1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0 if relevant else None

rows = []
for case in cases:
    hits = rag.retrieve(case["question"], top_k=4)
    ids = [h["doc_id"] for h in hits]
    answer = rag.answer(case["question"])
    rows.append({
        "id": case["id"],
        "recall_at_4": recall_at_k(ids, case["relevant_doc_ids"]),
        "mrr": reciprocal_rank(ids, case["relevant_doc_ids"]),
        "citation_urls_valid": all(s["source_url"].startswith(("https://", "http://", "local-file:")) for s in answer["sources"]),
        "abstain_expected": case.get("expect_abstain", False),
        "abstained": answer["mode"] == "abstain",
        "retrieved_doc_ids": ids
    })
print(json.dumps(rows, indent=2))
valid = [r for r in rows if r["recall_at_4"] is not None]
if valid:
    print(f"\nMean Recall@4: {sum(r['recall_at_4'] for r in valid)/len(valid):.3f}")
    print(f"Mean reciprocal rank: {sum(r['mrr'] for r in valid)/len(valid):.3f}")
print("\nManual review is still required for answer correctness, citation support, child suitability and safety.")
