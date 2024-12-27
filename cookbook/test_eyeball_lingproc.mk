
test-eyeball: build.d/test_eyeball.txt
	# ls -l $<
build.d/test_eyeball.txt: 
	python lib/sample_eyeball_output.py 2 $(LOCAL_LINGPROC_FILES)
