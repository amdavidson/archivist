import requests, json, datetime, os, time, glob, logging
from pathlib import Path

log = logging.getLogger(__name__)

def get_last_backup(pinboard_dir):
    backups = pinboard_dir.glob("*.json")
    oldest = datetime.datetime.fromtimestamp(0)
    for b in backups:
        bdate = datetime.datetime.fromtimestamp(float(b.stem))
        if bdate > oldest:
            oldest = bdate
    return oldest

def get_pinboard_dir(backups_folder):
    pinboard_dir = backups_folder / "pinboard"
    return pinboard_dir

def backup_pinboard(user, token, backups_folder):
    response = requests.get("https://api.pinboard.in/v1/posts/update?format=json&auth_token="+user+":"+token)

    apiupdated = datetime.datetime.strptime(json.loads(response.text)["update_time"], "%Y-%m-%dT%H:%M:%SZ")

    pinboard_dir = get_pinboard_dir(backups_folder)

    if apiupdated > get_last_backup(pinboard_dir) :
        log.info("New bookmarks added, pulling latest backup...")
        response = requests.get("https://api.pinboard.in/v1/posts/all?format=json&auth_token="+user+":"+token)
        backupfile = str(time.time()) + ".json" 
        pinboard_dir.mkdir(parents=True, exist_ok=True)
        backuppath = pinboard_dir / backupfile

        with open(backuppath, "w+") as f:
            f.write(response.text)
    else:
        log.info("No new bookmarks since last backup.")
