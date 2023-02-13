s = [777]

for _ in range(1, 16):
    n = s[-1]
    if n % 2 == 0:
        s.append(n // 2)
    else:
        s.append(n * 3 + 1)

table = [15, 3, 10, 1, 4, 5, 12, 13, 9, 2, 6, 11, 8, 7, 14, 0]
itable = [table.index(i) for i in range(16)]

print(s)
v = list(map(lambda x: itable[x % 0x10], s))
print(v)

print("SECCON{", end='')
for x in v:
    print(hex(x)[2:].upper(), end='')
print("}")
