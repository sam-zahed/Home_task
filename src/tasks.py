from collections import defaultdict
from typing import Any

from .models import Chunk, Document, Query, RetrievedChunk


def split_text_fixed(text: str, max_chars: int) -> list[str]:
    '''
    Split text into fixed-size chunks.

    Expected behavior:
    - strip surrounding whitespace
    - return [] for empty text
    - if max_chars <= 0, raise ValueError
    '''
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than 0")

    stripped = text.strip()
    if not stripped:
        return []

    return [stripped[i:i + max_chars] for i in range(0, len(stripped), max_chars)]


def chunk_document(document: Document, max_chars: int = 80) -> list[Chunk]:
    '''
    Convert a Document into retrieval Chunk objects.

    Rules:
    - preserve document and section metadata
    - skip empty sections
    - split long content using split_text_fixed
    - use deterministic chunk IDs
    '''
    chunks: list[Chunk] = []
    section_type_counter: dict[str, int] = defaultdict(int)

    for section in document.sections:
        parts = split_text_fixed(section.content, max_chars)
        if not parts:
            continue

        base_index = section_type_counter[section.section_type]

        metadata = {
            "source_type": document.source_type,
            "source_ref": document.source_ref,
            **document.metadata,
            **section.metadata,
        }

        for index, part in enumerate(parts):
            chunks.append(
                Chunk(
                    chunk_id=f"{document.document_id}:{section.section_type}:{base_index + index}",
                    document_id=document.document_id,
                    text=part,
                    section_type=section.section_type,
                    page_number=section.page_number,
                    metadata=metadata.copy(),
                )
            )

        section_type_counter[section.section_type] += len(parts)

    return chunks


def filter_chunks_by_metadata(
    chunks: list[RetrievedChunk],
    metadata_filter: dict[str, Any] | None,
) -> list[RetrievedChunk]:
    '''
    Return only chunks that match every key/value pair in metadata_filter.
    If metadata_filter is empty or None, return the input unchanged.
    '''
    if not metadata_filter:
        return chunks

    return [
        chunk
        for chunk in chunks
        if all(chunk.metadata.get(key) == value for key, value in metadata_filter.items())
    ]


def hybrid_retrieve(
    *,
    dense_results: list[RetrievedChunk],
    lexical_results: list[RetrievedChunk],
    query: Query,
    rank_constant: int = 60,
    solution_boost: float = 1.15,
) -> list[RetrievedChunk]:
    '''
    Fuse dense_results and lexical_results with Reciprocal Rank Fusion.

    Requirements:
    - apply query.metadata filtering before fusion
    - merge duplicates by chunk_id
    - keep document_id, text, section_type, page_number, metadata
    - assign the fused score to the returned RetrievedChunk.score
    - apply solution_boost after fusion
    - sort by score descending, then chunk_id ascending
    - return at most query.top_k items
    '''
    filtered_dense = filter_chunks_by_metadata(dense_results, query.metadata)
    filtered_lexical = filter_chunks_by_metadata(lexical_results, query.metadata)

    fused_scores: dict[str, float] = defaultdict(float)
    chunk_by_id: dict[str, RetrievedChunk] = {}

    for ranked_list in (filtered_dense, filtered_lexical):
        for rank_position, chunk in enumerate(ranked_list, start=1):
            fused_scores[chunk.chunk_id] += 1 / (rank_constant + rank_position)
            chunk_by_id.setdefault(chunk.chunk_id, chunk)

    fused_results: list[RetrievedChunk] = []
    for chunk_id, score in fused_scores.items():
        original = chunk_by_id[chunk_id]
        final_score = score
        if original.section_type == "solution":
            final_score *= solution_boost

        fused_results.append(
            RetrievedChunk(
                chunk_id=original.chunk_id,
                document_id=original.document_id,
                text=original.text,
                score=final_score,
                section_type=original.section_type,
                page_number=original.page_number,
                metadata=original.metadata.copy(),
            )
        )

    fused_results.sort(key=lambda chunk: (-chunk.score, chunk.chunk_id))
    return fused_results[:query.top_k]


def build_answer_payload(
    query: Query,
    retrieved_chunks: list[RetrievedChunk],
    max_citation_chunks: int = 3,
) -> dict[str, Any]:
    '''
    Build a response payload with:
    - answer
    - citations
    - metadata

    Do not call any external model.
    '''
    if not retrieved_chunks:
        return {
            "answer": "I could not find relevant support content.",
            "citations": [],
            "metadata": {
                "query": query.text,
                "result_count": 0,
            },
        }

    answer_chunks = retrieved_chunks[:max_citation_chunks]
    answer = " ".join(chunk.text for chunk in answer_chunks)

    citations = []
    seen_chunk_ids: set[str] = set()
    for chunk in retrieved_chunks:
        if chunk.chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(chunk.chunk_id)
        citations.append(
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "section_type": chunk.section_type,
                "page_number": chunk.page_number,
                "source_type": chunk.metadata["source_type"],
                "source_ref": chunk.metadata["source_ref"],
            }
        )
        if len(citations) >= max_citation_chunks:
            break

    return {
        "answer": answer,
        "citations": citations,
        "metadata": {
            "query": query.text,
            "result_count": len(retrieved_chunks),
        },
    }
