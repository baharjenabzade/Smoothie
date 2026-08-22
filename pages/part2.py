import streamlit as st

from utils.data_loader import load_part2
from rag.database import search_documents
from ai.part2 import generate_part2_help
from ai.evaluator import evaluate_part2


def show_part2():

    st.title("🎙️ IELTS Speaking Part 2")

    st.write(
        "Learn a memorable story, discover related cue cards, "
        "and practice your own two-minute response."
    )

    # ==================================================
    # LOAD CUE CARDS
    # ==================================================

    data = load_part2()

    if not data:

        st.error(
            "No Part 2 cue cards were found."
        )

        return

    selected = st.selectbox(
        "Choose a cue card",
        range(len(data)),
        format_func=lambda x: data[x]["topic"],
        key="part2_selected_card"
    )

    item = data[selected]

    current_question = item["question"]

    # ==================================================
    # RESET AI STORY WHEN CUE CARD CHANGES
    # ==================================================

    previous_question = st.session_state.get(
        "part2_story_question"
    )

    if (
        previous_question is not None
        and previous_question != current_question
    ):

        st.session_state.pop(
            "part2_story",
            None
        )

        st.session_state.pop(
            "part2_story_question",
            None
        )

    current_question = item["question"]

    # ==================================================
    # CUE CARD
    # ==================================================

    st.divider()

    st.subheader("📝 Cue Card")

    st.info(
        current_question
    )

    st.subheader(
        "You should talk about:"
    )

    for prompt in item["prompts"]:

        st.markdown(
            f"- {prompt}"
        )

    # ==================================================
    # AI STORY GENERATOR
    # ==================================================

    st.divider()

    st.subheader(
        "🧠 Build Your Two-Minute Story"
    )

    st.write(
        "The AI will create a memorable story based "
        "strictly on this cue card. You can then adapt "
        "the story to similar IELTS Part 2 topics."
    )

    if st.button(
        "✨ Generate My Story",
        use_container_width=True
    ):

        # ----------------------------------------------
        # SEARCH KNOWLEDGE BASE
        # ----------------------------------------------

        with st.spinner(
            "Searching the IELTS knowledge base..."
        ):

            results = search_documents(
                current_question,
                n_results=3
            )

        # ----------------------------------------------
        # GENERATE STORY
        # ----------------------------------------------

        with st.spinner(
            "Creating your two-minute story..."
        ):

            story = generate_part2_help(
                question=current_question,
                prompts=item["prompts"],
                knowledge_results=results
            )

        # ----------------------------------------------
        # SAVE STORY
        # ----------------------------------------------

        st.session_state[
            "part2_story"
        ] = story

        st.session_state[
            "part2_story_question"
        ] = current_question

    # ==================================================
    # DISPLAY AI STORY
    # ==================================================

    if (
        st.session_state.get(
            "part2_story_question"
        )
        == current_question
    ):

        st.divider()

        st.markdown(
            st.session_state["part2_story"]
        )

    # ==================================================
    # PREPARATION
    # ==================================================

    st.divider()

    st.subheader(
        "⏱️ 1-Minute Preparation"
    )

    st.write(
        "Use the preparation time to write keywords, "
        "not complete sentences."
    )

    if st.button(
        "▶️ Start 1-Minute Preparation"
    ):

        st.session_state[
            "part2_started"
        ] = True

    if st.session_state.get(
        "part2_started",
        False
    ):

        st.success(
            "Your preparation time has started. "
            "Organize your story using keywords."
        )

    # ==================================================
    # STUDENT ANSWER
    # ==================================================

    st.divider()

    st.subheader(
        "🎤 Your Two-Minute Answer"
    )

    answer = st.text_area(
        "Type your answer here:",
        height=350,
        placeholder=(
            "Tell your story naturally. "
            "Try to speak for approximately two minutes."
        )
    )

    # ==================================================
    # EVALUATION
    # ==================================================

    if st.button(
        "🤖 Evaluate My Part 2 Answer",
        use_container_width=True
    ):

        if not answer.strip():

            st.warning(
                "Please enter your answer."
            )

            return

        with st.spinner(
            "Evaluating your Part 2 response..."
        ):

            feedback = evaluate_part2(
                current_question,
                answer
            )

        st.divider()

        st.markdown(
            "## 📊 AI Feedback"
        )

        st.markdown(
            feedback
        )