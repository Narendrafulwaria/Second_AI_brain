---
category: Projects
created: 2026-07-17 07:46:39+00:00
embedding_id: cec523d5
id: cec523d5
links:
- 32cd6c84
tags:
- SecondSelf
- Personal Knowledge Management
- Streamlit
- Groq
- ' PARA Method'
title: Implementation plan for SecondSelf, a personal knowledge management system
  using the PARA method, Streamlit, and Groq.
---

File: implementation.md
# SecondSelf — Phase-Wise Implementation Plan

> **What to build, in what order.** Derived from [`architecture.md`](./architecture.md) and [`problemstatement.md`](./problemstatement.md).

---

## Overview

| Phase | Name | Week | Deliverable |
|-------|------|------|-------------|
| **0** | Project Setup | — | Repo scaffold, config, dependencies |
| **1** | Capture Pipeline | Week 1 | `capture.py` + 10+ real items in `raw/` |
| **2** | Auto-Classify | Week 2.1 | `classify.py` + PARA-organized `wiki/` |
| **3** | Auto-Link | Week 2.2 | `link.py` + embeddings + linked notes |
| **4** | Graph Builder | Week 3.1 | `build_graph.py` + `data/graph.json` |
| **5** | Graph UI + RAG + App | Week 3.2 + 4 | `ask.py`, `app.py`, interactive brain |
| **6** | Local Integration Testing | — | End-to-end pipeline verified locally |
| **7** | Real-Data Validation | — | 15+ notes, real Q&A, graph from real data |
| **8** | Deployment | — | Live public URL on Streamlit Cloud / HF Spaces |
| **9** | Final Testing + README | — | Public repo, docs, full acceptance sign-off |

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
                                                              │
                                                              ▼
                                            Phase 6 ──► Phase 7 ──► Phase 8 ──► Phase 9
