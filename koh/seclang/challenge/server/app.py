#!/usr/bin/env python3
import datetime
import flask
import functools
import json
import os
import re
import redis
import sqlite3
import shutil
import time

config = json.load(open("config.json"))
START = datetime.datetime.strptime(config['start'], "%Y/%m/%d %H:%M")
END   = START + datetime.timedelta(hours=1) * 7

app = flask.Flask(__name__)
is_debug = os.getenv("DEBUG", False)
#app.secret_key = os.getenv("APPKEY", "test").encode()
app.secret_key = os.getenv("APPKEY", "himitsu_no_nekoneko_nyannyanyanyan").encode()

PATH_DATABASE = os.getenv("DATABASE", "teams.db")
PATH_LOG_DATABASE = os.getenv("LOG_DATABASE", "log.db")
PATH_CONTAINER = os.getenv("CONTAINER", "./container")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_HOST", "6379"))

"""データベース取得"""
def get_db():
    db = getattr(flask.g, '_database', None)
    if db is None:
        db = flask.g._database = sqlite3.connect(PATH_DATABASE)
        db.row_factory = sqlite3.Row
    return db

def get_redis():
    conn = getattr(flask.g, '_redis', None)
    if conn is None:
        conn = flask.g._redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0
        )
    return conn

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, '_database', None)
    if db is not None:
        db.close()

