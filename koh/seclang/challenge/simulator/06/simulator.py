"""シミュレータ1
- すべての防衛点をとる
- たまに攻撃する
"""
import datetime
import json
import os
import random
import requests
import sqlite3
import threading
import time

CONFIG = json.load(open("../config.json"))
START = datetime.datetime.strptime(CONFIG['start'], '%Y/%m/%d %H:%M')
END   = START + datetime.timedelta(hours=7)
URL = os.getenv("URL", "http://localhost")

TICKETS = []
LABELS = []

"""ログを出力する
"""
def LOG(msg):
    print(f"[{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] {msg}")

"""クッキーを取得する
"""
def get_cookie():
    r = requests.post(f'{URL}/api/login',
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps({'token': TOKEN}))
    return r.cookies

"""テストケースの状態をチェックする
"""
def check_testcase(teamid):
    r = requests.get(f'{URL}/testcase/{teamid}', cookies=cookie)
    if r.status_code != 200:
        return LOG(f"ERROR: /testcase/{teamid} --> {r.status_code}")
    r = requests.get(f'{URL}/api/testcase/{teamid}', cookies=cookie)
    if r.status_code != 200:
        return LOG(f"ERROR: /api/testcase/{teamid} --> {r.status_code}")
    resp = json.loads(r.text)
    if resp['status'] != 'ok':
        return LOG(f"ERROR: /api/testcase/{teamid} --> {resp['error']}")
    LOG("OK: check_testcase")

"""ログの状態をチェックする
"""
def check_log():
    r = requests.get(f'{URL}/dashboard', cookies=cookie)
    if r.status_code != 200:
        return LOG(f"ERROR: /dashboard --> {r.status_code}")
    r = requests.get(f'{URL}/api/logs', cookies=cookie)
    if r.status_code != 200:
        return LOG(f"ERROR: /api/logs --> {r.status_code}")
    resp = json.loads(r.text)
    if resp['status'] != 'ok':
        return LOG(f"ERROR: /api/logs --> {resp['error']}")
    LOG(f"OK: check_log --> len(log)={len(resp['logs'])}")

"""アップロード状態をチェックする
"""
def check_upload(teamid):
    r = requests.get(f'{URL}/api/upload/{teamid}', cookies=cookie)
    if r.status_code != 200:
        return LOG(f"ERROR: /api/upload/{teamid} --> {r.status_code}")
    resp = json.loads(r.text)
    if resp['status'] != 'ok':
        return LOG(f"ERROR: /api/upload/{teamid} --> {resp['error']}")
    if resp['response']['result'] != 'ok':
        return LOG(f"ERROR: /api/upload/{teamid} --> {resp['response']['error']}")
    LOG(f"OK: check_upload --> {resp['response']['message']}")

"""コンテナをアップロードする
"""
def upload_container():
    which_path = 'a.zip' if random.randint(0, 1) else 'b.zip'
    f = (which_path, open(which_path, 'rb'), 'application/zip')
    r = requests.post(f'{URL}/api/upload',
                      files={'container': f},
                      cookies=cookie)
    if r.status_code != 200:
        return LOG(f"ERROR: /api/upload --> {r.status_code}")
    LOG(f"OK: upload_container --> {r.text}")

"""正解のフラグを送信する
"""
def submit_correct_flag():
    db = sqlite3.connect('../../server/teams.db')
    rows = db.execute("SELECT flag FROM teams WHERE id != ?", (TEAMID,)).fetchall()
    db.close()
    flag = random.choice(rows)[0]
    LOG(f"INFO: submit_correct_flag --> Sending '{flag}'")
    r = requests.post(f'{URL}/api/submit',
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps({'flag': flag}),
                      cookies=cookie)
    if r.status_code != 200:
        return LOG(f"ERROR: /api/submit --> {r.status_code} (submit_correct_flag)")
    resp = json.loads(r.text)
    if resp['status'] != 'ok':
        return LOG(f"ERROR: /api/submit --> {resp['error']} (submit_correct_flag)")
    LOG(f"OK: submit_correct_flag --> {resp['message']}")

"""不正解のフラグを送信する
"""
def submit_wrong_flag():
    time.sleep(10)
    flag = "@[;:],./\\" if random.randint(0, 1) else "SECCON{hoge!\"#$%&'()~=~|`{+*}<>?_hoge@[;:]./\\}"
    LOG(f"INFO: submit_wrong_flag --> Sending '{flag}'")
    r = requests.post(f'{URL}/api/submit',
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps({'flag': flag}),
                      cookies=cookie)
    if r.status_code != 200:
        return LOG(f"ERROR: /api/submit --> {r.status_code} (submit_wrong_flag)")
    resp = json.loads(r.text)
    if resp['status'] == 'ok':
        return LOG(f"ERROR: /api/submit --> {resp['message']} *** !MUST REJECT! ***")
    LOG(f"OK: submit_wrong_flag --> {resp['error']}")