```

---

## Phase 0 — Project Setup

**Goal:** Scaffold the repository so every later phase has a consistent foundation.

**Prerequisites:** Python 3.10+ installed, Git initialized, Groq API key obtained from [console.groq.com](https://console.groq.com).

### Tasks

#### 0.1 — Create directory structure

```bash
mkdir -p raw wiki data/embeddings static
mkdir -p wiki/Projects wiki/Areas wiki/Resources wiki/Archives
```

#### 0.2 — Create `requirements.txt`

```
streamlit>=1.30.0
groq>=0.4.0
sentence-transformers>=2.3.0
numpy>=1.24.0
scikit-learn>=1.3.0
pyyaml>=6.0
requests>=2.31.0
beautifulsoup4>=4.12.0
python-frontmatter>=1.0.0
python-dotenv>=1.0.0
```

#### 0.3 — Create `config.py`

Implement shared paths and constants as defined in `architecture.md` §6:

- `ROOT`, `RAW_DIR`, `WIKI_DIR`, `EMBEDDINGS_DIR`, `GRAPH_PATH`
- `PARA_CATEGORIES`, `EMBEDDING_MODEL`
- `SIMILARITY_THRESHOLD`, `TOP_K_LINKS`, `RAG_TOP_K`
- `GROQ_MODEL`, `GROQ_API_KEY` (from environment)

#### 0.4 — Create environment files

**`.env.example`**
```
GROQ_API_KEY=your_groq_api_key_here
```

**`.gitignore`**
```
.env
venv/
__pycache__/
*.pyc
data/embeddings/*.npy
.DS_Store
```

#### 0.5 — Initialize virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

#### 0.6 — Add placeholder files to preserve empty dirs

```
raw/.gitkeep
data/embeddings/.gitkeep
wiki/Projects/.gitkeep
wiki/Areas/.gitkeep
wiki/Resources/.gitkeep
wiki/Archives/.gitkeep
```

### Files Created

| File | Purpose |
|------|---------|
| `config.py` | Shared configuration |
| `requirements.txt` | Python dependencies |
| `.env.example` | API key template |
| `.gitignore` | Exclude secrets and caches |
| `raw/`, `wiki/`, `data/` | Data directories |

### Acceptance Criteria

- [ ] All directories exist per architecture §3
- [ ] `pip install -r requirements.txt` succeeds without errors
- [ ] `config.py` imports cleanly: `python -c "import config; print(config.ROOT)"`
- [ ] `.env` contains a valid `GROQ_API_KEY`
- [ ] Virtual environment is active and isolated

### Verification Command

```bash
python -c "from config import ROOT, RAW_DIR, WIKI_DIR; print('Setup OK:', ROOT)"
```

---

## Phase 1 — Capture Pipeline (Week 1: The Archivist)

**Goal:** One command captures any note, link, or file into `raw/` with a timestamp and unique ID.

**Prerequisites:** Phase 0 complete.

**Maps to:** `capture.py` — architecture §5.1

### Tasks

#### 1.1 — Implement `generate_id()`

- Return an 8-character hex string from `uuid.uuid4()`
- Must be unique and stable per capture

#### 1.2 — Implement `get_timestamp()`

- Return UTC time in ISO 8601 format: `2026-07-16T10:30:00Z`
- Use `datetime.now(timezone.utc).strftime(...)`

#### 1.3 — Implement `detect_type(args)`

- Parse CLI arguments: `--note`, `--link`, `--file`
- Return `"note"`, `"link"`, or `"file"`
- Error if no argument or multiple arguments provided

#### 1.4 — Implement `extract_content(type, source)`

| Type | Behavior |
|------|----------|
| `note` | Return the text string directly |
| `link` | Store URL as source; optionally fetch page title/text via `requests` + `beautifulsoup4` |
| `file` | Read text files directly; for binary files store filename + path reference in content |

#### 1.5 — Implement `save_capture(capture)`

- Build filename: `{id}_{timestamp}.json` (sanitize timestamp for filesystem)
- Write JSON to `raw/` per schema in architecture §4.1
- Return the filepath written

#### 1.6 — Implement CLI with `argparse`

```bash
python capture.py --note "My idea about RAG systems"
python capture.py --link "https://example.com/article"
python capture.py --file "./documents/report.txt"
```

#### 1.7 — Capture 10+ real items

Use your own scattered information — not dummy test strings:

- 5+ personal notes (ideas, todos, learnings)
- 3+ bookmarks/links you actually saved
- 2+ files (text notes, snippets, READMEs)

### Files Created

| File | Purpose |
|------|---------|
| `capture.py` | Capture CLI and pipeline |
| `raw/*.json` | 10+ real captured items |

### Acceptance Criteria

- [ ] `raw/` and `wiki/` folder structure exists
- [ ] One command captures a note, a link, AND a file
- [ ] Every capture has a `timestamp` + unique `id`
- [ ] Each JSON file matches the raw capture schema
- [ ] 10+ real items in `raw/` (not test data)
- [ ] 🏅 Badge: **The Archivist**

### Verification Commands

```bash
python capture.py --note "Learning plan for Python async"
python capture.py --link "https://docs.python.org/3/library/asyncio.html"
python capture.py --file "README.md"

# Confirm count and schema
python -c "
import json, pathlib
files = list(pathlib.Path('raw').glob('*.json'))
print(f'Captures: {len(files)}')
for f in files[:3]:
    d = json.loads(f.read_text())
    assert 'id' in d and 'timestamp' in d and 'type' in d
    print(f'  {d[\"id\"]} | {d[\"type\"]} | {d[\"timestamp\"]}')
"
```

---

## Phase 2 — Auto-Classify (Week 2.1: The Sorting Hat)

**Goal:** Send raw captures to Groq/Llama 3 and produce PARA-classified wiki notes with tags and summaries.

**Prerequisites:** Phase 1 complete (10+ items in `raw/`).

**Maps to:** `classify.py` — architecture §5.2

### Tasks

#### 2.1 — Implement `load_raw_captures()`

- Scan `raw/*.json` for unprocessed captures
- Skip files in `raw/processed/` (if using move-on-process strategy)
- Return list of parsed capture dicts

#### 2.2 — Implement `classify_capture(content)`

- Build PARA classification prompt (architecture §5.2)
- Call Groq API with `llama3-8b-8192`
- Parse JSON response: `{ "category", "tags", "summary" }`
- Retry up to 3 times on timeout; fallback to `Resources` on parse failure

#### 2.3 — Implement `slugify(summary)`

- Convert summary to filesystem-safe slug: `my-idea-about-rag.md`
- Truncate to 60 chars, lowercase, replace spaces with hyphens

#### 2.4 — Implement `write_wiki_note(capture, classification)`

- Determine target path: `wiki/{category}/{slug}.md`
- Write YAML frontmatter + body per architecture §4.2
- Carry `id` and `created` from raw capture
- Initialize `links: []` (populated in Phase 3)

#### 2.5 — Implement `mark_processed(capture_path)`

- Move raw JSON to `raw/processed/` OR add `"processed": true` flag
- Prevents re-classification on subsequent runs

#### 2.6 — Implement `run_classification_pipeline()`

- Orchestrate: load → classify → write → mark processed
- Print summary: `Classified 12 captures → wiki/`

#### 2.7 — Run on all Phase 1 captures

```bash
python classify.py
```

### Files Created

| File | Purpose |
|------|---------|
| `classify.py` | PARA classification pipeline |
| `wiki/{PARA}/*.md` | Classified markdown notes |
| `raw/processed/` | Processed raw captures (optional) |

### Acceptance Criteria

- [ ] Any raw capture → category + tags + summary automatically
- [ ] PARA categorization working (all 4 categories used appropriately)
- [ ] Wiki notes have valid YAML frontmatter
- [ ] Notes distributed across `wiki/Projects`, `Areas`, `Resources`, `Archives`
- [ ] Raw captures marked as processed (no duplicates on re-run)
- [ ] Groq API errors handled gracefully

### Verification Commands

```bash
python classify.py

# Inspect output
python -c "
import frontmatter, pathlib
notes = list(pathlib.Path('wiki').rglob('*.md'))
print(f'Wiki notes: {len(notes)}')
for f in notes[:5]:
    post = frontmatter.load(f)
    print(f'  {post[\"category\"]} | {post[\"title\"]} | tags={post[\"tags\"]}')
"
```

---

## Phase 3 — Auto-Link (Week 2.2: Connect the Dots)

**Goal:** Compute embeddings for each note, find semantically similar notes, and insert bidirectional wikilinks.

**Prerequisites:** Phase 2 complete (classified notes in `wiki/`).

**Maps to:** `link.py` — architecture §5.3

### Tasks

#### 3.1 — Implement `load_embedding_model()`

- Load `sentence-transformers` model: `all-MiniLM-L6-v2`
- Use singleton pattern — load once, reuse across calls
- First run downloads ~80MB model weights

#### 3.2 — Implement `compute_embedding(text)`

- Encode note body text → 384-dim numpy array
- Save to `data/embeddings/{note_id}.npy`
- Skip if embedding file already exists (unless `--force` flag)

#### 3.3 — Implement `load_all_embeddings()`

- Scan `data/embeddings/*.npy`
- Return dict: `{ note_id: numpy_array }`

#### 3.4 — Implement `find_similar(note_id, vector, all_embeddings, threshold)`

- Compute cosine similarity against all other embeddings
- Exclude self-comparison
- Filter scores >= `SIMILARITY_THRESHOLD` (0.75)
- Return top `TOP_K_LINKS` (5) matches sorted by score

#### 3.5 — Implement `insert_links(note_path, linked_notes)`

- Update frontmatter `links: [id1, id2, ...]`
- Append or update `## Related` section with `[[id]]` wikilinks
- Include similarity score in link label (optional)

#### 3.6 — Implement bidirectional linking

- When note A links to note B, also update note B to link back to note A
- Deduplicate — don't create duplicate links

#### 3.7 — Implement `run_linking_pipeline()`

```bash
python link.py           # process all notes
python link.py --force   # recompute all embeddings
```

#### 3.8 — Validate on 15+ real items

- Ensure at least 15 notes have embeddings
- Verify at least some auto-links were created between related notes

### Files Created

| File | Purpose |
|------|---------|
| `link.py` | Embedding + auto-linking pipeline |
| `data/embeddings/*.npy` | Cached embedding vectors |
| Updated `wiki/**/*.md` | Notes with `links` and `## Related` sections |

