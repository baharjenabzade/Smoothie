import streamlit as st

from utils.data_loader import load_part3
from ai.evaluator import evaluate_part3


def show_part3():

    st.title("💬 IELTS Speaking Part 3")

    st.write(
        "Practice abstract discussion questions "
        "and develop stronger arguments."
    )

    data = load_part3()

    selected_topic = st.selectbox(
        "Choose a topic",
        [item["topic"] for item in data]
    )

    topic_data = next(
        item for item in data
        if item["topic"] == selected_topic
    )

    st.divider()

    st.subheader("📚 Topic Vocabulary")

    cols = st.columns(2)

    for i, word in enumerate(topic_data["vocabulary"]):

        with cols[i % 2]:

            st.info(word)

    st.subheader("🔗 Useful Collocations")

    for collocation in topic_data["collocations"]:

        st.markdown(
            f"- **{collocation}**"
        )

    st.divider()

    for index, question in enumerate(
        topic_data["questions"]
    ):

        st.subheader(
            f"Question {index + 1}"
        )

        st.write(question)

        answer = st.text_area(
            "Your answer:",
            key=f"part3_answer_{selected_topic}_{index}",
            height=180
        )

        if st.button(
            "Evaluate",
            key=f"part3_evaluate_{selected_topic}_{index}"
        ):

            if not answer.strip():

                st.warning(
                    "Please enter your answer."
                )

            else:

                with st.spinner(
                    "AI examiner is evaluating your response..."
                ):

                    feedback = evaluate_part3(
                        question,
                        answer
                    )

                st.markdown("## 📊 Feedback")

                st.markdown(feedback)

        st.divider()