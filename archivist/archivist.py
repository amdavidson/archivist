import logging, sys

import archivist.pinboard as pinboard
import archivist.github as github

log = logging.getLogger(__name__)

class Archivist():
    def run(self, command, source):
        if command == "backup":

            if source == "github":
                log.info("Backing up Github")
                github.backup_github()
            elif source == "pinboard":
                log.info("Backing up Pinboard")
                pinboard.backup_pinboard()
            elif source == "all":
                log.info("Backing up all sources")
                github.backup_github()
                pinboard.backup_pinboard()
            else:
                log.error("Source %s not implemented" % source)

        else:
            log.error("Command %s not implemented" % command)
