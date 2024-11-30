## more tasks that are normally not used
COMPRESS_S3_PATH ?= s3://41-processed-data-staging/lingproc/lingproc-pos-spacy_v3.6.0-multilingual_v1-0-3/
parallel-s3-compress:
	python3 lib/s3_to_local_stamps.py --list-files --list-files-glob '*.bz2' $(COMPRESS_S3_PATH) \
	 | shuf \
	 | parallel --eta python3 lib/compress_s3_key.py {} 



# Define the source and destination buckets and folders
SOURCE_BUCKET := 41-processed-data-staging
SOURCE_FOLDER := lingproc/lingproc-pos-spacy_v3.6.0-multilingual_v1-0-3
DESTINATION_BUCKET := 42-processed-data-final
DESTINATION_FOLDER := lingproc/lingproc-pos-spacy_v3.6.0-multilingual_v1-0-3

# Target to copy an S3 folder from one bucket to another
copy-s3-folder: 
	AWS_CONFIG_FILE=.aws/config AWS_SHARED_CREDENTIALS_FILE=.aws/credentials \
	aws s3 sync s3://$(SOURCE_BUCKET)/$(SOURCE_FOLDER)/ s3://$(DESTINATION_BUCKET)/$(DESTINATION_FOLDER)/ 

PHONY_TARGETS += copy-s3-folder

## spacy model packaging
lb-spacy-package:
	mkdir -p models-package
	pipenv run python -m spacy package models/lb_model/model-best/ models-package/


test-aws: |.aws/credentials .aws/config
	AWS_CONFIG_FILE=.aws/config AWS_SHARED_CREDENTIALS_FILE=.aws/credentials \
	aws s3 ls s3://41-processed-data-staging/lingproc/lingproc-pos-spacy_v3.6.0-multilingual_v1-0-3/

create-aws-config: .aws/credentials .aws/config

.aws/config: | .env
	@echo "Creating local AWS CLI configuration: $@"
	mkdir -p .aws
	@echo "[default]" > .aws/config
	@echo "region = us-east-1" >> .aws/config
	@echo "output = json" >> .aws/config
	@echo "endpoint_url = $$(grep SE_HOST_URL .env | cut -d '=' -f2)" >> .aws/config


.aws/credentials: | .env
	@echo "Creating local AWS CLI configuration: $@"
	echo "[default]" > .aws/credentials
	@echo "aws_access_key_id = $$(grep SE_ACCESS_KEY .env | cut -d '=' -f2)" >> .aws/credentials
	@echo "aws_secret_access_key = $$(grep SE_SECRET_KEY .env | cut -d '=' -f2)" >> .aws/credentials
	
