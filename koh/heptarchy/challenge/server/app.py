#!/usr/bin/env python3
import datetime
import flask
import functools
import json
import os
import redis
import sqlite3
import time

app = flask.Flask(__name__)
is_debug = os.getenv("DEBUG", False)
#app.secret_key = os.getenv("APPKEY", "test2").encode()
app.secret_key = os.getenv("APPKEY", "uhouho_gorigori_gorimaccho").encode()

config = json.load(open("../server/config.json"))
START    = datetime.datetime.strptime(config['start'], "%Y/%m/%d %H:%M")
INTERVAL = datetime.timedelta(hours=1)
LANGUAGES = config['langs']

LANGS_PATH = os.getenv("LANGS_PATH", "../langs")
PATH_DATABASE = os.getenv("DATABASE", "teams.db")
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
            host=REDIS_HOST, port=REDIS_PORT, db=0
        )
    return conn

"""ログインを要求するAPI"""
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'teamid' in flask.session:
            return f(*args, **kwargs)
        else:
            return {'error': 'Login required'}, 400
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
                    'response': 'error',
                    'reason': f'Too many requests. Wait {s} seconds.'
                }
            else:
                # タイムスタンプの更新
                timestamp[flask.request.endpoint] = time.time()
                conn.hset('timestamp', flask.session['teamid'], json.dumps(timestamp))
                return f(*args, **kwargs)
        return decorated_function
    return _set_time_per_request

"""チームIDが存在するか確認する
"""
def sanitize_teamid(teamid):
    cur = get_db().execute("SELECT id FROM teams WHERE id = ?", (teamid,))
    rows = cur.fetchall()
    if len(rows) == 0:
        return None
    else:
        return rows[0]['id']

"""現在対象となっている言語情報を取得
"""
def get_lang():
    index = (datetime.datetime.now() - START) // INTERVAL
    if index < 0 or index >= len(LANGUAGES):
        return {'name': 'N/A', 'code': 'N/A', 'prog': 'N/A', 'compiler': 'N/A'}
    else:
        return LANGUAGES[index]

############
# Endpoint #
############
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'teamid' in flask.session:
        return flask.redirect('/dashboard')
    error = None
    if flask.request.method == 'POST':
        # ログイン操作
        token = flask.request.form.get('token', '')
        cur = get_db().execute('SELECT id, name FROM teams WHERE token = ?', (token,))
        rows = cur.fetchall()
        if len(rows) == 0:
            error = 'Invalid team token'
        else:
            flask.session['teamid'] = rows[0]['id']
            flask.session['teamname'] = rows[0]['name']
            return flask.redirect('/dashboard')

    return flask.render_template('index.html', error=error)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'teamid' not in flask.session:
        return flask.redirect('/')
    return flask.render_template('dashboard.html', lang=get_lang())

@app.route('/log', methods=['GET'])
def log():
    if 'teamid' not in flask.session:
        return flask.redirect('/')
    return flask.render_template('log.html', lang=get_lang())

@app.route('/rule', methods=['GET'])
def rule():
    return flask.render_template('rule.html')

###########
# GET API #
###########
@app.route('/api/teams')
@login_required
def api_get_teams():
    cur = get_db().execute('SELECT id, name FROM teams ORDER BY id ASC')
    teams = [{'id': row['id'], 'name': row['name']}
             for row in cur.fetchall()]
    return {'response': 'ok', 'teams': teams}

"""
@app.route('/api/ranking')
@login_required
def api_get_ranking():
    cur = get_db().execute('SELECT id, name, score FROM teams ORDER BY score DESC')
    teams = [{'id': row['id'], 'name': row['name'], 'score': row['score']}
             for row in cur.fetchall()]
    return {'response': 'ok', 'teams': teams}
"""

@app.route('/api/history')
@login_required
def api_get_history():
    cur = get_db().execute('SELECT name, history FROM teams')
    history = [(name, json.loads(history))
               for name, history in cur.fetchall()]
    return {'response': 'ok', 'history': history}

############
# POST API #
############
@app.route('/api/upload', methods=['POST'])
@login_required
@set_time_per_request(10)
def api_post_upload():
    lang = get_lang()
    if lang['name'] == 'N/A':
        return {'response': 'error', 'reason': 'Game is over'}

    code = flask.request.files.get('code')
    if not code:
        return {'response': 'error', 'reason': 'Empty code'}

    code = code.read()
    if len(code) > 10000:
        return {'response': 'error', 'reason': 'Code is too big (>10000)'}
    try:
        code = code.decode()
    except UnicodeDecodeError:
        return {'response': 'error', 'reason': 'Write code in valid UTF-8 characters'}

    data = {'teamid': flask.session['teamid'],
            'code': code,
            'filename': lang['code']}
    get_redis().lpush('/api/upload', json.dumps(data))

    return {'response': 'ok'}

###########
# Storage #
###########
@app.route('/storage/program', methods=['GET'])
def storage_program():
    lang = get_lang()
    if lang['name'] == 'N/A':
        return flask.abort(404)
    return flask.send_file(
        f'{LANGS_PATH}/{lang["name"].lower()}/{lang["prog"]}',
        as_attachment=True,
        download_name=lang["prog"]
    )

@app.route('/storage/compiler/<name>', methods=['GET'])
def storage_compiler(name):
    if get_lang()['name'] == 'N/A':
        return flask.abort(404)

    for lang in LANGUAGES:
        if lang['compiler'] == name:
            return flask.send_file(
                f'{LANGS_PATH}/{lang["name"].lower()}/{lang["compiler"]}',
                as_attachment=True,
                download_name=name
            )

    return flask.abort(404)


if __name__ == '__main__':
    if not is_debug:
        assert app.secret_key != b'test2', "*** CHANGE SECRET KEY!!! ***"

    app.run(debug=is_debug)
