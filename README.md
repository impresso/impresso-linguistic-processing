# Information on impresso linguistic preprocessing
This repository implements the following linguistic processing steps:
 - POS tagging
 - NER tagging
 - improved lemmatization

We do this for the following languages:
 - fr
 - de
 - lb
 - en

## Prerequisites
The build process has been tested on modern Linux and macOS systems and requires
Python 3.8. Under Debian, make sure to have the following packages installed:

```sh
$ # install python3.8 according to your OS
$ sudo apt install git git-lfs make moreutils  # needed for building
$ sudo apt rclone  # needed for uploading to s3
$ sudo apt jq  # needed for computing statistics
```

This repository uses `pipenv`.

```sh
$ git clone https://github.com/impresso/impresso-linguistic-preprocessing.git
$ cd impresso-linguistic-preprocessing
$ python3.8 -mpip install pipenv
$ python3.8 -mpipenv install
$ python3.8 -mpipenv shell
```
