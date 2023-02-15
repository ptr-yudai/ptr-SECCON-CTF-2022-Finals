import random

def isPrime(n, k=10):
    if n == 2 or n == 3:
        return True
    elif n & 1 == 0:
        return False

    r, s = 0, n-1
    while s & 1 == 0:
        s >>= 1
        r += 1

    for _ in range(k):
        a = random.randrange(2, n-1)
        x = pow(a, s, n)
        if x == 1 or n - x == 1:
            continue
        for _ in range(r-1):
            x = x * x % n
            if n - x == 1:
                break
        else:
            return False

    return True

def getPrime(bits):
    while True:
        p = random.randrange(1<<bits, 1<<(bits+1))
        if isPrime(p):
            return p

if __name__ == '__main__':
    p = getPrime(256)
    q = getPrime(256)
    r = getPrime(256)
    n = p*q*r
    e = 65537
    m = int.from_bytes(input("Text: ").encode(), 'big')
    if m > n:
        print("Too long")
        exit(1)

    c = pow(m, e, n)
    print(f"Cipher: {hex(c)}")

    phi = (p-1)*(q-1)*(r-1)
    d = pow(e, -1, phi)
    mm = pow(c, d, n)

    assert m == mm
