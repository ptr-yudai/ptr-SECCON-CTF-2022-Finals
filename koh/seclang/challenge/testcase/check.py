#!/usr/bin/env python3
import glob
import random
import re
import tempfile
import subprocess
import sys

def Template(f):
    template = f.read()
    while True:
        m = re.search(r'\$\{.*?\}', template)
        if not m: break
        v = str(eval(m.group()[2:-1], {}, {'randint': random.randint}))
        template = template[:m.start()] + v + template[m.end():]
    return template

if __name__ == '__main__':
    if len(sys.argv) > 1:
        l = [sys.argv[1] + '/']
    else:
        l = glob.glob("*/")

    for path in l:
        for _ in range(10):
            for name in ['program.sec', 'variant.sec']:
                code = Template(open(path + name))
                inp = Template(open(path + 'input.txt'))

                with tempfile.NamedTemporaryFile('w') as f:
                    f.write(code)
                    f.flush()

                    try:
                        # 解答を生成
                        p = subprocess.Popen(["python", "seclang.py", f.name],
                                             stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             cwd="../engine/interpreter/container")
                        answer, err = p.communicate(inp.encode(), timeout=5)
                    except subprocess.TimeoutExpired:
                        err = "Timeout expired"

                    if err:
                        print(f"\033[31;1m[-] {path}{name}: Interpreter failed\033[0m")
                        print(err)
                        print("[ INPUT ]")
                        print(inp)
                        continue

                    # コンパイル結果を取得
                    try:
                        p = subprocess.Popen(["./02_compile.sh", f.name],
                                             stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             cwd="../engine")
                        _, err = p.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        err = "Timeout expired"

                    if err:
                        print(f"\033[31;1m[-] {path}{name}: Compile faield\033[0m")
                        print(err)
                        print("[ INPUT ]")
                        print(inp)
                        continue

                    try:
                        p = subprocess.Popen(["./03_execute.sh"],
                                             stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             cwd="../engine")
                        out, err = p.communicate(inp.encode(), timeout=5)
                    except subprocess.TimeoutExpired:
                        err = "Timeout expired"

                    if err:
                        print(f"\033[31;1m[-] {path}{name}: Execution faield\033[0m")
                        print(err)
                        print("[ INPUT ]")
                        print(inp)
                        continue

                    if out != answer:
                        print(f"\033[31;1m[-] {path}{name}: Invalid output\033[0m")
                        print("[ INPUT ]")
                        print(inp)
                        print("[ OUTPUT (Interpreter) ]")
                        print(answer)
                        print("[ OUTPUT (Compiled) ]")
                        print(out)

                    else:
                        print(f"\033[32;1m[+] {path}{name}: OK\033[0m")


