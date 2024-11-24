# Information on impresso linguistic preprocessing

This repository implements the following linguistic processing steps:

- POS tagging
- NER tagging
- improved lemmatization

We do this for the following languages:

- fr
- de
- lb (only POS tagging)
- en

The Luxembourgish language model is taken from
https://github.com/PeterGilles/Luxembourgish-language-resources/tree/master/lux-tagger-July2023/model-best
und unknown licencing status. We set the version and name in the model's meta data to lux-tagger-July2023.

## Prerequisites

The build process has been tested on modern Linux and macOS systems and requires
Python 3.11. Under Debian, make sure to have the following packages installed:

```sh
$ # install python3.11 according to your OS
$ sudo apt install git git-lfs make moreutils  # needed for building
$ sudo apt rclone  # needed for uploading to s3
$ sudo apt jq  # needed for computing statistics
```

This repository uses `pipenv`.

```sh
$ git clone https://github.com/impresso/impresso-linguistic-processing.git
$ cd impresso-linguistic-processing
$ python3.11 -mpip install pipenv
$ python3.11 -mpipenv install
$ python3.11 -mpipenv shell
```

Adapt `env.sample` to your needs and copy it to `.env`.

# Running the pipeline

Adapt the local paths for the input and output directories according in the
`config.local.mk` (see `config.local.mk.sample` for an example).
and run the following command:

```sh
make newspaper -j N # process specific newspaper/year pairs in parallel

make each -j N #  process all newspapers in parallel
```

## Command-Line Options for `spacy_linguistic_processing.py`

The `spacy_linguistic_processing.py` script supports several command-line options:

- `--lid`: Path to the language identification file.
- `--language`: Specify a language code to use for all items.
- `-o`, `--output-path`: Path to the output file (default: `out.jsonl`).
- `--min-doc-length`: Minimum document length to process (default: 50).
- `--validate`: Validate the final language identification JSON against the schema.
- `--text-property`: Specify the JSON property that contains the full text (default: `ft`).
- `--git-version`: Set the git version to include in the output. If not set, the `GIT_VERSION` environment variable is used.
- `--quit-if-s3-output-exists`: Quit if the output file already exists in the specified S3 bucket.
- `--s3-output-path`: S3 path to upload the output file after processing or check if it already exists.
- `--keep-timestamp-only`: After uploading to S3, keep only the timestamp of the local output file for data efficiency.
