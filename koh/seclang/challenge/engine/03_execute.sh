#!/bin/sh
timeout -sKILL 10 \
        docker run --rm -i \
        --network none \
        -v "/tmp/program.elf:/tmp/program.elf:ro" \
        executor /tmp/program.elf # no sandbox
