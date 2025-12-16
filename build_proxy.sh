#!/bin/bash

set -o allexport
source helix_api/src/.env
set +o allexport

docker build \
  -t helix-api \
  -f Dockerfile_proxy \
  --build-arg http_proxy=http://localhost:3128 \
  --build-arg https_proxy=http://localhost:3128 \
  --build-arg TDP_PYPI="$TDP_PYPI" \
  --network=host \
  --progress plain \
  $PWD
