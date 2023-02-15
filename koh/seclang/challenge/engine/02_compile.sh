#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 program.sec"
    exit 1
elif ! [ -e "$1" ]; then
    echo "File not found: $1" >&2
    exit 1
elif [ -d "$1" ]; then
    echo "Not a file: $1" >&2
    exit 1
fi

CODE=$(realpath "$1")

# 1. Compile code
timeout -sKILL 10 \
        docker run --rm \
        --network none \
        -v "$CODE:/tmp/code.sec:ro" \
        compiler /tmp/code.sec >/tmp/code.S 2>/tmp/compile-error.log
if [ $? == 0 ]; then
    echo -e "\e[32;1mDONE: Compile OK\e[m"
else
    cat /tmp/compile-error.log
    echo -e "\e[31;1mFAIL: Compile Error\e[m"
    exit 1
fi

if [ -s /tmp/compile-error.log ]; then
    echo -e "\e[33;1mWARN: ***** You MUST NOT use stderr on remote, or every testcase fails *****\e[m"
fi

# 2. Generate executable
timeout -sKILL 10  \
        docker run --rm \
        --network none \
        -v "/tmp/code.S:/tmp/code.S:ro" \
        assembler /tmp/code.S > /tmp/prog.b64
if [ $? == 0 ]; then
    echo -e "\e[32;1mDONE: Assemble OK\e[m"
else
    echo -e "\e[31;1mFAIL: Assemble Error\e[m" >&2
    exit 1
fi

base64 -d /tmp/prog.b64 > /tmp/program.elf
chmod +x /tmp/program.elf
echo -e "\e[32;1mDONE: Output executable at '/tmp/program.elf'\e[m"
