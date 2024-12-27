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

# A variable for representing an empty string
EMPTY :=
  $(call log.debug, EMPTY)
###
# SETTINGS FOR THE BUILD PROCESS

# Load local config if it exists (ignore silently if it does not exists)
-include config.local.mk

# Load our make logging functions
include cookbook/log.mk

# Set the logging level: DEBUG, INFO, WARNING, ERROR
LOGGING_LEVEL ?= INFO
  $(call log.info, LOGGING_LEVEL)



# keep make output concise for longish recipes
ifeq "$(filter DEBUG,$(LOGGING_LEVEL))" "DEBUG"
  $(call log.debug, LOGGING_LEVEL)
MAKE_SILENCE_RECIPE ?= $(EMPTY)
else
MAKE_SILENCE_RECIPE ?= @
endif
  $(call log.debug, MAKE_SILENCE_RECIPE)

# Set the number of parallel embedding jobs to run
MAKE_PARALLEL_OPTION ?= --jobs 2
  $(call log.debug, MAKE_PARALLEL_OPTION)


ifndef git_version
git_version := $(shell git describe --tags --always)
endif
  $(call log.info, git_version)
export git_version

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


# help: Show this help message
help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  setup                 # Prepare the local directories"
	@echo "  collection            # Call `make all` for each newspaper found in the file $(NEWSPAPERS_TO_PROCESS_FILE)"
	@echo "  all                   # Resync the data from the S3 bucket to the local directory and process all years of a single newspaper"
	@echo "  newspaper             # Process a single newspaper for all years"
	@echo "  sync                  # Sync the data from the S3 bucket to the local directory"
	@echo "  resync                # Remove the local synchronization file stamp and sync again."
	@echo "  clean-build           # Remove the entire build directory"
	@echo "  clean-newspaper       # Remove the local directory for a single newspaper"
	@echo "  update-requirements   # Update the requirements.txt file with the current pipenv requirements."
	@echo "  lb-spacy-package      # Package the Luxembourgish spaCy model"
	@echo "  help                  # Show this help message"


.DEFAULT_GOAL := help
PHONY_TARGETS += help


###
# DEFINING THE NEWSPAPER LIST TO PROCESS
include cookbook/newspaper_list.mk

###
# DEFINING THE REQUIRED DATA INPUT PATHS
include cookbook/input_paths_rebuilt.mk

include cookbook/input_paths_langident.mk


###
# DEFINING THE OUTPUT PATHS
include cookbook/output_paths_lingproc.mk 


###
# TARGETS FOR THE BUILD PROCESS

include cookbook/setup_lingproc.mk




# Process a single newspaper
newspaper:
	$(MAKE) sync
	$(MAKE) lingproc-target

PHONY_TARGETS += newspaper

# Make newspaper from a clean fresh resync
# resync should not be parallel
# actual processing should be parallel
all: 
	$(MAKE) resync 
	$(MAKE) $(MAKE_PARALLEL_OPTION) lingproc-target

PHONY_TARGETS += all

# Process the text embeddings for each newspaper found in the file $(NEWSPAPERS_TO_PROCESS_FILE)
collection: newspaper-list-target
	for np in $(file < $(NEWSPAPERS_TO_PROCESS_FILE)) ; do \
		$(MAKE) NEWSPAPER="$$np"  all  ; \
	done

PHONY_TARGETS += collection

# SYNCING THE INPUT AND OUTPUT DATA FROM S3 TO LOCAL DIRECTORY



sync: sync-input sync-output

PHONY_TARGETS += sync


# defines sync-input-rebuilt as multifile prerequisite of sync-input
include cookbook/sync_rebuilt.mk

# Note: sync-output-lingproc is defined in cookbook/sync_lingproc.mk

include cookbook/sync_lingproc.mk


include cookbook/processing_lingproc.mk

#
include cookbook/clean.mk
%.d:
	mkdir -p $@


update-requirements:
	pipenv requirements > requirements.txt
	



# declare all phony targets
.PHONY: $(PHONY_TARGETS)

### Functions to convert local paths to s3 paths and vice versa
include cookbook/local_to_s3.mk



include lib/more_tasks.mk

# generates human readable output for inspection
include cookbook/test_eyeball_lingproc.mk