### Acceptance Criteria

- [ ] Embeddings computed per note
- [ ] Related notes auto-linked (no manual tagging)
- [ ] Bidirectional links inserted
- [ ] `## Related` section present in linked notes
- [ ] Similarity threshold configurable via `config.py`
- [ ] Runs on 15+ real items → organized, linked `wiki/`
- [ ] 🏅 Badge: **The Librarian**

### Verification Commands

```bash
python link.py

python -c "
import numpy as np, pathlib, frontmatter
emb = list(pathlib.Path('data/embeddings').glob('*.npy'))
notes = list(pathlib.Path('wiki').rglob('*.md'))
linked = [f for f in notes if frontmatter.load(f).get('links')]
print(f'Embeddings: {len(emb)}')
print(f'Wiki notes: {len(notes)}')
print(f'Notes with links: {len(linked)}')
"
```

---

## Phase 4 — Graph Builder (Week 3.1: The Cartographer)

**Goal:** Convert the linked wiki into a nodes-and-edges JSON graph model.

**Prerequisites:** Phase 3 complete (linked notes with embeddings).

**Maps to:** `build_graph.py` — architecture §5.4

### Tasks

#### 4.1 — Implement `parse_wiki_notes()`

- Walk `wiki/**/*.md`
- Parse YAML frontmatter + body with `python-frontmatter`
- Extract: `id`, `title`, `category`, `tags`, `links`, body text
- Generate `content_preview` (first 200 chars of body)

