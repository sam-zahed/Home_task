from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DocumentSection:
    section_type: str
    content: str
    heading: str | None = None
    page_number: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Document:
    document_id: str
    source_type: str
    source_ref: str
    title: str
    sections: list[DocumentSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    section_type: str
    page_number: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    score: float
    section_type: str
    page_number: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Query:
    text: str
    top_k: int = 5
    metadata: dict[str, Any] = field(default_factory=dict)


sample_documents = [
    Document(
        document_id="KB-001",
        source_type="kb",
        source_ref="KB-001",
        title="Reset VPN Access",
        metadata={"product": "vpn", "audience": "staff"},
        sections=[
            DocumentSection("title", "Reset VPN Access"),
            DocumentSection("description", "User cannot connect after a password change."),
            DocumentSection("solution", "Remove the saved VPN profile, sign in again, and re-approve MFA."),
            DocumentSection("notes", "Applies to managed Windows laptops."),
        ],
    ),
    Document(
        document_id="KB-002",
        source_type="kb",
        source_ref="KB-002",
        title="Install Office 365",
        metadata={"product": "office", "audience": "staff"},
        sections=[
            DocumentSection("title", "Install Office 365"),
            DocumentSection("description", "Guide for installing Office applications."),
            DocumentSection("solution", "Open Company Portal and install Microsoft 365 Apps."),
        ],
    ),
    Document(
        document_id="PDF-001",
        source_type="pdf",
        source_ref="vpn-manual.pdf",
        title="VPN Manual",
        metadata={"product": "vpn", "audience": "all"},
        sections=[
            DocumentSection("page_text", "Open the VPN client and select your university profile.", page_number=3),
            DocumentSection("page_text", "If login fails after a password reset, remove the old saved profile.", page_number=4),
            DocumentSection("page_text", "Approve the MFA request on your phone to complete sign-in.", page_number=4),
        ],
    ),
]

dense_results = [
    RetrievedChunk(
        chunk_id="KB-001:solution:0",
        document_id="KB-001",
        text="Remove the saved VPN profile.",
        score=0.91,
        section_type="solution",
        metadata={"source_type": "kb", "source_ref": "KB-001", "product": "vpn"},
    ),
    RetrievedChunk(
        chunk_id="PDF-001:page_text:1",
        document_id="PDF-001",
        text="If login fails after a password reset, remove the old saved profile.",
        score=0.89,
        section_type="page_text",
        page_number=4,
        metadata={"source_type": "pdf", "source_ref": "vpn-manual.pdf", "product": "vpn"},
    ),
    RetrievedChunk(
        chunk_id="KB-002:solution:0",
        document_id="KB-002",
        text="Open Company Portal and install Microsoft 365 Apps.",
        score=0.51,
        section_type="solution",
        metadata={"source_type": "kb", "source_ref": "KB-002", "product": "office"},
    ),
]

lexical_results = [
    RetrievedChunk(
        chunk_id="PDF-001:page_text:1",
        document_id="PDF-001",
        text="If login fails after a password reset, remove the old saved profile.",
        score=12.0,
        section_type="page_text",
        page_number=4,
        metadata={"source_type": "pdf", "source_ref": "vpn-manual.pdf", "product": "vpn"},
    ),
    RetrievedChunk(
        chunk_id="KB-001:solution:0",
        document_id="KB-001",
        text="Remove the saved VPN profile.",
        score=11.5,
        section_type="solution",
        metadata={"source_type": "kb", "source_ref": "KB-001", "product": "vpn"},
    ),
    RetrievedChunk(
        chunk_id="KB-002:solution:0",
        document_id="KB-002",
        text="Open Company Portal and install Microsoft 365 Apps.",
        score=8.8,
        section_type="solution",
        metadata={"source_type": "kb", "source_ref": "KB-002", "product": "office"},
    ),
]
