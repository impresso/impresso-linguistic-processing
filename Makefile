# Description: Makefile for linguistic processing for newspapers
# Read the README.md for more information on how to use this Makefile.
# Or run `make` for online help.

###
# SETTINGS FOR THE MAKE PROGRAM

# Define the shell to use for executing commands
SHELL:=/bin/bash

# Enable strict error handling
export SHELLOPTS:=errexit:pipefail

# Keep intermediate files generated for the build process
.SECONDARY:

# Delete intermediate files if the target fails
.DELETE_ON_ERROR:

# suppress all default rules
.SUFFIXES:

###
# SETTINGS FOR THE BUILD PROCESS

# Load local config if it exists (ignore silently if it does not exists)
-include config.local.mk

# Set the logging level: DEBUG, INFO, WARNING, ERROR
LOGGING_LEVEL ?= INFO
  $(call log.info, LOGGING_LEVEL)

# Load our make logging functions
include lib/log.mk

# Set the number of parallel embedding jobs to run
MAKE_PARALLEL_OPTION ?= --jobs 2
  $(call log.debug, MAKE_PARALLEL_OPTION)


###
# SETTING DEFAULT VARIABLES FOR THE PROCESSING

# The build directory where all local input and output files are stored
# The content of BUILD_DIR be removed anytime without issues regarding s3
BUILD_DIR ?= build.d
  $(call log.debug, BUILD_DIR)

# Specify the newspaper to process. Just a suffix appended to the s3 bucket name
# s3 is ok!  Can also be actionfem/actionfem-1933
NEWSPAPER ?= actionfem
  $(call log.info, NEWSPAPER)


# A file containing a space-separated line with all newspapers to process
# Feel free to handcraft another file with the newspapers you want to process
# This file is automatically populated from the content of s3 rebuilt bucket
NEWSPAPERS_TO_PROCESS_FILE ?= $(BUILD_DIR)/newspapers.txt
  $(call log.debug, NEWSPAPERS_TO_PROCESS_FILE)

# When determining the order of years of a newspaper to process, order them by recency
# (default or order them randomly? By recency, larger newer years are processed first,
# avoiding waiting for the most recent years to be processed). By random order,
# recomputations by different machines working on the dataset are less likely to happen.
NEWSPAPER_YEAR_SORTING ?= shuf
# for the default order, comment the line above and uncomment the line below
#NEWSPAPER_YEAR_SORTING ?= cat
  $(call log.debug, NEWSPAPER_YEAR_SORTING)

# Target 
newspaper-list-target: $(NEWSPAPERS_TO_PROCESS_FILE)

# Rule to generate the file containing the newspapers to process
# we shuffle the newspapers to avoid recomputations by different machines working on the dataset
$(NEWSPAPERS_TO_PROCESS_FILE): $(BUILD_DIR)
	python -c \
	"import lib.s3_to_local_stamps as m; import random; \
	s3 = m.get_s3_resource(); \
	bucket = s3.Bucket('$(IN_S3_BUCKET_REBUILT)'); \
    result = bucket.meta.client.list_objects_v2(Bucket=bucket.name, Delimiter='/'); \
	l = [prefix['Prefix'][:-1] for prefix in result.get('CommonPrefixes', [])]; \
	random.shuffle(l); \
    print(*l)" \
	> $@

###
# SPACY MODEL SETTINGS

# Not yet needed

###
# DEFINING THE REQUIRED DATA INPUT PATHS
# all paths are defined as s3 paths and local paths
# local paths are relative to $BUILD_DIR
# s3 paths are relative to the bucket
# The paths are defined as variables to make it easier to change them in the future.
# Input paths start with IN_ and output paths with OUT_
# Make variables for s3 paths are defined as OUT_S3_ or IN_S3_
# If more than one input is needed, the variable names are IN_1_S3_ or OUT_2_S3_
# Make variables for local paths are defined as OUT_LOCAL_ or IN_LOCAL_

# The input bucket
IN_S3_BUCKET_REBUILT ?= 22-rebuilt-final

# The input path
IN_S3_PATH_REBUILT := s3://$(IN_S3_BUCKET_REBUILT)/$(NEWSPAPER)
  $(call log.debug, IN_S3_PATH_REBUILT)

# The local path
IN_LOCAL_PATH_REBUILT := $(BUILD_DIR)/$(IN_S3_BUCKET_REBUILT)/$(NEWSPAPER)
  $(call log.debug, IN_LOCAL_PATH_REBUILT)

# langident bucket
IN_S3_BUCKET_PROCESSED_DATA := 42-processed-data-final