#### 4.2 — Implement `extract_links(note)`

- Read `links` from frontmatter
- Also parse `[[wikilink]]` patterns from `## Related` section
- Return edge list: `[{ source, target, similarity }]`
- Deduplicate edges (A→B and B→A → keep one, or keep both as undirected)

#### 4.3 — Implement `build_graph(notes, edges)`

- Map each note → node object per architecture §4.3
- Set `group` = `category` for vis-network coloring
- Attach `meta` block: `generated_at`, `node_count`, `edge_count`

#### 4.4 — Implement `validate_graph(graph)`

- Remove edges referencing non-existent node IDs
- Deduplicate edges
- Handle empty wiki gracefully (zero nodes, zero edges)

#### 4.5 — Implement `export_graph(graph, path)`

- Write pretty-printed JSON to `data/graph.json`
- Print summary: `Graph: 15 nodes, 8 edges → data/graph.json`

#### 4.6 — Assign PARA colors to nodes

| Category | Color |
|----------|-------|
| Projects | `#FF6B6B` |
| Areas | `#4ECDC4` |
| Resources | `#45B7D1` |
| Archives | `#96CEB4` |

```bash
python build_graph.py
```

### Files Created

| File | Purpose |
|------|---------|
| `build_graph.py` | Wiki → graph JSON pipeline |
| `data/graph.json` | Exported graph data |

### Acceptance Criteria

- [ ] Script builds nodes + edges from notes and exports clean JSON
- [ ] Every wiki note appears as a node
- [ ] Every link appears as an edge
- [ ] `content_preview` populated for hover display
- [ ] `meta` block has accurate counts
- [ ] No orphan edges
- [ ] Built from real notes, not dummy data

### Verification Commands

```bash
python build_graph.py

python -c "
import json
g = json.load(open('data/graph.json'))
print(f'Nodes: {g[\"meta\"][\"node_count\"]}, Edges: {g[\"meta\"][\"edge_count\"]}')
print(f'Sample node: {g[\"nodes\"][0][\"label\"]}')
"
```

---

## Phase 5 — Graph UI, RAG, and Streamlit App (Week 3.2 + Week 4)

**Goal:** Render the interactive brain graph, implement ask-your-brain Q&A, and assemble everything into a Streamlit app.

**Prerequisites:** Phase 4 complete (`data/graph.json` exists).

**Maps to:** `ask.py` + `app.py` + vis-network — architecture §5.5, §5.6, §5.7

### Tasks

---

### 5A — Interactive Graph UI (Week 3.2)

#### 5A.1 — Create `static/graph.html` template

- Embed vis-network CDN (`vis-network/vis-network.min.js`)
- Accept graph JSON injected via JavaScript variable
- Configure force-directed layout (architecture §5.5)

#### 5A.2 — Implement graph rendering function in `app.py`

- Load `data/graph.json`
- Inject nodes/edges into HTML template
- Color nodes by PARA `group`
- Enable hover tooltips showing `content_preview`
- Enable drag-to-explore and scroll-to-zoom

#### 5A.3 — Test graph standalone

- Open graph in browser or via `streamlit run app.py`
- Verify all nodes visible, edges connect correctly
- Hover shows note preview

