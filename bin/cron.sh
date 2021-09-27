#!/bin/bash

podman run --rm  \
    -v $XDG_CONFIG_HOME/archivist/archivist.yml:/archivist/archivist.yml:z \
    -v $HOME/tmp/backups/archivist:/backups:z \
    amdavidson/archivist:latest $@
