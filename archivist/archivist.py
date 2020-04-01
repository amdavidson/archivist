import logging, sys

from archivist.lib import Config
import archivist.pinboard as pinboard
import archivist.github as github

log = logging.getLogger(__name__)

c = Config()
c.init()

class Archivist():
    def run(self, command, source):
        if command == "backup":

            if source == "github":
                log.info("Backing up Github")
                github.backup_github(c.c["github_user"], c.backupdir())
            elif source == "pinboard":
                log.info("Backing up Pinboard")
                pinboard.backup_pinboard(c.c["pinboard_user"], c.c["pinboard_token"], c.backupdir())
            elif source == "all":
                log.info("Backing up all sources")
                if c.c["github_enabled"]:
                    log.info("Backing up Github")
                    github.backup_github(c.c["github_user"], c.backupdir())
                if c.c["pinboard_enabled"]:
                    log.info("Backing up Pinboard")
                    pinboard.backup_pinboard(c.c["pinboard_user"], c.c["pinboard_token"], c.backupdir())
            else:
                log.error("Source %s not implemented" % source)

        else:
            log.error("Command %s not implemented" % command)