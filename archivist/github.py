import requests, json, logging, os
from pathlib import Path
import pygit2

log = logging.getLogger(__name__)

def backup_gh_repos(user, backupdir):
    response = requests.get("https://api.github.com/users/"+user+"/repos")

    repos = json.loads(response.text)

    for repo in repos:
        log.info("Backing up: " + repo["name"])
        dest = backupdir / "repo" / repo["full_name"]
        localrepopath = pygit2.discover_repository(str(dest))
        if localrepopath == None:
            log.info("Cloning repo...")
            pygit2.clone_repository(repo['clone_url'], str(dest), bare=True)
        else:
            log.info("Fetching updates...")
            localrepo = pygit2.Repository(localrepopath).remotes["origin"].fetch()

def backup_gh_gists(user, backupdir):
    response = requests.get("https://api.github.com/users/"+user+"/gists")

    gists = json.loads(response.text)

    for gist in gists:
        log.info("Backing up: " + gist["id"])
        dest = backupdir / "gist" / gist["owner"]["login"] / gist["id"]
        localgistpath = pygit2.discover_repository(str(dest))
        if localgistpath == None:
            log.info("Cloning gist...")
            pygit2.clone_repository(gist['git_pull_url'], str(dest), bare=True)
        else:
            log.info("Fetching updates...")
            pygit2.Repository(localgistpath).remotes["origin"].fetch()

def get_github_dir(backupdir):
    github_dir = backupdir / "github"
    return github_dir

def backup_github(user, backupdir): 
    github_dir = get_github_dir(backupdir)
    backup_gh_repos(user, github_dir)
    backup_gh_gists(user, github_dir)