"""時間制限があるAPI"""
def limit_time(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if datetime.datetime.now() > END:
            return {'status': 'error', 'error': 'Game is over'}
        else:
            return f(*args, **kwargs)
    return decorated_function

"""ログインを要求するAPI"""
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'teamid' in flask.session:
            return f(*args, **kwargs)
        else:
            return {'status': 'error', 'error': 'Login required'}
    return decorated_function

"""連続使用を禁止するAPI (login_requiredを先に置くこと)"""
def set_time_per_request(seconds):
    def _set_time_per_request(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            conn = get_redis()
            timestamp = conn.hget('timestamp', flask.session['teamid'])
            if timestamp is None:
                conn.hset('timestamp', flask.session['teamid'], '{}')
                return f(*args, **kwargs)

            timestamp = json.loads(timestamp)
            if flask.request.endpoint not in timestamp:
                timestamp[flask.request.endpoint] = time.time()
                conn.hset('timestamp', flask.session['teamid'], json.dumps(timestamp))
                return f(*args, **kwargs)

            # 時間経過の確認
            l = timestamp[flask.request.endpoint]
            if time.time() - float(l) < seconds:
                s = int(seconds + float(l) - time.time()) + 1
                return {
                    'status': 'error',
                    'error': f'Too many requests. Wait {s} seconds.'
                }
            else:
                # タイムスタンプの更新
                timestamp[flask.request.endpoint] = time.time()
                conn.hset('timestamp', flask.session['teamid'], json.dumps(timestamp))
                return f(*args, **kwargs)
        return decorated_function
    return _set_time_per_request

"""サイズ制限のあるAPI"""
def limit_content_length(max_length):
    def _limit_content_length(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            s = flask.request.content_length
            if s is not None and s > max_length:
                return {
                    'status': 'error',
                    'error': f'Content length exceeds maximum size: {{ max_length }} bytes'
                }
            else:
                return f(*args, **kwargs)
        return decorated_function
    return _limit_content_length

"""チームIDが存在するか確認する
"""
def sanitize_teamid(teamid):
    cur = get_db().execute(
        "SELECT id FROM teams WHERE id = ?", (teamid,)
    )
    rows = cur.fetchall()
    if len(rows) == 0:
        return None
    else:
        return rows[0]['id']

"""ログインページ"""
@app.route('/')
def index():
    if 'teamid' in flask.session:
        return flask.redirect('/dashboard')
    # 未ログイン
    return flask.render_template('index.html')

"""ルールページ"""
@app.route('/rule')
def rule():
    return flask.render_template('rule.html')

"""ダッシュボード"""
@app.route('/dashboard')
def dashboard():
    if 'teamid' not in flask.session:
        return flask.redirect('/')
    # ログイン済
    return flask.render_template('dashboard.html')

"""コード実行フォーム"""
@app.route('/playground/<int:teamid>')
def playground(teamid):
    if 'teamid' not in flask.session:
        return flask.redirect('/')

    # 全チーム情報取得
    cur = get_db().execute("SELECT id, name FROM teams ORDER BY id ASC")
    rows = cur.fetchall()
    teamname = None
    teams = []
    for row in rows:
        teams.append({'id': row['id'], 'name': row['name']})
        if row['id'] == teamid:
            teamname = row['name']
    if teamname is None:
        # 不正なチームID
        return flask.redirect('/')

    return flask.render_template('playground.html',
                                 teamid=teamid, teamname=teamname, teams=teams)

"""テストケース状態"""
@app.route('/testcase/<int:teamid>')
def testcase(teamid):
    if 'teamid' not in flask.session:
        return flask.redirect('/')

    # 全チーム情報取得
    cur = get_db().execute("SELECT id, name FROM teams ORDER BY id ASC")
    rows = cur.fetchall()
    teamname = None
    teams = []
    for row in rows:
        teams.append({'id': row['id'], 'name': row['name']})
        if row['id'] == teamid:
            teamname = row['name']
    if teamname is None:
        # 不正なチームID
        return flask.redirect('/')

    return flask.render_template('testcase.html',
                                 teamid=teamid, teamname=teamname, teams=teams)

"""コンパイル結果表示ページ"""
@app.route('/result/compile/<ticket>')
def result_compile(ticket):
    if not re.fullmatch('[0-9a-f]{32}', ticket):
        return flask.redirect('/')

    return flask.render_template('result_compile.html', ticket=ticket)

"""実行結果表示ページ"""
@app.route('/result/execute/<label>')
def result_execute(label):
    if not re.fullmatch('[0-9a-f]{32}', label):
        return flask.redirect('/')

    return flask.render_template('result_execute.html', label=label)


###########
# GET API #
###########
"""全チーム情報取得
"""
@app.route('/api/teams')
@login_required
def api_get_teams():
    try:
        cur = get_db().execute(
            "SELECT id, name, score, pwned FROM teams ORDER BY score DESC"
        )
        teams = []
        for row in cur.fetchall():
            teams.append({'id': row['id'],
                          'name': row['name'],
                          'score': row['score'],
                          'pwned': json.loads(row['pwned'])})
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
    else:
        return {'status': 'ok', 'teams': teams}

"""テストケース状況取得
"""
@app.route('/api/testcase/<int:teamid>')
@login_required
def api_get_testcase(teamid):
    try:
        cur = get_db().execute(
            "SELECT history FROM teams WHERE id = ?",
            (teamid,)
        )
        rows = cur.fetchall()
        if len(rows) == 0:
            return {'status': 'error', 'error': 'Invalid team ID'}

        return {'status': 'ok', 'testcase': json.loads(rows[0]['history'])}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

"""コンパイル結果取得
"""
@app.route('/api/compile/<ticket>')
@login_required
def api_get_compile_status(ticket):
    if not re.fullmatch('[0-9a-f]{32}', ticket):
        return {"status": "error", "error": "Invalid ticket"}

    conn = get_redis()
    result = conn.hget('/api/compile/status', ticket)

    if result:
        return {"status": "ok", "response": json.loads(result)}
    else:
        return {"status": "wait"}

"""実行結果取得
"""
@app.route('/api/execute/<label>')
@login_required
def api_get_execute_status(label):
    if not re.fullmatch('[0-9a-f]{32}', label):
        return {"status": "error", "error": "Invalid label"}

    conn = get_redis()
    result = conn.hget('/api/execute/status', label)

    if result:
        return {"status": "ok", "response": json.loads(result)}
    else:
        return {"status": "wait"}

"""アップロード結果取得
"""
@app.route('/api/upload/<int:teamid>')
@login_required
def api_get_upload_status(teamid):
    teamid = sanitize_teamid(teamid)
    if teamid is None:
        return {"status": "error", "error": "Invalid team ID"}

    conn = get_redis()
    result = conn.hget('/api/upload/status', teamid)

    if result:
        return {"status": "ok", "response": json.loads(result)}
    else:
        return {"status": "ok", "response": {
            "result": "ok", "message": "No changes have been made"
        }}

"""ログ取得
"""
@app.route('/api/logs')
@login_required
def api_get_logs():
    db = sqlite3.connect(PATH_LOG_DATABASE, timeout=10)
    cur = db.execute('SELECT message FROM log ORDER BY id DESC LIMIT 30')
    rows = cur.fetchall()
    db.close()
    return {"status": "ok", "logs": rows}

############
# POST API #
############
"""チームログインAPI
チームトークンを利用してチームアカウントにログインする。
"""
@app.route('/api/login', methods=['POST'])
def api_post_login():
    token = flask.request.json.get("token", None)
    if not token:
        return {"status": "error", "error": "Empty token"}

    cur = get_db().execute(
        "SELECT id, name FROM teams WHERE token = ?", (token,)
    )
    rows = cur.fetchall()

    if len(rows) == 1:
        flask.session['teamid'] = rows[0]['id']
        return {"status": "ok"}
    elif len(rows) > 1:
        return {"status": "error", "error": "Duplicated token"}
    else:
        return {"status": "error", "error": "Invalid token"}

"""環境アップロード
自チームのJITを更新する。
"""
@app.route('/api/upload', methods=['POST'])
@login_required
@set_time_per_request(30)
@limit_content_length(1 * 1024 * 1024)
@limit_time
def api_post_upload():
    filestorage = flask.request.files.get("container")
    if not filestorage:
        return {"status": "error", "error": "Empty file"}

    if os.path.splitext(filestorage.filename)[1] != '.zip':
        return {"status": "error", "error": "Invalid zip file"}

    # タイムスタンプ確認
    cur = get_db().execute('SELECT timestamp FROM teams WHERE id=?',
                           (flask.session['teamid'],))
    rows = cur.fetchall()
    if len(rows) == 0:
        return {'status': 'error', 'error': 'Invalid team (server error)'}
    timestamp = datetime.datetime.strptime(rows[0][0], '%Y/%m/%d %H:%M:%S')
    if datetime.datetime.now() < timestamp + datetime.timedelta(minutes=30):
        delta = timestamp + datetime.timedelta(minutes=30) - datetime.datetime.now()
        return {'status': 'error', 'error': f'Wait {delta.seconds // 60} minutes'}

    # zipを移動する
    teamid = flask.session['teamid']
    path_dir = f"{PATH_CONTAINER}/{teamid}/container"

    # 古いディレクトリを削除
    shutil.rmtree(path_dir, ignore_errors=True)

    # チーム用ディレクトリを作成してDockerfileをコピー
    os.makedirs(path_dir, exist_ok=True)
    with open(f"{PATH_CONTAINER}/{teamid}/Dockerfile", "w") as fw, \
         open(f"{PATH_CONTAINER}/Dockerfile", "r") as fr:
        dockerfile = fr.read()
        fw.write(dockerfile)

    path = f"{path_dir}/{os.urandom(8).hex()}.zip"
    filestorage.save(path)

    data = {'teamid': teamid, 'path': os.path.realpath(path)}
    conn = get_redis()
    conn.lpush('/api/upload', json.dumps(data))

    return {'status': 'ok'}

"""コードコンパイル
チームのコンパイラを使ってコードをコンパイルする。
"""
@app.route('/api/compile', methods=['POST'])
@login_required
@set_time_per_request(10)
@limit_content_length(1 * 1024 * 1024)
@limit_time
def api_post_compile():
    target = flask.request.json.get("target", None)
    if not target:
        return {"status": "error", "error": "No target specified"}
    target = sanitize_teamid(target)
    if target is None:
        return {"status": "error", "error": "Invalid target"}
    code = flask.request.json.get("code", None)
    if not code:
        return {"status": "error", "error": "Empty code"}

    ticket = os.urandom(16).hex()
    data = {'teamid': flask.session['teamid'], 'target': target,
            'ticket': ticket, 'code': code}

    conn = get_redis()
    conn.lpush('/api/compile', json.dumps(data))

    return {"status": "ok", "ticket": ticket}

"""コード実行
コンパイル済みのコードを指定の入力とともに実行する。
"""
@app.route('/api/execute/<ticket>', methods=['POST'])
@login_required
@set_time_per_request(10)
@limit_content_length(1 * 1024 * 1024)
@limit_time
def api_post_execute(ticket):
    if not re.fullmatch('[0-9a-f]{32}', ticket):
        return {"status": "error", "error": "Invalid ticket"}

    inp = flask.request.json.get("input", "")
    if not re.fullmatch('([0-9a-fA-F]{2})*', inp):
        return {"status": "error", "error": "Input is not hex string"}

    conn = get_redis()
    if not conn.hexists('codestore', ticket):
        return {"status": "error", "error": "Ticket not found"}

    label = os.urandom(16).hex()
    data = {'label': label, 'ticket': ticket,
            'input': inp, 'sandbox': False}
    conn.lpush('/api/execute', json.dumps(data))

    return {"status": "ok", "label": label}

"""フラグ投稿
"""
@app.route('/api/submit', methods=['POST'])
@login_required
@set_time_per_request(5)
@limit_content_length(1024)
@limit_time
def api_post_submit():
    flag = flask.request.json.get("flag", "").strip()
    if not re.fullmatch('SECCON\{.+\}', flag):
        return {"status": "error", "error": "Invalid flag format"}

    # 自チームを確認
    db = sqlite3.connect(PATH_DATABASE)
    cur = db.execute('SELECT name, score, pwned FROM teams WHERE id=?',
                     (flask.session['teamid'],))
    rows = cur.fetchall()
    if len(rows) == 0:
        return {"status": "error", "error": "Invalid team (server error)"}
    myname, score, pwned = rows[0]
    pwned = json.loads(pwned)

    # 対象チームを確認
    cur = db.execute('SELECT id, name, pwncnt FROM teams WHERE flag=?', (flag,))
    rows = cur.fetchall()
    if len(rows) == 0:
        return {"status": "error", "error": "Wrong flag"}
    target, pwnname, pwncnt = rows[0]
    if target == flask.session['teamid']:
        # 自分のチーム
        return {"status": "error", "error": "This is your team flag"}
    if target in pwned:
        # すでに攻撃済み
        return {"status": "error", "error": "You have already pwned the flag"}

    # 更新
    pwned.append(target)
    db.execute('UPDATE teams SET score=?, pwned=? WHERE id=?',
               (score + 20, json.dumps(pwned), flask.session['teamid']))
    db.execute('UPDATE teams SET pwncnt=? WHERE id=?',
               (pwncnt + 1, target))
    db.commit()
    db.close()

    # ログをセット
    now = datetime.datetime.now().strftime('%H:%M:%S')
    db = sqlite3.connect(PATH_LOG_DATABASE, timeout=10)
    db.execute('INSERT INTO log(message) VALUES(?)',
               (f'[{now}] "{myname}" pwned "{pwnname}"',))
    db.commit()
    db.close()

    return {"status": "ok", "message": "Pwned!"}

if __name__ == '__main__':
    if not is_debug:
        assert app.secret_key != b'test', "*** CHANGE SECRET KEY!!! ***"

    if not os.path.exists(PATH_CONTAINER):
        os.mkdir(PATH_CONTAINER)

    app.run(debug=is_debug)
