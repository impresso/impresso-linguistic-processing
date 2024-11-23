#!/usr/bin/env python3

"""
Script to_ preprocess text for topic modeling, utilizing precomputed language
identification results.
"""

import argparse
import collections
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Generator, IO, Optional

import boto3
import dotenv
import jsonschema
import smart_open
import spacy

dotenv.load_dotenv()


log = logging.getLogger(__name__)

SCHEMA_BASE_URI = (
    "https://impresso.github.io/impresso-schemas/json/linguistic_annotation/"
)

IMPRESSO_SCHEMA = "ling_spacy.schema.json"


# TAG map for lb language processing
LB_TAG_MAP = {
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


def get_s3_client() -> boto3.client:
    """Returns a boto3.client object for interacting with S3.

    Returns:
        boto3.client: A boto3.client object for interacting with S3.
    """
    import boto3  # noqa: E402

    boto3.setup_default_session(
        aws_access_key_id=os.getenv("SE_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("SE_SECRET_KEY"),
    )

    return boto3.client(
        "s3", endpoint_url=os.getenv("SE_HOST_URL", "https://os.zhdk.cloud.switch.ch/")
    )


def get_next_doc(
    infile: str, client: Optional[Any] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Generates documents from a file line by line.

    Args:
        infile (str):a The path to the input file.
        client (Optional[Any]): The S3 client to use for reading the file.
            Defaults to None.

    Yields:
        Generator[Dict[str, Any], None,t None]: A generator yielding documents as
            dictionaries.
    """
    transport_params = {}
    if client is not None:
        transport_params = {"client": client}
    with smart_open.open(infile, "r", transport_params=transport_params) as instream:
        for line in instream:
            yield json.loads(line)


def output_doc(doc: Dict[str, Any], out_file: "IO[str]") -> None:
    """
    Outputs a document to the specified file.

    Args:
        doc (Dict[str, Any]): The document to output.
        out_file (IO[str]): The file object to write the document to.
    """
    print(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), file=out_file)


def read_langident(path: str, client: Optional[Any] = None) -> Dict[str, str]:
    """
    Reads language identification results from a file.

    Args:
        path (str): The (s3) path to the language identification file.
        client (Optional[Any]): The S3 client to use for reading the file.
    Returns:
        Dict[str, str]: A dictionary mapping document IDs to their identified languages.
    """

    result = {}
    transport_params = {}
    if client is not None:
        transport_params = {"client": client}

    with smart_open.open(
        path,
        "r",
        encoding="utf-8",
        transport_params=transport_params,
    ) as f:
        for line in f:
            try:
                contentitem = json.loads(line)
                result[contentitem["id"]] = contentitem.get("lg")
            except KeyError:
                log.error("Problem %s", line)
    return result


def get_timestamp() -> str:
    """
    Generates a timestamp in a specific format.

    Returns:
        str: The generated timestamp.
    """
    timestamp = datetime.utcnow().isoformat(sep="T", timespec="seconds") + "Z"
    return timestamp


LANG2MODEL = {
    "de": "de_core_news_md",
    "fr": "fr_core_news_md",
    "en": "en_core_web_md",
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
        self.S3_CLIENT = (
            get_s3_client()
            if self.args.INPUT.startswith("s3://")
            or str(self.args.lid).startswith("s3://")
            else None
        )
        self.language_proc_units: Dict[str, spacy.language.Language] = {}
        self.lang_ident_data: Dict[str, str] | None = (
            read_langident(self.args.lid, client=self.S3_CLIENT)
            if self.args.lid
            else None
        )
        self.model_versions: Dict[str, str] = {}  # Store model versions
        self.git_version = (
            self.args.git_version
            if self.args.git_version
            else os.environ.get("GIT_VERSION", "unknown")
        )
        if self.args.validate:
            with smart_open.open(
                SCHEMA_BASE_URI + IMPRESSO_SCHEMA,
                "r",
            ) as f:
                self.schema = json.load(f)
            self.schema_validator = jsonschema.Draft7Validator(
                schema=self.schema,
                resolver=jsonschema.RefResolver(
                    referrer=self.schema,
                    base_uri=SCHEMA_BASE_URI,
                ),
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
            nlp.max_length = 100000
            self.language_proc_units[lang] = nlp
            self.model_versions[lang] = (
                "spacy@"
                + spacy.__version__
                + ":"
                + nlp.meta["lang"]
                + "_"
                + nlp.meta["name"]
                + "@"
                + nlp.meta["version"]
                + ":"
                + "|".join(nlp.pipe_names)
            )
            log.info("LOADED PIPELINE %s %s", nlp, nlp.pipeline)
            log.info("model_id: %s", self.model_versions[lang])
        else:
            log.error("No model found for %s", lang)

    def process_doc(
        self,
        json_obj: Dict[str, Any],
        timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Processes a single document, adding linguistic annotations.

        Args:
            json_obj (Dict[str, Any]): The document to process.
            timestamp (str): The current timestamp.

        Returns:
            Optional[Dict[str, Any]]: The processed document or None if processing
                fails.
        """
        docid = json_obj["id"]

        full_text = json_obj.get(self.args.text_property)
        if full_text is None:
            log.warning(
                "Full text property `%s` unavailable in `%s`",
                self.args.text_property,
                docid,
            )
            return None
        full_text_len = len(full_text)
        if full_text_len == 0:
            log.info("Empty text: %s", docid)
            self.stats["CONTENT-ITEMS-EMPTY"] += 1
            return None
        elif full_text_len < self.args.min_doc_length:
            log.info("Short text (%s chars): %s ", full_text_len, docid)
            self.stats["CONTENT-ITEMS-SHORT"] += 1
            return None

        lang = None
        lid_path = "default"

        if self.args.language:
            lang = self.args.language
            self.stats["LANG-FROM-ARG"] += 1
        elif self.lang_ident_data:
            lang = self.lang_ident_data.get(docid)
            if lang:
                self.stats["LANG-FROM-LID"] += 1
                lid_path = self.args.lid
        if lang is None:
            lang = json_obj.get("lg")
            if lang:
                self.stats["LANG-FROM-DOC"] += 1
            else:
                self.stats["LANG-NONE"] += 1
                log.warning(
                    "Skipping %s. Language is None. Text: `%s`",
                    docid,
                    json_obj.get("ft", "")[:50],
                )
                return None

        if lang not in LANG2MODEL:
            log.error(
                "No spacy model for language %s found: content item: %s", lang, docid
            )
            return None
        if lang not in self.language_proc_units:
            self.create_lpu(lang)

        self.stats["CONTENT-ITEMS-OK"] += 1
        preprocessed_text = []
        doc = self.language_proc_units[lang](full_text)

        for sent in doc.sents:
            preprocessed_sent = []

            for tok in sent:
                tok_dict = {
                    "t": tok.text,
                    "p": (
                        LB_TAG_MAP.get(tok.tag_, "X") if lang == "lb" else tok.pos_
                    ),  # Use TAG_MAP for Luxembourgish
                    "o": tok.idx,
                }
                if tok.text != tok.lemma_:
                    tok_dict["l"] = tok.lemma_

                if tok.ent_type_:
                    tok_dict["e"] = f"{tok.ent_iob_}-{tok.ent_type_}"

                preprocessed_sent.append(tok_dict)

            preprocessed_text.append({"lg": lang, "tok": preprocessed_sent})

        return {
            "id": docid,
            "ts": timestamp,
            "sents": preprocessed_text,
            "model_id": self.model_versions[lang],
            "lid_path": lid_path,
            "lingproc_git": self.git_version,
            "char_count": full_text_len,
            "min_chars": self.args.min_doc_length,
        }

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
            for i, json_obj in enumerate(
                get_next_doc(infile, client=self.S3_CLIENT), start=1
            ):
                if json_obj is None:
                    continue
                processed_doc = self.process_doc(json_obj, timestamp)
                if self.args.validate and processed_doc is not None:
                    try:
                        self.schema_validator.validate(processed_doc)
                        log.debug("Document %s is valid", processed_doc["id"])
                    except jsonschema.ValidationError as e:
                        log.error("Validation error: %s", e)
                        exit(1)
                    except jsonschema.SchemaError as e:
                        log.error("Schema error: %s", e)
                        exit(1)

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
        "--language", help="Specify a language code to use for all items"
    )
    parser.add_argument(
        "-o", "--output-file", default="out.jsonl", help="Path to output file"
    )
    parser.add_argument("--min-doc-length", type=int, default=50)
    parser.add_argument(
        "--validate",
        action="store_true",
        help=(
            "validate final lang identification JSON against schema (default"
            " %(default)s)"
        ),
    )
    parser.add_argument(
        "--text-property",
        default="ft",
        help="Specify the JSON property that contains the full text (%(default)s)",
    )
    parser.add_argument(
        "--git-version",
        help=(
            "Set the git version to include in the output. If not set, the GIT_VERSION"
            " environment variable is used."
            "Normally the output of `git describe --tags --always` is used."
        ),
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)-15s %(filename)s:%(lineno)d %(levelname)s: %(message)s",
    )

    # Launching application...
    LinguisticProcessing(args).run()
