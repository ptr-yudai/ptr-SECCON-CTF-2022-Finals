#!/bin/bash
set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <input.rs>"
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
if [[ "$(docker images -q compiler_rust 2> /dev/null)" == "" ]]; then
    echo -e "\e[33;1m[+] First time to compile. Building container...\e[m"
    docker build . -t compiler_rust
fi

# Create workdir
TIMESTAMP=$(date +%Y%m%d%H%M%S)
WORKDIR=$(mktemp -dt "XXXXXXXXXXXXXXXX")
trap 'rm -rf -- "$WORKDIR"' EXIT

# Compile
cp "$CODE" "$WORKDIR/main.rs"
timeout -sKILL 10 \
        docker run --rm \
        -v "$WORKDIR:/tmp" \
        compiler_rust /tmp/main.rs
cp "$WORKDIR/output.bin" ./output.bin

echo -e "\e[32;1m[+] Compile done\e[m"

# Generate target
echo -e "\e[33;1m[+] The server will check only '.text' section to reduce computation time.\e[m"
echo -e "\e[32;1m[+] Calcualte score by:"
echo -e "objcopy -O binary --only-section=.text mission-3 mission-3.text"
echo -e "./compare mission-3.text output.text\e[m"

objcopy -O binary --only-section=.text output.bin "$WORKDIR/output.text"
mv "$WORKDIR/output.text" output.text
