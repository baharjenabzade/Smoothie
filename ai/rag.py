from rag.database import search_documents
from ai.llm import ask_ai



PART1_TOPICS = [
    "Headphones",
    "Social Media",
    "Teachers",
    "Watches",
    "Science",
    "Parks",
    "Cars",
    "Websites",
    "Mirrors",
    "Shopping",
    "Music",
    "Clothing",
    "Films",
    "Art",
    "Singing",
    "History",
    "Morning Time",
    "Outer Space",
    "Old Buildings",
    "Sports",
    "Jokes",
    "Tidiness",
    "Video Games",
    "Technology",
    "Food",
    "Cooking",
    "Books",
    "Travel",
    "Hobbies",
    "Friends",
    "Family",
    "Work",
    "Studies"
]

def identify_topic(question):

    topic_list = "\n".join(
        f"- {topic}"
        for topic in PART1_TOPICS
    )

    prompt = f"""
You are an IELTS Speaking Part 1 topic classifier.

Identify the SINGLE most specific topic of the
following IELTS Speaking Part 1 question.

AVAILABLE TOPICS:

{topic_list}

QUESTION:
{question}

Rules:

1. Choose exactly ONE topic.
2. Choose the most specific topic.
3. Do not choose a broad related topic.
4. Do not choose "Technology" if the question
   specifically asks about Video Games.
5. Do not choose "Music" if the question is about
   Video Games.
6. Do not choose a related topic.

Examples:

"Do you play video games?"
→ Video Games

"What kind of games do you like playing?"
→ Video Games

"Do you listen to music every day?"
→ Music

"What kind of music do you enjoy?"
→ Music

"Do you use social media?"
→ Social Media

"How often do you use your computer?"
→ Technology

Return ONLY the topic name.
"""

    topic = ask_ai(prompt).strip()

    # Clean possible formatting
    topic = topic.replace('"', "").strip()

    for valid_topic in PART1_TOPICS:

        if topic.lower() == valid_topic.lower():
            return valid_topic

    return None

def get_part1_question_context(
    question,
    n_results=8
):

    # First identify the exact topic
    topic = identify_topic(question)

    print(f"Detected IELTS topic: {topic}")

    # Search ONLY within that topic
    results = search_documents(
        question,
        n_results=n_results,
        topic=topic
    )

    if not results:
        return "", topic

    context = []

    for document, metadata in results:

        context.append(
            f"""
TOPIC: {metadata.get("topic", "Unknown")}

QUESTION:
{metadata.get("question", "")}

QUESTION TYPE:
{metadata.get("question_type", "")}

FREQUENCY:
{metadata.get("frequency", "Unknown")}

CONTENT:
{document}
"""
        )

    return "\n\n".join(context), topic


