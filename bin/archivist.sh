#!/bin/bash

CURRENTDIR="$(dirname "$0")"
ROOT_DIR="$CURRENTDIR/.."

(cd $ROOT_DIR && pipenv run python3 archivist.py "$@")
