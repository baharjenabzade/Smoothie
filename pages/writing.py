import streamlit as st

from utils.data_loader import load_writing
from ai.evaluator import (
    generate_essay,
    evaluate_essay
)


def show_writing():

    st.title("✍️ IELTS Writing Task 2")

    st.write(
        "Generate model essays, study their structure, "
        "or submit your own essay for AI feedback."
    )

    data = load_writing()

    essay_types = [
        item["type"]
        for item in data
    ]

    selected_type = st.selectbox(
        "Question type",
        essay_types
    )

    item = next(
        x for x in data
        if x["type"] == selected_type
    )

    st.divider()

    st.subheader("📝 IELTS Question")

    st.info(
        item["question"]
    )

    st.divider()

    tab1, tab2 = st.tabs(
        [
            "🤖 Generate Model Essay",
            "📝 Evaluate My Essay"
        ]
    )

    with tab1:

        st.write(
            "Generate a Band 8-style model essay "
            "and study the vocabulary and ideas."
        )

        if st.button(
            "Generate Essay",
            type="primary"
        ):

            with st.spinner(
                "Writing your model essay..."
            ):

                result = generate_essay(
                    item["question"]
                )

            st.markdown(result)

    with tab2:

        essay = st.text_area(
            "Paste your IELTS essay here:",
            height=400
        )

        word_count = len(
            essay.split()
        )

        st.write(
            f"Word count: **{word_count}**"
        )

        if word_count < 250:

            st.warning(
                "IELTS Writing Task 2 requires at least 250 words."
            )

        if st.button(
            "Evaluate My Essay",
            type="primary"
        ):

            if not essay.strip():

                st.warning(
                    "Please enter your essay."
                )

            else:

                with st.spinner(
                    "The AI examiner is evaluating your essay..."
                ):

                    result = evaluate_essay(
                        item["question"],
                        essay
                    )

                st.markdown(
                    result
                )