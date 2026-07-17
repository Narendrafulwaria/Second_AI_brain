# SecondSelf — Edge Cases & Corner Scenarios

> **Every way the system can break, misbehave, or surprise you — and how to handle it.**  
> Derived from [`architecture.md`](./architecture.md) and [`implementation.md`](./implementation.md).

---

## How to Use This Document

Each edge case follows this format:

| Column | Meaning |
|--------|---------|
| **ID** | Unique reference (e.g. `CAP-01`) |
| **Scenario** | What can go wrong |
| **Impact** | Severity: `Critical` / `High` / `Medium` / `Low` |
| **Expected Behavior** | What the system should do |
| **Module** | Which file handles it |
| **Test** | How to reproduce (where applicable) |

Use this during **Phase 6–7** integration testing and before **Phase 8** deployment.

---

## 1. Setup & Configuration (`config.py`, Phase 0)

| ID | Scenario | Impact | Expected Behavior | Module | Test |
|----|----------|--------|-------------------|--------|------|
| CFG-01 | `GROQ_API_KEY` not set in `.env` | Critical | Fail fast with clear message: `"GROQ_API_KEY not found. Copy .env.example to .env"` | `config.py` | Rename `.env` and run `classify.py` |
| CFG-02 | `GROQ_API_KEY` is invalid or expired | Critical | Groq returns 401; surface readable error, do not crash silently | `classify.py`, `ask.py` | Use fake key `gsk_invalid` |
| CFG-03 | Required directories missing (`raw/`, `wiki/`, `data/`) | High | Auto-create directories on first run via `Path.mkdir(parents=True, exist_ok=True)` | `config.py` | Delete `raw/` and run `capture.py` |
| CFG-04 | Python version < 3.10 | High | `requirements.txt` install may fail; document minimum version in README | setup | `python --version` |
| CFG-05 | `pip install` fails (network timeout) | Medium | User retries; no partial state written | setup | Disconnect network during install |
| CFG-06 | Running on Windows with path separators | Medium | Use `pathlib.Path` everywhere — never hardcode `/` | all | Capture file with `C:\Users\...` path |
| CFG-07 | Project root moved or run from wrong directory | High | `config.ROOT` resolves relative to `config.py` location, not CWD | `config.py` | `cd ..` then `python PERSONAL_AI_SECOND_BRAIN/capture.py` |
| CFG-08 | `.env` accidentally committed to Git | Critical | `.gitignore` blocks it; warn in README never to commit secrets | `.gitignore` | `git status` should not show `.env` |
| CFG-09 | Virtual environment not activated | Medium | Import errors or wrong package versions; document activation in README | setup | Run without `venv\Scripts\activate` |
| CFG-10 | `sentence-transformers` model download fails (no internet) | High | `link.py` and `ask.py` fail with network error message; suggest retry | `link.py`, `ask.py` | Run offline on fresh install |

---

## 2. Capture Pipeline (`capture.py`, Phase 1)

### 2.1 CLI Input Edge Cases

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| CAP-01 | No arguments provided | Medium | Print usage help, exit code 1 | `python capture.py` |
| CAP-02 | Multiple flags at once (`--note` + `--link`) | Medium | Reject: "Provide exactly one of --note, --link, or --file" | `python capture.py --note "x" --link "y"` |
| CAP-03 | Empty note string `--note ""` | Medium | Reject: "Note content cannot be empty" | `python capture.py --note ""` |
| CAP-04 | Note with only whitespace `--note "   "` | Medium | Strip and reject if empty after strip | `python capture.py --note "   "` |
| CAP-05 | Extremely long note (100K+ chars) | Low | Accept and save; warn if > 50K chars | Paste large text block |
| CAP-06 | Note with special characters / emoji / Unicode | Low | Save as UTF-8 JSON without corruption | `python capture.py --note "日本語 🧠 test"` |
| CAP-07 | Note with embedded newlines and quotes | Low | JSON-escape correctly; file remains valid JSON | Multi-line note with `"quotes"` |

