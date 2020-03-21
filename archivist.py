#!/usr/bin/env python

from github import backup_github
from pinboard import backup_pinboard
from lib import Log
import sys

log = Log()
log.LOGLEVEL = 1

command = sys.argv[1] if len(sys.argv) > 1 else "backup"
source = sys.argv[2] if len(sys.argv) > 2 else "all"

if command == "backup":

    if source == "github":
        log("Backing up Github")
        backup_github()
    elif source == "pinboard":
        log("Backing up Pinboard")
        backup_pinboard()
    elif source == "all":
        log("Backing up all sources")
        backup_github()
        backup_pinboard()
    else:
        print("Source %s not implemented" % source)

else:
    print("Command %s not implemented" % command)
