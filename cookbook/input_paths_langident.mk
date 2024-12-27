$(call log.debug, COOKBOOK BEGIN INCLUDE: cookbook/input_paths_langident.mk)

# DEFINING THE REQUIRED DATA INPUT PATHS
# all paths are defined as s3 paths and local paths
# local paths are relative to $BUILD_DIR
# s3 paths are relative to the bucket
# The paths are defined as variables to make it easier to change them in the future.
# Input paths start with IN_ and output paths with OUT_
# Make variables for s3 paths are defined as OUT_S3_ or IN_S3_
# If more than one input is needed, the variable names are IN_1_S3_ or OUT_2_S3_
# Make variables for local paths are defined as OUT_LOCAL_ or IN_LOCAL_

# langident bucket
IN_S3_BUCKET_LANGINDENT := 42-processed-data-final
  $(call log.debug, IN_S3_BUCKET_LANGINDENT)

IN_PROCESS_LABEL_LANGINDENT ?= langident
  $(call log.debug, IN_PROCESS_LABEL_LANGINDENT)

IN_PROCESS_SUBTYPE_LABEL_LANGINDENT ?=
  $(call log.debug, IN_PROCESS_SUBTYPE_LABEL_LANGINDENT)

# @FIX NOT USED  s3://42-processed-data-final/langident/langident_v1-4-4/ACI/ACI-1832.jsonl.bz2
IN_TASK ?=


# @FIX s3://42-processed-data-final/langident/langident_v1-4-4/ACI/ACI-1832.jsonl.bz2
IN_MODEL_ID ?= 

IN_RUN_VERSION_LANGINDENT ?= v1-4-4
  $(call log.debug, IN_RUN_VERSION_LANGINDENT)

# @FIX 
IN_RUN_ID_LANGIDENT ?= $(IN_PROCESS_LABEL_LANGINDENT)_$(IN_RUN_VERSION_LANGINDENT)
  $(call log.debug, IN_RUN_ID_LANGIDENT)

IN_S3_PATH_LANGIDENT := s3://$(IN_S3_BUCKET_LANGINDENT)/$(IN_PROCESS_LABEL_LANGINDENT)/$(IN_RUN_ID_LANGIDENT)/$(NEWSPAPER)
  $(call log.debug, IN_S3_PATH_LANGIDENT)
  
IN_LOCAL_PATH_LANGIDENT := $(BUILD_DIR)/$(IN_S3_BUCKET_LANGINDENT)/$(IN_PROCESS_LABEL_LANGINDENT)/$(IN_RUN_ID_LANGIDENT)/$(NEWSPAPER)
  $(call log.debug, IN_LOCAL_PATH_LANGIDENT)


$(call log.debug, COOKBOOK END INCLUDE: cookbook/input_paths_langident.mk)