IN_PROCESS_LABEL ?= langident

IN_PROCESS_SUBTYPE_LABEL ?=

# @FIX NOT USED  s3://42-processed-data-final/langident/langident_v1-4-4/ACI/ACI-1832.jsonl.bz2
IN_TASK ?=

# @FIX s3://42-processed-data-final/langident/langident_v1-4-4/ACI/ACI-1832.jsonl.bz2
IN_MODEL_ID ?= 

IN_RUN_VERSION ?= v1-4-4

# @FIX 
IN_RUN_ID ?= $(IN_PROCESS_LABEL)_$(IN_RUN_VERSION)

IN_S3_PATH_PROCESSED_DATA := s3://$(IN_S3_BUCKET_PROCESSED_DATA)/$(IN_PROCESS_LABEL)/$(IN_RUN_ID)/$(NEWSPAPER)
  $(call log.debug, IN_S3_PATH_PROCESSED_DATA)
  
IN_LOCAL_PATH_PROCESSED_DATA := $(BUILD_DIR)/$(IN_S3_BUCKET_PROCESSED_DATA)/$(IN_PROCESS_LABEL)/$(IN_RUN_ID)/$(NEWSPAPER)
  $(call log.debug, IN_LOCAL_PATH_PROCESSED_DATA)


###
# DEFINING THE OUTPUT PATHS

# The output bucket
OUT_S3_BUCKET_PROCESSED_DATA ?= 40-processed-data-sandbox

OUT_PROCESS_LABEL ?= lingproc
  $(call log.debug, OUT_PROCESS_LABEL)

OUT_PROCESS_SUBTYPE_LABEL ?= 
  $(call log.debug, OUT_PROCESS_SUBTYPE_LABEL)
  
OUT_TASK ?= pos

OUT_MODEL_ID ?= spacy_v3.6.0-multilingual
  $(call log.debug, OUT_MODEL_ID)

OUT_RUN_VERSION ?= v1-0-2
  $(call log.debug, OUT_RUN_VERSION)
  
OUT_RUN_ID ?= $(OUT_PROCESS_LABEL)-$(OUT_TASK)-$(OUT_MODEL_ID)_$(OUT_RUN_VERSION)
  $(call log.debug, OUT_RUN_ID)
  

# The s3 output path
OUT_S3_PATH_PROCESSED_DATA := s3://$(OUT_S3_BUCKET_PROCESSED_DATA)/$(OUT_PROCESS_LABEL)$(OUT_PROCESS_SUBTYPE_LABEL)/$(OUT_RUN_ID)/$(NEWSPAPER)
  $(call log.debug, OUT_S3_PATH_PROCESSED_DATA)

# The local path in BUILD_DIR
OUT_LOCAL_PATH_PROCESSED_DATA := $(BUILD_DIR)/$(OUT_S3_BUCKET_PROCESSED_DATA)/$(OUT_PROCESS_LABEL)$(OUT_PROCESS_SUBTYPE_LABEL)/$(OUT_RUN_ID)/$(NEWSPAPER)
  $(call log.debug, OUT_LOCAL_PATH_PROCESSED_DATA)

###
# LINGUISTIC PROCESSOR SETTINGS

###
# S3 STORAGE UPDATE SETTINGS

# Prevent any output to s3 even if s3-output-path is set
# EMBEDDING_S3_OUTPUT_DRY_RUN?= --s3-output-dry-run
# To disable the dry-run mode, comment the line above and uncomment the line below
EMBEDDING_S3_OUTPUT_DRY_RUN ?=
  $(call log.debug, EMBEDDING_S3_OUTPUT_DRY_RUN)

# Keep only the local timestam output files after uploading (only relevant when
# uploading to s3)
#
EMBEDDING_KEEP_TIMESTAMP_ONLY_OPTION ?= --keep-timestamp-only
# To disable the keep-timestamp-only mode, comment the line above and uncomment the line below
#EMBEDDING_KEEP_TIMESTAMP_ONLY_OPTION ?= 
  $(call log.debug, EMBEDDING_KEEP_TIMESTAMP_ONLY_OPTION)


# Quit the processing if the output file already exists in s3
# double check if the output file exists in s3 and quit if it does
EMBEDDING_QUIT_IF_S3_OUTPUT_EXISTS ?= --quit-if-s3-output-exists
# To disable the quit-if-s3-output-exists mode, comment the line above and uncomment the line below
#EMBEDDING_QUIT_IF_S3_OUTPUT_EXISTS ?=
  $(call log.debug, EMBEDDING_QUIT_IF_S3_OUTPUT_EXISTS)


