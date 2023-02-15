#!/usr/bin/env python3
from api_compile import do_compile, do_assemble
from api_execute import do_execute
from api_update import do_update, cleanup_image
from update_flag import update_flag
from testcase import run_testcase
import datetime
import json
import os
import redis
import sqlite3
import sys
import multiprocessing
import time

from functools import partial
print = partial(print, flush=True)

config = json.load(open("../server/config.json"))
START    = datetime.datetime.strptime(config['start'], "%Y/%m/%d %H:%M")
END      = START + datetime.timedelta(hours=1) * 7
INTERVAL_TEST = datetime.timedelta(minutes=5)
INTERVAL_FLAG = datetime.timedelta(hours=1)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_HOST", "6379"))
PATH_DATABASE = os.getenv("DATABASE", "../server/teams.db")

print(f"START: {START}")
print(f"END  : {END}")
print(f"TEST INTERVAL: {INTERVAL_TEST}")
print(f"FLAG INTERVAL: {INTERVAL_FLAG}")

"""ログ出力
"""
def LOG(msg):
    print(f"{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}: {msg}")

"""時間の切り上げ
"""
def round_time(dt, delta):
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = delta.seconds - (seconds % delta.seconds)
    return dt + datetime.timedelta(0, rounding, -dt.microsecond)

"""/api/compileからのコンパイル要求を処理
"""
def consume_compile_request():
    conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    data = conn.rpop('/api/compile')
    if data is None: return

    data = json.loads(data)
    teamid = data['teamid']
    target = data['target']
    ticket = data['ticket']
    code = data['code']
    LOG(f"[compile] from={teamid} to={target}: {ticket}")

    # Compile
    asm, err = do_compile(target, code)
    if err:
        conn.hset('/api/compile/status', ticket, json.dumps({
            'result': 'error',
            'source': code,
            'error': err.decode()
        }))
        return

    # Assemble
    path, err = do_assemble(asm)
    if err:
        conn.hset('/api/compile/status', ticket, json.dumps({
            'result': 'error',
            'source': code,
            'asm': asm,
            'error': err.decode()
        }))
        return

    # 結果をステータスに通知する
    conn.hset('/api/compile/status', ticket, json.dumps({
        'result': 'ok',
        'source': code,
        'asm': asm
    }))
    # チケットとELF,ターゲットIDのパスを紐付ける
    conn.hset('codestore', ticket, os.path.realpath(path))
    conn.hset('targetstore', ticket, target)

"""/api/executeからの実行要求を処理
"""
def consume_execute_request():
    conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    data = conn.rpop('/api/execute')
    if data is None: return

    data = json.loads(data)
    label = data['label']
    ticket = data['ticket']
    inp = bytes.fromhex(data['input'])
    sandbox = data['sandbox']
    LOG(f"[execute] {label} (ticket: {ticket})")

    path = conn.hget('codestore', ticket).decode()
    target = int(conn.hget('targetstore', ticket))

    out, err = do_execute(target, path, inp, sandbox)
    if err:
        conn.hset('/api/execute/status', label, json.dumps({
            'result': 'error',
            'input': data['input'],
            'error': err
        }))
        return

    # 出力をステータスに通知する
    conn.hset('/api/execute/status', label, json.dumps({
        'result': 'ok',
        'input': data['input'],
        'output': out
    }))

"""/api/uploadからのbuild要求を処理
"""
def consume_update_request():
    conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    data = conn.rpop('/api/upload')
    if data is None: return

    data = json.loads(data)
    teamid = data['teamid']
    path = data['path']
    LOG(f"[update] {teamid}: {path}")

    conn.hset('/api/upload/status', teamid, json.dumps({
        'result': 'ok',
        'message': 'Updating...'
    }))
    err = do_update(teamid, path) # docker build
    if err:
        conn.hset('/api/upload/status', teamid, json.dumps({
            'result': 'error',
            'error': err
        }))
    else:
        # コンテナ更新日時を変更
        db = sqlite3.connect(PATH_DATABASE, timeout=10)
        db.execute('UPDATE teams SET timestamp=? WHERE id=?',
                   (datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'), teamid))
        db.commit()
        db.close()

        time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        conn.hset('/api/upload/status', teamid, json.dumps({
            'result': 'ok',
            'message': f'Successfully updated on {time}'
        }))

    try:
        os.remove(path)
    except OSError:
        pass

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        update_flag()
        print(f"[+] Initialized flag")

    while datetime.datetime.now() < START:
        time.sleep(1)

    time_test = round_time(datetime.datetime.now(), INTERVAL_TEST)
    time_flag = round_time(datetime.datetime.now(), INTERVAL_FLAG)
    print(f"[+] Next TEST: {time_test}")
    print(f"[+] Next FLAG: {time_flag}")
    procList = []

    while datetime.datetime.now() < END:
        # リクエストを処理
        proc = multiprocessing.Process(target=consume_compile_request)
        procList.append(proc)
        proc.start()
        proc = multiprocessing.Process(target=consume_execute_request)
        procList.append(proc)
        proc.start()
        proc = multiprocessing.Process(target=consume_update_request)
        procList.append(proc)
        proc.start()

        if datetime.datetime.now() > time_flag:
            time_flag += INTERVAL_FLAG
            # フラグを更新する
            proc = multiprocessing.Process(target=update_flag)
            procList.append(proc)
            proc.start()
            # ついでに古いイメージを削除
            proc = multiprocessing.Process(target=cleanup_image)
            procList.append(proc)
            proc.start()

        if datetime.datetime.now() > time_test:
            round_num = (datetime.datetime.now() - START) // INTERVAL_TEST
            time_test += INTERVAL_TEST
            # テストケースを実行する
            proc = multiprocessing.Process(target=run_testcase,
                                           args=(round_num,))
            procList.append(proc)
            proc.start()

        time.sleep(0.5)

        # ゾンビの回収
        removeList = [proc for proc in procList if not proc.is_alive()]
        for proc in removeList:
            proc.join()
            procList.remove(proc)

    print("[+] Game is over!")
