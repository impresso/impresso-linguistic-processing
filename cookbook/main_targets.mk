###############################################################################
# MAIN PROCESSING TARGETS
# Core targets for newspaper processing pipeline
###############################################################################

$(call log.debug, COOKBOOK BEGIN INCLUDE: cookbook/main_targets.mk)

# TARGET: newspaper
# Process a single newspaper through the linguistic processing pipeline
# Dependencies: 
# - sync: Ensures data is synchronized
# - lingproc-target: Performs the actual processing
newspaper:
	$(MAKE) sync
	$(MAKE) lingproc-target

PHONY_TARGETS += newspaper

# TARGET: all
# Complete processing with fresh data sync
# Steps:
# 1. Resync data (serial)
# 2. Process data (parallel)
all: 
	$(MAKE) resync 
	$(MAKE) $(MAKE_PARALLEL_OPTION) lingproc-target

PHONY_TARGETS += all

# TARGET: collection
# Process multiple newspapers from NEWSPAPERS_TO_PROCESS_FILE
# Iterates through newspaper list and runs 'make all' for each
collection: newspaper-list-target
	for np in $(file < $(NEWSPAPERS_TO_PROCESS_FILE)) ; do \
		$(MAKE) NEWSPAPER="$$np"  all  ; \
	done

PHONY_TARGETS += collection

$(call log.debug, COOKBOOK END INCLUDE: cookbook/main_targets.mk)
