#!/usr/bin/env python3

"""
Script to preprocess text for topic modeling, utilizing precomputed language identification results.
"""

import argparse
import collections
import json
import logging
import os
from datetime import datetime
from typing import Generator, Dict, Optional

import spacy
from smart_open import open

log = logging.getLogger(__name__)

# TAG map for lb language processing
TAG_MAP = {
    "$": "PUNCT",
    "ADJ": "ADJ",
    "AV": "ADV",
    "APPR": "ADP",
    "APPRART": "ADP",
    "D": "DET",
    "KO": "CONJ",
    "N": "NOUN",
    "P": "ADV",
    "TRUNC": "X",
    "AUX": "AUX",
    "V": "VERB",
    "MV": "VERB",
    "PTK": "PART",
    "INTER": "PART",
    "NUM": "NUM",
    "_SP": "SPACE",
}


def get_next_doc(infile: str) -> Generator[Dict[str, any], None, None]:
    """
    Generates documents from a file line by line.

    Args:
        infile (str): The path to the input file.

    Yields:
        Generator[Dict[str, any], None, None]: A generator yielding documents as
            dictionaries.
    """
    with open(infile, "r") as instream:
        for line in instream:
            yield json.loads(line)


def output_doc(doc: Dict[str, any], out_file: "IO[str]") -> None:
    """
    Outputs a document to the specified file.

    Args:
        doc (Dict[str, any]): The document to output.
        out_file (IO[str]): The file object to write the document to.
    """
    print(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), file=out_file)


def read_langident(path: str) -> Dict[str, str]:
    """
    Reads language identification results from a file.

    Args:
        path (str): The path to the file containing language identification results.

    Returns:
        Dict[str, str]: A dictionary mapping document IDs to their identified languages.
    """
    result = {}
    with open(path, "r", encoding="utf-8") as f:
        for l in f:
            try:
                contentitem = json.loads(l)
                result[contentitem["id"]] = contentitem.get("lg")
            except KeyError:
                log.error("Problem %s", l)
    return result


def get_timestamp() -> str:
    """
    Generates a timestamp in a specific format.

    Returns:
        str: The generated timestamp.
    """
    time = datetime.now()
    timestamp = "%d-%d-%dT%02d:%02d:%02d" % (
        time.year,
        time.month,
        time.day,
        time.hour,
        time.minute,
        time.second,
    )
    return timestamp


LANG2MODEL = {
    "de": "de_core_news_md",
    "fr": "fr_core_news_md",
    "en": "en-core-web-md",
    "lb": "./models/lb_model/model-best/",
}


class LinguisticProcessing:
    def __init__(self, args: argparse.Namespace):
        """
        Initializes the LinguisticProcessing class.

        Args:
            args (argparse.Namespace): The command line arguments.
        """
        self.args = args
        self.language_proc_units: Dict[str, spacy.language.Language] = {}
        self.lang_ident_data: Dict[str, str] | None = (
            read_langident(self.args.lid) if self.args.lid else None
        )

        self.stats = collections.Counter()

    def create_lpu(self, lang: str) -> None:
        """
        Creates a language processing unit for the specified language.

        Args:
            lang (str): The language code.
        """
        lang2model = LANG2MODEL
        if lang not in self.language_proc_units and lang in lang2model:
            nlp = spacy.load(lang2model.get(lang, lang), disable=["parser"])
            nlp.add_pipe("sentencizer", first=True)
            nlp.max_length = 500000
            self.language_proc_units[lang] = nlp
            log.info("LOADED PIPELINE %s %s", nlp, nlp.pipeline)
        else:
            log.error("No model found for %s", lang)

    def process_doc(
        self,
        json_obj: Dict[str, any],
        timestamp: str,
    ) -> Optional[Dict[str, any]]:
        """
        Processes a single document, adding linguistic annotations.

        Args:
            json_obj (Dict[str, any]): The document to process.
            language_proc_units (Dict[str, spacy.language.Language]): The language processing units.
            timestamp (str): The current timestamp.

        Returns:
            Optional[Dict[str, any]]: The processed document or None if processing fails.
        """
        docid = json_obj["id"]
        if self.lang_ident_data:

            lang = self.lang_ident_data.get(
                docid
            )  # Use .get() to handle missing IDs gracefully
            if lang:
                self.stats["LANG-FROM-LID"] += 1
        if lang is None:
            lang = json_obj.get("lg")
            self.stats["LANG-FROM-DOC"] += 1

        if lang not in LANG2MODEL:
            log.error("No language %s found for %s", lang, docid)
            return None
        if lang not in self.language_proc_units:
            self.create_lpu(lang)

        try:
            full_text = json_obj["ft"]
        except KeyError:
            log.error("No full text found for %s", docid)
            return None
        if len(full_text) < self.args.min_doc_length:
            log.warning(
                "Document %s too short (%d): %s", docid, len(full_text), full_text
            )
            return None

        preprocessed_text = []
        doc = self.language_proc_units[lang](full_text)

        for sent in doc.sents:
            preprocessed_sent = []

            for tok in sent:
                tok_dict = {
                    "t": tok.text,
                    "p": (
                        TAG_MAP.get(tok.pos_, "X") if lang == "lb" else tok.pos_
                    ),  # Use TAG_MAP for Luxembourgish
                    "o": tok.idx,
                }
                if tok.text != tok.lemma_:
                    tok_dict["l"] = tok.lemma_

                if tok.ent_type_:
                    tok_dict["e"] = f"{tok.ent_iob_}-{tok.ent_type_}"

                preprocessed_sent.append(tok_dict)

            preprocessed_text.append({"lg": lang, "tok": preprocessed_sent})

        return {"ts": timestamp, "id": docid, "sents": preprocessed_text}

    def run(self) -> None:
        """
        Runs the linguistic processing on all documents.
        """
        infile = self.args.INPUT
        timestamp = get_timestamp()
        collection = os.path.basename(infile).split("-")[0]
        year = infile.split("-")[-1][:4]
        log.info("Working on file %s %s %s", infile, collection, year)

        with open(self.args.output_file, "w") as out_file:
            for i, json_obj in enumerate(get_next_doc(infile), start=1):
                if json_obj is None:
                    continue
                processed_doc = self.process_doc(json_obj, timestamp)
                if processed_doc is not None:
                    output_doc(processed_doc, out_file)
                if i % 200 == 0:
                    log.info("Processed %d documents", i)

        for k in self.stats:
            log.info("%s: %d", k, self.stats[k])
        log.info("Done with file %s", infile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Linguistically process texts with POS tagging, lemmatization, etc."
    )
    parser.add_argument(help="Path to impresso rebuilt file", dest="INPUT")
    parser.add_argument("--lid", help="Path to language identification file")
    parser.add_argument(
        "-o", "--output-file", default="out.jsonl", help="Path to output file"
    )
    parser.add_argument("--min-doc-length", type=int, default=200)

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)-15s %(levelname)s: %(message)s"
    )

    # Launching application...
    LinguisticProcessing(args).run()
