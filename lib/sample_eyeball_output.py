#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Linguistic Processing Output Sampler and Viewer

This module provides functionality to sample and display linguistic processing output with:
- Random sampling from JSONL files
- Offset-aware text reconstruction
- Multiple output formats:
  * Console output with configurable display
  * TSV export with metadata
- Configurable POS tag display
- Support for multiple input files

Examples:
    Basic usage with console output:
        >>> processor = SampleProcessor(['input.jsonl'])
        >>> processor.run()

    Multiple files with TSV export:
        >>> processor = SampleProcessor(
        ...     input_files=['file1.jsonl', 'file2.jsonl'],
        ...     num_samples=10,
        ...     output='samples.tsv'
        ... )
        >>> processor.run()

    Command line usage:
        $ python sample_eyeball_output.py input.jsonl -n 5  # Basic sampling
        $ python sample_eyeball_output.py *.jsonl -o samples.tsv  # TSV export
        $ python sample_eyeball_output.py input.jsonl --no-pos  # Hide POS tags
        $ python sample_eyeball_output.py input.jsonl --max-chars 300  # Longer display

Output Formats:
    Console:
        - Article URL
        - Title with tokens
        - First 3 sentences
        Optional POS tags shown as TOKEN/TAG

    TSV:
        - newspaper: Source newspaper (from filename)
        - link: Full impresso article URL
        - title: Complete title text
        - text: First 3 sentences
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Sequence, Union
import random
import csv
import argparse
import smart_open
import re


def format_sentence_with_offsets(tokens: List[Dict]) -> str:
    """Format a sentence respecting token offsets.

    Args:
        tokens: List of token dictionaries with 't' (text) and 'o' (offset) keys

    Returns:
        str: Formatted text with proper spacing
    """
    if not tokens:
        return ""

    result = []
    last_end = tokens[0]["o"]  # Use the offset of the first token as the initial start

    for token in tokens:
        # Add padding spaces if there's a gap
        offset = token["o"]
        if offset > last_end:
            result.append(" " * (offset - last_end))

        result.append(token["t"])
        last_end = offset + len(token["t"])

    return "".join(result)


def analyze_title_in_text(title: str, full_text: str) -> Dict[str, bool]:
    """Analyze the relationship between the title and the full text.

    Args:
        title: The title string
        full_text: The full text string

    Returns:
        Dict[str, bool]: Analysis results
    """
    ADVERTISEMENT = re.compile(
        r"""^
      \s* adv\. \s* \d+ \s* page \s* \d+ \s*
    | \s* publicité \s* \d+ page \s* \d+ \s*
    $""",
        flags=re.IGNORECASE + re.VERBOSE,
    )
    len_title = len(title)
    len_full_text = len(full_text)
    analysis = {
        "exact_prefix": False,
        "ellipsis": None,
        "alnum_prefix": None,
        "alnum_infix": None,
        "UNK": None,
        "title_longer": len_title > len_full_text,
        "advertisement": None,
    }
    # Check for "UNKNOWN" or "UNTITLED" in title
    if title.strip().upper() in {"UNKNOWN", "UNTITLED"}:
        analysis["UNK"] = True
        return analysis

    if re.match(ADVERTISEMENT, title):
        analysis["advertisement"] = True
        return analysis

    # Check if title is longer than full text
    # We do not need to further analyze in this case
    if len_title > len_full_text:
        return analysis

    # Check for exact prefix match
    # there are rare cases where the actual title ends with ...
    # https://impresso-project.ch/app/issue/armeteufel-1911-06-04-a/view?p=1&articleId=i0010
    if full_text.startswith(title):
        analysis["exact_prefix"] = True
        return analysis

    # Check for ellipsis and remove if present
    if title.endswith("..."):
        analysis["ellipsis"] = True
        title = title[:-3]

    if full_text.startswith(title):
        analysis["exact_prefix"] = True
        return analysis

    alphanum_title = "".join(c for c in title if c.isalnum())
    alphanum_text = "".join(c for c in full_text if c.isalnum())
    if alphanum_text.startswith(alphanum_title):
        analysis["alnum_prefix"] = True
        return analysis

    # Sometimes the actual title has a preceding smaller subtitle and therefore is not
    # the prefix of the full text. In order to not overmatch, we only test this if at
    # least one whitespace is present in the title and the title is at least 20
    # characters long

    if " " in title and len_title >= 20:
        if alphanum_title in alphanum_text:
            analysis["alnum_infix"] = True
            return analysis
    return analysis