---

### 5B — RAG Q&A (Week 4.1: The Oracle)

#### 5B.1 — Implement `retrieve_relevant_notes(question, top_k)`

- Embed the question using same `all-MiniLM-L6-v2` model
- Cosine similarity against all cached embeddings
- Return top-K notes with scores

#### 5B.2 — Implement `build_rag_prompt(question, notes)`

- Format retrieved notes with title + content
- Use RAG prompt template from architecture §5.6

#### 5B.3 — Implement `synthesize_answer(prompt)`

- Call Groq API with assembled prompt
- Return answer string

#### 5B.4 — Implement `ask(question)` — the main entry point

```python
def ask(question: str) -> dict:
    """
    Returns: {
        "answer": str,
        "sources": [{"id": str, "title": str, "score": float}],
        "scores": [float]
    }
    """
```

- Handle no-results case: return polite "not enough information" message
- Handle API failures gracefully

#### 5B.5 — Test with real questions

Ask questions about your own captured notes:

```bash
python -c "from ask import ask; print(ask('What am I learning about Python?'))"
```

---

### 5C — Streamlit App (Week 4.2)

#### 5C.1 — Implement `app.py` layout

```
┌─────────────────────────────────────────────┐
│  SecondSelf — Your Personal AI Second Brain   │
├────────────────────┬────────────────────────┤
│  🧠 Knowledge Graph │  💬 Ask Your Brain      │
│  (vis-network)      │  [text input] [button]  │
│                     │  [answer + sources]     │
├────────────────────┴────────────────────────┤
│  Sidebar: note count, link count, categories │
└─────────────────────────────────────────────┘
```

#### 5C.2 — Wire components

| Component | Implementation |
|-----------|---------------|
| Graph panel | `st.components.v1.html(render_graph(), height=600)` |
| Ask panel | `st.text_input` + `st.button` → `ask(question)` |
| Answer display | `st.markdown(answer)` + source citations |
| Sidebar | `st.metric` for node/edge counts, category breakdown |
| Auto-rebuild | If `graph.json` missing, call `build_graph.py` |

#### 5C.3 — Run locally

```bash
streamlit run app.py
```

### Files Created

| File | Purpose |
|------|---------|
| `ask.py` | RAG Q&A pipeline |
| `app.py` | Streamlit UI (graph + search) |
| `static/graph.html` | vis-network template (optional) |

### Acceptance Criteria

- [ ] Interactive force-directed graph renders from `graph.json`
- [ ] Hover reveals note content preview
- [ ] Drag + zoom work
- [ ] `ask()` returns answers synthesized from your own notes
- [ ] Source citations shown with each answer
- [ ] One Streamlit app contains both graph and search bar
- [ ] Built from real notes, not dummy data
- [ ] 🏅 Badge: **The Cartographer** + **The Oracle**

### Verification Commands

```bash
streamlit run app.py
# Open http://localhost:8501
# 1. Verify graph renders with colored nodes
# 2. Hover a node — preview appears
# 3. Ask a real question — answer cites your notes
```

---

## Phase 6 — Local Integration Testing

**Goal:** Verify the full pipeline works end-to-end on your local machine.

**Prerequisites:** Phases 0–5 complete.

### Tasks

#### 6.1 — Run full pipeline from scratch

```bash
# Step 1: Capture new item
python capture.py --note "Integration test note about machine learning"

# Step 2: Classify
python classify.py

# Step 3: Link
python link.py

# Step 4: Build graph
python build_graph.py

# Step 5: Launch app
streamlit run app.py
```

#### 6.2 — Verify data flows correctly

| Check | Expected |
|-------|----------|
| New capture appears in `raw/` | JSON with id + timestamp |
| Classification creates wiki note | Markdown in correct PARA folder |
| Linking updates note | `links` in frontmatter, `## Related` section |
| Graph includes new note | Node in `graph.json` |
| App shows new node | Visible in graph UI |
| Ask returns relevant answer | Answer cites the new note |

#### 6.3 — Test error paths

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty note capture | Rejected with error message |
| Invalid file path | Error, exit code 1 |
| Groq API key missing | Clear error about `GROQ_API_KEY` |
| Empty wiki folder | Empty graph with `node_count: 0` |
| Question with no relevant notes | "Not enough information" response |
| Missing `graph.json` | App auto-rebuilds or shows setup message |

