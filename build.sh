#!/bin/bash

set -o allexport
source helix_api/src/.env
set +o allexport

docker build \
    -t helix-api \
    -f Dockerfile \
    --build-arg TDP_PYPI="$TDP_PYPI" \
    $PWD
