---
name: add-poetry-data
description: Workflow for adding new poetry data from external sources (e.g. chinese-poetry repo) into this project
---

# Add Poetry Data Workflow

## Goal
Extract 五言/七言 couplets (片句) from external poetry data sources and merge them into the project's poetry database.

## Data Format

**poetry-data.json** (full data):
```json
{
  "titles": ["Title 0", "Title 1", ...],  // index-based lookup
  "authors": ["Author 0", "Author 1", ...],
  "couplets": [
    ["上句", "下句", titleIndex, authorIndex],  // full couplet format
    ...
  ]
}
```

**poetry-data-lite.json** (distilled, max ~10K entries): same format, includes a 5th field `heat` score per couplet.

## Steps

### 1. Clone source data
Clone the `chinese-poetry` repo. On Windows, may need a proxy:
```
$env:HTTP_PROXY = "http://127.0.0.1:7890"
$env:HTTPS_PROXY = "http://127.0.0.1:7890"
git clone --depth 1 https://github.com/chinese-poetry/chinese-poetry.git
```

### 2. Understand source format
Each poetry JSON file has entries like:
```json
{"author": "苏轼", "paragraphs": ["上句内容，下句内容。", ...], "rhythmic": "词牌名"}
```
Note: 词 (ci poetry) has variable-length lines within paragraphs, not uniform 5/7 characters.

### 3. Extract 五言/七言片句
- Split each paragraph string on the first comma-like separator (，, ，；, etc.) to get upper/lower lines.
- Strip all punctuation, keep only Chinese characters.
- **Only keep pairs where BOTH upper and lower are exactly 5 or 7 characters, and match in length.**
- This filters out most 词 since they have irregular line lengths, but many 词 still contain valid 5/7 pairs.

### 4. Merge into poetry-data.json
- Load existing `poetry-data.json` and the extracted couplets.
- Build maps of `title_to_idx` and `author_to_idx` from existing data.
- For each new couplet: append new title/author strings if not seen, then append `[upper, lower, titleIdx, authorIdx]` to couplets.
- Deduplicate by `upper|lower|title|author` key.
- Save back as JSON.

### 5. Rebuild lite data (≤10K entries)
Use the existing distillation approach (see `build-scored-data.js` or `build-lite.py`):
- **Reference matching**: 唐诗三百首, 宋词三百首 (+500), textbook poems (+450).
- **Content matching**: famous lines like "明月几时有", "了却君王天下事" (+400).
- **Poet tiers**: S-tier (李白/杜甫/白居易/王维/苏轼) +200, A-tier +150, B-tier +100, C-tier +70.
- Score each poem, attach heat score to every couplet.
- Sort by heat descending, deduplicate, take top 10,000.
- Ensure all textbook-matched poems are included even if below cutoff.
- Remap title/author indices for the lite subset.

### 6. Test with the retriever
- Search for known famous phrases (e.g. "了却" → should find "了却君王天下事，赢得生前身后名" by 辛弃疾 with heat 999).
- Test both lite and full data paths.

### 7. Push to GitHub
Commit changes including:
- Updated `poetry-data.json` (note: file may exceed GitHub's 50MB recommendation)
- Updated `poetry-data-lite.json`
- Any new extraction/build scripts
- Updated `README.md` if feature description changes

Push. May need proxy on restricted networks.

## Files in this project
- `poetry-data.json` — full database (250K+ titles, 12K+ authors, 1.2M+ couplets)
- `poetry-data-lite.json` — distilled ~10K entries
- `build-scored-data.js` — original JS distillation script
- `build-lite.py` — Python equivalent distillation script
- `extract_song.py` — 宋词 extraction script (reusable pattern)
- `merge_song.py` — merge script (reusable pattern)
