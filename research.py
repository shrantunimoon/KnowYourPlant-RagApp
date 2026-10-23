"""PubMed literature discovery via NCBI E-utilities."""
import requests
import xml.etree.ElementTree as ET

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
HEADERS = {"User-Agent": "KnowYourPlantEducationalPrototype/1.0 (contact: configure-your-email)"}

def search_pubmed(term: str, limit: int = 8):
    session = requests.Session()
    session.headers.update(HEADERS)
    search = session.get(BASE + "esearch.fcgi", params={
        "db": "pubmed", "term": term, "retmax": min(max(int(limit), 1), 20),
        "sort": "date", "retmode": "json"
    }, timeout=20)
    search.raise_for_status()
    ids = search.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    fetch = session.get(BASE + "efetch.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "xml"
    }, timeout=30)
    fetch.raise_for_status()
    root = ET.fromstring(fetch.text)
    output = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID", default="")
        title_el = article.find(".//ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else "Untitled article"
        abstract_parts = []
        for el in article.findall(".//Abstract/AbstractText"):
            label = el.attrib.get("Label")
            text = "".join(el.itertext()).strip()
            abstract_parts.append((f"{label}: " if label else "") + text)
        year = article.findtext(".//PubDate/Year", default="")
        if not year:
            medline = article.findtext(".//PubDate/MedlineDate", default="")
            year = medline[:4] if medline else "Year unavailable"
        output.append({
            "pmid": pmid, "title": title, "year": year,
            "abstract": " ".join(abstract_parts)[:2500] or "No abstract available.",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        })
    return output
