import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import socket
import struct
import time

def send_bytes(sock, data):
    assert len(data) < 0x10000
    sock.send(struct.pack('<H', len(data)))
    sock.send(data)

def recv_bytes(sock):
    size = struct.unpack('<H', sock.recv(2))[0]
    return sock.recv(size)

# Constants and flags
IP   = '192.168.1.103'
PORT = 12345

# Parameters
p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
g = 2

while True:
    parameters = dh.DHParameterNumbers(p, g).parameters(default_backend())
    priv = parameters.generate_private_key()
    pub1 = priv.public_key()
    pub_bytes = pub1.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            s.settimeout(4)
            s.bind((IP, PORT))
            s.listen(1)
            cli, addr = s.accept()
            print("[+] accept():", addr)

            # 1. Receive flag1
            print("[+] FLAG1:", recv_bytes(cli))

            # 2. Key exchange
            send_bytes(cli, pub_bytes)
            pub2 = serialization.load_pem_public_key(recv_bytes(cli))
            shared = priv.exchange(pub2)
            digest = hashes.Hash(hashes.SHA256())
            digest.update(shared)
            key = base64.urlsafe_b64encode(digest.finalize()[:32])

            # 3. Receive flag2
            f = Fernet(key)
            flag = f.decrypt(recv_bytes(cli))
            print("[+] FLAG2:", flag)

    except Exception as e:
        print("[-]", e)
        exit(1)
