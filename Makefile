# Makefile for linguistic processing for newspapers
# Read the README.md for more information on how to use this Makefile.
# Or run `make` for online help.

###
# SETTINGS FOR THE MAKE PROGRAM

# Define the shell to use for executing commands
SHELL := /bin/bash

# Enable strict error handling
export SHELLOPTS := errexit:pipefail

# Keep intermediate files generated for the build process
.SECONDARY:

# Delete intermediate files if the target fails
.DELETE_ON_ERROR:

# Suppress all default rules
.SUFFIXES:

# A variable for representing an empty string
EMPTY :=
  $(call log.debug, EMPTY)

###
# SETTINGS FOR THE BUILD PROCESS

# Load local config if it exists (ignore silently if it does not exist)
-include config.local.mk

# Load our make logging functions
include cookbook/log.mk

# Set the logging level: DEBUG, INFO, WARNING, ERROR
LOGGING_LEVEL ?= INFO
  $(call log.info, LOGGING_LEVEL)

# Keep make output concise for longish recipes
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

# Get the current git version
ifndef git_version
git_version := $(shell git describe --tags --always)
endif
  $(call log.info, git_version)
export git_version

###
# SETTING DEFAULT VARIABLES FOR THE PROCESSING

# The build directory where all local input and output files are stored
# The content of BUILD_DIR can be removed anytime without issues regarding s3
BUILD_DIR ?= build.d
  $(call log.debug, BUILD_DIR)

# Specify the newspaper to process. Just a suffix appended to the s3 bucket name
# s3 is ok! Can also be actionfem/actionfem-1933
NEWSPAPER ?= actionfem
  $(call log.info, NEWSPAPER)

# Help: Show this help message
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
# INCLUDES AND CONFIGURATION FILES
#------------------------------------------------------------------------------

# Load newspaper list configuration and processing rules
include cookbook/newspaper_list.mk

# Load input path definitions for rebuilt content
include cookbook/input_paths_rebuilt.mk

# Load input path definitions for language identification
include cookbook/input_paths_langident.mk

# Load output path definitions for linguistic processing
include cookbook/output_paths_lingproc.mk 

# Load setup rules for linguistic processing
include cookbook/setup_lingproc.mk

###
# MAIN TARGETS
#------------------------------------------------------------------------------

include cookbook/main_targets.mk

###
# SYNCHRONIZATION TARGETS
#------------------------------------------------------------------------------

# Synchronize both input and output data with S3
sync: sync-input sync-output

PHONY_TARGETS += sync

# Include synchronization rules for rebuilt content
include cookbook/sync_rebuilt.mk

# Include synchronization rules for linguistic processing output
include cookbook/sync_lingproc.mk

# Include cleanup rules
include cookbook/clean.mk


###
# PROCESSING TARGETS
#------------------------------------------------------------------------------

# Include main linguistic processing rules
include cookbook/processing_lingproc.mk



###
# FINAL DECLARATIONS AND UTILITIES
#------------------------------------------------------------------------------

# Declare all targets that don't produce files
.PHONY: $(PHONY_TARGETS)

# Include path conversion utilities
include cookbook/local_to_s3.mk

# Include testing and inspection utilities
include cookbook/test_eyeball_lingproc.mk
