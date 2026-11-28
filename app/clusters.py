"""Topic clusters: broad themes that group related speaking topics.

A topic may belong to several clusters (an app you use is both Technology and daily life). Topic
names must match ``Question.topic``. Relationships between topics are derived from shared clusters.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Cluster:
    slug: str
    name: str
    blurb: str
    topics: tuple[str, ...]


CLUSTERS: tuple[Cluster, ...] = (
    Cluster("technology", "Technology & digital life", "Apps, websites, devices and how we learn and talk online.",
            ("Technology", "Gadget you own", "Useful website", "Favourite app", "Social media", "Online learning", "Useful invention")),
    Cluster("people", "People & relationships", "People who shaped you, helped you or share your time.",
            ("Influential person", "Helpful person", "Someone you admire", "Good company", "Teacher", "Interesting job")),
    Cluster("money", "Money, shopping & decisions", "Spending, saving, buying and the choices behind them.",
            ("Expensive purchase", "Saving money", "Shopping trip", "Something you want", "Big decision", "Gadget you own")),
    Cluster("memories", "Time, memories & events", "Moments from the past, busy days and celebrations.",
            ("Childhood memory", "Memorable event", "Busy day", "Festival", "Memorable journey", "Hometown")),
    Cluster("education", "Education, learning & skills", "Studying, teachers, books and skills you picked up.",
            ("Skill you learned", "Online learning", "Teacher", "Book you enjoyed", "Work and Study", "Useful website")),
    Cluster("nature-travel", "Nature, environment & travel", "Journeys, natural places and looking after the planet.",
            ("Travel", "Memorable journey", "Natural place", "Environment", "Place to visit")),
    Cluster("work", "Work, careers & ambitions", "Jobs, goals and the plans you are working towards.",
            ("Work and Study", "Interesting job", "Career ambition", "Big decision", "Skill you learned")),
    Cluster("culture", "Culture, art & entertainment", "Films, music, books, hobbies and festivals.",
            ("Film you enjoyed", "Music", "Festival", "Book you enjoyed", "Hobbies", "Social media")),
    Cluster("lifestyle", "Food, health & lifestyle", "What you eat, how you stay healthy and how you spend your day.",
            ("Food and Cooking", "Special meal", "Healthy habit", "Sport or exercise", "Hobbies", "Busy day")),
    Cluster("places", "Places & hometowns", "Where you live, buildings you like and places you visit.",
            ("Hometown", "Favourite building", "Place to visit", "Natural place", "Memorable journey")),
)

CLUSTER_SLUGS: frozenset[str] = frozenset(c.slug for c in CLUSTERS)


def clusters_for_topic(topic: str) -> list[str]:
    key = topic.strip().lower()
    return [c.slug for c in CLUSTERS if any(t.lower() == key for t in c.topics)]
