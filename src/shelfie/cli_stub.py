"""Headless CLI stub for environments without PySide6.
Displays library/feature placeholders so CI and sandboxes can still run.
"""
from __future__ import annotations

import argparse
import json
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="shelfie-cli", description="Shelfie headless stub")
    parser.add_argument("--list", action="store_true", help="List demo books")
    parser.add_argument("--genres", action="store_true", help="List seeded genres")
    args = parser.parse_args(argv)

    demo_books = [
        {
            "title": "Your First 1000 Copies",
            "author": "Tim Grahl",
            "genre": "Business, Entrepreneurship & Marketing",
        },
        {
            "title": "Metaphysics 101",
            "author": "A. Mystic",
            "genre": "Spirituality, Consciousness & Metaphysics",
        },
    ]
    genres = [
        "Astrology & Esoterica",
        "Business, Entrepreneurship & Marketing",
        "Classics & Literature",
        "Contemporary Fiction & YA",
        "Creativity, Art & Making",
        "Driving / DMV (Practical)",
        "Faith, Purpose & Life Design",
        "Health, Longevity & Body",
        "Miscellaneous",
        "Money, Finance & Wealth",
        "Nature, Ecology & Earth-Wisdom",
        "Productivity, Habits & Personal Growth",
        "Psychology & Human Behavior",
        "Relationships, Communication & Attachment",
        "Science, Cosmos & Big Ideas",
        "Self-Love, Confidence & Mindset",
        "Shadow Work, Trauma & Healing",
        "Spirituality, Consciousness & Metaphysics",
    ]

    if args.list:
        print(json.dumps(demo_books, indent=2))
        return 0
    if args.genres:
        print(json.dumps(genres, indent=2))
        return 0

    print(
        "Shelfie headless mode: GUI not started. Try --list or --genres, or install PySide6 and run GUI."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
