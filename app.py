import streamlit as st

from pages.part1 import show_part1
from pages.part2 import show_part2
from pages.part3 import show_part3
from pages.writing import show_writing
from pages.knowledge_base import show_knowledge_base

st.set_page_config(
    page_title="IELTS AI Learning",
    page_icon="🎓",
    layout="wide"
)


# -------------------------
# CSS
# -------------------------

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 10px;
    }

    .subtitle {
        text-align: center;
        font-size: 20px;
        color: #666;
        margin-bottom: 40px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# -------------------------
# Sidebar
# -------------------------

st.sidebar.title("🎓 IELTS AI")

page = st.sidebar.radio(
    "Choose a section",
    [
        "🏠 Home",
        "🎤 Speaking Part 1",
        "🎙️ Speaking Part 2",
        "💬 Speaking Part 3",
        "✍️ Writing Task 2",
        "📚 Knowledge Base"
    ]
)


# -------------------------
# Home
# -------------------------

if page == "🏠 Home":

    st.markdown(
        '<div class="main-title">🎓 IELTS AI Learning</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Practice. Learn. Speak. Improve.</div>',
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.subheader("🎤 Speaking")

        st.write(
            "Practice all three parts of IELTS Speaking "
            "with questions, model answers and AI feedback."
        )

    with col2:

        st.subheader("📚 Vocabulary")

        st.write(
            "Learn topic-specific vocabulary "
            "and natural collocations."
        )

    with col3:

        st.subheader("🤖 AI Feedback")

        st.write(
            "Get detailed feedback on your speaking "
            "and writing answers."
        )

    st.divider()

    st.header("🚀 Choose Your Practice")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🎤 Speaking Part 1",
            use_container_width=True
        ):

            st.session_state["page"] = "Speaking Part 1"

        if st.button(
            "🎙️ Speaking Part 2",
            use_container_width=True
        ):

            st.session_state["page"] = "Speaking Part 2"

    with col2:

        if st.button(
            "💬 Speaking Part 3",
            use_container_width=True
        ):

            st.session_state["page"] = "Speaking Part 3"

        if st.button(
            "✍️ Writing Task 2",
            use_container_width=True
        ):

            st.session_state["page"] = "Writing Task 2"

    st.divider()

    st.header("💡 How to use the platform")

    steps = [
        ("1️⃣", "Choose a topic"),
        ("2️⃣", "Study useful vocabulary"),
        ("3️⃣", "Read the sample answers"),
        ("4️⃣", "Create your own answer"),
        ("5️⃣", "Get AI feedback"),
        ("6️⃣", "Practice again")
    ]

    for icon, text in steps:

        st.markdown(
            f"### {icon} {text}"
        )


# -------------------------
# Pages
# -------------------------

elif page == "🎤 Speaking Part 1":

    show_part1()


elif page == "🎙️ Speaking Part 2":

    show_part2()


elif page == "💬 Speaking Part 3":

    show_part3()


elif page == "✍️ Writing Task 2":

    show_writing()
    
elif page == "📚 Knowledge Base":

    show_knowledge_base()