class SampleProcessor:
    """Process and display samples from linguistic processing output.

    Attributes:
        input_files: List of input JSONL files to sample from
        num_samples: Number of random samples per file
        show_pos: Whether to show POS tags
        max_chars: Maximum characters to display in console output
        output: Optional output file path for TSV export
    """

    def __init__(
        self,
        input_files: Sequence[Union[str, Path]],
        num_samples: int = 5,
        show_pos: bool = True,
        max_chars: int = 200,
        output: Optional[Union[str, Path]] = None,
    ) -> None:
        self.input_files = [Path(f) for f in input_files]
        self.num_samples = num_samples
        self.show_pos = show_pos
        self.max_chars = max_chars
        self.output = Path(output) if output else None
        self.writer: Optional[csv.writer] = None  # Add type annotation

    def format_sentences(self, sentences: List[Dict]) -> str:
        """Format sentences with configurable display options."""
        result = []
        for sent in sentences:
            if self.show_pos:
                tokens = [f"{t['t']}/{t['p']}" for t in sent["tokens"]]
                result.append(" ".join(tokens))
            else:
                result.append(format_sentence_with_offsets(sent["tokens"]))
        return "".join(result)

    def process_file(self, path: Path) -> None:
        """Process a single input file."""
        with smart_open.open(path) as f:
            try:
                lines = f.readlines()
            except OSError:
                logging.warning("Error reading file %s. Skipping...", path)
                return
            samples = random.sample(lines, min(self.num_samples * 2, len(lines)))
            count = 0
            for line in samples:
                if count >= self.num_samples:
                    break
                doc = json.loads(line)
                doc_id = doc.get("ci_id", "No ID")

                title = doc.get("tsents", [])
                if not title:
                    continue
                count += 1

                if self.output:
                    self._write_tsv_row(
                        path.stem, doc_id, title, doc.get("sents", [])[:3]
                    )
                else:
                    self._print_console_output(doc_id, title, doc.get("sents", [])[:3])

    def _write_tsv_row(
        self, newspaper: str, doc_id: str, title: List[Dict], sentences: List[Dict]
    ) -> None:
        """Write a single row to TSV output."""
        if self.writer is None:
            raise ValueError("CSV writer is not initialized.")

        link = f"https://impresso-project.ch/app/article/{doc_id}"
        formatted_title = self.format_sentences(title)
        formatted_text = self.format_sentences(sentences)

        # Perform analysis on the title and full text
        full_text = self.format_sentences(sentences)
        analysis = analyze_title_in_text(formatted_title, full_text)

        # Prepare the row data
        row = [
            newspaper,
            link,
            formatted_title.replace("\t", " "),
            formatted_text.replace("\t", " "),
            analysis["ellipsis"],
            analysis["exact_prefix"],
            analysis["alnum_prefix"],
            analysis["alnum_infix"],
            analysis["UNK"],
            analysis["title_longer"],
            analysis["advertisement"],
        ]

        # Log the row content
        logging.debug("Writing row to TSV: %s", row)

        # Include analysis keys in the TSV row
        self.writer.writerow(row)

    def _print_console_output(
        self, doc_id: str, title: List[Dict], sentences: List[Dict]
    ) -> None:
        """Print formatted output to console."""
        formatted_title = self.format_sentences(title)
        formatted_text = self.format_sentences(sentences)

        print(f"Document ID: https://impresso-project.ch/app/article/{doc_id}")
        print(f"Title: {formatted_title[:self.max_chars]}")
        print(f"Sentences: {formatted_text[:self.max_chars]}")
        print()

    def run(self) -> None:
        """Process all input files."""
        if self.output:
            with open(self.output, "w", newline="", encoding="utf-8") as f:
                self.writer = csv.writer(
                    f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"
                )
                self.writer.writerow(
                    [
                        "newspaper",
                        "link",
                        "title",
                        "text",
                        "ellipsis",
                        "exact_prefix",
                        "alnum_prefix",
                        "UNK",
                    ]
                )
                for file in self.input_files:
                    logging.info("Processing %s", file)
                    self.process_file(file)
        else:
            for file in self.input_files:
                logging.info("Processing %s", file)
                self.process_file(file)


def parse_arguments(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "input_files", nargs="+", type=Path, help="Input JSONL files to process"
    )
    parser.add_argument(
        "-n",
        "--num-samples",
        type=int,
        default=5,
        help="Number of random samples per file (default: 5)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output TSV file (if not specified, prints to console)",
    )
    parser.add_argument(
        "--no-pos", action="store_true", help="Display text without POS tags"
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=200,
        help="Maximum characters to display per section (default: 200)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    parser.add_argument("-l", "--log-file", type=Path, help="Log file path")

    return parser.parse_args(args)


def setup_logging(log_level: str, log_file: Optional[Path] = None) -> None:
    """Configure logging."""
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=handlers,
        force=True,
    )


def main(args: Optional[Sequence[str]] = None) -> None:
    """Main function to run the processor."""
    options = parse_arguments(args)
    setup_logging(options.log_level, options.log_file)

    processor = SampleProcessor(
        input_files=options.input_files,
        num_samples=options.num_samples,
        show_pos=not options.no_pos,
        max_chars=options.max_chars,
        output=options.output,
    )

    processor.run()


if __name__ == "__main__":
    main()
