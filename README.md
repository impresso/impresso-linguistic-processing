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
Python 3.11. Under Ubuntu/Debian
, make sure to have the following packages installed:

```sh
# install python3.11 according to your OS
sudo apt update
sudo apt upgrade -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 -y
sudo apt install python3.11-distutils -y
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
sudo apt install git git-lfs make moreutils  # needed for building
sudo apt jq  # needed for computing statistics
```

This repository uses `pipenv`.

```sh
git clone https://github.com/impresso/impresso-linguistic-processing.git
cd impresso-linguistic-processing
python3.11 -mpip install pipenv
python3.11 -mpipenv install
python3.11 -mpipenv shell
```

For s3-based file processing, the following environment variables need to be set:

```sh
SE_ACCESS_KEY=
SE_SECRET_KEY=
SE_HOST_URL=
```

If your global environment does not contain these variables, you can set them in a local
`.env` file. The `python-dotenv` package is used to read these variables.

```sh
cp env.sample .env
edit .env
```

# Running the pipeline

## Local configuration

Adapt the local paths for the input and output directories in the
`config.local.mk` (see `config.local.mk.sample` for default settings.)

```sh
cp config.local.mk.sample config.local.mk
edit config.local.mk
```

## Running the pipeline

The build process is controlled by the `Makefile`.

```sh
make help  # show available targets

make newspaper -j N # process specific newspaper/year pairs in parallel typically for testing

make collection  MAKE_PARALLEL_OPTION=16   #  process all newspapers using parallel processing within newspaper/year pairs
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

# Uploading to impresso S3 bucket

Ensure that the environment variables `SE_ACCESS_KEY` and `SE_SECRET_KEY` for access to the
S3 impresso infrastructure are set, e.g., by setting them in a local `.env` file.

The build process uploads the processed data to the impresso S3 bucket.

Release notes:

- 2024-11-27: v1-0-3
  - chore: improve logging and add length limit for input text
- 2024-11-25: v1-0-1
  - fix: POS tagging of lb was buggy (all tags set to X). This has been fixed.
  - feat: Generate log files for each newspaper/year pair and upload it to s3.
  - feat: Support agreed nameing convention for output files.
  - feat: Process directly from s3 input data, on-the-fly mirroring per newspaper for
    slim builds
  - note: no change to spaCy pipelines apart from lb POS tag mapping
- 2024-04-24: v1-0-0
  - First public release of the impresso linguistic processing pipeline.
