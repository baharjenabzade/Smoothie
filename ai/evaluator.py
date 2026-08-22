from ai.llm import ask_ai
from ai.prompts import (
    PART1_EVALUATION_PROMPT,
    PART2_EVALUATION_PROMPT,
    PART3_EVALUATION_PROMPT,
    ESSAY_GENERATION_PROMPT,
    ESSAY_EVALUATION_PROMPT
)


def evaluate_part1(question, answer):
    prompt = PART1_EVALUATION_PROMPT.format(
        question=question,
        answer=answer
    )

    return ask_ai(prompt)


def evaluate_part2(question, answer):
    prompt = PART2_EVALUATION_PROMPT.format(
        question=question,
        answer=answer
    )

    return ask_ai(prompt)


def evaluate_part3(question, answer):
    prompt = PART3_EVALUATION_PROMPT.format(
        question=question,
        answer=answer
    )

    return ask_ai(prompt)


def generate_essay(question):
    prompt = ESSAY_GENERATION_PROMPT.format(
        question=question
    )

    return ask_ai(prompt)


def evaluate_essay(question, essay):
    prompt = ESSAY_EVALUATION_PROMPT.format(
        question=question,
        essay=essay
    )

    return ask_ai(prompt)