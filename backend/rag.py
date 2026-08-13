"""
RAG retrieval + answering, adapted from Phase 1's chat.py.

Key change from Phase 1: retrieval is now scoped to a single subject/course
via a metadata filter, so a question asked in the "Finance" conversation
only pulls from Finance material — not AI or BBA content leaking in.
"""

import os
from dotenv import load_dotenv
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from groq import Groq

load_dotenv()

# Resolve relative to THIS file, not the current working directory — so it
# works whether uvicorn is launched from backend/ or the project root.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join(_PROJECT_ROOT, "chroma_db"))

TOP_K = 4

# llama-3.3-70b-versatile was deprecated by Groq (announced June 17, 2026).
# openai/gpt-oss-120b is Groq's recommended replacement.
# Check https://console.groq.com/docs/models for current model names.
MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

SYSTEM_PROMPT = """You are a study assistant for the subject: {subject}.

Strict rules:
- Answer ONLY using the provided context below. If the answer isn't in \
the context, say clearly: "That's not covered in the material I have — \
I won't guess." Do not use outside knowledge to fill the gap.
- Every claim must be traceable to the provided context — tag it with \
[source.pdf, page N] right after the claim.
- Be direct. Don't pad answers with unnecessary caveats once you've \
answered from the context.

Tone rules — this matters as much as the grounding rule:
- State facts directly, in your own words, like a knowledgeable tutor \
talking to a student — not like a system narrating its own sourcing. \
Never say "the course material defines...", "it is also described as...", \
"according to the material..." or similar meta-phrases. The citation tag \
after the sentence already shows where it came from; you don't need to \
say it in words too.
- Don't wrap long phrases from the source in quotation marks. Paraphrase \
in plain language instead — quoting is only for a genuinely short, \
load-bearing term (a single technical term or short definition), never \
a full sentence.
- Write the way you'd explain it out loud to someone studying for an \
exam, not the way you'd write a legal citation.

Diagrams:
- When a question is about a process, sequence, architecture, pipeline, \
network/graph structure, or anything else with real spatial or \
step-by-step structure — and especially if the person asks for a \
diagram, graph, flowchart, or visual — include a Mermaid diagram, built \
only from what's in the provided context.
- Put it in its own fenced code block starting with ```mermaid and \
ending with ``` — never draw the diagram as ASCII art or plain text, \
and never put anything other than valid Mermaid syntax inside that \
fenced block.
- Use the Mermaid diagram type that actually fits: flowchart (`graph TD` \
/ `graph LR`) for processes and pipelines, `sequenceDiagram` for \
interactions over time, `classDiagram` or `graph` for structures and \
relationships (e.g. a Bayesian network's nodes and arcs).
Voice:
- You're a tutor who's genuinely glad to help, not a search engine with a \
personality bolted on. Warm and encouraging is good; filler and fake \
enthusiasm are not — earn the warmth by being useful.
- It's fine to briefly acknowledge a good question or connect it to what \
the student asked before, when that's natural. Don't do this every \
single message or it becomes noise.
"""

CORRECTION_INSTRUCTIONS = """
The student flagged your previous answer as wrong or unclear. Their note: \
"{note}"

Re-answer the same question from scratch, using the same context rules \
above. Take the correction seriously — if they're right, fix it plainly \
("You're right, here's the correct version:"). If the context actually \
supports your original answer, say so clearly and point to exactly where \
in the context it's grounded, rather than just repeating yourself. Don't \
be defensive either way.
"""

_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
_client = PersistentClient(path=CHROMA_DIR)
_collection = _client.get_or_create_collection(
    name="study_material", embedding_function=_embedding_fn
)

_groq_client = None


def get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set — check your .env file")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def retrieve(question: str, subject: str, k: int = TOP_K):
    """Retrieval scoped to a single subject via metadata filter — this is
    what keeps courses from bleeding into each other. Normalized to
    lowercase to match how ingest.py stores subjects, regardless of how
    the course name is capitalized when it arrives from the API."""
    results = _collection.query(
        query_texts=[question],
        n_results=k,
        where={"subject": subject.lower()},
    )
    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    return list(zip(chunks, metadatas))


def build_context(retrieved) -> str:
    parts = []
    for chunk, meta in retrieved:
        tag = f"[{meta['source']}, page {meta['page']}]"
        parts.append(f"{tag}\n{chunk}")
    return "\n\n---\n\n".join(parts)


def _call_groq(messages: list[dict]) -> str:
    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.1,
            messages=messages,
        )
    except Exception as e:
        # Surface the real reason (bad model name, bad key, rate limit, etc.)
        # instead of letting it bubble into a generic, bodyless 500.
        raise RuntimeError(f"Groq API call failed: {e}") from e
    return response.choices[0].message.content


def answer_question(question: str, subject: str, history: list[dict]) -> str:
    """
    subject: must match the 'subject' value used when ingesting PDFs
             (see ingest.py) — keep this consistent with your data/
             subfolder naming, e.g. normalize both to lowercase.
    history: prior turns in this conversation, as [{"role", "content"}, ...]
             — used for conversational continuity, not for retrieval.
    """
    retrieved = retrieve(question, subject)

    if not retrieved:
        return (
            f"I don't have any material loaded for {subject} yet. "
            f"Run ingest.py with PDFs in data/{subject.lower()}/ first."
        )

    context = build_context(retrieved)
    user_message = (
        f"Context from {subject} course material:\n\n{context}\n\n"
        f"---\n\nQuestion: {question}"
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(subject=subject)}]
    messages.extend(history[-6:])  # last few turns, kept short to control token cost
    messages.append({"role": "user", "content": user_message})

    return _call_groq(messages)


def regenerate_answer(question: str, prior_answer: str, note: str, subject: str, history: list[dict]) -> str:
    """Re-answers the same question after the student flags the prior
    answer as wrong, with the correction note folded into the system
    prompt. Retrieval is re-run (not reused) in case the original
    retrieval simply missed the right chunk."""
    retrieved = retrieve(question, subject)
    if not retrieved:
        return (
            f"I don't have any material loaded for {subject} yet. "
            f"Run ingest.py with PDFs in data/{subject.lower()}/ first."
        )

    context = build_context(retrieved)
    user_message = (
        f"Context from {subject} course material:\n\n{context}\n\n"
        f"---\n\nOriginal question: {question}\n\n"
        f"Your previous answer:\n{prior_answer}"
    )

    system = SYSTEM_PROMPT.format(subject=subject) + CORRECTION_INSTRUCTIONS.format(note=note or "It didn't look right.")
    messages = [{"role": "system", "content": system}]
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})

    return _call_groq(messages)