#!/usr/bin/env python3

import requests, json, datetime, os, time, glob
from lib import Log, Config
from pathlib import Path


log = Log()
log.LOGLEVEL=1

backupdir = Path.home() / "backups/pinboard"

config = Config()
c = config.init()

def get_last_backup():
    backups = backupdir.glob("*.json")
    oldest = datetime.datetime.fromtimestamp(0)
    for b in backups:
        bdate = datetime.datetime.fromtimestamp(float(b.stem))
        if bdate > oldest:
            oldest = bdate
    return oldest


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

if __name__ == '__main__':
    backup_pinboard()
