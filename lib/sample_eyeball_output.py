#!/usr/bin/env python3

import json
from typing import List, Dict
import smart_open
import sys
import random


def format_sentences(sentences: List[Dict]) -> str:
    """Format sentences as TOKEN1/POSTAG1 TOKEN2/POSTAG2."""
    result = []
    for sent in sentences:
        tokens = [f"{t['t']}/{t['p']}" for t in sent["tok"]]
        result.append(" ".join(tokens))
    return " || ".join(result)


def explore_output(
    jsonl_paths: List[str], num_lines: int, max_chars: int = 200
) -> None:
    """Explore linguistic processing output, showing title and first 3 sentences."""
    for jsonl_path in jsonl_paths:
        with smart_open.open(jsonl_path) as f:
            lines = f.readlines()
            sampled_lines = random.sample(lines, min(num_lines, len(lines)))
            for line in sampled_lines:
                doc = json.loads(line)
                doc_id = doc.get("ci_id", "No ID")

                print(f"Document ID: {doc_id}")
                # Format title
                title = doc.get("tsents", [])[:3]
                formatted_title = format_sentences(title)
                print(f"Title: {formatted_title[:max_chars]}")

                # Format sentences
                sentences = doc.get("sents", [])[:3]
                formatted_sentences = format_sentences(sentences)
                print(f"Sentences: {formatted_sentences[:max_chars]}")

                print("\n---\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            f"Usage: {sys.argv[0]} <num_lines> <path_to_jsonl1> [<path_to_jsonl2> ...]"
        )
        sys.exit(1)
    num_lines = int(sys.argv[1])
    jsonl_paths = sys.argv[2:]
    explore_output(jsonl_paths, num_lines)
