## more tasks that are normally not used
COMPRESS_S3_PATH ?= s3://41-processed-data-staging/lingproc/lingproc-pos-spacy_v3.6.0-multilingual_v1-0-3/
parallel-s3-compress:
	python3 lib/s3_to_local_stamps.py --list-files --list-files-glob '*.bz2' $(COMPRESS_S3_PATH) \
	 | parallel -j $(MAKE_PARALLEL_OPTION) python3 lib/compress_s3_key.py {} 