"""コンパイル要求を送る
"""
def request_compile(teamid=None):
    if teamid is None:
        teamid = random.randint(1, 10)
        time.sleep(15)
    code = open("x.sec", "r").read()
    r = requests.post(f'{URL}/api/compile',
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps({'code': code, 'target': teamid}),
                      cookies=cookie)
    if r.status_code != 200:
        return LOG(f"ERROR: /api/compile --> {r.status_code}")
    resp = json.loads(r.text)
    if resp['status'] != 'ok':
        return LOG(f"ERROR: /api/compile --> {resp['error']}")
    ticket = resp['ticket']
    LOG(f"OK 1: request_compile --> ticket='{ticket}'")
    for _ in range(10):
        time.sleep(1)
        r = requests.get(f'{URL}/api/compile/{ticket}', cookies=cookie)
        if r.status_code != 200:
            return LOG(f"ERROR: /api/compile/{ticket} --> {r.status_code}")
        resp = json.loads(r.text)
        if resp['status'] == 'wait':
            continue
        elif resp['status'] != 'ok':
            return LOG(f"ERROR: /api/compile/{ticket} --> {resp['error']}")
        if resp['response']['result'] == 'error':
            return LOG(f"OK 2: request_compile --> !Compile Error!")
        break
    else:
        return LOG(f"ERROR: /api/compile/{ticket} --> !TIMEOUT!")
    TICKETS.append(ticket)
    LOG(f"OK 2: request_compile --> '{ticket}' compiled successfully!")

"""実行要求を送る
"""
def request_execute():
    if len(TICKETS) == 0:
        return LOG("INFO: Empty tickets. Skipping.")
    ticket = random.choice(TICKETS)
    l = random.randint(0, 0x100)
    r = requests.post(f'{URL}/api/execute/{ticket}',
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps({'input': os.urandom(l).hex()}),
                      cookies=cookie)
    if r.status_code != 200:
        return LOG(f"ERROR: /api/execute/{ticket} --> {r.status_code}")
    resp = json.loads(r.text)
    if resp['status'] != 'ok':
        return LOG(f"ERROR: /api/execute/{ticket} --> {resp['error']}")
    label = resp['label']
    LOG(f"OK 1: request_execute --> label='{label}'")
    for _ in range(10):
        time.sleep(1)
        r = requests.get(f'{URL}/api/execute/{label}', cookies=cookie)
        if r.status_code != 200:
            return LOG(f"ERROR: /api/execute/{label} --> {r.status_code}")
        resp = json.loads(r.text)
        if resp['status'] == 'wait':
            continue
        elif resp['status'] != 'ok':
            return LOG(f"ERROR: /api/execute/{label} --> {resp['error']}")
        if resp['response']['result'] != 'ok':
            return LOG(f"OK 2: request_compile --> !Runtime Error!")
        break
    else:
        return LOG(f"ERROR: /api/execute/{label} --> !TIMEOUT!")
    LOG(f"OK 2: request_execute --> '{label}' run successfully!")

"""別スレッドで関数を実行する
"""
def go(f, args=()):
    th = threading.Thread(target=f, args=args)
    th.start()
    return th

# この変数を変更してシミュレータを調整する
TOKEN = 'test_token6'
TEAMID = 6
DELTA_CHECK  = datetime.timedelta(seconds=90)
DELTA_UPLOAD = datetime.timedelta(minutes=10)
DELTA_SUBMIT = datetime.timedelta(minutes=120)
DELTA_COMPILE = datetime.timedelta(minutes=6)
DELTA_EXECUTE = datetime.timedelta(minutes=7)

if __name__ == '__main__':
    cookie = get_cookie()
    time_check  = datetime.datetime.now()
    time_upload = datetime.datetime.now()
    time_submit = datetime.datetime.now()
    time_compile = datetime.datetime.now()
    time_execute = datetime.datetime.now()

    thList = []
    while datetime.datetime.now() < END:
        time.sleep(0.5)
        removeList = [th for th in thList if not th.is_alive()]
        for th in removeList:
            th.join()
            thList.remove(th)

        # サイトチェック
        if datetime.datetime.now() > time_check:
            time_check += DELTA_CHECK
            thList.append( go(check_testcase, (TEAMID, )) )
            thList.append( go(check_log) )
            thList.append( go(check_upload, (TEAMID, )) )

        # コンテナアップロード
        if datetime.datetime.now() > time_upload:
            time_upload += DELTA_UPLOAD
            thList.append( go(upload_container) )

        # 他チームのフラグ送信
        if datetime.datetime.now() > time_submit:
            time_submit += DELTA_SUBMIT
            thList.append( go(submit_correct_flag) )
            thList.append( go(submit_wrong_flag) )

        # コンパイル
        if datetime.datetime.now() > time_compile:
            time_compile += DELTA_COMPILE
            thList.append( go(request_compile, (TEAMID, )) ) # 自分
            thList.append( go(request_compile) ) # 誰か

        # 実行
        if datetime.datetime.now() > time_execute:
            time_execute += DELTA_EXECUTE
            thList.append( go(request_execute) )
