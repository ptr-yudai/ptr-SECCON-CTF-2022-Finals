#!/bin/bash
set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <input.c>"
    exit 1
elif ! [ -e "$1" ]; then
    echo "File not found: $1" >&2
    exit 1
elif [ -d "$1" ]; then
    echo "Not a file: $1" >&2
    exit 1
fi

CODE=$(realpath "$1")

# Build image
if [[ "$(docker images -q compiler_wasm 2> /dev/null)" == "" ]]; then
    echo -e "\e[33;1m[+] First time to compile. Building container...\e[m"
    docker build . -t compiler_wasm
fi

# Create workdir
TIMESTAMP=$(date +%Y%m%d%H%M%S)
WORKDIR=$(mktemp -dt "XXXXXXXXXXXXXXXX")
trap 'rm -rf -- "$WORKDIR"' EXIT

# Compile
cp "$CODE" "$WORKDIR/wmain.c"
timeout -sKILL 10 \
        docker run --rm \
        -v "$WORKDIR:/tmp" \
        compiler_wasm /tmp/wmain.c
cp "$WORKDIR/mission-7.js" ./mission-7.js
cp "$WORKDIR/mission-7.wasm" ./mission-7.wasm

echo -e "\e[32;1m[+] Compile done\e[m"
echo -e "\e[32;1m[+] Calcualte score by:\n./compare ../dist/mission-7.wasm mission-7.wasm\e[m"
