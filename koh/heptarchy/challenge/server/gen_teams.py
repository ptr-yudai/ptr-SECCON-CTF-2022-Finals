import datetime
import json
import os
import random
import sqlite3

teams = [
    {
        "name": "organizers",
        "password": "icTt-kXGEzM=",
        "team_token": "5E5xBQZP3GsHyUGeRNDruTr1P_gFkZi6nbnmY0t5a2g="
    },
    {
        "name": "perfect blue",
        "password": "AvUHaTlZt3w=",
        "team_token": "qH4pS42mJ5gf2uvm_iAp2MFYfO0OR9gYey14RomIEpY="
    },
    {
        "name": "DiceGang",
        "password": "aXLdmW3LUAA=",
        "team_token": "NNZA_AZxbpBX-zBPuVpRbZUJ1nx1PAaCZUli8bJ6Kw4="
    },
    {
        "name": "Super Guesser",
        "password": "XwhQ-kI8WDc=",
        "team_token": "yQQFmlV2Quf4uZjczXVuRMpnN4pahxRPoOVXyImITr0="
    },
    {
        "name": "hxp",
        "password": "sZlLu-DkQ0U=",
        "team_token": "Fuor0Ic32j9KIsldUDS0V1Qd4IpLqF_65QncBx6FMT4="
    },
    {
        "name": "AAA",
        "password": "9kL854_R9E8=",
        "team_token": "_ZtDU7-KS5r_AtkkJiGLy-5r0kHWtmRSDi0RsbED3xg="
    },
    {
        "name": "TSG",
        "password": "gZhm1mjtKw8=",
        "team_token": "BDj4fkkM69uxWAvxI1y-K9QHIOyF1aU2jwtlKiJR95o="
    },
    {
        "name": "Straw Hat",
        "password": "2NBu9WnQYog=",
        "team_token": "UfsD8DMWI2_LLL-TvKLfW_I4byOklEkzMVkIJHbrbBY="
    },
    {
        "name": "Cha Shu",
        "password": "H1VuPHboi50=",
        "team_token": "CUOOWIJbH9xnrvE2QUaCpoBoDmNB_fzuoEoQUbLb3_0="
    },
    {
        "name": "KMA.L3N0V0",
        "password": "Yn8wmnzpkL0=",
        "team_token": "vCGJfeZWj-Sca6iXbdOS_Jmq5-iSRwSHuG_WkTdb2Qo="
    }
]

teams = [
    {
        "name": "KUDoS",
        "password": "T0NpPmWYaMk=",
        "team_token": "69k90TcfCtGDHRQBGt_GslCci_NHz4PG70SEFBqRmsU="
    },
    {
        "name": "_(-.- _) )_",
        "password": "8VZmNMIDGYo=",
        "team_token": "1vRTC-5wp3aMDXxvaosWaIBEKY6aVPkdB1VSD5rTyGI="
    },
    {
        "name": "ids-TeamCC",
        "password": "UoQFbTKUQ_Y=",
        "team_token": "amxtn-k2sCvgJFdLPtrvTlTh9M56tEpC-2e0fDgDHcU="
    },
    {
        "name": "TokyoWesterns",
        "password": "94E_DAOWBN8=",
        "team_token": "6iSMo0m8ShHAxMgnpU6HHcKB8W_JzJVaMRf9LCN9UZk="
    },
    {
        "name": "traP",
        "password": "KCRmjtDwFM4=",
        "team_token": "nGoG4Teq5mWDTi1dCHDrBkw9T5q_Xh2nxgqpILZYU44="
    },
    {
        "name": "Double Lariat",
        "password": "0UPO7RuiQ64=",
        "team_token": "EtvC5ZgJgvrW7_nv2EYx5MOFV1lbzSqXtrCNIFLnKWY="
    },
    {
        "name": "AERO SANITY",
        "password": "MiJigzRyDvQ=",
        "team_token": "b-biFmwru5aN4kKA5NcB1L-2jn2hI_uSGkL8KsKMjH8="
    },
    {
        "name": "Team Enu",
        "password": "lDQq520P7Mo=",
        "team_token": "qQUzSXz2UHoIrGpepOr2TJ6aPoLlbHkg9PwJxELT33s="
    },
    {
        "name": "chocorusk",
        "password": "nrvfcpgA3Jg=",
        "team_token": "qNxvtO-pRNqJrmmTN7ngCgCwKvuge8QHxRxtGQmFUDg="
    },
    {
        "name": "parabola0149",
        "password": "YosZZNFDbh8=",
        "team_token": "XsPN22Z91aRZy3H_kMl03pVdasGUMt4rSeB5JrEhPk8="
    },
    {
        "name": "catapult",
        "password": "hM50xMHh36Q=",
        "team_token": "4rw0432k2PE331sHs7zY6C__iSsgERg8dKSAUReglS8="
    },
    {
        "name": "rokata",
        "password": "9Dmn6ikiif4=",
        "team_token": "zyHekqp0bt0MRLCJjgsXS5dCzjU04DxDY3Wo1klU3RM="
    }
]

if os.path.exists('teams.db'):
    c = input("Are you sure you want to reset all team information? [y/N]")
    if c == 'y' or c == 'Y':
        os.unlink('teams.db')
    else:
        exit(1)

with sqlite3.connect('teams.db') as conn:
    cur = conn.cursor()
    # チームテーブル
    # name: チーム名
    # token: チームトークン（パスワード）
    # history: テストケース結果のログ
    cur.execute("""
CREATE TABLE teams(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name STRING UNIQUE,
  token STRING UNIQUE,
  history STRING DEFAULT '[]',
  score INTEGER DEFAULT 0
)
    """)

    teams = [[team['name'], team['team_token']] for team in teams]
    cur.executemany("INSERT INTO teams(name, token) VALUES(?, ?)", teams)
    conn.commit()

with sqlite3.connect('teams.db') as conn:
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode = WAL")
    conn.commit()
