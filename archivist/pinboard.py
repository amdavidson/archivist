import requests, json, datetime, os, time, glob, logging
from pathlib import Path

log = logging.getLogger(__name__)

def get_old_backups(pinboard_dir):
    newest = datetime.datetime.fromtimestamp(0)
    old_backups = []
    for b in pinboard_dir.glob("*.json"):
        old_backups.append(b)
        bdate = datetime.datetime.fromtimestamp(float(b.stem))
        if bdate > newest:
            newest = bdate
    return newest, old_backups

def backup_pinboard(config):
    response = requests.get("https://api.pinboard.in/v1/posts/update?format=json&auth_token="+config["user"]+":"+config["token"])

    apiupdated = datetime.datetime.strptime(json.loads(response.text)["update_time"], "%Y-%m-%dT%H:%M:%SZ")

    pinboard_dir = Path(config["backup_folder"])

    newest_backup, old_backups = get_old_backups(pinboard_dir)

    if apiupdated > newest_backup:
        log.info("New bookmarks added, pulling latest backup...")
        response = requests.get("https://api.pinboard.in/v1/posts/all?format=json&auth_token="+config["user"]+":"+config["token"])
        backupfile = str(time.time()) + ".json" 
        pinboard_dir.mkdir(parents=True, exist_ok=True)
        backuppath = pinboard_dir / backupfile

        with open(backuppath, "w+") as f:
            f.write(response.text)

        if not config.get("keep_old", False):
            log.info("Cleaning up old backups.")
            for b in old_backups:
                b.unlink()

        
    else:
        log.info("No new bookmarks since last backup.")