###
# TARGETS FOR THE BUILD PROCESS

# Prepare the local directories
setup:
	# Create the local directory
	mkdir -p $(IN_LOCAL_PATH_REBUILT)
	mkdir -p $(OUT_LOCAL_PATH_PROCESSED_DATA)
	mkdir -p $(IN_LOCAL_PATH_PROCESSED_DATA)
	#$(MAKE) check-python-installation
	$(MAKE) newspaper-list-target




# Process a single newspaper
newspaper:
	$(MAKE) sync
	$(MAKE) processing-target

# Process the text embeddings for each newspaper found in the file $(NEWSPAPERS_TO_PROCESS_FILE)
each:
	for np in $(file < $(NEWSPAPERS_TO_PROCESS_FILE)) ; do \
		$(MAKE) NEWSPAPER="$$np" all  ; \
	done


# SYNCING THE INPUT AND OUTPUT DATA FROM S3 TO LOCAL DIRECTORY

# Sync  the data from the S3 bucket to the local directory for input of textembeddings and output of textembeddings
sync: sync-input sync-output

sync-input: sync-input-rebuilt sync-input-processed

# The local per-newspaper synchronization file stamp for the rebuilt input data: What is on S3 has been synced?
IN_LOCAL_REBUILT_SYNC_STAMP_FILE := $(IN_LOCAL_PATH_REBUILT).last_synced
  $(call log.debug, IN_LOCAL_REBUILT_SYNC_STAMP_FILE)

sync-input-rebuilt: $(IN_LOCAL_REBUILT_SYNC_STAMP_FILE)

# The local per-newspaper synchronization file stamp for the processed input data: What is on S3 has been synced?
IN_LOCAL_PROCESSED_DATA_SYNC_STAMP_FILE := $(IN_LOCAL_PATH_PROCESSED_DATA).last_synced
  $(call log.debug, IN_LOCAL_PROCESSED_DATA_SYNC_STAMP_FILE)

sync-input-processed: $(IN_LOCAL_PROCESSED_DATA_SYNC_STAMP_FILE)

# The local per-newspaper synchronization file stamp for the output text embeddings: What is on S3 has been synced?
OUT_LOCAL_PROCESSED_DATA_SYNC_STAMP_FILE := $(OUT_LOCAL_PATH_PROCESSED_DATA).last_synced
  $(call log.debug, OUT_LOCAL_PROCESSED_DATA_SYNC_STAMP_FILE)



sync-output: sync-output-processed-data

sync-output-processed-data: $(OUT_LOCAL_PROCESSED_DATA_SYNC_STAMP_FILE)


# Remove the local synchronization file stamp and redoes everything, ensuring a full sync with the remote server.
resync: clean-sync
	$(MAKE) sync

clean-sync:
	rm -vf $(IN_LOCAL_REBUILT_SYNC_STAMP_FILE) $(OUT_LOCAL_PROCESSED_DATA_SYNC_STAMP_FILE) || true

# Rule to sync the input data from the S3 bucket to the local directory
$(IN_LOCAL_PATH_REBUILT).last_synced:
	mkdir -p $(@D) && \
	python lib/s3_to_local_stamps.py \
	   $(IN_S3_PATH_REBUILT) \
	   --local-dir $(BUILD_DIR) \
	   --stamp-extension .stamp \
	   2> >(tee $@.log >&2) && \
	touch $@

# Rule to sync the input data from the S3 bucket to the local directory
$(IN_LOCAL_PATH_PROCESSED_DATA).last_synced:
	mkdir -p $(@D) && \
	python lib/s3_to_local_stamps.py \
	   $(IN_S3_PATH_PROCESSED_DATA) \
	   --local-dir $(BUILD_DIR) \
	   --write-content \
	   2> >(tee $@.log >&2) && \
	touch $@


# Rule to sync the output data from the S3 bucket to the local directory
$(OUT_LOCAL_PATH_PROCESSED_DATA).last_synced:
	mkdir -p $(@D) && \
	python lib/s3_to_local_stamps.py \
	   $(OUT_S3_PATH_PROCESSED_DATA) \
	   --local-dir $(BUILD_DIR) \
	   --stamp-extension '' \
	   2> >(tee $@.log >&2) && \
	touch $@


