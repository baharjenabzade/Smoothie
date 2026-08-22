from rag.database import search_documents
from ai.llm import ask_ai


def get_part2_question_context(
    question,
    n_results=3
):
    """
    Retrieve supplementary IELTS knowledge.

    IMPORTANT:
    This information is only supporting material.
    The selected cue card always has higher priority.
    """

    results = search_documents(
        question,
        n_results=n_results
    )

    if not results:
        return ""

    context = []

    for document, metadata in results:

        context.append(
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

    return "\n\n".join(context)


def generate_part2_help(
    question,
    prompts=None,
    knowledge_results=None
):

    # ==================================================
    # 1. KNOWLEDGE BASE
    # ==================================================

    if knowledge_results is not None:

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

        context = get_part2_question_context(
            question,
            n_results=3
        )

    # ==================================================
    # 2. CUE CARD BULLET POINTS
    # ==================================================

    if prompts:

        prompt_points = "\n".join(
            f"- {p}"
            for p in prompts
        )

    else:

        prompt_points = (
            "No additional bullet points were provided."
        )

    # ==================================================
    # 3. AI PROMPT
    # ==================================================

    prompt = f"""

You are an expert IELTS Speaking Part 2 tutor,
IELTS examiner, and English language teacher.

The student is preparing for IELTS Speaking Part 2.

Your task is to create ONE memorable,
natural, approximately TWO-MINUTE spoken story
for the EXACT cue card provided below.

==================================================
CURRENT CUE CARD
==================================================

THIS IS THE MOST IMPORTANT INFORMATION.

CURRENT CUE CARD:

{question}


YOU SHOULD TALK ABOUT:

{prompt_points}


==================================================
ABSOLUTE TOPIC PRIORITY
==================================================

The CURRENT CUE CARD is the source of truth.

You MUST answer this exact cue card.

First identify the MAIN TOPIC.

The MAIN TOPIC is the subject the examiner
actually wants the student to discuss.

For example:

CUE CARD:
"Describe a piece of technology that you find useful."

MAIN TOPIC:
TECHNOLOGY

Possible object:
Laptop

Secondary detail:
The laptop was a gift.

In this example:

TECHNOLOGY = MAIN TOPIC

LAPTOP = SPECIFIC EXAMPLE

GIFT = BACKGROUND DETAIL


IMPORTANT:

A secondary detail must NEVER become the main topic.

For example, if the cue card is about
TECHNOLOGY, do NOT create a story mainly about:

- receiving a gift
- a birthday
- friends surprising the student
- opening a present
- gift giving

The technology itself must remain the CENTRAL
SUBJECT of the answer.

The story may mention that the laptop was a gift,
but this should normally be only a small supporting
detail.


==================================================
TOPIC PRIORITY ORDER
==================================================

Always follow this order:

1. CURRENT CUE CARD
2. CUE CARD BULLET POINTS
3. MAIN TOPIC
4. TOPIC-SPECIFIC VOCABULARY
5. TOPIC-SPECIFIC COLLOCATIONS
6. STORY DETAILS
7. KNOWLEDGE BASE


Never reverse this order.


==================================================
KNOWLEDGE BASE
==================================================

The following information comes from the IELTS
knowledge base.

It is ONLY supplementary information.

It may contain:

- other IELTS questions
- sample answers
- vocabulary
- collocations
- ideas
- related topics
- examples

DO NOT treat these retrieved examples as the
current cue card.

If the knowledge base contains a different topic,
IGNORE that topic as the main subject.

You may borrow useful vocabulary or ideas ONLY
when they are relevant to the CURRENT cue card.

-------------------------

{context}

-------------------------


==================================================
1. CREATE THE CORE STORY
==================================================

Create ONE memorable personal story.

The story should be:

- realistic
- personal
- easy to visualize
- easy to remember
- emotionally engaging
- logically organized
- useful for IELTS Speaking
- adaptable to similar Part 2 topics

However:

RELEVANCE IS MORE IMPORTANT THAN FLEXIBILITY.

The story must first answer the CURRENT cue card.


==================================================
2. TWO-MINUTE SAMPLE ANSWER
==================================================

Write ONE complete IELTS Speaking Part 2
sample answer.

Target length:

250-300 words.

The answer should take approximately
TWO MINUTES when spoken naturally.

The answer MUST:

- directly answer the cue card
- address EVERY bullet point
- keep the main topic central
- sound conversational
- sound spontaneous
- contain specific details
- contain a memorable moment
- include personal feelings
- include natural transitions
- have a clear beginning, development and ending

Do NOT write an academic essay.

This is SPEAKING.

The answer should sound like something
a strong IELTS candidate could actually say.

Do NOT make it sound memorized.

Do NOT overuse complicated vocabulary.


==================================================
3. MANDATORY GRAMMAR
==================================================

The sample answer MUST contain ALL of the
following grammar structures.

These are NOT optional.

-----------------------------------------------
A. PRESENT PERFECT
-----------------------------------------------

Use at least ONE natural present perfect
sentence.

Example:

"I've been using it for several years now."

The sentence must relate to the current topic.


-----------------------------------------------
B. CONDITIONAL
-----------------------------------------------

Use at least ONE natural conditional sentence.

Prefer a useful second or third conditional
when appropriate.

Example:

"If I hadn't had this laptop at university,
I would have struggled much more with my projects."

The conditional must relate to the topic.


-----------------------------------------------
C. THE MORE..., THE MORE...
-----------------------------------------------

Use this exact structure at least ONCE.

Example:

"The more I use it, the more I realize
how much time it saves me."

Do NOT omit this structure.


-----------------------------------------------
D. NOT ONLY..., BUT ALSO...
-----------------------------------------------

Use this exact structure at least ONCE.

Example:

"It's not only useful for studying,
but also for communicating with other people."

Do NOT omit this structure.


-----------------------------------------------
E. RELATIVE CLAUSE
-----------------------------------------------

Use at least ONE natural relative clause.

Example:

"It's a device that I rely on almost every day."


-----------------------------------------------
F. PAST PERFECT
-----------------------------------------------

Use at least ONE natural past perfect sentence
where appropriate.

Example:

"By the time I started university,
I had already become dependent on technology
for studying."


-----------------------------------------------
G. COMPARISON
-----------------------------------------------

Use at least ONE natural comparison.

Example:

"It's much more convenient than using my phone
for long assignments."


IMPORTANT:

All grammar structures must be connected to
the CURRENT CUE CARD.

Do not create random sentences simply to
satisfy the grammar checklist.


==================================================
4. TOPIC-SPECIFIC VOCABULARY
==================================================

Generate 12-15 vocabulary items.

At least 80% of these items MUST directly relate
to the MAIN TOPIC of the current cue card.

For example, if the topic is TECHNOLOGY,
prefer vocabulary such as:

- user-friendly
- cutting-edge
- practical
- efficient
- time-saving
- portable
- reliable
- multifunctional
- convenient
- digital device
- productivity
- processing power
- software
- wireless connectivity
- technological advancement

DO NOT prioritize vocabulary about:

- gifts
- birthdays
- presents
- surprises
- celebrations

unless the CURRENT cue card is actually about
those subjects.

For every item provide:

WORD / EXPRESSION:
Meaning:
Example related to the CURRENT TOPIC:


==================================================
5. TOPIC-SPECIFIC COLLOCATIONS
==================================================

Generate 10-12 collocations.

At least 80% MUST directly relate to the
CURRENT MAIN TOPIC.

For a technology topic, useful examples include:

- improve productivity
- save a considerable amount of time
- access information instantly
- stay connected
- keep up with technological advances
- improve efficiency
- perform multiple tasks
- solve a practical problem
- use a user-friendly interface
- rely heavily on technology
- make everyday tasks easier
- become an essential part of my routine

Do NOT generate gift-related collocations
just because the story contains a gift.

For every collocation provide:

COLLOCATION:
Meaning:
Example:


==================================================
6. PHRASAL VERBS
==================================================

Give 5-8 phrasal verbs related to the
CURRENT MAIN TOPIC.

For example, for technology:

- set up
- log in
- look up
- back up
- plug in
- switch on
- carry out
- keep up with

For each:

PHRASAL VERB:
Meaning:
Example related to the current topic:


==================================================
7. IDIOMS
==================================================

Give 3-5 natural idioms that can be used
when discussing the CURRENT TOPIC.

Avoid obscure or unnatural idioms.

For each:

IDIOM:
Meaning:
Example:


==================================================
8. STORY MAP
==================================================

After the sample answer, create a short story map.

BEGINNING:
How the story begins.

DEVELOPMENT:
What happened next.

MEMORABLE MOMENT:
The most memorable event.

ENDING:
How the situation ended.

REFLECTION:
What the student learned, realized,
or felt.


==================================================
9. RELATED PART 2 TOPICS
==================================================

Identify 4-6 OTHER IELTS Speaking Part 2
cue cards that could use the SAME CORE STORY.

The topics must be genuinely adaptable.

For each:

RELATED TOPIC:
...

WHY IT WORKS:
...

WHAT TO CHANGE:
...


The student should be able to reuse roughly
70-80% of the story while changing only
some details.

Do NOT suggest unrelated topics.

For example, a technology story could potentially
be adapted to topics about:

- an important piece of equipment
- something that makes life easier
- an invention
- something useful you own
- a product you use frequently

But only recommend topics where the story
actually works.


==================================================
10. STORY ADAPTATION GUIDE
==================================================

Explain exactly how the student can adapt
the core story.

For example:

CURRENT TOPIC:
Focus on how the technology is useful.

TOPIC ABOUT AN INVENTION:
Focus on how the technology changed
the way people do something.

TOPIC ABOUT SOMETHING YOU BOUGHT:
Change the opening to explain why you bought it.

TOPIC ABOUT SOMETHING THAT MAKES LIFE EASIER:
Emphasize the practical benefits.


==================================================
11. OTHER USEFUL PHRASES
==================================================

Give useful phrases that the student can use
for this topic.

INTRODUCING THE TOPIC:

- ...
- ...
- ...


DESCRIBING THE OBJECT / PERSON / PLACE:

- ...
- ...
- ...


GIVING DETAILS:

- ...
- ...
- ...


EXPLAINING USEFULNESS:

- ...
- ...
- ...


EXPRESSING FEELINGS:

- ...
- ...
- ...


DESCRIBING CHANGE:

- ...
- ...
- ...


ENDING THE STORY:

- ...
- ...
- ...


REFLECTING:

- ...
- ...
- ...


==================================================
12. GRAMMAR USED IN THE ANSWER
==================================================

After writing the sample answer, identify
the exact sentences where the required grammar
was used.

Use this format:

PRESENT PERFECT:
"Exact sentence from the answer."
→ Explanation


CONDITIONAL:
"Exact sentence from the answer."
→ Explanation


THE MORE..., THE MORE...:
"Exact sentence from the answer."
→ Explanation


NOT ONLY..., BUT ALSO...:
"Exact sentence from the answer."
→ Explanation


RELATIVE CLAUSE:
"Exact sentence from the answer."
→ Explanation


PAST PERFECT:
"Exact sentence from the answer."
→ Explanation


COMPARISON:
"Exact sentence from the answer."
→ Explanation


IMPORTANT:

Only quote sentences that actually appear
in the sample answer.


==================================================
13. FLEXIBLE GRAMMAR PATTERNS
==================================================

Give 5-8 reusable grammar patterns that
the student can adapt.

Include examples using:

- If...
- I've...
- The more..., the more...
- Not only..., but also...
- What made it particularly memorable was...
- Looking back,...
- One thing I particularly remember is...
- It was something that...


==================================================
14. IELTS DELIVERY TIP
==================================================

Explain how the student can remember the
story without memorizing every sentence.

Tell them to remember:

1. Setting
2. Main subject
3. Beginning
4. Development
5. Memorable moment
6. Result
7. Reflection

The goal is to remember the STORY,
not every sentence.


==================================================
FINAL QUALITY CONTROL
==================================================

Before returning the answer, silently check
everything below.

DO NOT SHOW THIS CHECKLIST TO THE STUDENT.


---------- TOPIC CHECK ----------

What is the MAIN TOPIC?

It MUST match the CURRENT cue card.

If the cue card is about TECHNOLOGY,
technology must remain the central subject.


---------- STORY CHECK ----------

[ ] Does the story answer the current cue card?

[ ] Does it address every bullet point?

[ ] Is the main subject the cue-card topic?

[ ] Is any secondary event taking too much space?

[ ] If there is a gift, birthday, friend,
    trip, or other secondary detail, is it
    actually secondary?

[ ] Would the story still make sense if the
    secondary event were removed?


---------- VOCABULARY CHECK ----------

At least 80% of vocabulary must relate
directly to the CURRENT MAIN TOPIC.

At least 80% of collocations must relate
directly to the CURRENT MAIN TOPIC.

If the cue card is technology, vocabulary
about gifts must NOT dominate.


---------- GRAMMAR CHECK ----------

The sample answer MUST contain:

[ ] Present perfect

[ ] Conditional

[ ] "The more..., the more..."

[ ] "Not only..., but also..."

[ ] Relative clause

[ ] Past perfect

[ ] Comparison


If ANY required structure is missing,
rewrite the sample answer.


---------- LENGTH CHECK ----------

The sample answer must be approximately
250-300 words.


---------- IELTS CHECK ----------

[ ] Natural spoken English

[ ] Band 7-9 appropriate language

[ ] Not an academic essay

[ ] Not unnecessarily complicated

[ ] Memorable

[ ] Easy to adapt

[ ] Directly relevant to the cue card


If any check fails, rewrite the answer
before returning it.


==================================================
OUTPUT FORMAT
==================================================

🎯 MAIN TOPIC:

...


🎯 CORE STORY:

...


🎤 TWO-MINUTE SAMPLE ANSWER:

...


📖 STORY MAP:

BEGINNING:
...

DEVELOPMENT:
...

MEMORABLE MOMENT:
...

ENDING:
...

REFLECTION:
...


🔄 RELATED PART 2 TOPICS:

1.
RELATED TOPIC:
...

WHY IT WORKS:
...

WHAT TO CHANGE:
...


2.
RELATED TOPIC:
...

WHY IT WORKS:
...

WHAT TO CHANGE:
...


3.
RELATED TOPIC:
...

WHY IT WORKS:
...

WHAT TO CHANGE:
...


4.
RELATED TOPIC:
...

WHY IT WORKS:
...

WHAT TO CHANGE:
...


🧩 STORY ADAPTATION GUIDE:

...


📚 TOPIC VOCABULARY:

...


🔗 TOPIC COLLOCATIONS:

...


🔄 PHRASAL VERBS:

...


💬 IDIOMS:

...


✨ OTHER USEFUL PHRASES:

INTRODUCING THE TOPIC:
...

DESCRIBING:
...

GIVING DETAILS:
...

EXPLAINING USEFULNESS:
...

EXPRESSING FEELINGS:
...

DESCRIBING CHANGE:
...

ENDING:
...

REFLECTING:
...


🧠 GRAMMAR USED IN THE ANSWER:

PRESENT PERFECT:
...

CONDITIONAL:
...

THE MORE..., THE MORE...:
...

NOT ONLY..., BUT ALSO...:
...

RELATIVE CLAUSE:
...

PAST PERFECT:
...

COMPARISON:
...


🧠 FLEXIBLE GRAMMAR PATTERNS:

...


🎓 IELTS DELIVERY TIP:

...
"""

    return ask_ai(prompt)