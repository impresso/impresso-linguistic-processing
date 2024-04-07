
## configuration for testing
# Just execute the same targets on test data


IMPRESSO_REBUILT_DATA_DIR ?= test/rebuilt-data
IMPRESSO_LANGIDENT_DATA_DIR ?= test/langident
BUILD_DIR ?= testbuild


include Makefile
