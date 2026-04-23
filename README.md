# RAG Backend — Interview Task

A mini **Retrieval-Augmented Generation** backend covering ingestion, retrieval, and answer construction.

## Project Structure

```
├── tasks.ipynb            # Main notebook with implementation & inline tests
├── src/
│   ├── __init__.py
│   ├── models.py          # Dataclasses: Document, Chunk, RetrievedChunk, Query
│   └── tasks.py           # Core functions (chunking, retrieval, answer payload)
├── tests/
│   └── test_task.py       # Pytest suite
├── pyproject.toml
└── README.md
```

## Tasks Overview

### Task 1 — Chunking with Metadata Preservation

**Functions:** `split_text_fixed`, `chunk_document`

Converts `Document` objects into retrieval-ready `Chunk` objects.

- Splits long sections using a fixed-size character splitter
- Produces deterministic chunk IDs in the format `DocumentID:SectionType:Index`
- Preserves document-level and section-level metadata, `page_number`, `source_type`, and `source_ref`
- Skips sections whose content is empty or whitespace-only
- Raises `ValueError` when `max_chars <= 0`

### Task 2 — Hybrid Retrieval with Metadata Filtering

**Functions:** `filter_chunks_by_metadata`, `hybrid_retrieve`

Fuses dense and lexical retrieval results using **Reciprocal Rank Fusion (RRF)**.

- **Metadata filtering:** AND logic — a chunk must match *all* provided filter key/value pairs
- **RRF formula:** `rrf_score += 1 / (rank_constant + rank_position)` with `rank_position` starting at **1**
- **Deduplication:** chunks appearing in both lists are merged by `chunk_id`, scores accumulated
- **Solution boost:** applied *after* fusion — `solution` chunks get their fused score multiplied by `solution_boost`
- **Sorting:** descending by score, ascending by `chunk_id` as tiebreaker
- Returns at most `query.top_k` results

### Task 3 — Answer Payload with Citations

**Function:** `build_answer_payload`

Constructs a structured response dictionary.

```python
{
    "answer": "...",
    "citations": [
        {
            "chunk_id": "...",
            "document_id": "...",
            "section_type": "...",
            "page_number": 4,
            "source_type": "pdf",
            "source_ref": "vpn-manual.pdf",
        }
    ],
    "metadata": {
        "query": "...",
        "result_count": 2,
    },
}
```

- Concatenates top chunk texts into a short answer
- Citations are unique by `chunk_id` and maintain ranking order
- Fallback: returns `"I could not find relevant support content."` when no results exist

## Setup & Running

**Requirements:** Python ≥ 3.11

### Install test dependency

```bash
python -m pip install pytest
```

### Run tests

```bash
python -m pytest tests/ -v
```

### Run via notebook

Open `tasks.ipynb` and run all cells. Each task section includes inline assertions that print a pass/fail message.

## Design Decisions

| Decision | Rationale |
|---|---|
| Fixed-size chunking | Simple and predictable; sufficient for this exercise without semantic chunking overhead |
| RRF over score interpolation | Dense and lexical scores are on different scales; rank-based fusion is scale-agnostic |
| Solution boost post-fusion | Ensures the boost does not distort individual ranking contributions |
| `defaultdict` for score accumulation | Clean deduplication — same `chunk_id` from both sources automatically sums |
| Global `section_type_counter` | Prevents chunk ID collisions when multiple sections share the same `section_type` |
