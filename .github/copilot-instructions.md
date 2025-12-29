# Aletheia AI Coding Instructions

**Project**: Health article credibility analysis tool (Chrome extension + Flask backend)

## Architecture Overview

**Aletheia** analyzes health/medical articles to uncover funding sources, conflicts of interest, and compare coverage with counter-perspectives.

### Component Breakdown

1. **Chrome Extension** (`extension/`) - UI layer

   - `manifest.json`: Declares extension permissions (activeTab, sidePanel)
   - `background.js`: Opens sidebar, extracts URL/title from clicked article
   - `sidebar/sidebar.js`: Calls `/analyze` API, displays credibility scores + funding
   - `sidebar/sidebar.html/css`: Renders results UI

2. **Flask Backend** (`backend/app.py`) - Analysis engine

   - `/analyze` endpoint: orchestrates 4-step analysis workflow
   - Caches publication profiles in `data/publications.json`
   - Integrates with: OpenAI, Tavily (search), BeautifulSoup (scraping)

3. **Publication Researcher** (`backend/services/publication_researcher.py`)

   - Hybrid research: web search (Tavily) + about page scraping + AI analysis
   - AI prompt extracts structured JSON with credibility_score (0-10 scale)
   - **Scoring logic**: Funding transparency & primary source links matter MORE than author credentials

4. **Data Files**
   - `data/publications.json`: Cache of researched domains (avoid re-research)
   - `data/myths.json`: Common health myths to detect in article titles

## Critical Data Flows

**Main Analysis Workflow** (in `@app.route('/analyze')` order):

1. Extract domain from URL
2. Lookup/research main publication → get credibility_score
3. Scan article title against myth keywords
4. Search for counter-perspective using 3 query strategies
5. Generate comparative analysis (credibility gap, red/green flags)
6. Return missing context items (max 5)

**Credibility Scoring** (see `calculate_promise_score` heuristics):

- Cache lookup first (skip research if complete)
- Domain whitelists: NIH/CDC/Nature (+2-3), Mayo Clinic (+2)
- Red flags: Commercial domains, blogs (-2), known misinformation (0)
- Content signals: "peer-reviewed", "clinical trial" (+1.5)
- Negative signals: "secret", "doctors hate", "miracle" (-2)

**Counter-Perspective Search** (`find_counter_perspective`):

- Try 3 different search queries to find alternatives
- Only analyze candidates with promise_score ≥ 4
- Stop early if candidate ≥ 7 (high quality)
- Return None if no counter-source outperforms main source

## Key Development Patterns

### Publication Data Structure

Every cached publication object must include:

```python
{
  "name": "Publication Name",
  "domain": "example.com",
  "credibility_score": 5.5,
  "funding_sources": ["Advertising", "Independent"],
  "conflicts_of_interest": ["Owned by pharma X"],
  "red_flags": [],
  "green_flags": []
}
```

Use `is_publication_complete()` to validate before caching.

### Error Handling

- Web search failures: catch, log, continue to next query (don't break flow)
- About page scraping: try 6 URL patterns; fallback to "not accessible"
- AI analysis: validate JSON response structure before returning

### External APIs

- **OpenAI**: Structured prompt for publication analysis (see publication_researcher.py line ~130)
- **Tavily**: Multi-query search with `max_results=3`, `search_depth="basic"`
- **Requests/BeautifulSoup**: Scrape about pages with Mozilla UA header, 5s timeout

## Project-Specific Conventions

1. **Emoji logging**: Use ✅🔍⚠️🚫📊 for status tracking (helps debugging)
2. **Print statements**: Extensive console logging with timestamps/steps (no logging.py)
3. **File I/O**: Update `publications.json` after each new research via `json.dump()`
4. **Credibility gaps**: If counter_score > main_score + 3, flag as warning
5. **Domain extraction**: Use `urlparse().netloc.replace('www.', '')` pattern
6. **Myth detection**: Simple substring match on lowercase title against keyword lists

## Common Tasks

### Add a new publication whitelist domain

In `calculate_promise_score()`, add to existing lists:

```python
if any(x in domain_lower for x in ['newdomain.org', ...]):
    score += 2
```

### Update credibility scoring weights

Modify heuristics in `calculate_promise_score()` or AI prompt in `publication_researcher.py`

### Add new myth keywords

Update `data/myths.json` format: `{"keywords": ["phrase1", "phrase2"]}`

### Extend counter-perspective search

Modify `search_queries` list in `find_counter_perspective()` or adjust `promise_score` cutoff threshold

## Environment Setup

**Dependencies** (see `requirements.txt`):

- Flask 3.0.0, CORS support
- OpenAI 1.54.0, Tavily Python client
- BeautifulSoup4 for scraping
- python-dotenv for API key loading

**Required env vars** (`.env`):

- `OPENAI_API_KEY`
- `TAVILY_API_KEY`

**Backend startup**: `python app.py` (runs on port 5000, CORS enabled)

**Extension testing**: Load `extension/` as unpacked extension in Chrome dev mode

---

_Last updated: 2025-12-28. For questions on architecture, see inline comments in `app.py` Step 1-4 workflow._