### 2.2 Link Capture Edge Cases

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| CAP-08 | Invalid URL format `--link "not-a-url"` | Medium | Reject or save with warning; validate scheme (`http`/`https`) | `python capture.py --link "not-a-url"` |
| CAP-09 | Valid URL but page unreachable (404, timeout) | Medium | Save capture with URL as source; content = URL or error note | Dead URL |
| CAP-10 | URL returns non-HTML (PDF, image) | Low | Store URL + content type in metadata; minimal text extraction | `python capture.py --link "https://example.com/file.pdf"` |
| CAP-11 | URL with login wall / paywall | Low | Save URL; content = fetched partial text or placeholder | Paywalled article URL |
| CAP-12 | URL with redirect chain | Low | Follow redirects (max 5); store final URL | Shortened bit.ly link |
| CAP-13 | Very long URL (> 2000 chars) | Low | Accept; truncate display in metadata if needed | URL with many query params |

### 2.3 File Capture Edge Cases

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| CAP-14 | File path does not exist | High | Error: "File not found: {path}", exit code 1 | `python capture.py --file "missing.txt"` |
| CAP-15 | File is a directory, not a file | Medium | Error: "Path is a directory, not a file" | `python capture.py --file "./raw"` |
| CAP-16 | Binary file (image, .exe, .zip) | Medium | Save with metadata; content = filename + "binary file" note (v1: no extraction) | `python capture.py --file "photo.jpg"` |
| CAP-17 | PDF file (v1: no pdfplumber) | Medium | Save reference + filename; content = "[PDF file: name.pdf]" placeholder | `python capture.py --file "report.pdf"` |
| CAP-18 | Empty text file (0 bytes) | Medium | Reject: "File is empty" | Create empty `.txt` and capture |
| CAP-19 | Very large file (> 10 MB text) | Low | Accept but warn; truncate content to configurable max (e.g. 100K chars) | Large log file |
| CAP-20 | File with no read permission | High | Error: "Permission denied: {path}" | System-protected file |
| CAP-21 | File path with spaces or special chars | Low | Handle via `pathlib`; quote paths in CLI docs | `python capture.py --file "my notes.txt"` |
| CAP-22 | Symlink to file | Low | Follow symlink and capture target content | Symlinked file |

### 2.4 Storage & ID Edge Cases

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| CAP-23 | Duplicate capture (same content twice) | Low | Allow — each gets unique ID; dedup is Phase 2+ concern | Capture same note twice |
| CAP-24 | ID collision (extremely unlikely) | Low | Regenerate ID if file already exists | Mock collision in test |
| CAP-25 | Filename with `:` from ISO timestamp (Windows) | High | Sanitize timestamp for filesystem: replace `:` with `-` | Capture on Windows |
| CAP-26 | `raw/` directory not writable | Critical | Error: "Cannot write to raw/ directory" | Set read-only permissions |
| CAP-27 | Disk full during write | Critical | Catch `OSError`; report "Disk full", do not write partial JSON | Simulate full disk |
| CAP-28 | Concurrent captures (two terminals) | Low | Both succeed with unique IDs; no file locking needed in v1 | Run two captures simultaneously |

---

## 3. Classification Pipeline (`classify.py`, Phase 2)

### 3.1 Raw Input Edge Cases

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| CLS-01 | `raw/` folder is empty | Low | Print "No captures to classify", exit 0 | Delete all raw files |
| CLS-02 | All raw captures already processed | Low | Print "0 new captures", exit 0 | Re-run `classify.py` |
| CLS-03 | Corrupt JSON in raw file | High | Skip file, log error with filename, continue batch | Manually corrupt a JSON |
| CLS-04 | Raw JSON missing required fields (`id`, `content`) | High | Skip file, log "Invalid capture schema" | Delete `id` field from JSON |
| CLS-05 | Raw capture with empty `content` | Medium | Skip or classify as Archives with tag `empty` | Empty content field |
| CLS-06 | Raw capture with very short content ("ok") | Low | Classify normally; LLM may assign generic tags | `--note "ok"` then classify |
| CLS-07 | Raw capture in non-UTF-8 encoding | Medium | Read with `errors='replace'`; never crash | Binary chars in JSON string |

