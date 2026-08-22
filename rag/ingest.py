from pathlib import Path
import hashlib

from pypdf import PdfReader
from docx import Document

from rag.database import add_document


def create_id(text):

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def chunk_text(
    text,
    chunk_size=800,
    overlap=150
):

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        )

        if chunk.strip():

            chunks.append(chunk)

        start += (
            chunk_size - overlap
        )

    return chunks


def extract_pdf(path):

    reader = PdfReader(path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            text += page_text + "\n"

    return text


def extract_docx(path):

    document = Document(path)

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():

            paragraphs.append(
                paragraph.text
            )

    return "\n".join(paragraphs)


def extract_txt(path):

    return Path(path).read_text(
        encoding="utf-8"
    )


def extract_file(path):

    extension = Path(path).suffix.lower()

    if extension == ".pdf":

        return extract_pdf(path)

    elif extension == ".docx":

        return extract_docx(path)

    elif extension == ".txt":

        return extract_txt(path)

    else:

        raise ValueError(
            f"Unsupported file type: {extension}"
        )


def ingest_file(
    path,
    source_name,
    category="general",
    topic="general"
):

    text = extract_file(path)

    chunks = chunk_text(text)

    added = 0

    for index, chunk in enumerate(chunks):

        document_id = create_id(
            f"{source_name}_{index}_{chunk}"
        )

        metadata = {
            "source": source_name,
            "category": category,
            "topic": topic,
            "chunk": index
        }

        add_document(
            text=chunk,
            metadata=metadata,
            document_id=document_id
        )

        added += 1

    return added