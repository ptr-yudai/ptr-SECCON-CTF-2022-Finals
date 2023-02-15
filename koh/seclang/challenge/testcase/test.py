#!/usr/bin/env python3
import os
from random import randint
import re
import subprocess
import sys
import tempfile
import time

def Template(template):
    while True:
        m = re.search(r'\$\{.*?\}', template)
        if not m: break
        v = str(eval(m.group()[2:-1]))
        template = template[:m.start()] + v + template[m.end():]
    return template

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} [interpreter|compiler] <code.sec>")
        exit(1)

    path_code = sys.argv[2]
    path_inp  = os.path.dirname(sys.argv[2]) + '/input.txt'

    code = Template(open(path_code).read())
    inp  = Template(open(path_inp ).read())

    print("[ CODE ]")
    print(code)

    print("[ INPUT ]")
    print(inp)

    with tempfile.NamedTemporaryFile('w') as f:
        f.write(code)
        f.flush()

        if sys.argv[1] == 'interpreter':
            p = subprocess.Popen(["python", "seclang.py", f.name],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd="../engine/interpreter/container")
            out, err = p.communicate(inp.encode(), timeout=10)

        else:
            p = subprocess.Popen(["./02_compile.sh", f.name],
                                 cwd="../engine")
            _, err = p.communicate(timeout=10)
            if err: exit(1)

            p = subprocess.Popen(["./03_execute.sh"],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd="../engine")
            out, err = p.communicate(inp.encode(), timeout=10)

    if err:
        print("[ ERROR ]")
        print(err.decode())
    else:
        print("[ OUTPUT ]")
        print(out.decode())