### 3.2 LLM / Groq Edge Cases

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| CLS-08 | Groq API timeout | High | Retry 3x with exponential backoff (1s, 2s, 4s); skip on final failure | Mock timeout |
| CLS-09 | Groq rate limit (429) | High | Backoff and retry; if persistent, pause and log | Rapid-fire 50 classifications |
| CLS-10 | LLM returns invalid JSON | High | Log raw response; fallback: `category: Resources`, `tags: [uncategorized]`, `summary: first 80 chars of content` | Mock malformed response |
| CLS-11 | LLM returns unknown PARA category ("Ideas") | Medium | Map to nearest valid category or default to `Resources` | Prompt with ambiguous content |
| CLS-12 | LLM returns empty tags list | Low | Accept; store `tags: []` | Very vague one-word note |
| CLS-13 | LLM returns too many tags (> 20) | Low | Truncate to top 10 tags | N/A |
| CLS-14 | LLM summary contains quotes breaking YAML | Medium | Escape/sanitize summary for YAML frontmatter | Summary with `"quotes"` |
| CLS-15 | LLM summary is very long (> 200 chars) | Low | Truncate summary to 200 chars for title field | Long-winded LLM response |
| CLS-16 | Content triggers LLM safety filter | Medium | Skip note, log "Classification blocked", do not crash | N/A |
| CLS-17 | Network offline during classification | High | Fail with clear network error after retries | Disconnect network |

### 3.3 Wiki Write Edge Cases

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| CLS-18 | Slug collision (two notes → same filename) | High | Append short ID suffix: `my-note-a1b2c3d4.md` | Two notes with same summary |
| CLS-19 | Summary produces empty slug after slugify | Medium | Fallback slug: `note-{id}` | Summary = "---" or "***" |
| CLS-20 | Slug with only special characters | Medium | Fallback slug: `note-{id}` | Summary = "!!! @@@" |
| CLS-21 | PARA subfolder missing | Low | Auto-create `wiki/{category}/` | Delete `wiki/Projects/` |
| CLS-22 | Wiki file already exists (re-classify) | Medium | Skip if already in wiki/ with same ID; or overwrite with `--force` | Re-run on processed capture |
| CLS-23 | Content with Markdown syntax in body | Low | Preserve as-is in body; do not double-escape | Note with `# headers` and `**bold**` |
| CLS-24 | Content with YAML-breaking `---` in body | Medium | Use `python-frontmatter` correctly; body after closing `---` | Note starting with dashes |

---

## 4. Auto-Linking Pipeline (`link.py`, Phase 3)

### 4.1 Embedding Edge Cases

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| LNK-01 | No wiki notes exist | Medium | Print "No notes to link", exit 0 | Empty `wiki/` |
| LNK-02 | Only one note exists | Low | Compute and save embedding; no links created (nothing to compare) | Single note in wiki |
| LNK-03 | Note body is empty (only frontmatter) | Medium | Skip embedding or embed title only; log warning | Empty body wiki note |
| LNK-04 | Note body is very short (< 10 chars) | Low | Embed anyway; likely no matches above threshold | Body = "TODO" |
| LNK-05 | Embedding file already exists | Low | Skip recomputation unless `--force` | Re-run `link.py` |
| LNK-06 | Embedding file corrupted / wrong shape | Medium | Delete and recompute on next run | Corrupt `.npy` file |
| LNK-07 | Model download interrupted | High | Clear error with retry instructions | Kill download mid-way |
| LNK-08 | Out of memory during embedding (huge note) | Medium | Truncate text to model max length (512 tokens) before embedding | 500K char note |

