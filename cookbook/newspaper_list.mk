$(call log.debug, COOKBOOK BEGIN INCLUDE: cookbook/newspaper_list.mk)


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

PHONY_TARGETS += newspaper-list-target

# Rule to generate the file containing the newspapers to process
# we shuffle the newspapers to avoid recomputations by different machines working on the dataset
$(NEWSPAPERS_TO_PROCESS_FILE): | $(BUILD_DIR)
	python -c \
	"import lib.s3_to_local_stamps as m; import random; \
	s3 = m.get_s3_resource(); \
	bucket = s3.Bucket('$(IN_S3_BUCKET_REBUILT)'); \
    result = bucket.meta.client.list_objects_v2(Bucket=bucket.name, Delimiter='/'); \
	l = [prefix['Prefix'][:-1] for prefix in result.get('CommonPrefixes', [])]; \
	random.shuffle(l); \
    print(*l)" \
	> $@


$(call log.debug, COOKBOOK END INCLUDE: cookbook/newspaper_list.mk)
