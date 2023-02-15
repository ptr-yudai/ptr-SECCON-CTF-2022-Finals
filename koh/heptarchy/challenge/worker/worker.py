#!/usr/bin/env python3
import datetime
import glob
import json
import multiprocessing
import os
import redis
import sqlite3
import subprocess
import time

from functools import partial
print = partial(print, flush=True)

config = json.load(open("../server/config.json"))
START    = datetime.datetime.strptime(config['start'], "%Y/%m/%d %H:%M")
INTERVAL = datetime.timedelta(hours=1)
LANGUAGES = config['langs']

END = START + datetime.timedelta(hours=1) * 7
INTERVAL_TEST = datetime.timedelta(minutes=5)

LANGS_PATH = os.getenv("LANGS_PATH", "../langs")
STORAGE_PATH = os.getenv("STORAGE", "./storage")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_HOST", "6379"))
PATH_DATABASE = os.getenv("DATABASE", "../server/teams.db")

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

"""現在対象となっている言語情報を取得
"""
def get_lang():
    index = (datetime.datetime.now() - START) // INTERVAL
    if index < 0 or index >= len(LANGUAGES):
        return None
    else:
        return LANGUAGES[index]

def get_storage_path(teamid):
    dirpath = f'{STORAGE_PATH}/{teamid}'
    os.makedirs(dirpath, exist_ok=True)
    return os.path.realpath(dirpath)

def set_result(ranking):
    db = sqlite3.connect(PATH_DATABASE, timeout=10)
    for (teamid, rank, diff, score) in ranking:
        cur = db.execute("SELECT history FROM teams WHERE id = ?", (teamid,))
        rows = cur.fetchall()
        if len(rows) == 0:
            LOG("[set_result] Invalid team ID (unreachable)")
            continue

        history = json.loads(rows[0][0])
        history.append({
            'teamid': teamid,
            'rank': rank,
            'diff': diff,
            'score': score
        })
        db.execute("UPDATE teams SET history = ? WHERE id = ?",
                   (json.dumps(history), teamid))
    db.commit()
    db.close()

"""/api/uploadからのbuild要求を処理
"""
def consume_update_request():
    conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    data = conn.rpop('/api/upload')
    if data is None: return

    data = json.loads(data)
    teamid = data['teamid']
    code = data['code']
    filename = data['filename']

    LOG(f"[update_request] team: {teamid}")
    with open(f'{get_storage_path(teamid)}/{filename}', 'w') as f:
        f.write(code)

"""コンパイル & 比較
"""
def check_code(round_num, prevLang):
    lang = get_lang()
    if lang is None:
        LOG("[check_code] Game is over")
        return
    else:
        LOG(f"[check_code] round_num={round_num}")
        if prevLang is not None and lang != prevLang:
            lang = prevLang
            LOG(f"[check_code] First time to test, using previous language...")

    db = sqlite3.connect(PATH_DATABASE, timeout=10)
    cur = db.execute("SELECT id, token FROM teams")
    teams = cur.fetchall()
    db.close()

    diffs = {}
    for (teamid, _) in teams:
        path = f"{get_storage_path(teamid)}/{lang['code']}"
        if not os.path.isfile(path):
            LOG(f"[check_code] No code registered for {lang['name']} (teamid={teamid})")
            continue

        # コンパイル
        container_name = os.urandom(4).hex()
        try:
            r = subprocess.run(
                ['docker', 'run', '--rm', '--network', 'none',
                 '--name', container_name,
                 '-v', f'{get_storage_path(teamid)}:/tmp',
                 lang["image"], f'/tmp/{lang["code"]}'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            subprocess.run(['docker', 'kill', container_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if r.returncode != 0:
                LOG(f"[check_code] Compile failed (teamid={teamid})")
                print(r.stderr.decode())
                continue
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'kill', container_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            LOG(f"[check_code] Compile timeout (teamid={teamid})")
            continue

        # 必要ならtextセクションを切り出す
        if lang['smal']:
            try:
                r = subprocess.run(
                    ['objcopy', '-O', 'binary', '--only-section=.text',
                     f'{get_storage_path(teamid)}/{lang["output"]}',
                     f'{get_storage_path(teamid)}/extracted.bin'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
                if r.returncode != 0:
                    LOG(f"[check_code] Extract failed (teamid={teamid})")
                    LOG(r.stderr.decode())
                    continue
            except subprocess.TimeoutExpired:
                LOG(f"[check_code] Extract timeout (teamid={teamid})")
                continue
            target = 'extracted.bin'
        else:
            target = lang['output']

        # 比較
        answer_path = os.path.realpath(f'{LANGS_PATH}/{lang["name"].lower()}/{lang["ans"]}')
        container_name = os.urandom(4).hex()
        try:
            r = subprocess.run(
                ['docker', 'run', '--rm', '--network', 'none',
                 '--name', container_name,
                 '-v', f'{answer_path}:/tmp/answer:ro',
                 '-v', f'{get_storage_path(teamid)}:/workdir',
                 'comparator', '/tmp/answer', f'/workdir/{target}'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            subprocess.run(['docker', 'kill', container_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if r.returncode != 0:
                LOG(f"[check_code] Compare failed (teamid={teamid})")
                print(r.stderr.decode())
                continue

            diffs[teamid] = int(r.stdout)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'kill', container_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            LOG(f"[check_code] Compare timeout (teamid={teamid})")
            continue

    token_by_id = {}
    for (teamid, token) in teams:
        if teamid not in diffs:
            diffs[teamid] = 9999999999
        token_by_id[teamid] = token

    score_send = []
    score = config['score']['max']
    ranking = []
    rank = 1
    for teamid, diff in sorted(diffs.items(), key=lambda x:x[1]):
        if diff > 99999:
            score = 0
        if len(ranking) > 0 \
           and ranking[-1][2] == diff:
            # 前の順位と同じスコア
            ranking.append((teamid, ranking[-1][1], diff, ranking[-1][3]))
            score_send.append({
                'team_token': token_by_id[teamid], 'point': ranking[-1][3]
            })
        else:
            ranking.append((teamid, rank, diff, score))
            score_send.append({
                'team_token': token_by_id[teamid], 'point': score
            })
        score -= config['score']['stride']
        if score <= 0:
            score = 1
        rank += 1

    LOG(f"[check_code] ranking: {ranking}")

    # dbを更新する
    set_result(ranking)

    # スコアボードに送る
    data = json.dumps({
        'category_name': 'Heptarchy',
        'round': round_num,
        'scores': score_send,
        'override': False
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

if __name__ == '__main__':
    while datetime.datetime.now() < START:
        time.sleep(1)

    time_test = round_time(datetime.datetime.now(), INTERVAL_TEST)
    print(f"[+] Next TEST: {time_test}")
    prevLang = None
    procList = []
    while datetime.datetime.now() < END:
        # リクエストを処理
        proc = multiprocessing.Process(target=consume_update_request)
        procList.append(proc)
        proc.start()

        # 点数生成
        if datetime.datetime.now() > time_test:
            round_num = (datetime.datetime.now() - START) // INTERVAL_TEST
            time_test += INTERVAL_TEST
            proc = multiprocessing.Process(target=check_code,
                                           args=(round_num, prevLang))
            procList.append(proc)
            proc.start()
            prevLang = get_lang()

        time.sleep(0.5)

        # ゾンビの回収
        removeList = [proc for proc in procList if not proc.is_alive()]
        for proc in removeList:
            proc.join()
            procList.remove(proc)

    print("[+] Game is over!")
