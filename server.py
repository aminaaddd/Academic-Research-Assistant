from mcp.server.fastmcp import FastMCP
from arxiv_helper import search_arxiv, get_paper_by_id

mcp = FastMCP("Academic Research Assistant")

# In-memory search history for this session
search_history = []


# ── TOOL 1 ──────────────────────────────────────────────────────────────────
@mcp.tool()
def search_papers(query: str, category: str = "", max_results: int = 5) -> str:
    """Search arXiv for academic papers by keyword or topic.
    Use this when the user wants to find papers on a subject.
    Optionally filter by category (e.g. cs.AI, cs.LG, physics.ml).
    Leave category empty to search all fields."""

    full_query = f"{query} cat:{category}" if category else query

    # Track search history
    search_history.append({
        "query": query,
        "category": category,
        "max_results": max_results
    })

    try:
        papers = search_arxiv(full_query, max_results)
    except Exception as e:
        return f"Error contacting arXiv: {str(e)}"

    if not papers:
        return f"No papers found for query: '{query}'" + (f" in category: {category}" if category else "")

    results = []
    for p in papers:
        results.append(
            f"ID: {p['id']}\n"
            f"Title: {p['title']}\n"
            f"Authors: {', '.join(p['authors'][:3])}{'...' if len(p['authors']) > 3 else ''}\n"
            f"Published: {p['published']}\n"
            f"Categories: {', '.join(p['categories'])}\n"
            f"PDF: {p['pdf_url']}"
        )
    return f"Found {len(papers)} paper(s):\n\n" + "\n\n---\n\n".join(results)


# ── TOOL 2 ──────────────────────────────────────────────────────────────────
@mcp.tool()
def get_paper_details(arxiv_id: str) -> str:
    """Fetch full metadata and abstract for a specific arXiv paper by its ID.
    Use this when you have an arXiv ID (e.g. 2301.12345) and want the full
    title, authors, abstract, categories, and PDF link."""

    # Basic format validation
    if not arxiv_id or len(arxiv_id) < 5:
        return f"Invalid arXiv ID: '{arxiv_id}'. Expected format: 2301.12345"

    try:
        paper = get_paper_by_id(arxiv_id)
    except Exception as e:
        return f"Error fetching paper '{arxiv_id}': {str(e)}"

    if not paper:
        return (
            f"No paper found with ID: '{arxiv_id}'.\n"
            f"Check the ID format — it should look like: 2301.12345"
        )

    return (
        f"Title: {paper['title']}\n"
        f"Authors: {', '.join(paper['authors'])}\n"
        f"Published: {paper['published']}\n"
        f"Categories: {', '.join(paper['categories'])}\n\n"
        f"Abstract:\n{paper['abstract']}\n\n"
        f"PDF: {paper['pdf_url']}"
    )


# ── TOOL 3 ──────────────────────────────────────────────────────────────────
@mcp.tool()
def search_by_author(author_name: str, max_results: int = 5) -> str:
    """Find papers published by a specific author on arXiv.
    Use this when the user asks about a researcher's publications or
    wants to explore work by a specific person."""

    if not author_name.strip():
        return "Please provide an author name."

    # Track in search history
    search_history.append({
        "query": f"author:{author_name}",
        "category": "",
        "max_results": max_results
    })

    try:
        papers = search_arxiv(f"au:{author_name}", max_results)
    except Exception as e:
        return f"Error contacting arXiv: {str(e)}"

    if not papers:
        return f"No papers found for author: '{author_name}'. Try a different spelling or last name only."

    results = []
    for p in papers:
        results.append(
            f"- [{p['id']}] {p['title']}\n"
            f"  Authors: {', '.join(p['authors'][:3])}\n"
            f"  Published: {p['published']} | Categories: {', '.join(p['categories'])}"
        )

    return f"Papers by {author_name} ({len(papers)} found):\n\n" + "\n\n".join(results)