### 4.2 Similarity & Linking Edge Cases

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| LNK-09 | No notes above similarity threshold | Low | Save embeddings only; no links added | Unrelated notes at threshold 0.75 |
| LNK-10 | All notes above threshold (everything links to everything) | Medium | Cap at `TOP_K_LINKS` (5) per note; tune threshold up | 5 similar notes, threshold 0.3 |
| LNK-11 | Threshold too low (0.3) — spurious links | Medium | Document recommended range 0.65–0.85; user tunes `config.py` | Set threshold to 0.3 |
| LNK-12 | Threshold too high (0.95) — no links | Low | Document tuning guide; zero links is valid | Set threshold to 0.95 |
| LNK-13 | Bidirectional link already exists | Low | Deduplicate; do not add duplicate `[[id]]` | Re-run `link.py` |
| LNK-14 | Note A links to B, but B file is missing | High | Skip orphan link; log warning in `build_graph.py` | Delete linked note file |
| LNK-15 | Self-link (note matches itself) | Low | Exclude self from similarity comparison | N/A |
| LNK-16 | Identical notes (duplicate content, different IDs) | Medium | Link with high similarity; user may dedup manually | Capture same text twice, full pipeline |
| LNK-17 | Notes in different languages | Low | Multilingual model handles reasonably; links may be weaker | Mix English + Hindi notes |
| LNK-18 | `## Related` section already exists | Low | Append new links; do not duplicate section header | Re-run linking on linked note |
| LNK-19 | Frontmatter `links` array malformed | Medium | Reset to `[]` and rebuild links | Manually corrupt YAML |

---

## 5. Graph Builder (`build_graph.py`, Phase 4)

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| GRPH-01 | Empty `wiki/` folder | Low | Write `graph.json` with `node_count: 0`, `edge_count: 0` | No wiki notes |
| GRPH-02 | Wiki note missing `id` in frontmatter | High | Skip note, log warning | Remove `id` from frontmatter |
| GRPH-03 | Wiki note with invalid YAML frontmatter | High | Skip note, log parse error | Corrupt frontmatter |
| GRPH-04 | Edge references non-existent node ID | Medium | Remove orphan edge during validation | Link to deleted note |
| GRPH-05 | Duplicate edges (A→B and A→B again) | Low | Deduplicate edges in validation step | Re-run graph build |
| GRPH-06 | Bidirectional edges (A→B and B→A) | Low | Keep both or collapse to one — document choice (keep one) | Linked pair |
| GRPH-07 | Node with no edges (isolated note) | Low | Include as node with zero edges — valid state | Unrelated note |
| GRPH-08 | Very long `content_preview` | Low | Truncate to 200 chars with `...` suffix | Long note body |
| GRPH-09 | `content_preview` contains HTML/JS | Medium | Strip tags; escape for JSON safety | Note with `<script>` tags |
| GRPH-10 | Unknown PARA category in frontmatter | Low | Default group to `Resources`; gray color in graph | `category: Misc` |
| GRPH-11 | `graph.json` already exists | Low | Overwrite on rebuild | Re-run `build_graph.py` |
| GRPH-12 | Special characters in node `label` | Low | JSON-escape; vis-network handles UTF-8 | Label with emoji |
| GRPH-13 | 200+ nodes (performance) | Medium | vis-network may slow; document max recommended 200 for v1 | Scale test |
| GRPH-14 | Zero edges but many nodes | Low | Valid graph — constellation of isolated nodes | High threshold, many notes |

---

