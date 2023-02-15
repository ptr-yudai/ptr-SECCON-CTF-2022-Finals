#!/bin/bash
set -e

# Build compiler
(
    cd compiler
    docker build . -t compiler
)

# Build assembler
(
    cd assembler
    docker build . -t assembler
)

# Build executor
(
    cd executor
    docker build . -t executor
)

# Build interpreter
(
    cd interpreter/container
    docker build . -t interpreter
)

# Build interpreter (remote)
(
    cd interpreter
    docker-compose build
)
