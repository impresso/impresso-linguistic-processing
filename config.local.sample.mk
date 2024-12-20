# adapt any variable here


# Sample configuration for local build settings

# # Set the logging level: DEBUG, INFO, WARNING, ERROR
# LOGGING_LEVEL ?= INFO

# # Set the number of parallel embedding jobs to run
# MAKE_PARALLEL_OPTION ?= --jobs 4

# # Set the Git version (default is the output of `git describe --tags --always`)
# GIT_VERSION ?= $(shell git describe --tags --always)

# # The build directory where all local input and output files are stored
# BUILD_DIR ?= build.d

# # Specify the newspaper to process. Just a suffix appended to the s3 bucket name
# NEWSPAPER ?= actionfem

# # A file containing a space-separated line with all newspapers to process
# NEWSPAPERS_TO_PROCESS_FILE ?= $(BUILD_DIR)/newspapers.txt

# # Order the years of a newspaper to process by recency (default is random order)
# NEWSPAPER_YEAR_SORTING ?= shuf
# # For the default order, comment the line above and uncomment the line below
# # NEWSPAPER_YEAR_SORTING ?= cat

# # The input bucket for rebuilt data
# IN_S3_BUCKET_REBUILT ?= 22-rebuilt-final

# # The input bucket for processed data
# IN_S3_BUCKET_PROCESSED_DATA ?= 42-processed-data-final

# # The process label for input data
# IN_PROCESS_LABEL ?= langident

# # The run version for input data
# IN_RUN_VERSION ?= v1-4-4

# # The output bucket for processed data
# OUT_S3_BUCKET_PROCESSED_DATA ?= 40-processed-data-sandbox

# # The process label for output data
# OUT_PROCESS_LABEL ?= lingproc

# # The task for output data
# OUT_TASK ?= pos

# # The model ID for output data
# OUT_MODEL_ID ?= spacy_v3.6.0-multilingual

# # The run version for output data
# OUT_RUN_VERSION ?= v1-0-2

# # Prevent any output to S3 even if s3-output-path is set
# PROCESSING_S3_OUTPUT_DRY_RUN ?=

# # Keep only the local timestamp output files after uploading
# PROCESSING_KEEP_TIMESTAMP_ONLY_OPTION ?= --keep-timestamp-only

# # Quit the processing if the output file already exists in S3
# PROCESSING_QUIT_IF_S3_OUTPUT_EXISTS ?= --quit-if-s3-output-exists
