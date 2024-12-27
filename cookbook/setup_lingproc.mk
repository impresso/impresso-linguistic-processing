$(call log.debug, COOKBOOK BEGIN INCLUDE: cookbook/setup_lingproc.mk)

# Detect the operating system
OS ?= $(shell uname -s)
  $(call log.debug, OS)

# Initialize INSTALLER
INSTALLER ?= unknown

# If Linux, check the distribution
ifeq ($(OS),Linux)
    DISTRO := $(shell grep -Ei 'debian|ubuntu' /etc/os-release 2>/dev/null)
    ifneq ($(DISTRO),)
        INSTALLER := apt
    endif
else ifeq ($(OS),Darwin)
    INSTALLER := brew
endif
  $(call log.debug, INSTALLER)

# Prepare the local directories
setup:
	# Create the local directory
	mkdir -p $(IN_LOCAL_PATH_REBUILT)
	mkdir -p $(OUT_LOCAL_PATH_LINGPROC)
	#$(MAKE) check-python-installation
	# Sync the newspaper media list to process (testing s3 connectivity as well)
	$(MAKE) newspaper-list-target
	$(MAKE) check-spacy-pipelines

check-spacy-pipelines:
	$(MAKE_SILENCE_RECIPE)python3 -m spacy validate || \
	{ echo "Spacy pipelines are not properly installed! Please install the required pipelines." ; exit 1; }

PHONY_TARGETS += check-spacy-pipelines


PHONY_TARGETS += setup



check-python-installation:
	#
	# TEST PYTHON INSTALLATION FOR mallet topic inference ...
	python3 lib/test_jpype_installation.py || \
	{ echo "Double check whether the required python packages are installed! or you running in the correct python environment!" ; exit 1; }
	# OK: PYTHON ENVIRONMENT IS FINE!

PHONY_TARGETS +=  check-python-installation
update-requirements:
	pipenv requirements > requirements.txt

PHONY_TARGETS += update-requirements
$(call log.debug, COOKBOOK END INCLUDE: cookbook/setup_lingproc.mk)
