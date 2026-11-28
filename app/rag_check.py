"""Validate the reference answers and preview what would be retrieved.

    python -m app.rag_check
    python -m app.rag_check --part 2 --question "Describe a book you enjoyed"
"""

import argparse
from collections import Counter

from app.rag.retrieval import SampleIndex, samples_dir
from app.rag.samples import load_samples


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--question", default="")
    args = ap.parse_args()

    samples, problems = load_samples(samples_dir())
    print(f"Folder: {samples_dir()}\nLoaded {len(samples)} valid sample(s).")
    for part in (1, 2, 3):
        bands = Counter(s.band for s in samples if s.part == part)
        print(f"  Part {part}: {sum(bands.values())}  bands {dict(sorted(bands.items()))}")
    for p in problems:
        print("  PROBLEM:", p)
    if args.part and args.question:
        for s in SampleIndex(samples).select(part=args.part, question=args.question, answer="", k=3):
            print(f"\n[{s.source}] band {s.band:g}: {s.question}")


if __name__ == "__main__":
    main()
