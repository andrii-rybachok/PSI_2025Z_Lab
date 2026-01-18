import json
import socket
import struct
from typing import Any, Dict, Optional


def send_json(sock: socket.socket, obj: Dict[str, Any]) -> None:
    data = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    sock.sendall(struct.pack("!I", len(data)) + data)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("connection closed")
        buf += chunk
    return buf


def recv_json(sock: socket.socket) -> Dict[str, Any]:
    header = _recv_exact(sock, 4)
    (length,) = struct.unpack("!I", header)
    if length <= 0 or length > 10_000_000:
        raise ValueError(f"invalid frame length: {length}")
    payload = _recv_exact(sock, length)
    return json.loads(payload.decode("utf-8"))


def make_client_hello(p: int, g: int, A: int) -> Dict[str, Any]:
    return {"type": "CLIENT_HELLO", "p": p, "g": g, "A": A}


def make_server_hello(B: int) -> Dict[str, Any]:
    return {"type": "SERVER_HELLO", "B": B}


def make_secure(ciphertext_b64: str, mac_b64: Optional[str]) -> Dict[str, Any]:
    msg: Dict[str, Any] = {"type": "SECURE", "ciphertext": ciphertext_b64}
    if mac_b64 is not None:
        msg["mac"] = mac_b64
    return msg


def parse_int_field(obj: Dict[str, Any], field: str) -> int:
    if field not in obj:
        raise ValueError(f"missing field: {field}")
    
    val = obj[field]
    if not isinstance(val, int):
        raise ValueError(f"field {field} must be int")
    return val


def parse_str_field(obj: Dict[str, Any], field: str) -> str:
    if field not in obj:
        raise ValueError(f"missing field: {field}")
    val = obj[field]
    if not isinstance(val, str):
        raise ValueError(f"field {field} must be str")
    return val
