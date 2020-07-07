#!/bin/bash

CURRENTDIR="$(dirname "$0")"
ROOT_DIR="$CURRENTDIR/.."

cd $ROOT_DIR

docker run --rm  \
    -v $(pwd)/archivist.yml:/archivist/archivist.yml \
    -v /tmp/backups:/backups \
    amdavidson/archivist:latest $@
