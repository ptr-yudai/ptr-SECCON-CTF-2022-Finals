import datetime
import json
import os
import random
import sqlite3

if os.path.exists('log.db'):
    c = input("Are you sure you want to reset all report log? [y/N]")
    if c == 'y' or c == 'Y':
        os.unlink('log.db')
    else:
        print("[-] Aborting")
        exit(1)

with sqlite3.connect('log.db') as conn:
    cur = conn.cursor()
    cur.execute("""
CREATE TABLE log(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message STRING
)
    """)
    cur.execute("PRAGMA journal_mode = WAL")
    conn.commit()
