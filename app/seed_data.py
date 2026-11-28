"""Starter question bank. All questions are original practice material written for this project."""

from collections.abc import Iterator
from typing import Any

PART_1: dict[str, list[str]] = {
    "Hometown": [
        "Where is your hometown, and what is it like?",
        "What do you like most about living there?",
        "Has your hometown changed much since you were a child?",
        "Would you recommend your hometown to visitors? Why, or why not?",
    ],
    "Work and Study": [
        "Are you currently working or studying?",
        "What made you choose that job or subject?",
        "What is the most challenging part of your typical day?",
        "Would you like to change your career or field of study in the future?",
    ],
    "Hobbies": [
        "What do you usually do in your free time?",
        "Is there a hobby you would like to try in the future?",
        "Do you prefer spending your free time indoors or outdoors?",
        "Did you have different hobbies when you were younger?",
    ],
    "Food and Cooking": [
        "What kinds of food do you enjoy eating most?",
        "Do you often cook for yourself, or do you prefer eating out?",
        "Is there a traditional dish from your country that you like?",
        "Has your diet changed in recent years?",
    ],
    "Technology": [
        "What technology do you use most often in your daily life?",
        "How do you usually keep in touch with friends and family?",
        "Is there any piece of technology you could not live without?",
        "Do you think you spend too much time on your phone?",
    ],
    "Travel": [
        "Do you enjoy travelling? Why, or why not?",
        "Do you prefer travelling alone or with other people?",
        "What was the most recent trip you took?",
        "Is there a place you would love to visit in the future?",
    ],
}

PART_2: dict[str, tuple[str, list[str]]] = {
    "Hometown": (
        "Describe a place in your town or city where you like to spend time.",
        [
            "where the place is",
            "how often you go there",
            "what you do there",
            "and explain why you like spending time there",
        ],
    ),
    "Work and Study": (
        "Describe a teacher or colleague who helped you learn something important.",
        [
            "who this person is",
            "how you know them",
            "what they helped you learn",
            "and explain why it was important to you",
        ],
    ),
    "Hobbies": (
        "Describe a hobby or activity that you enjoy doing in your free time.",
        [
            "what the activity is",
            "when and where you do it",
            "who you do it with",
            "and explain why you enjoy it",
        ],
    ),
    "Food and Cooking": (
        "Describe a meal that you enjoyed eating with other people.",
        [
            "what the meal was",
            "who you ate it with",
            "where and when you had it",
            "and explain why you remember it well",
        ],
    ),
    "Technology": (
        "Describe a piece of technology that you find useful in your daily life.",
        [
            "what it is",
            "how long you have had it",
            "how you use it",
            "and explain why it is useful to you",
        ],
    ),
    "Travel": (
        "Describe a journey or trip that you would like to take again.",
        [
            "where you went",
            "who you went with",
            "what you did there",
            "and explain why you would like to do it again",
        ],
    ),
}

PART_3: dict[str, list[str]] = {
    "Hometown": [
        "How do life and opportunities differ between big cities and small towns?",
        "Why do many young people move away from the place where they grew up?",
        "What should local governments do to make cities more pleasant to live in?",
    ],
    "Work and Study": [
        "Is it more important to enjoy your job or to earn a high salary? Why?",
        "How might technology change the kinds of jobs people do in the future?",
        "What qualities make a good teacher, in your opinion?",
    ],
    "Hobbies": [
        "Why do some people prefer hobbies they do alone while others prefer group activities?",
        "How have the ways people spend their free time changed over the last few decades?",
        "Do you think people today have enough free time? Why, or why not?",
    ],
    "Food and Cooking": [
        "Why do you think traditional dishes are becoming less common in many countries?",
        "How does fast food affect people's health and lifestyles?",
        "Should schools teach children how to cook? Why, or why not?",
    ],
    "Technology": [
        "What are the advantages and disadvantages of relying on technology for communication?",
        "Do you think older people find it harder to adapt to new technology? Why?",
        "How might artificial intelligence change everyday life in the next twenty years?",
    ],
    "Travel": [
        "What are the benefits and drawbacks of mass tourism for local communities?",
        "Is it better to travel independently or with an organised tour? Why?",
        "How might the way people travel change in the future?",
    ],
}


def iter_seed_questions() -> Iterator[dict[str, Any]]:
    for topic, texts in PART_1.items():
        for text in texts:
            yield {"part": 1, "topic": topic, "text": text, "cue_points": None}
    for topic, (text, cues) in PART_2.items():
        yield {"part": 2, "topic": topic, "text": text, "cue_points": list(cues)}
    from app.seed_cue_cards import EXTRA_PART_2

    for topic, (text, cues) in EXTRA_PART_2.items():
        yield {"part": 2, "topic": topic, "text": text, "cue_points": list(cues)}
    for topic, texts in PART_3.items():
        for text in texts:
            yield {"part": 3, "topic": topic, "text": text, "cue_points": None}
