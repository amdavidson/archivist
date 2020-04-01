import requests, json, datetime, os, time, glob, logging
from pathlib import Path

log = logging.getLogger(__name__)

def get_last_backup(backups_folder):
    backups = backups_folder.glob("*.json")
    oldest = datetime.datetime.fromtimestamp(0)
    for b in backups:
        bdate = datetime.datetime.fromtimestamp(float(b.stem))
        if bdate > oldest:
            oldest = bdate
    return oldest


def backup_pinboard(user, token, backups_folder):
    response = requests.get("https://api.pinboard.in/v1/posts/update?format=json&auth_token="+user+":"+token)

    apiupdated = datetime.datetime.strptime(json.loads(response.text)["update_time"], "%Y-%m-%dT%H:%M:%SZ")

    if apiupdated > get_last_backup(backups_folder) :
        log.info("New bookmarks added, pulling latest backup...")
        response = requests.get("https://api.pinboard.in/v1/posts/all?format=json&auth_token="+user+":"+token)
        backupfile = str(time.time()) + ".json" 
        backuppath = backups_folder / backupfile
        backups_folder.mkdir(parents=True, exist_ok=True)

        with open(backuppath, "w+") as f:
            f.write(response.text)
    else:
        log.info("No new bookmarks since last backup.")
