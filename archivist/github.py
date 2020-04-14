import requests, json, logging, os
from pathlib import Path
import pygit2

log = logging.getLogger(__name__)

def backup_gh_repos(user, backupdir, token=None, backup_list=None, exclude_list=None):

    callbacks = None

    if token != None:
        log.info("Authenticating with Github, and pulling all repositories")
        response = requests.get("https://api.github.com/user/repos?visibility=all", auth=(user, token))
        repos = json.loads(response.text)
        cred = pygit2.UserPass(user, token)
        callbacks = pygit2.RemoteCallbacks(credentials=cred)
    else:
        response = requests.get("https://api.github.com/users/"+user+"/repos")
        repos = json.loads(response.text)
    
    to_backup = []

    if backup_list != None:
        for repo in repos:
            if repo["name"] in backup_list:
                to_backup.append(repo)
    else:
        if exclude_list != None:
            for repo in repos:
                if repo["name"] not in exclude_list:
                    to_backup.append(repo)
        else:
            to_backup = repos


    for repo in to_backup:
        log.info("Backing up: " + repo["name"])
        dest = backupdir / "repo" / repo["full_name"]
        localrepopath = pygit2.discover_repository(str(dest))
        if localrepopath == None:
            log.info("Cloning repo...")
            pygit2.clone_repository(repo['clone_url'], str(dest), bare=True, callbacks=callbacks)
        else:
            log.info("Fetching updates...")
            localrepo = pygit2.Repository(localrepopath).remotes["origin"].fetch(callbacks=callbacks)

def backup_gh_gists(user, backupdir, token=None, backup_list=None, exclude_list=None):
    if token != None:
        response = requests.get("https://api.github.com/users/"+user+"/repos", auth=(user, token))
    else:
        response = requests.get("https://api.github.com/users/"+user+"/repos")
    gists = json.loads(response.text)

    to_backup = []
    if backup_list != None:
        for gist in gists:
            if str(gist["id"]) in backup_list:
                to_backup.append(gist)
    else:
        if exclude_list != None:
            for gist in gists:
                if str(gist["id"]) not in exclude_list:
                    to_backup.append(gist)
        else:
            to_backup = gists


    for gist in to_backup:
        log.info("Backing up: " + str(gist["id"]))
        dest = backupdir / "gist" / str(gist["owner"]["login"]) / str(gist["id"])
        localgistpath = pygit2.discover_repository(str(dest))
        if localgistpath == None:
            log.info("Cloning gist...")
            pygit2.clone_repository(gist['clone_url'], str(dest), bare=True)
        else:
            log.info("Fetching updates...")
            pygit2.Repository(localgistpath).remotes["origin"].fetch()

def backup_github(config): 
    disable_gists = config.get("disable_gists", False)
    disable_repos = config.get("disable_repos", False)
    github_dir = Path(config["backup_folder"])
    if not disable_repos: backup_gh_repos(config["user"], github_dir, 
            config.get("token", None),
            config.get("repo_backup_list", None),
            config.get("repo_exclude_list", None))
    if not disable_gists: backup_gh_gists(config["user"], github_dir, 
            config.get("token", None),
            config.get("gist_backup_list", None),
            config.get("gist_exclude_list", None))
