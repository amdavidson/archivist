#!/usr/bin/env python3

import requests
import json
import os
from pathlib import Path
import pygit2
from lib import Log

user = "amdavidson"
backupdir = Path.home() / "backups/github"
log = Log()
log.LOGLEVEL = 1

def backup_gh_repos():
    response = requests.get("https://api.github.com/users/"+user+"/repos")

    repos = json.loads(response.text)

    for repo in repos:
        log("Backing up: " + repo["name"])
        dest = backupdir / "repo" / repo["full_name"]
        localrepopath = pygit2.discover_repository(str(dest))
        if localrepopath == None:
            log("Cloning repo...")
            pygit2.clone_repository(repo['clone_url'], str(dest), bare=True)
        else:
            log("Fetching updates...")
            localrepo = pygit2.Repository(localrepopath).remotes["origin"].fetch()

def backup_gh_gists():
    response = requests.get("https://api.github.com/users/"+user+"/gists")

    gists = json.loads(response.text)

    for gist in gists:
        log("Backing up: " + gist["id"])
        dest = backupdir / "gist" / gist["owner"]["login"] / gist["id"]
        localgistpath = pygit2.discover_repository(str(dest))
        if localgistpath == None:
            log("Cloning gist...")
            pygit2.clone_repository(gist['git_pull_url'], str(dest), bare=True)
        else:
            log("Fetching updates...")
            pygit2.Repository(localgistpath).remotes["origin"].fetch()

def backup_github(): 
    backup_gh_repos()
    backup_gh_gists()

if __name__ == '__main__':
    backup_github()
