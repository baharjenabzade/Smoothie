import streamlit as st
import tempfile
import os

from rag.ingest import ingest_file
from rag.database import count_documents


def show_knowledge_base():

    st.title("📚 IELTS Knowledge Base")

    st.write(
        """
        Upload IELTS preparation documents to expand
        the AI tutor's knowledge.
        """
    )

    st.info(
        """
        Supported formats:
        PDF, DOCX, TXT
        """
    )

    uploaded_file = st.file_uploader(
        "Upload a document",
        type=[
            "pdf",
            "docx",
            "txt"
        ]
    )

    category = st.selectbox(
        "Document category",
        [
            "Part 1",
            "Part 2",
            "Part 3",
            "Vocabulary",
            "Collocations",
            "Writing",
            "General"
        ]
    )

    topic = st.text_input(
        "Topic",
        value="general"
    )

    if uploaded_file:

        if st.button(
            "➕ Add to Knowledge Base"
        ):

            suffix = os.path.splitext(
                uploaded_file.name
            )[1]

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            ) as temp:

                temp.write(
                    uploaded_file.read()
                )

                temp_path = temp.name

            try:

                with st.spinner(
                    "Processing document..."
                ):

                    chunks = ingest_file(
                        path=temp_path,
                        source_name=uploaded_file.name,
                        category=category,
                        topic=topic
                    )

                st.success(
                    f"Added {chunks} knowledge chunks."
                )

            finally:

                os.remove(
                    temp_path
                )

    st.divider()

    st.metric(
        "Knowledge chunks",
        count_documents()
    )