$(call log.debug, COOKBOOK BEGIN INCLUDE: cookbook/setup.mk)

# general setup and functionality for running the cookbook





# Create directory if it doesn't exist
%.d:
	mkdir -p $@



# Update Python package requirements
update-requirements:
	pipenv requirements > requirements.txt

$(call log.debug, COOKBOOK END INCLUDE: cookbook/setup.mk)
