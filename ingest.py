"""
Ingest PDFs into a local vector store (ChromaDB).

Drop PDFs into the data/ folder, tagged by subject subfolder, e.g.:
    data/ai/artificial_intelligence_tutorial.pdf
    data/finance/principles_of_finance.pdf

Folder names should match your course names exactly (lowercased, spaces
kept as-is) — see rag.py, which lowercases the incoming course name
before filtering by subject.

Run: python ingest.py

Safe to re-run any time — uses upsert (not add), so re-ingesting the
same file overwrites its old chunks instead of erroring on duplicate IDs.
A failure on one PDF is logged and skipped, not fatal to the whole run.
"""

import hashlib
from pathlib import Path
from pypdf import PdfReader
import chromadb
from chromadb.utils import embedding_functions

DATA_DIR = Path("data")
CHROMA_DIR = "chroma_db"
CHUNK_SIZE = 800       # characters per chunk
CHUNK_OVERLAP = 150    # overlap so context isn't cut mid-idea

# Free, local embedding model — no API key, no cost.
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Simple sliding-window chunker."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return [c.strip() for c in chunks if c.strip()]


def extract_pdf_text(pdf_path: Path) -> list[tuple[str, int]]:
    """Returns list of (page_text, page_number) tuples."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((text, i + 1))
    return pages


def make_chunk_id(subject: str, filename: str, page_num: int, chunk_idx: int) -> str:
    """Deterministic ID from content identity, not a global counter.
    Same file + page + chunk always produces the same ID, so re-running
    ingest.py overwrites cleanly via upsert instead of colliding."""
    raw = f"{subject}::{filename}::p{page_num}::c{chunk_idx}"
    return hashlib.sha1(raw.encode()).hexdigest()


def ingest_pdf(collection, pdf_path: Path, subject: str) -> int:
    """Ingests one PDF. Returns number of chunks added. Raises on failure
    so the caller can log and continue with the next file.

    Deletes any existing chunks for this (subject, filename) pair first.
    Without this, replacing a PDF with an updated version can leave stale
    chunks behind — either because the new file has fewer chunks on some
    page than the old one (so old IDs never get overwritten), or because
    you renamed the file (so the old one just sits there alongside the
    new one, and retrieval mixes outdated content with current content)."""
    collection.delete(where={
        "$and": [{"subject": subject}, {"source": pdf_path.name}]
    })

    pages = extract_pdf_text(pdf_path)
    chunk_count = 0

    for page_text, page_num in pages:
        chunks = chunk_text(page_text, CHUNK_SIZE, CHUNK_OVERLAP)
        for chunk_idx, chunk in enumerate(chunks):
            chunk_id = make_chunk_id(subject, pdf_path.name, page_num, chunk_idx)
            collection.upsert(
                ids=[chunk_id],
                documents=[chunk],
                metadatas=[{
                    "subject": subject,
                    "source": pdf_path.name,
                    "page": page_num,
                }],
            )
            chunk_count += 1

    return chunk_count


def main():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name="study_material",
        embedding_function=embedding_fn,
    )

    if not DATA_DIR.exists():
        print("No data/ folder found. Create it and add subject subfolders with PDFs.")
        return

    subject_dirs = sorted([d for d in DATA_DIR.iterdir() if d.is_dir()])
    if not subject_dirs:
        print(f"No subject subfolders found inside {DATA_DIR}/. Nothing to ingest.")
        return

    print(f"Found {len(subject_dirs)} subject folder(s): {[d.name for d in subject_dirs]}\n")

    total_chunks = 0
    summary = {}

    for subject_dir in subject_dirs:
        subject = subject_dir.name.lower()
        pdf_files = list(subject_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"[{subject}] No PDFs found — skipping.")
            summary[subject] = 0
            continue

        subject_chunks = 0
        for pdf_path in pdf_files:
            print(f"[{subject}] Processing {pdf_path.name}...")
            try:
                added = ingest_pdf(collection, pdf_path, subject)
                subject_chunks += added
                print(f"[{subject}]   -> {added} chunks ingested")
            except Exception as e:
                # Log and continue — one bad PDF should never take down
                # the rest of the run.
                print(f"[{subject}]   !! FAILED on {pdf_path.name}: {e}")

        summary[subject] = subject_chunks
        total_chunks += subject_chunks

    print(f"\n{'='*50}")
    print("Ingestion summary:")
    for subject, count in summary.items():
        status = "OK" if count > 0 else "EMPTY/FAILED"
        print(f"  {subject:25s} {count:5d} chunks   [{status}]")
    print(f"{'='*50}")
    print(f"Done. Ingested {total_chunks} total chunks into '{CHROMA_DIR}'.")


if __name__ == "__main__":
    main()