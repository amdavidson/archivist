# Archivist 

The archivist is run from a either a `archivist.py` script or a Docker container.

## Script Use
Running `bin/archivist.sh` alone will back up all configured services.

You can also back up a single service by running `bin/archivist.sh backup service`

## Docker Use

The docker container needs two volumes, one mounted wherever you store the backups and 
the other at `/archivist/archivist.yml` for the config file.

Example:
```bash
docker run --rm \
-v /home/host-user/host_backup_dir:/backups \
-v /home/host-user/archivist_config.yml:/archivist/archivist.yml \
amdavidson/archivist
```


## Configuring the Archivist

The Archivist is configured with a `yaml` file stored at one of these locations:
- `./archivist.yml`
- `$XDG_CONFIG_HOME/archivist/archivist.yml`
- `~/.config/archivist/archivist.yml`
- `~/.archivist.yml`
- `/etc/archivist/archivist.yml`

Example:
```yaml
services:
    github:
        name: "Github"
        service_type: github
        backup_folder: /home/user/backups/github
        user: gh-user 
        token: 0xDEADBEEF
        disable_repos: False
        disable_gists: False
        repo_backup_list:
            - important-repository
        gist_backup_list
            - 1337
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

#### IMAP Servers
The Archivist is currently tested against Fastmail, other IMAP servers may present issues. Report an issue with any problesm you see.
