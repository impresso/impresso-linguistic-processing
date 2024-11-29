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
import sys
import time
from typing import Any, Dict, Generator, IO, Optional

import dotenv
import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7
import smart_open
import spacy

from s3_to_local_stamps import (
    keep_timestamp_only,
    parse_s3_path,
    get_s3_client,
    s3_file_exists,
    upload_file_to_s3,
    get_timestamp,
    have_same_md5,
)

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


def initialize_validator(
    schema_base_uri=SCHEMA_BASE_URI, schema=IMPRESSO_SCHEMA
) -> jsonschema.Draft7Validator:
    """
    Initializes the schema validator.
    """
    with smart_open.open(
        schema_base_uri + schema,
        "r",
    ) as f:
        schema = json.load(f)

    registry = Registry().with_resource(
        schema_base_uri,
        Resource.from_contents(schema),
    )

    validator = jsonschema.Draft7Validator(
        schema=schema, resolver=registry.resolver(DRAFT7)
    )
    return validator


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
        # Check if the output file already exists in S3 and avoid lengthy processing
        if self.args.quit_if_s3_output_exists and (s3out := self.args.s3_output_path):
            if s3_file_exists(self.S3_CLIENT, s3out):
                log.warning(
                    "%s exists. Exiting without processing %s", s3out, self.args.INPUT
                )
                exit(3)
            else:
                log.info("%s does not exist. Proceeding with processing.", s3out)
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
            self.schema_validator = initialize_validator()

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
            nlp.max_length = self.args.max_doc_length + 1
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
            log.debug(
                "Full text property `%s` unavailable in `%s`",
                self.args.text_property,
                docid,
            )
            self.stats["CONTENT-ITEMS-NO-TEXT"] += 1
            return None

        full_text_len = len(full_text)
        if full_text_len == 0:
            log.debug("Empty text: %s", docid)
            self.stats["CONTENT-ITEMS-EMPTY"] += 1
            return None
        elif full_text_len < self.args.min_doc_length:
            log.debug("Short text (%s chars): %s ", full_text_len, docid)
            self.stats["CONTENT-ITEMS-SHORT"] += 1
            return None
        elif full_text_len > self.args.max_doc_length:
            log.debug("Long text (%s chars): %s ", full_text_len, docid)
            self.stats["CONTENT-ITEMS-LONG"] += 1
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
                    full_text[:50],
                )
                return None

        if lang not in LANG2MODEL:
            log.error("No spacy model for language %s: content item: %s", lang, docid)
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
                    "p": (LB_TAG_MAP.get(tok.tag_, "X") if lang == "lb" else tok.pos_),
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
            "max_chars": self.args.max_doc_length,
        }

    def run(self) -> None:
        """
        Runs the linguistic processing on all documents.
        """
        infile = self.args.INPUT
        outfile: str = self.args.output_path
        s3_outfile: str = self.args.s3_output_path
        timestamp: str = get_timestamp()
        collection: str = os.path.basename(infile).split("-")[0]
        year: str = infile.split("-")[-1][:4]

        total_doc_count = len(self.lang_ident_data)
        newspaper = outfile.split("/")[-1].split(".")[0]
        start_time = time.time()
        processed_doc_count = 1
        log.info("Processing %s %s %s", infile, collection, year)

        with smart_open.open(outfile, "w") as out:
            doc_iter = enumerate(get_next_doc(infile, client=self.S3_CLIENT), start=1)
            for i, json_obj in doc_iter:
                if json_obj is None:
                    continue
                processed_doc = self.process_doc(json_obj, timestamp)
                if self.args.validate and processed_doc is not None:
                    if not self.validate_document(processed_doc):
                        sys.exit(1)

                if processed_doc is not None:
                    output_doc(processed_doc, out)
                    processed_doc_count += 1
                    if processed_doc_count % 1000 == 0:
                        end_time = time.time()

                        log.info(
                            "Processed %d content items with content (total with"
                            " unprocessable: %d/%d in %s) in %d secs/1k content items",
                            processed_doc_count,
                            i,
                            total_doc_count,
                            newspaper,
                            round((end_time - start_time), 1),
                        )
                        start_time = end_time
        log.info(
            "Processed %d processable documents (total documents: %d)",
            processed_doc_count,
            i,
        )

        for k in self.stats:
            log.info("%s: %d", k, self.stats[k])
        log.info("File %s successfully processed locally.", infile)

        # Upload the output file to S3 if specified
        if s3_outfile:
            upload_file_to_s3(self.S3_CLIENT, outfile, s3_outfile)

            if self.args.keep_timestamp_only:
                keep_timestamp_only(outfile)

    def upload_file_to_s3(self, local_file_path: str, s3_path: str) -> None:
        """Uploads a local file to an S3 bucket if it doesn't already exist and verifies the upload."""
        bucket, key = parse_s3_path(s3_path)
        if s3_file_exists(self.S3_CLIENT, bucket, key):
            log.warning(
                "The file s3://%s/%s already exists. Skipping upload.", bucket, key
            )
            return

        try:
            # Upload the file to S3
            log.info("Uploading %s to s3://%s/%s", local_file_path, bucket, key)
            self.S3_CLIENT.upload_file(local_file_path, bucket, key)
            log.info(
                "Successfully uploaded %s to s3://%s/%s", local_file_path, bucket, key
            )

            # Verify the upload by comparing MD5 checksums
            if have_same_md5(local_file_path, s3_path, self.S3_CLIENT):
                log.info("File %s successfully verified after upload.", local_file_path)
            else:
                log.error(
                    "MD5 checksum mismatch: local file %s != s3 file %s",
                    local_file_path,
                    s3_path,
                )
                raise ValueError("MD5 checksum mismatch after upload.")

        except FileNotFoundError:
            log.error("The file %s was not found.", local_file_path)
        except self.S3_CLIENT.exceptions.NoCredentialsError:
            log.error("Credentials not available.")
        except self.S3_CLIENT.exceptions.PartialCredentialsError:
            log.error("Incomplete credentials provided.")
        except Exception as e:
            log.error("An error occurred: %s", e)

    def validate_document(self, document: Dict[str, Any]) -> bool:
        """
        Validates a document against the schema.

        Args:
            document (Dict[str, Any]): The document to validate.

        Returns:
            bool: True if the document is valid, False otherwise.
        """
        try:
            self.schema_validator.validate(document)
            log.debug("Document %s is valid", document["id"])
            return True
        except jsonschema.ValidationError as e:
            log.error("Validation error: %s", e)
            return False
        except jsonschema.SchemaError as e:
            log.error("Schema error: %s", e)
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Linguistically process texts with POS tagging, lemmatization, etc. If"
            " --quit-if-s3-output-exists is set, the script will exit with exit code 3"
            " without processing if the output file already exists in the specified S3"
            " bucket."
        )
    )
    parser.add_argument(help="Path to impresso rebuilt file", dest="INPUT")
    parser.add_argument("--lid", help="Path to language identification file")
    parser.add_argument(
        "--language", help="Specify a language code to use for all items"
    )
    parser.add_argument(
        "-o", "--output-path", default="out.jsonl", help="Path to output file"
    )
    parser.add_argument("--min-doc-length", type=int, default=50)
    parser.add_argument("--max-doc-length", type=int, default=50000)
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
    parser.add_argument(
        "--quit-if-s3-output-exists",
        action="store_true",
        help="Quit if the output file already exists in the specified S3 bucket",
    )
    parser.add_argument(
        "--s3-output-path",
        help=(
            "S3 path to upload the output file after processing or check if it already"
            " exists"
        ),
    )
    parser.add_argument(
        "--keep-timestamp-only",
        action="store_true",
        help=(
            "After uploading to S3, keep only the timestamp of the local output file"
            " for data efficiency. Defaults: %(default)s"
        ),
    )
    parser.add_argument(
        "--log-file",
        help=(
            "Path to the log file (compression depending on smart_open and file"
            " extension)"
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not log to console, only to the log file (if specified).",
    )
    args = parser.parse_args()

    # Configure logging
    if args.quiet:
        log_handlers = []
    else:
        log_handlers = [logging.StreamHandler()]
    if args.log_file:

        class SmartFileHandler(logging.FileHandler):
            def _open(self):
                return smart_open.open(self.baseFilename, self.mode, encoding="utf-8")

        log_handlers.append(SmartFileHandler(args.log_file, mode="w"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)-15s %(filename)s:%(lineno)d %(levelname)s: %(message)s",
        handlers=log_handlers,
        force=True,
    )
    log.info("Called with args: %s", args)

    # Launching application...
    LinguisticProcessing(args).run()
    sys.exit(0)
