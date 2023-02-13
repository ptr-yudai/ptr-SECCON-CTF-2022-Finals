from ptrlib import *

with open("FLAG.txt", "rb") as f:
    flag = f.read().strip()

S = [i for i in range(0x100)]
j, h = 0, 0xba77c1
for i in range(0x100):
    j = (j + S[i] + h) % 0x100
    S[i], S[j] = S[j], S[i]
    h = (h * h) % (1 << 32)

for block in chunks(flag, 8, b'\x00'):
    j = key = 0
    for i in range(8):
        j = (j + S[i]) % 0x100
        S[i], S[j] = S[j], S[i]
        key = (key << 8) | S[(S[i] + S[j]) % 0x100]
    print(hex(key ^ u64(block)), end=", ")
print()
