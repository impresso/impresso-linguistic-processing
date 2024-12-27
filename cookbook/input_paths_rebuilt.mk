$(call log.debug, COOKBOOK BEGIN INCLUDE: cookbook/input_paths_rebuilt.mk)

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
  $(call log.debug, IN_S3_BUCKET_REBUILT)

# The input path
IN_S3_PATH_REBUILT := s3://$(IN_S3_BUCKET_REBUILT)/$(NEWSPAPER)
  $(call log.debug, IN_S3_PATH_REBUILT)

# The local path
IN_LOCAL_PATH_REBUILT := $(BUILD_DIR)/$(IN_S3_BUCKET_REBUILT)/$(NEWSPAPER)
  $(call log.debug, IN_LOCAL_PATH_REBUILT)


$(call log.debug, COOKBOOK END INCLUDE: cookbook/input_paths_rebuilt.mk)
