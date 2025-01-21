import bz2
import json

import argparse
from collections import defaultdict, Counter
from urllib.parse import urlparse
from s3_to_local_stamps import get_s3_client
import logging


def list_s3_files(bucket, prefix):
    s3 = get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

    files = []
    for page in pages:
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".jsonl.bz2"):
                files.append(obj["Key"])
    return files


def get_length_of_json_sents(sents):
    """
        {
      "ci_id": "waeschfra-1884-05-10-a-i0005",
      "ts": "2025-01-02T23:49:10Z",
      "sents": [
        {
          "lg": "fr",
          "tokens": [
            { "t": "Bier", "p": "PROPN", "o": 0, "e": "B-PER" },
            { "t": ",", "p": "PUNCT", "o": 4 },
            { "t": "incendie", "p": "NOUN", "o": 6 },
            { "t": "éclate", "p": "VERB", "o": 15, "l": "éclater" },
            { "t": ".", "p": "PUNCT", "o": 22 }
          ]
        },
        {
          "lg": "fr",
          "tokens": [
            { "t": "Mme", "p": "NOUN", "o": 24, "e": "B-PER" },
            { "t": "X", "p": "ADJ", "o": 28, "e": "I-PER" },
            { "t": "affolée", "p": "NOUN", "o": 30, "l": "affolé" },
            { "t": ".", "p": "PUNCT", "o": 37 }
          ]
        }
      ],
      "model_id": "spacy@3.6.1:fr_core_news_md",
      "char_count": 297
    }
    """
    last_token = sents[-1]["tokens"][-1]
    return last_token["o"] + len(last_token["t"])


def init_counter():
    props = [
        "has_text",
        "has_title",
        "exact_prefix",
        "title_longer",
        "ellipsis",
        "alnum_infix",
        "alnum_prefix",
        "unknown",
        "advertisement",
    ]
    props_values = [f"{prop}={value}" for prop in props for value in [True]]
    return Counter(**dict.fromkeys(props_values, 0))


def read_title_status_from_s3(bucket, key):
    s3 = get_s3_client()
    response = s3.get_object(Bucket=bucket, Key=key)
    compressed_data = response["Body"].read()
    decompressed_data = bz2.decompress(compressed_data).decode("utf-8")

    title_status = init_counter()
    year = None
    for line in decompressed_data.splitlines():
        record = json.loads(line)
        status = {}
        # status = {'exact_prefix': , 'title_longer': 0, 'ellipsis': 1, 'alnum_infix': 3, 'alnum_prefix': 26}
        status["has_text"] = record["char_count"] > 0
        status["has_title"] = bool(record["tsents"])
        status.update(record["title_status"])

        newspaper, year = record["ci_id"].split("-")[0:2]
        if status["has_text"] and not status["has_title"]:
            logging.warning(
                f"No TITLE: https://impresso-project.ch/app/article/{record['ci_id']} "
            )
        if status["has_title"] and "&#" in "".join(
            t["t"] for t in record["tsents"][0]["tokens"]
        ):
            logging.warning(
                "HTML entities in title:"
                f" https://impresso-project.ch/app/article/{record['ci_id']} "
            )
        for key, value in status.items():
            title_status[f"{key}={value}"] += 1
            if key == "title_longer" and value:
                title_length = get_length_of_json_sents(record["tsents"])
                fulltext_length = (
                    get_length_of_json_sents(sents)
                    if (sents := record.get("sents"))
                    else 0
                )
                if (diff := title_length - fulltext_length) > 5:

                    logging.warning(
                        f"Title longer ({diff} chars):"
                        f" https://impresso-project.ch/app/article/{record['ci_id']} "
                    )
    if year is None:
        # file was empty
        return {}
    result = {"year": year, "newspaper": newspaper}
    result.update(title_status)
    return {"year": result}


def aggregate_title_status(bucket, prefix):
    files = list_s3_files(bucket, prefix)

    for key in files:
        title_status = read_title_status_from_s3(bucket, key)
        if title_status:
            print(json.dumps(title_status))


def parse_s3_path(s3_path):
    parsed_url = urlparse(s3_path)
    bucket = parsed_url.netloc
    prefix = parsed_url.path.lstrip("/")
    return bucket, prefix


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate title_status from S3 JSONL.BZ2 files."
    )
    parser.add_argument(
        "s3_path", type=str, help="S3 path in the format s3://bucket/prefix"
    )
    args = parser.parse_args()
    logging.warning("Starting aggregation %s", args)
    bucket, prefix = parse_s3_path(args.s3_path)
    aggregate_title_status(bucket, prefix)


if __name__ == "__main__":
    main()