## 6. RAG Q&A (`ask.py`, Phase 5)

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| ASK-01 | Empty question string | Medium | Reject: "Please enter a question" | `ask("")` |
| ASK-02 | Question with only whitespace | Medium | Strip and reject if empty | `ask("   ")` |
| ASK-03 | No embeddings exist | High | Return "Knowledge base is empty. Capture and classify notes first." | Run ask before link.py |
| ASK-04 | No notes above similarity threshold for question | Medium | Return "I don't have enough information to answer that." | "What's the weather today?" |
| ASK-05 | Question matches many notes equally | Low | Return top-K (5) by score; LLM synthesizes from all | Broad question |
| ASK-06 | Question in different language than notes | Low | Embed and retrieve cross-lingually; answer quality may vary | Hindi question, English notes |
| ASK-07 | Very long question (1000+ chars) | Low | Truncate question to 500 chars before embedding | Paste essay as question |
| ASK-08 | Groq API failure during synthesis | High | Return error: "Unable to generate answer. Please try again." | Invalid API key |
| ASK-09 | LLM hallucinates beyond retrieved notes | High | Prompt instructs "ONLY use provided notes"; cite sources in response | Ask ambiguous question |
| ASK-10 | Retrieved notes contradict each other | Medium | LLM should acknowledge conflict in answer | Contradictory notes |
| ASK-11 | Single note retrieved with low score (0.3) | Medium | Only use notes above minimum score floor (e.g. 0.4) | Tangentially related question |
| ASK-12 | Question about future events / external facts | Low | "I don't have enough information" — not in notes | "Who won the 2028 election?" |
| ASK-13 | Embedding model not loaded (first run) | High | Load model on first `ask()` call; show loading indicator in UI | Fresh install |
| ASK-14 | `top_k` > total notes | Low | Return all available notes | 3 notes, `top_k=10` |

---

## 7. Streamlit App (`app.py`, Phase 5)

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| APP-01 | `graph.json` missing on startup | High | Auto-run `build_graph.py` OR show setup instructions with command | Delete `graph.json` |
| APP-02 | `graph.json` is corrupt / invalid JSON | High | Catch `JSONDecodeError`; show error + "Run: python build_graph.py" | Corrupt JSON |
| APP-03 | `graph.json` has zero nodes | Medium | Show empty state: "No notes yet. Run the capture pipeline." | Empty wiki |
| APP-04 | vis-network CDN unreachable | High | Show fallback message; graph panel displays error, ask panel still works | Block CDN in browser |
| APP-05 | Graph with 100+ nodes — browser slow | Medium | Show performance warning in sidebar; suggest filtering | Large graph |
| APP-06 | Node hover tooltip with very long preview | Low | Truncate preview in tooltip to 200 chars | Long note |
| APP-07 | User clicks "Ask" with empty input | Low | Show validation message; do not call API | Click Ask without typing |
| APP-08 | User spams Ask button (rate limit) | Medium | Disable button during API call; show spinner | Rapid clicks |
| APP-09 | `ask()` takes > 10 seconds | Medium | Show `st.spinner("Thinking...")` during call | Slow network |
| APP-10 | Streamlit page refresh during ask | Low | State resets; no partial answer shown | Refresh mid-query |
| APP-11 | Mobile viewport — graph too small | Low | Graph panel scrollable; min-height 400px | Open on phone |
| APP-12 | Dark/light mode rendering issues | Low | vis-network uses fixed colors; acceptable in v1 | Toggle OS theme |

---

