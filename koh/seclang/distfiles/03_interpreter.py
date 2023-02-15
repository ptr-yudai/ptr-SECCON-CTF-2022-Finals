#!/usr/bin/env python3
##################################################################
# This script runs a SecLang program with remote interpreter.    #
# Use this script when you're not sure what behavior is expected #
# with your SecLang code.                                        #
##################################################################
import sys

HOST = "*** CHANGE HERE TO REMOTE IP ***"
PORT = 12345

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} program.sec")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        program = f.read()

    from pwn import *  # pip install pwntools
    sock = remote(HOST, PORT)
    sock.sendline(program.encode())
    sock.sendline(b"__SECLANG_EOF__")
    sock.interactive()
