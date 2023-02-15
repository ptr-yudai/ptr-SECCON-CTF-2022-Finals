import datetime
import os
import subprocess
import sqlite3
import tempfile

PATH_DATABASE = os.getenv("DATABASE", "../server/teams.db")

"""ログ出力
"""
def LOG(msg):
    print(f"{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}: {msg}")

def do_execute(teamid, path, inp, sandbox):
    if sandbox:
        arg = ['/app/sandbox', '/tmp/program']
    else:
        arg = ['/tmp/program']

    db = sqlite3.connect(PATH_DATABASE, timeout=10)
    cur = db.execute("SELECT flag FROM teams WHERE id=?", (teamid,))
    rows = cur.fetchall()
    if len(rows) == 0:
        LOG(f"[do_execute] *** FLAG NOT FOUND (target: {teamid}) ***")
        flag = ""
    else:
        flag = rows[0][0]

    with tempfile.NamedTemporaryFile('w') as f:
        f.write(flag)
        f.flush()

        container_name = os.urandom(4).hex()
        try:
            proc = subprocess.Popen(
                ['docker', 'run', '--rm', '-i', '--network', 'none',
                 '--name', container_name,
                 '-v', f'{f.name}:/flag.txt:ro',
                 '-v', f'{path}:/tmp/program:ro',
                 'executor'] + arg,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, _ = proc.communicate(inp, timeout=10)

        except subprocess.TimeoutExpired:
            proc.kill()
            subprocess.run(['docker', 'kill', container_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return None, 'Timeout (executor)'

        else:
            subprocess.run(['docker', 'kill', container_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if len(out) > 0x1000:
                return None, 'Too much output (executor)'

            if b'SECCON{' in out:
                LOG(f"[do_execute] Likely flag by {teamid}: {path}: {inp}")
            return out.hex(), None