## 8. Pipeline & Integration Edge Cases (Phases 6–7)

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| PIPE-01 | Run `classify.py` before any captures | Low | "No captures to classify" — no error | Empty `raw/` |
| PIPE-02 | Run `link.py` before `classify.py` | Medium | "No wiki notes found" — no crash | Skip classify step |
| PIPE-03 | Run `build_graph.py` before `link.py` | Low | Graph with nodes, zero edges — valid | Skip link step |
| PIPE-04 | Run `ask.py` before full pipeline | High | Empty knowledge base message | Only Phase 0 done |
| PIPE-05 | Re-run full pipeline on same data | Medium | Idempotent: no duplicate wiki notes or links | Run classify twice |
| PIPE-06 | Capture new note after graph built | Medium | Graph stale until `build_graph.py` re-run; app should note this | Add note, don't rebuild |
| PIPE-07 | Delete a wiki note manually | Medium | Orphan edges removed on next `build_graph.py` | Delete `.md` file |
| PIPE-08 | Edit wiki note body manually | Low | Embedding stale until `link.py --force` | Edit note content |
| PIPE-09 | Change PARA category manually in frontmatter | Low | Graph rebuild picks up new category/color | Move note between folders |
| PIPE-10 | Partial pipeline failure mid-batch | High | Failed item logged and skipped; rest continue | Kill network mid-classify |
| PIPE-11 | Run pipeline steps out of order | High | Each step validates prerequisites; clear error messages | `link.py` before `classify.py` |
| PIPE-12 | Two notes with same ID (manual edit) | High | Graph deduplicates by ID; log duplicate warning | Copy ID in frontmatter |

---

## 9. Deployment Edge Cases (Phase 8)

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| DEP-01 | `GROQ_API_KEY` not set in Streamlit secrets | Critical | App loads; ask panel shows "API key not configured" | Deploy without secret |
| DEP-02 | First deploy — model download timeout | High | Streamlit may timeout on cold start; document re-deploy or pre-cache model | Fresh HF/Streamlit deploy |
| DEP-03 | `requirements.txt` version conflict | High | Build fails; pin versions in requirements | Unpinned deps |
| DEP-04 | Repo too large (committed embeddings) | Medium | `.gitignore` embeddings or use Git LFS; warn in README | Large `.npy` files in repo |
| DEP-05 | `graph.json` not committed — empty graph on deploy | High | Commit pre-built `graph.json` + `wiki/` OR auto-build on startup | Deploy without data |
| DEP-06 | Streamlit Cloud memory limit exceeded | High | Reduce graph size; lazy-load embeddings | 500+ notes |
| DEP-07 | Streamlit Cloud sleeps after inactivity | Low | Cold start delay on first visit; acceptable for demo | Wait 30 min, revisit |
| DEP-08 | HTTPS mixed content (HTTP CDN) | Medium | Use HTTPS CDN for vis-network | Check browser console |
| DEP-09 | Concurrent users on public URL | Low | v1: read-only demo; no write conflicts | Multiple browsers |
| DEP-10 | Groq free tier exhausted on public app | High | Rate limit message in UI; document daily limits | Heavy public usage |
| DEP-11 | GitHub repo is private — Streamlit can't access | High | Make repo public or use deploy token | Private repo deploy |
| DEP-12 | Windows-developed, Linux-deployed path issues | Medium | Always use `pathlib`; never hardcode backslashes | Deploy from Windows dev |

---

## 10. Data Integrity Edge Cases

| ID | Scenario | Impact | Expected Behavior | Test |
|----|----------|--------|-------------------|------|
| DAT-01 | Manual edit breaks frontmatter YAML | High | `build_graph.py` skips file with parse error | Remove closing `---` |
| DAT-02 | Note ID in frontmatter doesn't match filename | Low | ID from frontmatter is canonical; filename is cosmetic | Rename file |
| DAT-03 | `links` array contains ID with no matching note | Medium | Orphan edge removed at graph build | Link to deleted note |
| DAT-04 | `[[wikilink]]` in body but not in frontmatter `links` | Low | `build_graph.py` parses both sources; deduplicate | Manual wikilink only |
| DAT-05 | Embedding exists but wiki note deleted | Medium | Orphan `.npy` ignored during retrieval | Delete note, keep `.npy` |
| DAT-06 | Wiki note exists but no embedding | Medium | `ask.py` skips note without embedding; `link.py` can backfill | Skip link step for one note |
| DAT-07 | `raw/processed/` out of sync with `wiki/` | Low | Re-classify with `--force` flag to reprocess | Delete wiki note, keep processed raw |
| DAT-08 | Git merge conflict in markdown note | Medium | User resolves manually; document in README | Merge conflict in wiki |