def generate_part1_help(
    question,
    knowledge_results=None
):

    # --------------------------------------------------
    # USE RETRIEVED KNOWLEDGE IF IT WAS ALREADY SEARCHED
    # --------------------------------------------------

    if knowledge_results is not None:

        if knowledge_results:

            context_parts = []

            for document, metadata in knowledge_results:

                context_parts.append(
                    f"""
TOPIC: {metadata.get("topic", "General")}

QUESTION:
{metadata.get("question", "")}

QUESTION TYPE:
{metadata.get("question_type", "")}

FREQUENCY:
{metadata.get("frequency", "Unknown")}

CONTENT:
{document}
"""
                )

            context = "\n\n".join(context_parts)

        else:

            context = ""
        detected_topic = None
    else:

        context, detected_topic = get_part1_question_context(
        question,
        n_results=8
    )

    # --------------------------------------------------
    # IELTS PART 1 PROMPT
    # --------------------------------------------------

    prompt = f"""
You are an expert IELTS Speaking tutor and IELTS
curriculum designer.

The student is practicing IELTS Speaking Part 1.

Your goal is NOT to give the student a memorized answer.

Your goal is to teach the student how to develop
natural ideas, vocabulary, collocations and flexible
connections to other topics.

==================================================
STUDENT QUESTION
==================================================

{question}


==================================================
IELTS KNOWLEDGE BASE
==================================================

{context}


==================================================
CORE REQUIREMENTS
==================================================

The response must be specifically designed for
IELTS Speaking Part 1.

The student should be able to use the language
naturally in a real speaking test.

Use Band 7-9 appropriate English, but prioritize
naturalness and clarity over unnecessarily difficult
vocabulary.

Do NOT make the response sound like an IELTS
Writing Task 2 essay.

Do NOT encourage memorization.

Do NOT invent statistics or factual claims unless
they are necessary and clearly presented as general
ideas.

If the knowledge base describes a topic as a
reported/current IELTS topic, do NOT claim that it
is guaranteed to appear in the real examination.


==================================================
1. CURRENT TOPIC
==================================================

The retrieval system has identified the main
IELTS topic as:

{detected_topic}

Treat this as the PRIMARY topic.

The student asked:

{question}

IMPORTANT:

The primary topic MUST remain the subject of
the sample answers.

Related topics are only supporting categories.

For example:

PRIMARY TOPIC:
Video Games

RELATED TOPICS:
Music
Technology
Entertainment
Hobbies

The sample answers must be about VIDEO GAMES.

Do NOT answer the question about Music or
Technology just because those topics are related.

If the question is:

"Do you play video games?"

the answer should discuss playing video games,
gaming habits, game types, gaming experiences,
etc.

Music or Technology may only be mentioned if
they naturally support the answer.

==================================================
2. THREE POSSIBLE IDEAS
==================================================

Give three realistic ideas the student could use
to answer the question.

The ideas should be personal and easy to develop.

Each idea should contain:

- the main idea
- a reason
- a possible example/detail

Avoid giving three ideas that are basically the same.


==================================================
3. USEFUL VOCABULARY
==================================================

Give 8-12 useful words or expressions related to
the question.

Prioritize vocabulary that a student can actually
use while speaking.

For each item provide:

WORD / EXPRESSION:
Meaning:
Natural example:


==================================================
4. USEFUL COLLOCATIONS
==================================================

Give 8-12 natural IELTS speaking collocations.

The collocations must be genuinely useful for the
specific topic.

For example, for MUSIC:

- have a particular taste in music
- listen to music on a daily basis
- discover new artists
- keep up with music trends
- help me unwind
- lift my mood

Do NOT simply create adjective + noun combinations.

Prefer natural verb + noun, adjective + noun,
verb + preposition and idiomatic combinations.


==================================================
5. SAMPLE ANSWERS
==================================================

Generate THREE different sample answers.

IMPORTANT:

Each answer must be approximately 40-55 seconds
when spoken at a natural IELTS speaking speed.

Target approximately 80-110 words per answer.

The answers must:

- directly answer the question
- sound spontaneous and conversational
- contain natural grammar
- include useful topic-related collocations
- contain at least one reason or explanation
- contain a specific example, experience or detail
- use a mixture of simple and complex sentences
- avoid sounding memorized
- avoid unnecessary idioms
- avoid excessive advanced vocabulary
- be meaningfully different from each other

The three answers should demonstrate different
ways of developing an answer.

For example:

Answer 1:
Personal experience

Answer 2:
Technology/social-media angle

Answer 3:
Lifestyle/culture angle


==================================================
6. BROAD RELATED TOPICS
==================================================

This section is VERY IMPORTANT.

Do NOT simply list synonyms or extremely narrow
variations of the current topic.

Instead, identify BROADER CATEGORIES that could
help the student continue speaking if they do not
have enough vocabulary about the current topic.

The related categories should act as "idea bridges."

For example, if the current topic is MUSIC:

Technology
    - AI-generated music
    - music recommendation algorithms
    - streaming platforms
    - music production software

Social Media
    - viral songs
    - music trends
    - discovering artists
    - influencers

Culture & Society
    - traditional music
    - cultural identity
    - music at celebrations
    - differences between generations

Entertainment
    - concerts
    - festivals
    - movies and soundtracks
    - celebrities

Lifestyle
    - relaxation
    - commuting
    - daily routines
    - hobbies

Education
    - learning instruments
    - music classes
    - practicing


Generate 5-7 BROAD related categories.

For each category generate 3-5 useful subcategories.

The related categories should NOT always be the
same categories.

Choose categories that make logical sense for the
current topic.


==================================================
7. IDEA BRIDGES
==================================================

Explain how the student can move from the current
topic to one of the broader categories.

For example:

MUSIC → TECHNOLOGY

Possible idea:
"I mostly listen to music through streaming apps,
and recently I've noticed that AI-based
recommendations are quite good at helping me
discover new artists."

MUSIC → SOCIAL MEDIA

Possible idea:
"I actually discover a lot of new songs through
social media because short videos often make
certain songs go viral."

Give 3-5 useful idea bridges for the current topic.


==================================================
8. EMERGENCY VOCABULARY STRATEGY
==================================================

Imagine the student gets a question about the
current topic but does not know much vocabulary
about it.

Give 3 general strategies for answering anyway.

For example:

1. Connect the topic to technology.
2. Connect it to your daily routine.
3. Connect it to social media or modern life.

Give examples specifically adapted to the
student's current topic.


==================================================
9. IELTS SPEAKING TIP
==================================================

Give ONE short personalized IELTS Speaking Part 1
tip for this question.

The tip should focus on:

- developing the answer
- natural grammar
- vocabulary
- pronunciation
- avoiding memorization

Do not give a generic essay-writing tip.


==================================================
OUTPUT FORMAT
==================================================

CURRENT TOPIC:
...

IDEAS:
1. ...
2. ...
3. ...

VOCABULARY:
1. ...
2. ...
3. ...

COLLOCATIONS:
1. ...
2. ...
3. ...

SAMPLE ANSWER 1:
...

SAMPLE ANSWER 2:
...

SAMPLE ANSWER 3:
...

RELATED TOPICS:

CATEGORY 1:
- ...
- ...
- ...

CATEGORY 2:
- ...
- ...
- ...

CATEGORY 3:
- ...
- ...
- ...

CATEGORY 4:
- ...
- ...
- ...

CATEGORY 5:
- ...
- ...
- ...

IDEA BRIDGES:
1. ...
2. ...
3. ...
4. ...

IF YOU DON'T KNOW MUCH ABOUT THIS TOPIC:
1. ...
2. ...
3. ...

IELTS TIP:
...


FINAL QUALITY CHECK:

Before returning the response, silently check:

- Are all three answers approximately 80-110 words?
- Would each answer take approximately 40-55 seconds
  to say naturally?
- Does each answer directly answer the question?
- Are the collocations natural?
- Are the related topics broader than the current topic?
- Does each related category contain useful
  subcategories?
- Are there technology/social-media/culture/lifestyle
  connections where appropriate?
- Does the response sound conversational rather
  than like an essay?
- Does it avoid memorized-answer language?
"""

    return ask_ai(prompt)