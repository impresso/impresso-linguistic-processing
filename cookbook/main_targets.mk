$(call log.debug, COOKBOOK BEGIN INCLUDE: cookbook/main_targets.mk)

# Process a single newspaper through the linguistic processing pipeline
# Dependencies: sync and lingproc-target
newspaper:
	$(MAKE) sync
	$(MAKE) lingproc-target

PHONY_TARGETS += newspaper

# Perform complete processing of a newspaper with fresh data
# First performs resync (serially) then processing (in parallel)
all: 
	$(MAKE) resync 
	$(MAKE) $(MAKE_PARALLEL_OPTION) lingproc-target

PHONY_TARGETS += all

# Batch process multiple newspapers listed in NEWSPAPERS_TO_PROCESS_FILE
# Runs 'make all' for each newspaper in the list
collection: newspaper-list-target
	for np in $(file < $(NEWSPAPERS_TO_PROCESS_FILE)) ; do \
		$(MAKE) NEWSPAPER="$$np"  all  ; \
	done

PHONY_TARGETS += collection

$(call log.debug, COOKBOOK END INCLUDE: cookbook/main_targets.mk)
