# Archivist 

The archivist is run from a either a central `archivist.py` script

## Backing up all services

Running `./archivist.py` alone will backup all configured services.

## Backing up a single service

Using Github as the example service to backup:

Add `github_user` to `$HOME/.archivist.yml`

### Centrally

Run `./archivist.py backup github`

