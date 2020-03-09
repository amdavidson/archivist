#!/usr/bin/env python3

import requests
import json
import os
from pathlib import Path
import pygit2
from lib import Log

user = "amdavidson"
backupdir = Path.home() / "backups/github/"
log = Log()
log.LOGLEVEL = 1

def backup_github(): 
    response = requests.get("https://api.github.com/users/"+user+"/repos")

    repos = json.loads(response.text)

    for repo in repos:
        log("Backing up: " + repo["name"])
        dest = backupdir / repo["name"]
        localrepopath = pygit2.discover_repository(str(dest))
        if localrepopath == None:
            log("Cloning repo...")
            pygit2.clone_repository(repo['clone_url'], str(dest), bare=True)
        else:
            log("Fetching updates...")
            localrepo = pygit2.Repository(localrepopath).remotes["origin"].fetch()


backup_github()
