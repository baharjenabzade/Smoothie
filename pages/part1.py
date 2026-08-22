import streamlit as st

from rag.database import search_documents
from ai.rag import generate_part1_help


def show_part1():

    st.title("🎤 IELTS Speaking Part 1")

    st.write(
        "Practice IELTS Speaking Part 1 with AI-generated "
        "ideas, vocabulary, collocations, and sample answers."
    )

    question = st.text_input(
        "Enter a Part 1 question",
        placeholder="e.g. Do you listen to music?"
    )

    if st.button("✨ Get AI Help", use_container_width=True):

        if not question.strip():

            st.warning("Please enter a Part 1 question.")

            return

        # --------------------------------------------------
        # SEARCH KNOWLEDGE BASE
        # --------------------------------------------------

        with st.spinner(
            "Searching IELTS knowledge base..."
        ):

            results = search_documents(
                question,
                n_results=8
            )

        # --------------------------------------------------
        # GENERATE IELTS GUIDANCE
        # --------------------------------------------------

        with st.spinner(
            "Generating IELTS guidance..."
        ):

            response = generate_part1_help(
                question=question,
                knowledge_results=results
                )

        # --------------------------------------------------
        # DISPLAY RESULT
        # --------------------------------------------------

        st.divider()

        st.markdown(response)

        # --------------------------------------------------
        # KNOWLEDGE BASE SOURCES
        # --------------------------------------------------

        if results:

            st.divider()

            st.subheader("📚 Knowledge Used")

            for _, metadata in results:

                topic = metadata.get(
                    "topic",
                    "General"
                )

                frequency = metadata.get(
                    "frequency",
                    "N/A"
                )

                st.caption(
                    f"**Topic:** {topic} | "
                    f"**Frequency:** {frequency}"
                )