---

## 11. Security Edge Cases

| ID | Scenario | Impact | Expected Behavior | Mitigation |
|----|----------|--------|-------------------|------------|
| SEC-01 | API key hardcoded in source code | Critical | Never commit; use `.env` / Streamlit secrets | Code review |
| SEC-02 | User input passed directly to LLM prompt | Medium | Sanitize/truncate; no code execution from captures | Input length limits |
| SEC-03 | Captured URL points to malicious site | Low | Fetch with timeout; no JS execution; store text only | `requests` with timeout |
| SEC-04 | Path traversal in `--file` argument | High | Resolve path; reject `../../etc/passwd` patterns | `Path.resolve()` + root check |
| SEC-05 | XSS via note content in graph tooltip | Medium | Escape HTML in `content_preview` before injecting to vis-network | HTML escape |
| SEC-06 | Public deployment exposes personal notes | High | v1: demo with curated sample notes only; warn in README | Review committed wiki/ |
| SEC-07 | `.env` leaked in git history | Critical | Rotate API key immediately; use `git filter-repo` | `git log -- .env` |

---

## 12. Performance Edge Cases

| ID | Scenario | Impact | Threshold | Mitigation |
|----|----------|--------|-----------|------------|
| PERF-01 | O(n²) similarity with 500+ notes | High | > 500 notes | Document FAISS as post-v1 upgrade |
| PERF-02 | Embedding model load time (~5s) | Medium | Every cold start | Cache model in memory (singleton) |
| PERF-03 | `classify.py` batch of 100 notes | Medium | Groq rate limits | Add delay between API calls (0.5s) |
| PERF-04 | Graph render with 200+ nodes | Medium | Browser lag | Cap display or cluster nodes |
| PERF-05 | Large `graph.json` (> 5 MB) | Low | Slow page load | Compress previews; lazy-load content |
| PERF-06 | `sentence-transformers` RAM usage (~500 MB) | Medium | Low-memory environments | Document 2 GB RAM minimum |
| PERF-07 | Repeated `ask()` without caching | Low | Redundant embedding | Embed question once per call |

---

## 13. Corner Scenarios by User Journey

### Journey 1: First-Time User (Empty System)

```
User opens app → no graph.json → no wiki → no embeddings
```

| Step | Edge Case | Expected UX |
|------|-----------|-------------|
| Open app | No data at all | "Welcome! Run capture.py to get started" |
| Ask question | Empty knowledge base | "No notes found. Capture something first." |
| View graph | Zero nodes | Empty state illustration + setup commands |

### Journey 2: Power User (100+ Notes)

```
User has been capturing for weeks → performance degrades
```

| Step | Edge Case | Expected UX |
|------|-----------|-------------|
| Link notes | O(n²) slowdown | Progress bar; document FAISS upgrade path |
| View graph | Cluttered graph | Category filter in sidebar (post-v1) |
| Ask question | Slow retrieval | Spinner; response within 15s |

### Journey 3: Deployed Demo Visitor

```
Anonymous user opens public URL
```

