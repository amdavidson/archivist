# Archivist 

The archivist is run from a either a central `archivist.py` script or from one of the self contained individual source scripts.

## Backing up all services

Running `./archivist.yml` alone will backup all configured services.

## Backing up a single service

Using Github as the example service to backup:

Add `github_user` to `$HOME/.archivist.yml`

### Centrally

Run `./archivist.py backup github`

### Individually

Run `./github.py`
