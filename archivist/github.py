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

def backup_github(config): 
    disable_gists = config.get("disable_gists", False)
    disable_repos = config.get("disable_repos", False)
    github_dir = Path(config["backup_folder"])
    if not disable_repos: backup_gh_repos(config["user"], github_dir)
    if not disable_gists: backup_gh_gists(config["user"], github_dir)
