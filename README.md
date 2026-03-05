# Academic Research Assistant — MCP Server

An MCP server that gives AI assistants direct, structured access to the **arXiv preprint API**. Instead of relying on web search summaries, the AI can search for papers, retrieve full metadata, discover related work, and compare multiple papers side by side — all using real-time arXiv data.

---

## Setup

### Prerequisites
- Python ≥ 3.10
- `uv` package manager

### Installation

```bash
# 1. Clone / navigate to the project folder
cd research-server

# 2. Create and activate virtual environment
uv venv
source .venv/bin/activate          # Mac/Linux
.venv\Scripts\activate             # Windows (cmd)
source .venv/Scripts/activate      # Windows (Git Bash)

# 3. Install dependencies
uv pip install "mcp[cli]" requests
```

### Verify it works

```bash
# Run in MCP Inspector — all 5 tools should appear
mcp dev server.py
```

---

## Gemini CLI Configuration

<img width="936" height="227" alt="image" src="https://github.com/user-attachments/assets/564378be-056e-4303-baa8-7465974bc6e3" />

### Gemini CLI

Edit `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "academic-research": {
      "command": "C:/absolute/path/to/research-server/.venv/Scripts/python.exe",
      "args": ["C:/absolute/path/to/research-server/server.py"]
    }
  }
}
```

> ⚠️ Always use **absolute paths**. On Windows, use `.venv/Scripts/python.exe` (not `bin/python`).  
> Relaunch Gemini CLI after any config change.

---

## Tools

### `search_papers`
**Description:** Search arXiv for papers by keyword or topic, with an optional category filter.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | `str` | ✅ | Search keywords or topic |
| `category` | `str` | ❌ | arXiv category (e.g. `cs.AI`, `cs.LG`, `physics.ml`). Leave empty to search all. |
| `max_results` | `int` | ❌ | Number of results to return (default: 5) |

**Example prompt:** *"Search for recent papers on transformer architectures in cs.AI"*

---

### `get_paper_details`
**Description:** Fetch full metadata and abstract for a specific paper by its arXiv ID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `arxiv_id` | `str` | ✅ | arXiv paper ID, e.g. `2301.12345` |

**Example prompt:** *"Get the details for paper 2301.12345"*

---

### `search_by_author`
**Description:** Find all papers published by a specific researcher on arXiv.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `author_name` | `str` | ✅ | Full or partial author name |
| `max_results` | `int` | ❌ | Number of results to return (default: 5) |

**Example prompt:** *"What has Yann LeCun published recently?"*

---

### `get_related_papers`
**Description:** Find papers that share the same primary category as a given paper — useful for discovering related work.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `arxiv_id` | `str` | ✅ | arXiv ID of the source paper |
| `max_results` | `int` | ❌ | Number of related papers to return (default: 5) |

**Example prompt:** *"Find papers related to 2301.12345"*

---

### `compare_papers`
**Description:** Side-by-side structured comparison of 2–3 arXiv papers, including a summary of shared categories and date range.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `arxiv_ids` | `list[str]` | ✅ | List of 2–3 arXiv IDs to compare |

**Example prompt:** *"Compare papers 2301.12345, 2302.67890, and 2303.11111"*

---

## Resources

### `arxiv://search-history`
Returns a JSON list of all search operations performed in the current session. Includes the query string, category filter, and max_results for each search. Resets when the server restarts.

```json
{
  "total_searches": 3,
  "history": [
    { "query": "RLHF", "category": "cs.AI", "max_results": 5 },
    { "query": "author:Yann LeCun", "category": "", "max_results": 5 }
  ]
}
```

---

## Limitations

- **Rate limit:** arXiv API allows max 1 request per 3 seconds. The helper handles this automatically, but complex multi-tool workflows may be slow.
- **No persistence:** Search history and all data resets when the server is restarted.
- **No full-text search:** Only metadata and abstracts are available — not the full paper content.
- **arXiv only:** The server does not search other databases (PubMed, Semantic Scholar, IEEE, etc.).

---

## Comparison Results

### With vs. Without MCP Tools

| Dimension | Without Tools | With MCP Tools |
|-----------|--------------|----------------|
| **Accuracy** | May hallucinate paper titles, authors, or dates | Real metadata pulled directly from arXiv API |
| **Specificity** | Generic summaries of a research area | Exact titles, abstracts, IDs, and PDF links |
| **Completeness** | Limited to training data knowledge cutoff | Real-time access to latest preprints |
| **Confidence** | Hedges with "I think" / "around 2023" | Cites exact arXiv IDs and publication dates |
| **Composability** | One-shot answer only | Can chain: search → details → compare |
| **Latency** | Instant (single response) | Multiple tool round-trips (3s rate limit) |

### Prompting Strategy Comparison

| Strategy | Tool Calls Triggered | Planning Behavior | Output Quality |
|----------|---------------------|-------------------|----------------|
| **Strategy 1 — Minimal** (`"You have access to tools. Use them."`) | 1–2 tools, often just `search_papers` | Dives straight in, no plan | Partial answer, misses compare step |
| **Strategy 3 — Expert Workflow** (phased system prompt) | 4–6 tools across all phases | States intent before each tool call | Full pipeline: search → details → compare → synthesis |

**Key finding:** Strategy 3 consistently triggers the full `search_papers → get_paper_details → compare_papers` pipeline, while Strategy 1 often stops after the first search.

---

## File Structure

```
research-server/
├── server.py          # MCP server — all 5 tools + resource
├── arxiv_helper.py    # arXiv API helper (rate limiting + XML parsing)
├── README.md          # This file
└── .venv/             # Virtual environment (not committed)
```

---

## Rate Limit Note

arXiv requests are automatically spaced 3 seconds apart by `arxiv_helper.py`. Do not add extra `time.sleep()` calls in your tools — the helper handles it.