| Step | Edge Case | Expected UX |
|------|-----------|-------------|
| View graph | Pre-loaded demo data | Graph renders without setup |
| Ask question | Uses Groq API key (owner's) | Answer from demo notes |
| Spam questions | Rate limit hit | "Too many requests. Try again later." |

---

## 14. Edge Case Test Matrix (Phase 6–7 Checklist)

Use this checklist during integration testing. Mark each item after verifying expected behavior.

### Capture (`capture.py`)

- [ ] CAP-01: No arguments → usage help
- [ ] CAP-03: Empty note → rejected
- [ ] CAP-08: Invalid URL → rejected or warned
- [ ] CAP-14: Missing file → error exit 1
- [ ] CAP-25: Windows timestamp sanitization
- [ ] CAP-06: Unicode/emoji preserved

### Classify (`classify.py`)

- [ ] CLS-01: Empty raw/ → graceful message
- [ ] CLS-02: Re-run → skips processed
- [ ] CLS-08: API timeout → retries
- [ ] CLS-10: Bad LLM JSON → fallback category
- [ ] CLS-18: Slug collision → ID suffix

### Link (`link.py`)

- [ ] LNK-02: Single note → embedding only, no links
- [ ] LNK-05: Re-run → skips existing embeddings
- [ ] LNK-09: No matches → no links, no error
- [ ] LNK-13: Re-run → no duplicate links

### Graph (`build_graph.py`)

- [ ] GRPH-01: Empty wiki → zero-node graph
- [ ] GRPH-04: Orphan edges → removed
- [ ] GRPH-07: Isolated nodes → included

### Ask (`ask.py`)

- [ ] ASK-01: Empty question → rejected
- [ ] ASK-04: Irrelevant question → "not enough information"
- [ ] ASK-08: API failure → error message

### App (`app.py`)

- [ ] APP-01: Missing graph.json → auto-rebuild or instructions
- [ ] APP-03: Zero nodes → empty state
- [ ] APP-07: Empty ask input → validation message

### Pipeline

- [ ] PIPE-05: Re-run pipeline → idempotent
- [ ] PIPE-11: Out-of-order steps → clear errors
- [ ] PIPE-06: New capture → graph stale until rebuild

### Deployment

- [ ] DEP-01: Missing API secret → graceful degradation
- [ ] DEP-05: No data committed → empty or auto-build
- [ ] DEP-06: Large graph → loads without crash

---

## 15. Priority Summary

### Must Fix Before Deployment (Critical / High)

| ID | Scenario | Module |
|----|----------|--------|
| CFG-01 | Missing API key | `config.py` |
| CAP-14 | File not found | `capture.py` |
| CAP-25 | Windows filename colon | `capture.py` |
| SEC-04 | Path traversal | `capture.py` |
| SEC-06 | Personal data on public URL | deployment |
| CLS-08 | API timeout retry | `classify.py` |
| CLS-10 | Invalid LLM JSON fallback | `classify.py` |
| ASK-04 | No relevant notes response | `ask.py` |
| APP-01 | Missing graph.json recovery | `app.py` |
| DEP-01 | Missing deploy secret | `app.py` |

### Can Defer to Post-v1 (Low / Medium)

| ID | Scenario | Workaround |
|----|----------|------------|
| CAP-17 | PDF extraction | Placeholder text |
| LNK-11 | Threshold tuning | Document in README |
| PERF-01 | 500+ notes slowdown | FAISS upgrade |
| APP-11 | Mobile layout | Desktop-first demo |
| DEP-07 | Streamlit sleep | Accept for demo |

---

## 16. Quick Reference — Error Messages

Standardize these messages across modules for consistent UX:

| Situation | Message |
|-----------|---------|
| Missing API key | `"GROQ_API_KEY not found. Add it to .env or Streamlit secrets."` |
| Empty input | `"Input cannot be empty."` |
| File not found | `"File not found: {path}"` |
| No captures | `"No captures to classify. Run capture.py first."` |
| No wiki notes | `"No wiki notes found. Run classify.py first."` |
| No relevant answer | `"I don't have enough information to answer that."` |
| API failure | `"Unable to reach AI service. Please try again."` |
| Empty graph | `"No notes yet. Capture and classify to build your brain."` |
| Corrupt file | `"Skipping corrupt file: {filename}"` |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [`problemstatement.md`](./problemstatement.md) | What we're building |
| [`architecture.md`](./architecture.md) | How the system is designed |
| [`implementation.md`](./implementation.md) | Phase-wise build plan |

**Next step:** Implement Phase 0 per `implementation.md`, using this document as the test reference for Phases 6–7.
