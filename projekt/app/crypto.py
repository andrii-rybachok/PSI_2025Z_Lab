import base64
import hashlib
import hmac
import secrets
from typing import Tuple


def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def random_prime(min_n: int = 2000, max_n: int = 10000) -> int:
    if min_n >= max_n:
        raise ValueError("min_n must be < max_n")

    while True:
        n = secrets.randbelow(max_n - min_n) + min_n
        if n % 2 == 0:
            n += 1
        if n >= max_n:
            n = max_n - 1 if (max_n - 1) % 2 == 1 else max_n - 2
        if is_prime(n):
            return n


def choose_dh_params() -> Tuple[int, int]:
    p = random_prime(2000, 10000)
    g = secrets.randbelow(p - 3) + 2
    return p, g


def dh_generate_private(p: int) -> int:
    if p < 5:
        raise ValueError("p too small")
    return secrets.randbelow(p - 3) + 2


def dh_public(g: int, a: int, p: int) -> int:
    return pow(g, a, p)


def dh_shared(other_public: int, a: int, p: int) -> int:
    return pow(other_public, a, p)


def kdf(shared_secret: int) -> Tuple[bytes, bytes]:
    s = str(shared_secret).encode("utf-8")
    enc_key = hashlib.sha256(b"enc|" + s).digest()
    mac_key = hashlib.sha256(b"mac|" + s).digest()
    return enc_key, mac_key


def xor_stream(data: bytes, key: bytes) -> bytes:
    if not key:
        raise ValueError("empty key")
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = b ^ key[i % len(key)]
    return bytes(out)


def mac_tag(mac_key: bytes, data: bytes) -> bytes:
    return hmac.new(mac_key, data, hashlib.sha256).digest()


def b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))
