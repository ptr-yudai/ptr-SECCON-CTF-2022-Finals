import datetime
import glob
import json
import os
import random
import re
import redis
import sqlite3
import subprocess
import tempfile
import time

NUM_TESTCASE = 5
SCORE_UNIT = 2

TESTSTORE = os.getenv("TESTSTORE", "/tmp/tests")
PATH_DATABASE = os.getenv("DATABASE", "../server/teams.db")
PATH_TESTCASE = os.getenv("TESTCASE", "../testcase")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_HOST", "6379"))

if not os.path.exists(TESTSTORE):
    os.mkdir(TESTSTORE)

def Template(f):
    template = f.read()
    while True:
        m = re.search(r'\$\{.*?\}', template)
        if not m: break
        v = str(eval(m.group()[2:-1], {}, {'randint': random.randint}))
        template = template[:m.start()] + v + template[m.end():]
    return template

"""ログ出力
"""
def LOG(msg):
    print(f"{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}: {msg}")

def set_testcase(name, code, inp):
    db = sqlite3.connect(PATH_DATABASE, timeout=10)
    db.execute("INSERT INTO testcases(name, code, input) VALUES(?, ?, ?)",
               (name, code, inp))
    db.commit()
    db.close()

def add_testcase_slot(teamid):
    db = sqlite3.connect(PATH_DATABASE, timeout=10)
    cur = db.execute("SELECT history FROM teams WHERE id = ?", (teamid,))
    rows = cur.fetchall()
    if len(rows) == 0:
        print("[-] Invalid team ID")
        return

    history = rows[0][0]
    if not history:
        history = []
    else:
        history = json.loads(history)

    history.append({})
    db.execute("UPDATE teams SET history = ? WHERE id = ?",
               (json.dumps(history), teamid))
    db.commit()
    db.close()

def set_compile_result(teamid, name, is_ok, ticket, message):
    db = sqlite3.connect(PATH_DATABASE, timeout=10)
    cur = db.execute("SELECT history FROM teams WHERE id = ?", (teamid,))
    rows = cur.fetchall()
    if len(rows) == 0:
        print("[-] Invalid team ID")
        return

    history = json.loads(rows[0][0])
    history[-1][name] = {
        'compile': [is_ok, ticket, message]
    }
    db.execute("UPDATE teams SET history = ? WHERE id = ?",
               (json.dumps(history), teamid))
    db.commit()
    db.close()

def set_execute_result(teamid, name, is_ok, label, message):
    db = sqlite3.connect(PATH_DATABASE, timeout=10)
    cur = db.execute("SELECT history FROM teams WHERE id = ?", (teamid,))
    rows = cur.fetchall()
    if len(rows) == 0:
        print("[-] Invalid team ID")
        return

    history = json.loads(rows[0][0])
    history[-1][name]['execute'] = [is_ok, label, message]
    db.execute("UPDATE teams SET history = ? WHERE id = ?",
               (json.dumps(history), teamid))
    db.commit()
    db.close()

def add_score(teamid, score):
    db = sqlite3.connect(PATH_DATABASE, timeout=10)
    cur = db.execute("SELECT score, pwncnt FROM teams WHERE id = ?", (teamid,))
    rows = cur.fetchall()
    if len(rows) == 0:
        print("[-] Invalid team ID")
        return

    orig_score, pwncnt = rows[0]
    if pwncnt > 0:
        # このラウンドの点数は無効
        db.execute("UPDATE teams SET pwncnt = ? WHERE id = ?",
                   (pwncnt - 1, teamid))
    else:
        # 加点
        db.execute("UPDATE teams SET score = ? WHERE id = ?",
                   (orig_score + score, teamid))
    db.commit()
    db.close()

def get_pwncnt(teamid):
    db = sqlite3.connect(PATH_DATABASE, timeout=10)
    cur = db.execute("SELECT pwncnt FROM teams WHERE id = ?", (teamid,))
    rows = cur.fetchall()
    return rows[0][0]

