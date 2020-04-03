# Archivist 

The archivist is run from a either a central `archivist.py` script

Running `./archivist.py` alone will back up all configured services.

You can also back up a single service by running `./archivist.py backup service`


## Configuring the Archivist

The Archivist is configured with a `yaml` file at `~/.archivist.yml`

Example:
```yaml
backup_folder: /home/amd/backups

github_enabled: True
github_user: defunkt

pinboard_enabled: True
pinboard_user: idlewords
pinboard_token: 46a9d5bde718bf366178313019f04a753bad00685d38e3ec81c8628f35dfcb1b

imap_enabled: True
imap_localroot: maildir
imap_server: imap.email-host.com 
imap_user: me@email-host.com 
imap_password: hunter2 
imap_cleanup: True
```

## Supported Services

- Github
- Pinboard
- IMAP servers

### Service Notes

#### Github
The Archivist only supports backups of a users public repositories and gists at this time. See issue #2.

#### IMAP Servers
The Archivist is currently tested against Fastmail, other IMAP servers may present issues. Report an issue with any problesm you see.
