# Archivist 

The archivist is run from a either a central `archivist.py` script

Running `./archivist.py` alone will back up all configured services.

You can also back up a single service by running `./archivist.py backup service`


## Configuring the Archivist

The Archivist is configured with a `yaml` file at `~/.archivist.yml`

Example:
```yaml
services:
    github:
        name: "Github"
        service_type: github
        backup_folder: /home/user/backups/github
        user: gh-user 
    pinboard:
        name: "Pinboard"
        service_type: pinboard
        backup_folder: /home/user/backups/pinboard
        user: pbuser
        token: 0xDEADBEEF
    fastmail:
        name: "Email Host"
        service_type: imap
        backup_folder: /home/user/backups/fastmail
        server: imap.email.host.name
        user: user@email.host.name 
        password: Hunter2 
        cleanup: False
        compress: True
```

## Supported Services

- Github
- Pinboard
- IMAP servers

### Service Notes

#### Github
The Archivist only supports backups of a users public repositories and gists at this time. See [#2](https://github.com/amdavidson/archivist/issues/2).

#### IMAP Servers
The Archivist is currently tested against Fastmail, other IMAP servers may present issues. Report an issue with any problesm you see.