def get_answer(code, inp):
    with tempfile.NamedTemporaryFile('w') as f:
        f.write(code)
        f.flush()

        try:
            proc = subprocess.Popen(
                ['docker', 'run', '--rm', '-i', '--network', 'none',
                 '-v', f'{f.name}:/tmp/code.sec:ro',
                 'interpreter', '/tmp/code.sec'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, _ = proc.communicate(inp, timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            return ''
        else:
            return out.hex()

"""テストケースを実行する
"""
def run_testcase(round_num):
    print("[run_testcase]", datetime.datetime.now())
    conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    # テストケースを選択
    testList = random.sample(
        glob.glob(PATH_TESTCASE + '/*/'), k=NUM_TESTCASE
    )

    # コードと入力を生成
    testcases = []
    answers = {}
    for i, test in enumerate(testList):
        name = os.urandom(16).hex() # testcase name
        if random.randint(0, 1) == 0:
            code = Template(open(test + 'program.sec'))
        else:
            code = Template(open(test + 'variant.sec'))
        inp = Template(open(test + 'input.txt')).encode()

        # 解答を生成
        answers[name] = get_answer(code, inp)

        testcases.append((name, code, inp.hex()))
        set_testcase(name, code, inp.hex())

    # チームID一覧を取得
    db = sqlite3.connect(PATH_DATABASE, timeout=10)
    token_by_id = {}
    teams = []
    for teamid, token in db.execute("SELECT id, token FROM teams").fetchall():
        teams.append(teamid)
        token_by_id[teamid] = token
    db.close()

    # テストケースのコンパイルを要求
    tickets = {} # チケット一覧
    for teamid in teams:
        tickets[teamid] = []
        add_testcase_slot(teamid)
        for name, code, inp in testcases:
            ticket = os.urandom(16).hex()
            data = {'teamid': teamid, 'target': teamid,
                    'ticket': ticket, 'code': code}
            # 再優先で実行するためrpushする
            conn.rpush('/api/compile', json.dumps(data))

            tickets[teamid].append((name, ticket, inp))

    # コンパイル待ち
    labels = {teamid: [] for teamid in teams}
    labels_sbx = {teamid: [] for teamid in teams}
    while any(map(lambda l: len(l) > 0, tickets.values())):
        time.sleep(3)
        for teamid in teams: # 各チームについて
            for _ in range(len(tickets[teamid])): # すべての結果の取得を試みる
                # 最後のチケットを確認
                name, ticket, inp = tickets[teamid][-1]
                result = conn.hget('/api/compile/status', ticket)
                if not result: continue
                result = json.loads(result)

                if result['result'] == 'error':
                    # 失敗：結果を更新
                    set_compile_result(teamid, name, False, ticket, 'Compile error')
                else:
                    # 成功：実行に移行
                    set_compile_result(teamid, name, True, ticket, 'Compile success')
                    # 1. NoSBX
                    label = os.urandom(16).hex()
                    data = {'label': label, 'ticket': ticket,
                            'input': inp, 'sandbox': False}
                    conn.rpush('/api/execute', json.dumps(data))
                    labels[teamid].append((name, label))
                    # 2. SBX
                    label = os.urandom(16).hex()
                    data = {'label': label, 'ticket': ticket,
                            'input': inp, 'sandbox': True}
                    conn.rpush('/api/execute', json.dumps(data))
                    labels_sbx[teamid].append((name, label))

                # 最後のチケットを消費
                tickets[teamid].pop()

    errors = {teamid: {} for teamid in teams}
    outputs = {teamid: {} for teamid in teams}
    outputs_sbx = {teamid: {} for teamid in teams}
    while any(map(lambda l: len(l) > 0, labels.values())) or \
          any(map(lambda l: len(l) > 0, labels_sbx.values())):
        time.sleep(3)
        for teamid in teams: # 各チームについて
            # 1. NoSBX
            for _ in range(len(labels[teamid])): # すべての結果の取得を試みる
                # 最後のラベルを確認
                name, label = labels[teamid][-1]
                result = conn.hget('/api/execute/status', label)
                if not result: continue
                result = json.loads(result)

                if result['result'] == 'error':
                    # 失敗：エラーを保存
                    if name not in errors[teamid]:
                        errors[teamid][name] = (label, result['error'])
                else:
                    # 成功：出力を保存
                    outputs[teamid][name] = (label, result['output'])

                # 最後のラベルを消費
                labels[teamid].pop()

            # 2. SBX
            for _ in range(len(labels_sbx[teamid])): # すべての結果の取得を試みる
                # 最後のラベルを確認
                name, label = labels_sbx[teamid][-1]
                result = conn.hget('/api/execute/status', label)
                if not result: continue
                result = json.loads(result)

                if result['result'] == 'error':
                    # 失敗：エラーを保存
                    if name not in errors[teamid]:
                        errors[teamid][name] = (label, result['error'])
                else:
                    # 成功：出力を保存
                    outputs_sbx[teamid][name] = (label, result['output'])

                # 最後のラベルを消費
                labels_sbx[teamid].pop()

    # エラーを結果に反映
    for teamid in teams:
        for name in errors[teamid]:
            label, error = errors[teamid]
            set_execute_result(teamid, name, False, label, 'Execution error')

    # 出力を確認
    scores = {}
    for teamid in teams:
        ok_tests = set(outputs[teamid].keys()).intersection(
            outputs_sbx[teamid].keys()
        )
        scores[teamid] = 0
        for name in ok_tests:
            label, output = outputs[teamid][name]
            label_sbx, output_sbx = outputs_sbx[teamid][name]
            # 結果が解答と一致しているか確認
            if output != answers[name]:
                set_execute_result(teamid, name, False, label, f"Wrong answer")
                continue

            # SBX, NoSBXで結果が一致しているか確認
            if output != output_sbx:
                set_execute_result(teamid, name, False, label_sbx, f"Outputs differ with and without sandbox")
                continue

            # pwned
            if get_pwncnt(teamid) > 0:
                set_execute_result(teamid, name, False, label, f"Penalty (you've been pwned)")
                continue

            # 正解
            set_execute_result(teamid, name, True, label, "Testcase OK")
            scores[teamid] += SCORE_UNIT

    # 点数を更新
    score_send = []
    for teamid in teams:
        add_score(teamid, scores[teamid])
        score_send.append({
            'team_token': token_by_id[teamid], 'point': scores[teamid]
        })

    data = json.dumps({
        'category_name': 'SecLang',
        'round': round_num,
        'scores': score_send,
        'override': True
    })
    try:
        proc = subprocess.Popen(['./kothcli-client'],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = proc.communicate(data.encode(), timeout=10)
        LOG(f"[check_code] Score sending: done")
        if err:
            LOG("[check_code] ERROR?")
            LOG(f"err = '{err.decode()}'")
            LOG(data)
    except subprocess.TimeoutExpired:
        proc.kill()
        LOG("[check_code] ERROR: TimeoutExpired")
        LOG(data)

    print("[run_testcase] Done!")