#### 6.4 — Test CLI edge cases

```bash
python capture.py                          # no args → error
python capture.py --note ""                # empty note → error
python capture.py --file "nonexistent.txt" # bad path → error
python classify.py                         # re-run → skips processed
python link.py --force                     # recompute embeddings
```

### Acceptance Criteria

- [ ] Full pipeline runs without manual intervention
- [ ] New capture flows through all stages to the app
- [ ] Error paths handled gracefully (no crashes)
- [ ] Re-running stages is idempotent (no duplicates)
- [ ] All modules importable independently

---

## Phase 7 — Real-Data Validation

**Goal:** Confirm the system works with real personal knowledge — not test fixtures.

**Prerequisites:** Phase 6 complete.

### Tasks

#### 7.1 — Capture 15+ diverse real items

Ensure your knowledge base covers multiple topics:

| Type | Minimum Count | Examples |
|------|--------------|---------|
| Notes | 8+ | Ideas, learnings, todos, meeting notes |
| Links | 4+ | Articles, docs, tutorials you saved |
| Files | 3+ | Text files, code snippets, exports |

#### 7.2 — Run full pipeline on all items

```bash
python classify.py
python link.py
python build_graph.py
```

#### 7.3 — Validate classification quality

- Open 5 random wiki notes — do categories make sense?
- Are tags relevant and specific?
- Are summaries accurate one-liners?

#### 7.4 — Validate linking quality

- Check 5 linked note pairs — are they genuinely related?
- Tune `SIMILARITY_THRESHOLD` in `config.py` if too many/few links
- Recommended range: 0.65–0.85

#### 7.5 — Validate graph visualization

- All 15+ nodes visible and colored by category
- Clusters form around related topics
- Hover previews are readable

#### 7.6 — Validate Q&A with 5+ real questions

| Question Type | Example |
|--------------|---------|
| Factual | "What resources do I have about Python?" |
| Summarization | "What projects am I working on?" |
| Cross-note | "How do my learning goals connect to my projects?" |
| Out-of-scope | "What's the weather today?" → should say "not enough info" |
| Specific | "What did I note about [specific topic]?" |

### Acceptance Criteria

- [ ] 15+ real items captured, classified, linked, and graphed
- [ ] PARA categories assigned sensibly
- [ ] Auto-links connect genuinely related notes
- [ ] Graph clusters reflect real knowledge structure
- [ ] 5+ real questions answered with accurate source citations
- [ ] Out-of-scope questions handled gracefully

---

## Phase 8 — Deployment

**Goal:** Deploy the complete Streamlit app to a public URL.

**Prerequisites:** Phases 0–7 complete, GitHub repo created.

**Maps to:** architecture §8

### Tasks

#### 8.1 — Prepare repo for deployment

- Commit `wiki/`, `data/graph.json`, and `data/embeddings/` (or regenerate on first run)
- Ensure `requirements.txt` has pinned versions
- Verify `.env` is in `.gitignore`
- Add `packages.txt` if system dependencies needed (unlikely)

#### 8.2 — Create `README.md`

Include:

- Project description and live URL
- Architecture diagram (link to `architecture.md`)
- Setup instructions (clone, venv, pip install, .env)
- Usage: capture → classify → link → graph → ask
- Screenshots of graph + Q&A

#### 8.3 — Push to GitHub

```bash
git add .
git commit -m "Ship SecondSelf v1"
git push -u origin main
```

#### 8.4 — Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect GitHub repo
3. Set main file: `app.py`
4. Add secret: `GROQ_API_KEY`
5. Deploy

#### 8.5 — Alternative: Hugging Face Spaces

1. Create new Space with Streamlit SDK
2. Push repo contents
3. Add `GROQ_API_KEY` as Space secret
4. Space auto-builds and deploys

#### 8.6 — Verify deployed app

- Public URL loads without errors
- Graph renders with all nodes
- Ask panel returns answers
- First-load embedding model download completes (~80MB)

### Acceptance Criteria

- [ ] GitHub repo is public with clean README
- [ ] App deployed to Streamlit Cloud or HF Spaces
- [ ] Public URL accessible without login
- [ ] Graph and Q&A both work on deployed app
- [ ] `GROQ_API_KEY` stored as secret (not in code)
- [ ] 🏅 Badge: **The Oracle** (deployment complete)

