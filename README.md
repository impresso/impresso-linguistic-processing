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

# Running the pipeline

Adapt the local paths for the input and output directories in the `Makefile.local.mk` and run the following command:

```sh
make impresso-linguistic-processing-target -j N
```

# Uploading to impresso S3 bucket

Ensure that the environment variables SE_ACCESS_KEY and SE_SECRET_KEY for access to the
s3 impresso infrastructure are set, e.g. by setting them in a local .env files.

```sh
make upload-to-s3
```
