import chromadb
import json
from pathlib import Path

from rag.embeddings import create_embedding


DB_PATH = "./chroma_db"

client = chromadb.PersistentClient(
    path=DB_PATH
)

collection = client.get_or_create_collection(
    name="ielts_part1",
    metadata={"hnsw:space": "cosine"}
)


def add_document(
    text,
    metadata,
    document_id
):

    embedding = create_embedding(text)

    collection.upsert(
        ids=[document_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata]
    )


def search_documents(
    query,
    n_results=5,
    topic=None
):

    embedding = create_embedding(query)

    where = None

    if topic:
        where = {
            "topic": topic
        }

    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where=where
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    return list(
        zip(documents, metadatas)
    )


def count_documents():

    return collection.count()


def load_part1_topics():

    path = Path(
        "data/part1_topics.json"
    )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        topics = json.load(f)

    for topic in topics:

        topic_name = topic["topic"]

        for question_index, question in enumerate(
            topic["questions"]
        ):

            text = f"""
IELTS SPEAKING PART 1

TOPIC:
{topic_name}

CURRENT CYCLE:
{topic["current_cycle"]}

STATUS:
{topic["status"]}

FREQUENCY:
{topic["frequency"]}

RELATED TOPICS:
{", ".join(topic["related_topics"])}

QUESTION:
{question["question"]}

QUESTION TYPE:
{question["question_type"]}

IDEAS:
{chr(10).join("- " + x for x in question["ideas"])}

VOCABULARY:
{", ".join(question["vocabulary"])}

COLLOCATIONS:
{", ".join(question["collocations"])}

SAMPLE ANSWER 1:
{question["sample_answers"][0]}

SAMPLE ANSWER 2:
{question["sample_answers"][1]}

SAMPLE ANSWER 3:
{question["sample_answers"][2]}
"""

            metadata = {
                "topic": topic_name,
                "part": "1",
                "cycle": topic["current_cycle"],
                "status": topic["status"],
                "frequency": topic["frequency"],
                "question": question["question"],
                "question_type": question["question_type"]
            }

            document_id = (
                f"{topic_name}_{question_index}"
                .lower()
                .replace(" ", "_")
            )

            add_document(
                text=text,
                metadata=metadata,
                document_id=document_id
            )

    return len(topics)