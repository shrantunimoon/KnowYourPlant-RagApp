# Know Your Plant 🌱
**Know the plant, not just the brand.**

A recruiter-ready, educational RAG application exploring plant origins, geographic range, climate adaptations, uses, ecological relationships and research literature.

## What's included
- `app.py`: Streamlit interface with Discover, Ask Plant AI, Research Watch and How It Works tabs.
- `rag.py`: metadata-first retrieval, citation assembly, optional grounded LLM generation, and evidence-only fallback.
- `research.py`: PubMed E-utilities search for dated literature records and abstracts.
- `ingest.py`: local TXT/Markdown/PDF ingestion with page metadata.
- `evaluate.py`: Recall@k, MRR, URL validity and abstention checks on a small golden test set.
- `tests/`: unit tests for chunking, metadata and abstention.
- `data/plant_knowledge.json`: starter curated knowledge base.
- `data/eval_cases.json`: initial test questions.

## Run locally
Python 3.10 or 3.11 recommended.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

The app works without an LLM key. It uses TF-IDF retrieval and returns clearly labelled source excerpts. To enable answer synthesis, set `OPENAI_API_KEY` in your environment or Streamlit secrets. Never commit keys.

Example `.streamlit/secrets.toml` (do not commit this file):
```toml
OPENAI_API_KEY = "your-key"
OPENAI_MODEL = "gpt-4o-mini"
```

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository and push this folder (excluding `.venv`, keys, and private documents).
2. Go to https://share.streamlit.io/ and connect GitHub.
3. Choose the repository, branch, and `app.py` as the main file.
4. Under app settings, add `OPENAI_API_KEY` only if you want generated answers; otherwise leave it unset.
5. Deploy and test from a private/incognito browser window.
6. Test research search, source links, empty queries, unsupported questions, and error states.

For container deployment:
```bash
docker build -t know-your-plant .
docker run -p 8501:8501 know-your-plant
```

## Data and RAG design
1. **Ingest** sources and preserve title, URL, document ID, section and page where available.
2. **Chunk** by word count with overlap to reduce boundary loss.
3. **Retrieve** with a transparent TF-IDF baseline. This is intentionally simple and reproducible; compare it with dense embeddings and hybrid search before making quality claims.
4. **Generate** only from retrieved context when an API key is configured. Low temperature and explicit instructions reduce, but do not eliminate, unsupported claims.
5. **Cite** from retrieved metadata in application code. The model is not permitted to invent URLs.
6. **Abstain** when no useful retrieval evidence is found.
7. **Evaluate** retrieval and generation separately.

## Source strategy
- **Kew Plants of the World Online (POWO):** taxonomy, accepted names, distribution, descriptions and plant uses: https://powo.science.kew.org/
- **GBIF:** occurrence records and biodiversity data: https://www.gbif.org/ and https://techdocs.gbif.org/en/openapi/
- **PubMed / NCBI E-utilities:** research literature discovery: https://www.ncbi.nlm.nih.gov/home/develop/api/
- **Local documents:** use only content you have permission to ingest and redistribute.

Important distinctions:
- GBIF occurrences are observations, not a complete native-range map.
- “Native”, “introduced”, “cultivated” and “naturalized” should not be conflated.
- Traditional use, in-vitro findings, animal studies, clinical evidence and proven treatment are different evidence levels.
- PubMed search results may include studies with conflicting results; the presence of a paper is not proof of a claim.
- This starter dataset is illustrative. Before public use, expand it with reviewed, source-verified documents and record source access dates/licences.

## Evaluation strategy
Run:
```bash
python evaluate.py
pytest -q
```

Track:
- **Retrieval:** Recall@k, MRR, nDCG, source coverage and latency.
- **Generation:** factual correctness, faithfulness to retrieved passages, completeness and calibrated uncertainty.
- **Citations:** citation URL resolves, document exists, cited passage supports the claim, and page/section is correct.
- **Safety:** medical misinformation, toxic plant safety, unsafe ingestion/application advice and overconfident health claims.
- **Kid/adult UX:** age-appropriate reading level, concept understanding, readability and task completion.
- **Operational:** latency, API failures, cost per question, uptime and source refresh failures.

A recommended launch gate is zero critical safety failures in the reviewed test set, all displayed citations resolving to real source records, and domain review of high-impact botanical/health claims. Do not treat the small starter test set as statistical proof.

## Suggested next iteration
- Add source adapters for Kew/POWO and GBIF according to their terms and API availability.
- Add a hybrid dense + lexical retriever, reranker and query rewriting.
- Use an annotated expert-reviewed evaluation set with answerable/unanswerable questions.
- Add document versioning, source dates, licence metadata, ingestion logs and automated broken-link checks.
- Add user feedback and a process for correcting plant facts.

## Limitations
This is a functional starter implementation, not a verified comprehensive botanical database. The default retriever is lexical TF-IDF, not a vector database. It does not identify plants from photos. The app is educational and not a medical or toxicology authority.
