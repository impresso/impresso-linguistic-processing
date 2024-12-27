$(call log.debug, COOKBOOK BEGIN INCLUDE: cookbook/sync_rebuilt.mk)


### SYNCING THE INPUT DATA FROM S3 TO LOCAL DIRECTORY

sync-input:: sync-input-rebuilt 

PHONY_TARGETS += sync-input

# The local per-newspaper synchronization file stamp for the rebuilt input data: What is on S3 has been synced?
IN_LOCAL_REBUILT_SYNC_STAMP_FILE := $(IN_LOCAL_PATH_REBUILT).last_synced
  $(call log.debug, IN_LOCAL_REBUILT_SYNC_STAMP_FILE)

sync-input-rebuilt: $(IN_LOCAL_REBUILT_SYNC_STAMP_FILE)

PHONY_TARGETS += sync-input-rebuilt

# The local per-newspaper synchronization file stamp for the processed input data: What is on S3 has been synced?
IN_LOCAL_LANGIDENT_SYNC_STAMP_FILE := $(IN_LOCAL_PATH_LANGIDENT).last_synced
  $(call log.debug, IN_LOCAL_LANGIDENT_SYNC_STAMP_FILE)

# the suffix of for the local stamp files (added to the input paths on s3)
IN_LOCAL_REBUILT_STAMP_SUFFIX ?= .stamp
  $(call log.debug, IN_LOCAL_REBUILT_STAMP_SUFFIX)

# Rule to sync the input data from the S3 bucket to the local directory
$(IN_LOCAL_PATH_REBUILT).last_synced:
	mkdir -p $(@D) && \
	python lib/s3_to_local_stamps.py \
	   $(IN_S3_PATH_REBUILT) \
	   --local-dir $(BUILD_DIR) \
	   --stamp-extension $(IN_LOCAL_REBUILT_STAMP_SUFFIX) \
	   2> >(tee $@.log >&2) && \
	touch $@



$(call log.debug, COOKBOOK END INCLUDE: cookbook/sync_rebuilt.mk)