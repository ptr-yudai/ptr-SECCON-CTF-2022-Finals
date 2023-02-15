import datetime
import os
import sqlite3

PATH_DATABASE = os.getenv("DATABASE", "../server/teams.db")

"""ログ出力
"""
def LOG(msg):
    print(f"{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}: {msg}")

def gen_flag(teamname):
    v = os.urandom(16).hex()
    return "SECCON{" + teamname.replace(' ', '-') + "_" + v + "}"

"""フラグを更新する
"""
def update_flag():
    LOG(f"[update_flag] {datetime.datetime.now()}")
    db = sqlite3.connect(PATH_DATABASE, timeout=10)

    cur = db.execute("SELECT id, name FROM teams")
    for (teamid, teamname) in cur.fetchall():
        flag = gen_flag(teamname)
        db.execute("UPDATE teams SET flag=?, pwned='[]' WHERE id = ?",
                   (flag, teamid))

    db.commit()
    db.close()
    LOG("[update_flag] Done!")
