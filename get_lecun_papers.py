import requests
import xml.etree.ElementTree as ET

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"

def search_arxiv_recent(query, max_results=5):
    params = {
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results
    }
    resp = requests.get(ARXIV_API, params=params)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    results = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        paper = {
            "id": entry.findtext(f"{ATOM_NS}id", "").split("/abs/")[-1],
            "title": " ".join(entry.findtext(f"{ATOM_NS}title", "").split()),
            "published": entry.findtext(f"{ATOM_NS}published", "")[:10],
        }
        results.append(paper)
    return results

try:
    papers = search_arxiv_recent('au:"Yann LeCun"', max_results=10)
    for p in papers:
        print(f"- [{p['id']}] {p['title']} ({p['published']})")
except Exception as e:
    print(f"Error: {e}")
