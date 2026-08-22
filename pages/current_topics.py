import streamlit as st

from rag.database import (
    collection,
    load_part1_topics
)


def show_current_topics():

    st.title("🔥 Current IELTS Speaking Topics")

    st.caption(
        "Reported preparation topics — May to August 2026. "
        "These are not guaranteed exam questions."
    )

    st.divider()

    if "topics_loaded" not in st.session_state:

        st.session_state.topics_loaded = (
            collection.count() > 0
        )

    if not st.session_state.topics_loaded:

        st.warning(
            "Your IELTS Part 1 knowledge base "
            "has not been initialized yet."
        )

        if st.button(
            "📥 Load Current Part 1 Topics"
        ):

            with st.spinner(
                "Building IELTS knowledge base..."
            ):

                count = load_part1_topics()

            st.session_state.topics_loaded = True

            st.success(
                f"Loaded {count} IELTS topics."
            )

            st.rerun()

    else:

        st.success(
            f"{collection.count()} IELTS questions "
            "are currently available in your RAG database."
        )

    st.divider()

    st.subheader(
        "Current Topic Bank"
    )

    topics = [
        ("🎧", "Headphones", "NEW", "High"),
        ("📱", "Social Media", "NEW", "High"),
        ("👩‍🏫", "Teachers", "NEW", "High"),
        ("⌚", "Watches", "NEW", "High"),
        ("🔬", "Science", "NEW", "High"),
        ("🌳", "Parks", "NEW", "Medium"),
        ("🚗", "Cars", "NEW", "High"),
        ("🌐", "Websites", "NEW", "Medium"),
        ("🪞", "Mirrors", "NEW", "Medium"),
        ("🛍️", "Shopping", "NEW", "Medium"),
        ("🎵", "Music", "NEW", "High"),
        ("👕", "Clothing", "NEW", "Medium"),
        ("🎬", "Films & Cinemas", "NEW", "High"),
        ("🎨", "Art", "RETAINED", "Medium"),
        ("🎤", "Singing", "NEW", "Medium"),
        ("🏛️", "History", "NEW", "Medium"),
        ("🌅", "Morning Time", "NEW", "Medium"),
        ("🌌", "Outer Space & Stars", "NEW", "Medium"),
        ("🏢", "Old Buildings", "NEW", "Medium"),
        ("⚽", "Sports Programs", "NEW", "Medium"),
        ("😄", "Jokes & Comedies", "NEW", "Medium"),
        ("🧹", "Tidiness", "NEW", "Medium")
    ]

    for emoji, topic, status, frequency in topics:

        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [3, 1, 1]
            )

            with col1:

                st.markdown(
                    f"### {emoji} {topic}"
                )

            with col2:

                st.write(status)

            with col3:

                st.write(frequency)