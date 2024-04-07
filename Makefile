##########################################################################################
# Makefile for impresso linguistic preprocessing
#
# Note: Processing is done on locally stored data, not directly on s3 storage.


##########################################################################################
# Make setup

SHELL := pipenv run /bin/bash -u
export SHELLOPTS := errexit:pipefail
.SECONDARY:

# Defines local variables if file exists
# See README.md for details
-include Makefile.local.mk


# Configuration
LIB ?= lib
IMPRESSO_LANGIDENT_DATA_DIR ?= language-identification-output
IMPRESSO_REBUILT_DATA_DIR ?= rebuilt-data
BUILD_DIR ?= build.d
REBUILT_DIR ?= /srv/scratch2/climpresso/s3data/canonical-rebuilt-release


include lib/debug.mk

help:
	# Available targets:
	@echo "  impresso-linguistic-processing-target # Process all impresso rebuilt files."
	@echo "  update-requirements # Update the requirements.txt file with the current pipenv requirements."
	@echo "  test-txt # Test the linguistic preprocessing output."
.DEFAULT_GOAL := help
PHONY_TARGETS += help

##########################################################################################
# Make variables for impresso data infrastructure
# Variables in uppercase and underscores can be overwritten by the user at build time

# make sure that this directory points to a local copy of the impresso s3 data containers
# only read access is needed
IMPRESSO_REBUILT_DATA_DIR ?= rebuilt-data


# all known collection acronyms from the file system
COLLECTION_ACRONYMS ?= $(notdir $(wildcard $(IMPRESSO_REBUILT_DATA_DIR)/*))


# get path of all impresso rebuilt files
impresso-rebuilt-files := \
	$(wildcard \
		$(foreach ca,$(COLLECTION_ACRONYMS),\
			$(IMPRESSO_REBUILT_DATA_DIR)/$(ca)/*.jsonl.bz2\
		)\
	)


impresso-linguistic-processing-files := \
	$(subst $(IMPRESSO_REBUILT_DATA_DIR),$(BUILD_DIR)/,$(impresso-rebuilt-files))

impresso-linguistic-processing-target : $(impresso-linguistic-processing-files)

$(BUILD_DIR)/%.jsonl.bz2: $(IMPRESSO_REBUILT_DATA_DIR)/%.jsonl.bz2 $(IMPRESSO_LANGIDENT_DATA_DIR)/%.jsonl.bz2
	mkdir -p $(@D) &&\
	python3 $(LIB)/spacy_linguistic_preprocessing.py \
	      $< \
		  --lid $(word 2,$^) \
		  -o $@ \
		  2> $@.log


update-requirements:
	pipenv requirements > requirements.txt


test-txt:
	bzcat linguistic-preprocessing-output/waeschfra/waeschfra-1871.jsonl.bz2  |\
	jq -r '.sents[] | [(.tok[] | .t + "/" + .p + "/" + (if .l == "" or .l == null then .t else .l end))] | join(" ")'
	



# declare all phony targets
.PHONY: $(PHONY_TARGETS)
