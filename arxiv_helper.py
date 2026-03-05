"""arXiv API helper — handles HTTP requests and XML parsing."""
import time
import requests
import xml.etree.ElementTree as ET

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
_last_request_time = 0


def _rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 3:
        time.sleep(3 - elapsed)
    _last_request_time = time.time()


def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    """Search arXiv. Returns list of dicts:
    id, title, authors, abstract, published, categories, pdf_url"""
    _rate_limit()
    params = {"search_query": query, "start": 0, "max_results": max_results}
    resp = requests.get(ARXIV_API, params=params, timeout=15)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    results = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        paper = {
            "id": entry.findtext(f"{ATOM_NS}id", "").split("/abs/")[-1],
            "title": " ".join(entry.findtext(f"{ATOM_NS}title", "").split()),
            "authors": [a.findtext(f"{ATOM_NS}name", "")
                        for a in entry.findall(f"{ATOM_NS}author")],
            "abstract": " ".join(entry.findtext(f"{ATOM_NS}summary", "").split()),
            "published": entry.findtext(f"{ATOM_NS}published", "")[:10],
            "categories": [c.get("term", "")
                           for c in entry.findall(f"{ATOM_NS}category")],
            "pdf_url": "",
        }
        for link in entry.findall(f"{ATOM_NS}link"):
            if link.get("title") == "pdf":
                paper["pdf_url"] = link.get("href", "")
        results.append(paper)
    return results


def get_paper_by_id(arxiv_id: str) -> dict | None:
    """Fetch a single paper by its arXiv ID (e.g. '2210.03629').
    Returns a dict with the same keys as search_arxiv, or None."""
    results = search_arxiv(f"id:{arxiv_id}", max_results=1)
    return results[0] if results else None
