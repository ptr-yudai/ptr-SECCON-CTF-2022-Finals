import base64
import datetime
import os
import subprocess
import tempfile
import zipfile

STORAGE = os.getenv("STORAGE", "/tmp")

def gen_path(ext):
    name = os.urandom(16).hex()
    return f"{STORAGE}/{name}.{ext}"

"""ログ出力
"""
def LOG(msg):
    print(f"{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}: {msg}")

"""Sanity Checkプログラムを実行
"""
def run_fool_proof(teamid):
    # コンパイル
    with tempfile.NamedTemporaryFile('w') as f:
        f.write('func main() { print("Hello, World\\n"); return 0; }')
        f.flush()

        container_name = os.urandom(4).hex()
        try:
            proc = subprocess.Popen(
                ['docker', 'run', '--rm', '--network', 'none',
                 '--name', container_name,
                 '-v', f'{f.name}:/tmp/code.sec:ro',
                 f'compiler_{teamid}', '/tmp/code.sec'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            err = b'Timeout'

    subprocess.run(['docker', 'kill', container_name],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if err:
        return f'Hello World failed to compile: {err.decode()}'

    # アセンブル
    with tempfile.NamedTemporaryFile('w') as f:
        f.write(out.decode())
        f.flush()

        container_name = os.urandom(4).hex()
        try:
            proc = subprocess.Popen(
                ['docker', 'run', '--rm', '--network', 'none',
                 '-v', f'{f.name}:/tmp/code.S:ro',
                 f'assembler', '/tmp/code.S'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            err = b'Timeout'

    subprocess.run(['docker', 'kill', container_name],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if err:
        return f'Hello World failed to assemble: {err.decode()}'

    # ELFを保存
    path = gen_path('elf')
    with open(path, 'wb') as f:
        f.write(base64.b64decode(out))
    os.chmod(path, 0o555)

    # 実行
    container_name = os.urandom(4).hex()
    try:
        proc = subprocess.Popen(
            ['docker', 'run', '--rm', '-i', '--network', 'none',
             '-v', f'{path}:/tmp/program:ro',
             'executor', '/app/sandbox', '/tmp/program'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = proc.communicate(b'', timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        err = b'Timeout'

    subprocess.run(['docker', 'kill', container_name],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if err:
        return f'Hello World failed to execute: {err.decode()}'

    if out != b'Hello, World\n':
        return f'Hello World failed: Wrong output'

    return None


"""コンテナのビルドを実行する
"""
def do_update(teamid, path):
    try:
        # ZIPを展開
        to = os.path.dirname(path)
        with zipfile.ZipFile(path, 'r') as f:
            total = sum(e.file_size for e in f.infolist())
            if total > 10 * 1024 * 1024:
                # ZIP bomb対策
                raise "Archive too big. Maximum of 10M is allowed."

            for subfile in f.namelist():
                # extractはsymlinkや..を無視する
                f.extract(subfile, to)

        # コンテナをbuild
        try:
            r = subprocess.run(
                ['docker', 'build', '--force-rm', '--no-cache',
                 '-t', f'compiler_{teamid}', '.'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(to), # Dockerfileのある場所
                timeout=60*3
            )
            if r.returncode != 0:
                return f'Build failed: {r.stderr.decode()}'
        except subprocess.TimeoutExpired:
            return 'Build failed: Timeout'

    except Exception as e:
        return str(e)

    return run_fool_proof(teamid)

"""古いコンテナを削除する
"""
def cleanup_image():
    LOG("[cleanup_image] Removing old images...")
    os.system('docker rmi $(docker images -f "dangling=true" -q) 2>/dev/null')
