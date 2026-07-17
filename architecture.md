# SecondSelf — System Architecture

> **How we build the project.** Derived from [`problemstatement.md`](./problemstatement.md).

---

## 1. Architecture Overview

SecondSelf is a **file-based, pipeline-oriented personal knowledge system**. There is no database in v1 — the filesystem is the source of truth. Each pipeline stage reads from one folder, transforms data, and writes to the next.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SecondSelf — End-to-End Flow                      │
└─────────────────────────────────────────────────────────────────────────────┘

  User Input                    Processing Pipelines                    Output
  ──────────                    ───────────────────                    ──────

  note ──┐
  link ──┼──► capture.py ──► raw/ ──► classify.py ──► wiki/ ──► build_graph.py
  file ──┘         │                        │              │            │
                   │                        └──► link.py ──┘            │
                   │                             (embeddings)           ▼
                   │                                              graph.json
                   │                                                    │
                   │                                                    ▼
                   └──────────────────────────────────────► app.py (Streamlit)
                                                              ├── Graph UI
                                                              └── ask.py (RAG Q&A)
                                                                        │
                                                                        ▼
                                                              Public URL (deployed)
```

### Design Principles

| Principle | Decision |
|-----------|----------|
| **Filesystem as database** | `raw/` and `wiki/` are plain files — easy to inspect, version, and debug |
| **Pipeline stages are independent scripts** | Each week ships a working module; stages compose but don't tightly couple |
| **Local-first, free-tier AI** | Embeddings run locally (`sentence-transformers`); LLM calls use free Groq API |
| **Markdown as the wiki format** | Human-readable notes with YAML frontmatter for metadata |
| **JSON as the graph interchange** | `graph.json` decouples graph generation from rendering |
| **Single deployable app** | Streamlit bundles graph + search into one public-facing product |

---

## 2. Technology Stack

### Core

| Layer | Technology | Role |
|-------|-----------|------|
| Language | Python 3.10+ | All pipeline scripts and Streamlit app |
| Capture CLI | `argparse` / `click` | One-command capture interface |
| Storage | Local filesystem (`raw/`, `wiki/`) | Persistent data store |
| Wiki format | Markdown + YAML frontmatter | Structured, readable notes |
| Classification LLM | Groq API + Llama 3 | PARA categorization, tags, summaries |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | Local, free semantic similarity |
| Similarity | `numpy` / `scikit-learn` cosine similarity | Auto-linking threshold checks |
| Graph export | Python `json` module | `graph.json` nodes/edges |
| Graph rendering | `vis-network` (via Streamlit `components.html`) | Interactive force-directed graph |
| RAG Q&A | Embeddings + Groq LLM | Retrieval-augmented answers |
| UI + deployment | Streamlit + Streamlit Cloud / HF Spaces | Public web app |

### Key Dependencies (`requirements.txt`)

```
streamlit
groq
sentence-transformers
numpy
scikit-learn
pyyaml
requests
beautifulsoup4      # optional: link content extraction
python-frontmatter  # YAML frontmatter parsing
```

### External Services

| Service | Used In | Cost |
|---------|---------|------|
| Groq API | `classify.py`, `ask.py` | Free tier |
| Streamlit Cloud / HF Spaces | `app.py` deployment | Free tier |

---

## 3. Repository Structure

```
secondself/
├── docs/
│   ├── problemstatement.md
│   ├── architecture.md          ← this file
│   ├── implementation-plan.md
│   └── edge-case.md
│
├── raw/                         # Week 1 output — immutable captures
│   └── {id}_{timestamp}.json
│
├── wiki/                        # Week 2 output — organized markdown notes
│   ├── Projects/
│   ├── Areas/
│   ├── Resources/
│   └── Archives/
│
├── data/
│   ├── embeddings/              # Cached embedding vectors per note
│   │   └── {note_id}.npy
│   └── graph.json               # Week 3 output — graph data model
│
├── static/
│   └── graph.html               # vis-network standalone template (optional)
│
├── capture.py                   # Week 1 — capture pipeline
├── classify.py                  # Week 2.1 — PARA classification
├── link.py                      # Week 2.2 — embedding + auto-linking
├── build_graph.py               # Week 3.1 — wiki → graph.json
├── ask.py                       # Week 4.1 — RAG Q&A
├── app.py                       # Week 4.2 — Streamlit UI
├── config.py                    # Shared paths, thresholds, API keys
├── requirements.txt
├── .env.example                 # GROQ_API_KEY placeholder
└── README.md
```

---

## 4. Data Models

### 4.1 Raw Capture (`raw/{id}_{timestamp}.json`)

Every capture — note, link, or file — is stored as a JSON document.

```json
{
  "id": "a1b2c3d4",
  "timestamp": "2026-07-16T10:30:00Z",
  "type": "note | link | file",
  "content": "The raw text or extracted content",
  "source": "cli argument or file path or URL",
  "metadata": {
    "filename": "optional-original-name.pdf",
    "mime_type": "text/plain"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | UUID short hash — unique, stable identifier |
| `timestamp` | `ISO 8601` | UTC capture time |
| `type` | `enum` | `note`, `link`, or `file` |
| `content` | `string` | Raw or extracted text body |
| `source` | `string` | Original input (URL, filepath, or inline text) |
| `metadata` | `object` | Optional extra fields (filename, mime type) |

### 4.2 Wiki Note (`wiki/{PARA}/{slug}.md`)

Classified notes are promoted from `raw/` to `wiki/` as Markdown files with frontmatter.

```markdown
---
id: a1b2c3d4
title: "One-line summary from LLM"
category: Projects
tags: [python, ai, second-brain]
created: 2026-07-16T10:30:00Z
links: [e5f6g7h8, i9j0k1l2]
embedding_id: a1b2c3d4
---

Full note content here.

## Related
- [[e5f6g7h8]] — linked note title
- [[i9j0k1l2]] — linked note title
```

| Frontmatter Field | Type | Source |
|-------------------|------|--------|
| `id` | `string` | Carried from raw capture |
| `title` | `string` | LLM-generated one-line summary |
| `category` | `enum` | PARA: `Projects`, `Areas`, `Resources`, `Archives` |
| `tags` | `list[string]` | LLM-generated tags |
| `created` | `ISO 8601` | Original capture timestamp |
| `links` | `list[string]` | IDs of auto-linked related notes |
| `embedding_id` | `string` | Key into `data/embeddings/` |

### 4.3 Graph Model (`data/graph.json`)

```json
{
  "nodes": [
    {
      "id": "a1b2c3d4",
      "label": "One-line summary",
      "category": "Projects",
      "tags": ["python", "ai"],
      "content_preview": "First 200 chars of note body...",
      "group": "Projects"
    }
  ],
  "edges": [
    {
      "source": "a1b2c3d4",
      "target": "e5f6g7h8",
      "similarity": 0.82
    }
  ],
  "meta": {
    "generated_at": "2026-07-16T12:00:00Z",
    "node_count": 15,
    "edge_count": 8
  }
}
```

| Node Field | Purpose |
|------------|---------|
| `id` | Matches wiki note ID |
| `label` | Display name on graph |
| `category` / `group` | PARA category — drives node color |
| `content_preview` | Shown on hover popup |
| `tags` | Optional filter/grouping |

| Edge Field | Purpose |
|------------|---------|
| `source` / `target` | Linked note IDs |
| `similarity` | Cosine similarity score from auto-linking |

### 4.4 Embedding Cache (`data/embeddings/{note_id}.npy`)

- NumPy array (384-dim for `all-MiniLM-L6-v2`)
- Computed once per note, reused by `link.py` and `ask.py`
- Avoids recomputing embeddings on every query

---

## 5. Component Architecture

### 5.1 `capture.py` — The Archivist (Week 1)

**Responsibility:** Accept any input type and persist a standardized raw capture.

```
CLI Input
   │
   ├── --note "text"        → type: note
   ├── --link "url"         → type: link  (optional: fetch page text)
   └── --file "path"        → type: file  (read text / store reference)
   │
   ▼
generate_id() + timestamp()
   │
   ▼
build RawCapture JSON
   │
   ▼
write → raw/{id}_{timestamp}.json
   │
   ▼
print confirmation (id, path)
```

**Key functions:**

| Function | Input | Output |
|----------|-------|--------|
| `generate_id()` | — | 8-char hex UUID |
| `detect_type(args)` | CLI args | `note` / `link` / `file` |
| `extract_content(type, source)` | type + source | string content |
| `save_capture(capture)` | RawCapture dict | filepath written |

**Interface:**

```bash
python capture.py --note "My idea about RAG systems"
python capture.py --link "https://example.com/article"
python capture.py --file "./documents/report.pdf"
```

---

### 5.2 `classify.py` — The Sorting Hat (Week 2.1)

**Responsibility:** Read unprocessed raw captures, call Groq LLM, write classified wiki notes.

```
raw/*.json (unprocessed)
   │
   ▼
for each capture:
   │
   ├── build classification prompt (content + PARA instructions)
   ├── call Groq API (Llama 3)
   ├── parse response → { category, tags, summary }
   ├── write wiki/{category}/{slug}.md with frontmatter
   └── mark raw capture as processed (or move to raw/processed/)
```

**LLM prompt structure:**

```
You are a knowledge organizer. Classify this capture using the PARA method.

PARA categories:
- Projects: active work with a deadline
- Areas: ongoing responsibilities
- Resources: topics of interest for future reference
- Archives: inactive items

Return JSON: { "category": "...", "tags": [...], "summary": "..." }

Capture:
{content}
```

**Key functions:**

| Function | Input | Output |
|----------|-------|--------|
| `load_raw_captures()` | — | list of unprocessed raw JSON files |
| `classify_capture(content)` | string | `{ category, tags, summary }` |
| `write_wiki_note(capture, classification)` | raw + classification | markdown filepath |
| `run_classification_pipeline()` | — | count of notes classified |

---

### 5.3 `link.py` — Connect the Dots (Week 2.2)

**Responsibility:** Compute embeddings, find similar notes, insert bidirectional links.

```
wiki/**/*.md
   │
   ▼
for each note (new or all):
   │
   ├── extract body text
   ├── compute embedding → save data/embeddings/{id}.npy
   ├── compare against all existing embeddings (cosine similarity)
   ├── if similarity >= THRESHOLD (default 0.75):
   │     ├── add target id to note's frontmatter.links
   │     └── append [[target_id]] wikilink in Related section
   └── save updated markdown
```

**Similarity pipeline:**

```
new_note_embedding ──┐
                     ├── cosine_similarity() ──► score matrix
existing_embeddings ─┘
                              │
                              ▼
                    filter score >= 0.75
                              │
                              ▼
                    insert bidirectional links
```

**Key functions:**

| Function | Input | Output |
|----------|-------|--------|
| `load_embedding_model()` | — | `SentenceTransformer` instance (singleton) |
| `compute_embedding(text)` | string | numpy array |
| `load_all_embeddings()` | — | dict `{ id: vector }` |
| `find_similar(id, vector, threshold)` | id + vector | list of `(id, score)` |
| `insert_links(note_path, linked_ids)` | path + ids | updated markdown |

**Configurable threshold** (in `config.py`):

```python
SIMILARITY_THRESHOLD = 0.75  # tune based on real data
TOP_K_LINKS = 5              # max links per note
```

---

### 5.4 `build_graph.py` — The Cartographer (Week 3.1)

**Responsibility:** Parse all wiki notes and their links into a graph JSON model.

```
wiki/**/*.md
   │
   ▼
parse frontmatter + wikilinks
   │
   ├── each note  → node { id, label, category, tags, content_preview }
   └── each link  → edge { source, target, similarity }
   │
   ▼
validate (no orphan edges, deduplicate)
   │
   ▼
write → data/graph.json
```

**Key functions:**

| Function | Input | Output |
|----------|-------|--------|
| `parse_wiki_notes()` | — | list of note dicts |
| `extract_links(note)` | note dict | list of edge dicts |
| `build_graph(notes, edges)` | lists | graph dict |
| `export_graph(graph, path)` | graph dict | `graph.json` written |

**Node coloring by PARA category:**

| Category | Color |
|----------|-------|
| Projects | `#FF6B6B` (red) |
| Areas | `#4ECDC4` (teal) |
| Resources | `#45B7D1` (blue) |
| Archives | `#96CEB4` (green) |

---

### 5.5 Graph UI — vis-network (Week 3.2)

**Responsibility:** Render `graph.json` as an interactive force-directed graph.

Embedded inside Streamlit via `st.components.v1.html()`:

```
data/graph.json
   │
   ▼
Python loads JSON → inject into HTML template
   │
   ▼
vis-network renders:
   ├── nodes (sized/colored by category)
   ├── edges (weighted by similarity)
   ├── hover tooltip → content_preview
   ├── drag to reposition
   └── scroll to zoom
```

**vis-network configuration:**

```javascript
{
  physics: { enabled: true, solver: "forceAtlas2Based" },
  interaction: { hover: true, dragNodes: true, zoomView: true },
  nodes: { shape: "dot", scaling: { min: 10, max: 30 } },
  edges: { smooth: { type: "continuous" }, width: 1 }
}
```

---

### 5.6 `ask.py` — The Oracle (Week 4.1)

**Responsibility:** Retrieval-augmented Q&A over the user's own knowledge base.

```
user question (string)
   │
   ▼
embed question → query_vector
   │
   ▼
cosine_similarity(query_vector, all note embeddings)
   │
   ▼
retrieve top-K notes (default K=5)
   │
   ▼
build context prompt:
   "Answer based ONLY on these notes: [note1, note2, ...]
    Question: {question}"
   │
   ▼
call Groq LLM → synthesized answer
   │
   ▼
return { answer, sources: [note_ids] }
```

**Key functions:**

| Function | Input | Output |
|----------|-------|--------|
| `ask(question)` | string | `{ answer, sources, scores }` |
| `retrieve_relevant_notes(question, top_k)` | string + int | list of note dicts |
| `build_rag_prompt(question, notes)` | string + list | LLM prompt string |
| `synthesize_answer(prompt)` | string | answer string |

**RAG prompt template:**

```
You are a personal knowledge assistant. Answer the question using ONLY
the provided notes. If the notes don't contain enough information, say so.
Cite note titles when referencing specific information.

Notes:
{retrieved_notes}

Question: {question}

Answer:
```

---

### 5.7 `app.py` — Streamlit UI (Week 4.2)

**Responsibility:** Single deployable web app combining graph visualization and Q&A.

```
┌──────────────────────────────────────────────────────┐
│  SecondSelf — Your Personal AI Second Brain          │
├──────────────────────┬───────────────────────────────┤
│                      │                               │
│   🧠 Knowledge Graph │   💬 Ask Your Brain           │
│   (vis-network)      │   [search bar]                │
│                      │   [answer + sources]          │
│   hover → preview    │                               │
│   drag + zoom        │   Powered by ask.py           │
│                      │                               │
├──────────────────────┴───────────────────────────────┤
│  Sidebar: stats (note count, link count, categories) │
└──────────────────────────────────────────────────────┘
```

**Page layout:**

| Section | Component | Data Source |
|---------|-----------|-------------|
| Header | `st.title` | static |
| Graph panel | `st.components.v1.html` | `data/graph.json` |
| Ask panel | `st.text_input` + `st.button` | `ask.py` |
| Answer display | `st.markdown` + source citations | `ask()` response |
| Sidebar stats | `st.metric` | `graph.json` meta |

**App startup flow:**

1. Load `data/graph.json` (rebuild if stale via `build_graph.py`)
2. Render graph in left column
3. On question submit → call `ask(question)` → display answer + sources

---

## 6. Shared Configuration (`config.py`)

Centralizes paths, thresholds, and API settings used across all modules.

```python
from pathlib import Path

# Paths
ROOT = Path(__file__).parent
RAW_DIR = ROOT / "raw"
WIKI_DIR = ROOT / "wiki"
EMBEDDINGS_DIR = ROOT / "data" / "embeddings"
GRAPH_PATH = ROOT / "data" / "graph.json"

# PARA categories
PARA_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Linking
SIMILARITY_THRESHOLD = 0.75
TOP_K_LINKS = 5

# RAG
RAG_TOP_K = 5

# LLM (Groq)
GROQ_MODEL = "llama3-8b-8192"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
```

---

## 7. Data Flow Between Weeks

Each week's output is the next week's input. No week can be skipped.

```
Week 1                Week 2                    Week 3              Week 4
────────              ──────                    ──────              ──────

capture.py            classify.py               build_graph.py      ask.py
    │                     │                         │                  │
    ▼                     ▼                         ▼                  ▼
  raw/ ──────────────► wiki/ ──────────────────► graph.json ──────► app.py
                           │                                            │
                       link.py                                           ▼
                           │                                      Public URL
                       embeddings/
```

| Transition | What Moves | Format |
|------------|-----------|--------|
| Week 1 → 2 | `raw/*.json` | JSON captures → classified markdown |
| Week 2 → 3 | `wiki/**/*.md` + links | Markdown notes → graph nodes/edges |
| Week 3 → 4 | `graph.json` + `wiki/` + embeddings | Graph data + RAG retrieval |
| Week 4 → deploy | `app.py` + all data | Streamlit app → public URL |

---

## 8. Deployment Architecture

### Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # add GROQ_API_KEY

# Run pipeline
python capture.py --note "test"
python classify.py
python link.py
python build_graph.py
streamlit run app.py
```

### Production (Streamlit Cloud)

```
GitHub Repo
    │
    ▼
Streamlit Cloud (connects to repo)
    │
    ├── Reads requirements.txt → installs deps
    ├── Reads secrets → GROQ_API_KEY
    ├── Runs streamlit run app.py
    │
    ▼
Public URL: https://secondself.streamlit.app
```

**Deployment checklist:**

| Item | Detail |
|------|--------|
| Entry point | `app.py` |
| Python version | 3.10+ |
| Secrets | `GROQ_API_KEY` in Streamlit Cloud secrets |
| Data bundling | Pre-populated `wiki/` + `data/graph.json` committed to repo |
| Embedding model | First run downloads model (~80MB) — cache in deployment |

### Alternative: Hugging Face Spaces

- Same `app.py` entry point
- `README.md` with `sdk: streamlit` frontmatter
- Secrets via HF Spaces environment variables

---

## 9. Security & Configuration

| Concern | Approach |
|---------|----------|
| API keys | Stored in `.env` locally, Streamlit/HF secrets in production |
| `.env` | Listed in `.gitignore` — never committed |
| User data | All local files — no external data storage in v1 |
| Public deployment | Demo with pre-loaded sample notes; no user upload in v1 |
| Input validation | `capture.py` sanitizes filenames, validates URLs |

---

## 10. Error Handling Strategy

| Module | Failure Mode | Handling |
|--------|-------------|----------|
| `capture.py` | Invalid file path | Print error, exit code 1 |
| `capture.py` | Empty note text | Reject with message |
| `classify.py` | Groq API timeout | Retry 3x with backoff, skip note on failure |
| `classify.py` | Invalid LLM JSON response | Log raw response, use fallback category `Resources` |
| `link.py` | No existing notes to compare | Skip linking, save embedding only |
| `build_graph.py` | Empty wiki folder | Write empty graph with `node_count: 0` |
| `ask.py` | No relevant notes found | Return "I don't have enough information to answer that." |
| `ask.py` | Groq API failure | Return error message to UI |
| `app.py` | Missing `graph.json` | Auto-run `build_graph.py` or show setup instructions |

---

## 11. Performance Considerations

| Operation | Expected Scale | Strategy |
|-----------|---------------|----------|
| Embedding computation | 15–100 notes | Cache in `data/embeddings/`, compute once |
| Similarity comparison | O(n²) pairwise | Acceptable for <500 notes; optimize later with FAISS if needed |
| Graph rendering | <200 nodes | vis-network handles this natively |
| RAG retrieval | <100 notes | Brute-force cosine similarity is fast enough |
| LLM calls | Per classify + per ask | Groq free tier: monitor rate limits |

---

## 12. Extension Points (Post-v1)

These are **not** in scope for the 4-week build but the architecture supports them:

| Extension | How |
|-----------|-----|
| User uploads in deployed app | Add capture endpoint in `app.py` |
| Vector database (FAISS/Chroma) | Replace `data/embeddings/` with index |
| Real-time graph updates | WebSocket or Streamlit `st.rerun()` on new captures |
| Multi-user support | Add auth layer + per-user `wiki/` directories |
| PDF text extraction | Add `pypdf` or `pdfplumber` in `capture.py` |
| Obsidian compatibility | Wiki markdown + `[[wikilinks]]` already compatible |

---

## 13. Architecture Decision Records

| Decision | Choice | Rationale |
|----------|--------|-----------|
| No database | Filesystem only | Simpler setup, human-readable data, git-friendly |
| Markdown wiki format | YAML frontmatter + body | Readable, parseable, Obsidian-compatible |
| Local embeddings | sentence-transformers | Free, private, no API dependency for similarity |
| Groq for LLM | Free Llama 3 API | Zero cost for classify + ask |
| vis-network over Cytoscape | Lighter integration with Streamlit HTML component | Simpler embedding, good defaults |
| Streamlit over FastAPI+React | Single Python file deployment | Faster to ship, free hosting available |
| JSON graph interchange | Decouples build from render | `build_graph.py` and UI evolve independently |
| PARA categorization | Industry-standard knowledge framework | Clear, mutually exclusive categories |

---

## 14. Module Dependency Graph

```
config.py
    │
    ├── capture.py          (standalone — no deps on other modules)
    │
    ├── classify.py         (reads raw/, writes wiki/)
    │       └── uses: config, groq
    │
    ├── link.py             (reads/writes wiki/, writes embeddings/)
    │       └── uses: config, sentence-transformers
    │
    ├── build_graph.py      (reads wiki/, writes graph.json)
    │       └── uses: config
    │
    ├── ask.py              (reads wiki/, embeddings/, calls Groq)
    │       └── uses: config, sentence-transformers, groq
    │
    └── app.py              (reads graph.json, calls ask.py)
            └── uses: config, ask, build_graph, streamlit
```

No circular dependencies. Each module can be tested independently with fixture data from the previous stage.
