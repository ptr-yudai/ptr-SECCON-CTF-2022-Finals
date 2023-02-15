#!/bin/sh
#############################################################
# This script build compiler and assembler container.       #
# Run this script everytime after you update your compiler. #
#############################################################

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