# variable for all locally available rebuilt stamp files. Needed for dependency tracking
# of the build process. We discard errors as the path or file might not exist yet.
local-rebuilt-stamp-files := \
    $(shell ls -r $(IN_LOCAL_PATH_REBUILT)/*.jsonl.bz2.stamp 2> /dev/null \
      |$(if $(NEWSPAPER_YEAR_SORTING),$(NEWSPAPER_YEAR_SORTING),cat))
  $(call log.debug, local-rebuilt-stamp-files)

define local_rebuilt_stamp_to_local_processed_file
$(1:$(IN_LOCAL_PATH_REBUILT)/%.jsonl.bz2.stamp=$(OUT_LOCAL_PATH_PROCESSED_DATA)/%.jsonl.bz2)
endef


local-processed-files := \
 $(call local_rebuilt_stamp_to_local_processed_file,$(local-rebuilt-stamp-files))

  $(call log.debug, local-processed-files)

processing-target: sync $(local-processed-files)


# Rule to process a single newspaper
$(OUT_LOCAL_PATH_PROCESSED_DATA)/%.jsonl.bz2: $(IN_LOCAL_PATH_REBUILT)/%.jsonl.bz2.stamp $(IN_LOCAL_PATH_PROCESSED_DATA)/%.jsonl.bz2
	mkdir -p $(@D) && \
	python3 $(LIB)/spacy_linguistic_processing.py \
	      $(call local_to_s3,$<,.stamp) \
		  --lid $(word 2,$^) \
		  --validate \
		  -o $@ \
		  2> $@.log \
	|| rm -f $@



# Configuration
LIB ?= lib
IMPRESSO_LANGIDENT_DATA_DIR ?= language-identification-data
IMPRESSO_REBUILT_DATA_DIR ?= rebuilt-data




help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  impresso-linguistic-processing-target      # Process all impresso rebuilt files."
	@echo "  update-requirements                        # Update the requirements.txt file with the current pipenv requirements."
	@echo "  help                                       # Show this help message"

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

# $(BUILD_DIR)/%.jsonl.bz2: $(IMPRESSO_REBUILT_DATA_DIR)/%.jsonl.bz2 $(IMPRESSO_LANGIDENT_DATA_DIR)/%.jsonl.bz2
# 	mkdir -p $(@D) &&\
# 	python3 $(LIB)/spacy_linguistic_processing.py \
# 	      $< \
# 		  --lid $(word 2,$^) \
# 		  --validate \
# 		  -o $@ \
# 		  2> $@.log \
# 	|| rm -f $@



#: Actually upload the impresso linguistic information to s3 impresso bucket
upload-release-to-s3: impresso-linguistic-processing-target 
	rclone --verbose copy $(BUILD_DIR)/ s3-impresso:$(S3_BUCKET_LINGPROC_PATH)/$(S3_LINGPROC_VERSION) --include "*.jsonl.bz2" --ignore-existing \


#	&& rclone --verbose check $(BUILD_DIR)/$(LID_S3_LINGPROC_VERSIONVERSION)/ s3-impresso:$(S3_BUCKET_LINGPROC_PATH)/$(LID_VERSION)/


update-requirements:
	pipenv requirements > requirements.txt


test-txt:
	bzcat linguistic-preprocessing-output/waeschfra/waeschfra-1871.jsonl.bz2  |\
	jq -r '.sents[] | [(.tok[] | .t + "/" + .p + "/" + (if .l == "" or .l == null then .t else .l end))] | join(" ")'
	

lb-spacy-package:
	mkdir -p models-package
	pipenv run python -m spacy package models/lb_model/model-best/ models-package/

%.d:
	mkdir -p $@


# declare all phony targets
.PHONY: $(PHONY_TARGETS)

###
# HELPER FUNCTIONS USED IN RECIPES

# function to turn a local file path into a s3 file path, optionall cutting off the
# suffix given as argument
define local_to_s3
$(subst $(2),,$(subst $(BUILD_DIR),s3:/,$(1)))
endef
# Doctests for local_to_s3 function

# Example 1: Convert local path to S3 path without stripping any suffix
# Input: $(call local_to_s3,build.d/22-rebuilt-final/marieclaire/file.txt)
# Output: s3://22-rebuilt-final/marieclaire/file.txt
# $(call log.debug, $(call local_to_s3,build.d/22-rebuilt-final/marieclaire/file.txt))
# Example 2: Convert local path to S3 path and strip the .txt suffix
# Input: $(call local_to_s3,build.d/22-rebuilt-final/marieclaire/file.txt,.txt)
# Output: s3://22-rebuilt-final/marieclaire/file

# Example 3: Convert local path to S3 path and strip a custom suffix
# Input: $(call local_to_s3,build.d/22-rebuilt-final/marieclaire/file.custom,.custom)
# Output: s3://22-rebuilt-final/marieclaire/file
