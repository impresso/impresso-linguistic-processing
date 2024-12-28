$(call log.debug, COOKBOOK BEGIN INCLUDE: cookbook/clean.mk)


clean-newspaper: clean-sync
	
PHONY_TARGETS += clean-newspaper

clean-build:
	rm -rvf $(BUILD_DIR)

PHONY_TARGETS += clean-build

# Remove the local synchronization file stamp and redoes everything, ensuring a full sync with the remote server.
resync: clean-newspaper
	$(MAKE) sync

PHONY_TARGETS += resync

resync-output: clean-sync-lingproc
	$(MAKE) sync-output


$(call log.debug, COOKBOOK END INCLUDE: cookbook/clean.mk)
