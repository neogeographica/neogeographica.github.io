#!/usr/bin/env bash

SELF="${BASH_SOURCE[0]}"
while [[ -h "$SOURCE" ]]
do
  SELF="$(readlink "$SELF")"
done
cd -P "$(dirname "$SELF")/.."

docker run -it --rm -v "$PWD":/usr/src/neogeographica.github.io -w /usr/src/neogeographica.github.io site-gen site_gen.py