# ── TOOL 4 ──────────────────────────────────────────────────────────────────
@mcp.tool()
def get_related_papers(arxiv_id: str, max_results: int = 5) -> str:
    """Find papers that share the same categories as a given arXiv paper.
    Use this to discover related work after retrieving a paper's details.
    Requires a valid arXiv ID (e.g. 2301.12345)."""

    if not arxiv_id or len(arxiv_id) < 5:
        return f"Invalid arXiv ID: '{arxiv_id}'. Expected format: 2301.12345"

    try:
        paper = get_paper_by_id(arxiv_id)
    except Exception as e:
        return f"Error fetching paper '{arxiv_id}': {str(e)}"

    if not paper:
        return f"No paper found with ID: '{arxiv_id}'."

    if not paper.get("categories"):
        return f"Paper '{arxiv_id}' has no categories — cannot find related papers."

    # Use the first category to find related papers
    primary_category = paper["categories"][0]

    search_history.append({
        "query": f"related to {arxiv_id} via cat:{primary_category}",
        "category": primary_category,
        "max_results": max_results
    })

    try:
        related = search_arxiv(f"cat:{primary_category}", max_results + 1)
    except Exception as e:
        return f"Error searching related papers: {str(e)}"

    # Exclude the original paper from results
    related = [p for p in related if p["id"] != arxiv_id][:max_results]

    if not related:
        return f"No related papers found in category '{primary_category}'."

    results = []
    for p in related:
        results.append(
            f"- [{p['id']}] {p['title']}\n"
            f"  Authors: {', '.join(p['authors'][:3])}\n"
            f"  Published: {p['published']}"
        )

    return (
        f"Papers related to '{paper['title']}'\n"
        f"(Category: {primary_category}):\n\n" + "\n\n".join(results)
    )


# ── TOOL 5 ──────────────────────────────────────────────────────────────────
@mcp.tool()
def compare_papers(arxiv_ids: list[str]) -> str:
    """Compare 2 to 3 arXiv papers side by side in a structured format.
    Use this after retrieving paper details to highlight differences and
    similarities in topic, authors, date, and research focus.
    Requires a list of 2–3 valid arXiv IDs."""

    if len(arxiv_ids) < 2:
        return "Please provide at least 2 arXiv IDs to compare."
    if len(arxiv_ids) > 3:
        return "Please provide at most 3 arXiv IDs. You provided: " + str(len(arxiv_ids))

    papers = []
    for pid in arxiv_ids:
        try:
            p = get_paper_by_id(pid.strip())
        except Exception as e:
            return f"Error fetching paper '{pid}': {str(e)}"

        if not p:
            return (
                f"Could not find paper with ID: '{pid}'.\n"
                f"Make sure all IDs are valid before comparing."
            )
        papers.append(p)

    # Build structured comparison
    comparison = "=" * 60 + "\n"
    comparison += "PAPER COMPARISON\n"
    comparison += "=" * 60 + "\n\n"

    for i, p in enumerate(papers, 1):
        comparison += (
            f"Paper {i}\n"
            f"  ID:         {p['id']}\n"
            f"  Title:      {p['title']}\n"
            f"  Authors:    {', '.join(p['authors'][:4])}{'...' if len(p['authors']) > 4 else ''}\n"
            f"  Published:  {p['published']}\n"
            f"  Categories: {', '.join(p['categories'])}\n"
            f"  Abstract:   {p['abstract'][:400]}...\n"
            f"  PDF:        {p['pdf_url']}\n\n"
        )

    # Summary section
    comparison += "-" * 60 + "\n"
    comparison += "SUMMARY\n"
    comparison += "-" * 60 + "\n"
    comparison += f"Total papers compared: {len(papers)}\n"
    comparison += f"Date range: {min(p['published'] for p in papers)} → {max(p['published'] for p in papers)}\n"

    all_categories = set()
    for p in papers:
        all_categories.update(p["categories"])
    comparison += f"Shared research areas: {', '.join(sorted(all_categories))}\n"

    return comparison


# ── RESOURCE ─────────────────────────────────────────────────────────────────
@mcp.resource("arxiv://search-history")
def get_search_history() -> str:
    """Returns a JSON list of all searches performed this session.
    Includes query, category filter, and max results for each search."""
    import json
    if not search_history:
        return json.dumps({"message": "No searches performed yet.", "history": []}, indent=2)
    return json.dumps({"total_searches": len(search_history), "history": search_history}, indent=2)


# ── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()