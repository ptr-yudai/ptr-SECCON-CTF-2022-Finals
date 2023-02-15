import base64
import os
import subprocess
import tempfile

STORAGE = os.getenv("STORAGE", "/tmp")

def gen_path(ext):
    name = os.urandom(16).hex()
    return f"{STORAGE}/{name}.{ext}"

"""SecLangコードをNASM形式にコンパイルする
"""
def do_compile(teamid, code):
    with tempfile.NamedTemporaryFile('w') as f:
        f.write(code)
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
            out, err = b'', b'Timeout (compiler)'

    subprocess.run(['docker', 'kill', container_name],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if err:
        return None, err
    else:
        return out.decode(), None

"""NASMコードをELFファイルにアセンブルする
"""
def do_assemble(asm):
    # Link (assemble)
    with tempfile.NamedTemporaryFile('w') as f:
        f.write(asm)
        f.flush()

        container_name = os.urandom(4).hex()
        try:
            proc = subprocess.Popen(
                ['docker', 'run', '--rm', '--network', 'none',
                 '--name', container_name,
                 '-v', f'{f.name}:/tmp/code.S:ro',
                 'assembler', '/tmp/code.S'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = b'', b'Timeout (assembler)'

    subprocess.run(['docker', 'kill', container_name],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if err:
        return None, err
    else:
        # ELFを保存
        path = gen_path('elf')
        with open(path, 'wb') as f:
            f.write(base64.b64decode(out))
        os.chmod(path, 0o555)
        return path, None
