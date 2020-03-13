#!/usr/bin/env python3

import requests, json, datetime, os, time
from lib import Log, Config
from pathlib import Path

log = Log()
log.LOGLEVEL=1

backupdir = Path.home() / "backups/pinboard"

config = Config()
c = config.init()

def get_last_backup():
    log("WARN: not checking age of last backup, backing up anyways.", loglevel="warn")
    return datetime.datetime.fromtimestamp(0)

def backup_pinboard():
    response = requests.get("https://api.pinboard.in/v1/posts/update?format=json&auth_token="+c["pinboard_user"]+":"+c["pinboard_token"])

    apiupdated = datetime.datetime.strptime(json.loads(response.text)["update_time"], "%Y-%m-%dT%H:%M:%SZ")

    if apiupdated > get_last_backup() :
        log("New bookmarks added, pulling latest backup...")
        response = requests.get("https://api.pinboard.in/v1/posts/all?format=json&auth_token="+c["pinboard_user"]+":"+c["pinboard_token"])
        backupfile = str(time.time()) + ".json" 
        backuppath = backupdir / backupfile
        backupdir.mkdir(parents=True, exist_ok=True)

        with open(backuppath, "w+") as f:
            f.write(response.text)
    else:
        log("No new bookmarks since last backup.")
    
backup_pinboard()
