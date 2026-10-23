"""Ingest local .txt/.md/.pdf files into metadata-rich RAG documents.

Example:
  python ingest.py ./source_documents --output data/ingested_documents.json

Keep source attribution, title, source URL and page number when available.
Only ingest content you are permitted to store and redistribute.
"""
import argparse, json, re
from pathlib import Path
from pypdf import PdfReader

def clean(text):
    text = text.replace("\x00", " ")
    return re.sub(r"\s+", " ", text).strip()

def read_file(path: Path):
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages, 1):
            txt = clean(page.extract_text() or "")
            if txt:
                pages.append({"page": i, "text": txt})
        return pages
    if path.suffix.lower() in {".txt", ".md"}:
        return [{"page": None, "text": clean(path.read_text(encoding="utf-8", errors="ignore"))}]
    return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir", type=Path)
    ap.add_argument("--output", type=Path, default=Path("data/ingested_documents.json"))
    ap.add_argument("--base-url", default="")
    args = ap.parse_args()
    documents = []
    for path in sorted(args.input_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".pdf", ".txt", ".md"}:
            continue
        source_pages = read_file(path)
        for page_item in source_pages:
            if not page_item["text"]:
                continue
            page = page_item["page"]
            documents.append({
                "doc_id": f"local-{path.stem.lower().replace(' ', '-')}" + (f"-p{page}" if page else ""),
                "title": path.stem.replace("_", " ").title() + (f" (page {page})" if page else ""),
                "source_url": args.base_url or f"local-file:{path.name}",
                "section": "ingested_document",
                "page": page,
                "text": page_item["text"]
            })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(documents)} page/document records to {args.output}")

if __name__ == "__main__":
    main()