---

## Phase 9 — Final Testing + Documentation Sign-Off

**Goal:** Complete final verification and close out all project deliverables.

**Prerequisites:** Phase 8 complete (live URL working).

### Tasks

#### 9.1 — End-to-end deployed test

On the **live public URL** (not localhost):

1. Load the app — graph renders
2. Hover nodes — previews appear
3. Ask 3 real questions — answers cite notes
4. Check sidebar stats — counts match local data

#### 9.2 — Final deliverables checklist

- [ ] Public GitHub repo with clean README + setup instructions
- [ ] Live deployed URL — interactive graph + ask-your-brain search
- [ ] End-to-end flow verified: capture → classify → link → graph → ask
- [ ] All 4 weekly milestones complete:
  - [ ] Week 1: Capture Pipeline (The Archivist)
  - [ ] Week 2: Self-Organizing Wiki (The Librarian)
  - [ ] Week 3: Living Brain (The Cartographer)
  - [ ] Week 4: SecondSelf deployment (The Oracle)

#### 9.3 — Documentation review

| Document | Status |
|----------|--------|
| `problemstatement.md` | Complete |
| `architecture.md` | Complete |
| `implementation.md` | Complete |
| `edge-case.md` | To be created |
| `README.md` | Updated with live URL |

#### 9.4 — Record the live URL

Add to `README.md`:

```markdown
## Live Demo

🧠 **SecondSelf is live:** https://your-app.streamlit.app
```

### Acceptance Criteria

- [ ] Full pipeline works on deployed app
- [ ] All 4 badges earned
- [ ] README has setup instructions + live URL
- [ ] All documentation files complete
- [ ] Project ready for portfolio / submission

---

## Quick Reference — Command Cheat Sheet

```bash
# ── Setup (Phase 0) ──
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# ── Capture (Phase 1) ──
python capture.py --note "your note here"
python capture.py --link "https://example.com"
python capture.py --file "./path/to/file.txt"

# ── Classify (Phase 2) ──
python classify.py

# ── Link (Phase 3) ──
python link.py
python link.py --force

# ── Graph (Phase 4) ──
python build_graph.py

# ── App (Phase 5) ──
streamlit run app.py

# ── Quick Q&A test ──
python -c "from ask import ask; print(ask('your question'))"

# ── Full pipeline (Phase 6) ──
python capture.py --note "new note" && python classify.py && python link.py && python build_graph.py && streamlit run app.py
```

---

## Phase Dependencies

```
Phase 0 (Setup)
    │
    ▼
Phase 1 (capture.py) ──────────────────────────────┐
    │                                               │
    ▼                                               │
Phase 2 (classify.py)                               │
    │                                               │
    ▼                                               │
Phase 3 (link.py)                                   │
    │                                               │
    ▼                                               │
Phase 4 (build_graph.py)                            │
    │                                               │
    ▼                                               │
Phase 5 (ask.py + app.py) ◄────────────────────────┘
    │
    ▼
Phase 6 (Integration Testing)
    │
    ▼
Phase 7 (Real-Data Validation)
    │
    ▼
Phase 8 (Deployment)
    │
    ▼
Phase 9 (Final Sign-Off)
```

**Do not skip phases.** Each phase's output is the next phase's input.

---

## Estimated Timeline

| Phase | Effort | Cumulative |
|-------|--------|------------|
| 0 — Setup | 1–2 hours | Day 1 |
| 1 — Capture | 3–4 hours | Week 1 |
| 2 — Classify | 4–5 hours | Week 2 |
| 3 — Auto-Link | 4–5 hours | Week 2 |
| 4 — Graph Builder | 3–4 hours | Week 3 |
| 5 — UI + RAG + App | 6–8 hours | Week 3–4 |
| 6 — Integration Testing | 2–3 hours | Week 4 |
| 7 — Real-Data Validation | 2–3 hours | Week 4 |
| 8 — Deployment | 2–3 hours | Week 4 |
| 9 — Final Sign-Off | 1–2 hours | Week 4 |

**Total: ~30–40 hours over 4 weeks**
## Related
- [[738637d3]] (similarity: 0.91)