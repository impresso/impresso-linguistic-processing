###############################################################################
# TESTING AND INSPECTION TARGETS
# Targets for manual inspection of processing results
###############################################################################

$(call log.debug, COOKBOOK BEGIN INCLUDE: cookbook/test_eyeball_lingproc.mk)

# TARGET: test-eyeball
# Generate sample output for manual inspection
test-eyeball: build.d/test_eyeball.txt
	# ls -l $<

# Generate test sample from processed files
build.d/test_eyeball.txt: 
	python lib/sample_eyeball_output.py 2 $(LOCAL_LINGPROC_FILES)


$(call log.debug, COOKBOOK END INCLUDE: cookbook/test_eyeball_lingproc.mk)
