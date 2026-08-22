import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    file_path = DATA_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_part1():
    return load_json("part1.json")


def load_part2():
    return load_json("part2.json")


def load_part3():
    return load_json("part3.json")


def load_writing():
    return load_json("writing.json")