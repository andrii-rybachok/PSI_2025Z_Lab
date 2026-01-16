import argparse
import socket
from dataclasses import dataclass
from typing import Optional, Tuple

from .crypto import (
    choose_dh_params,
    dh_generate_private,
    dh_public,
    dh_shared,
    kdf,
)
from .protocol import make_client_hello, parse_int_field, recv_json, send_json
from .secure_channel import SecureChannel
from .keylog import log_keys


@dataclass
class Session:
    channel: SecureChannel


class MiniTLSClient:
    def __init__(self, host: str, port: int, use_mac: bool = True):
        self.host = host
        self.port = port
        self.use_mac = use_mac
        self.sock: Optional[socket.socket] = None
        self.session: Optional[Session] = None

    def connect(self) -> None:
        if self.sock is not None:
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print(f"[client] connected to {self.host}:{self.port}")

    def start_session(self, p: Optional[int] = None, g: Optional[int] = None) -> None:
        if self.sock is None:
            raise RuntimeError("not connected")

        if p is None or g is None:
            p2, g2 = choose_dh_params()
            p = p if p is not None else p2
            g = g if g is not None else g2

        a = dh_generate_private(p)
        A = dh_public(g, a, p)
        send_json(self.sock, make_client_hello(p, g, A))

        resp = recv_json(self.sock)
        if resp.get("type") != "SERVER_HELLO":
            raise RuntimeError(f"unexpected server message: {resp}")
        B = parse_int_field(resp, "B")

        shared = dh_shared(B, a, p)
        enc_key, mac_key = kdf(shared)
        self.session = Session(channel=SecureChannel(enc_key, mac_key, use_mac=self.use_mac))
        log_keys(role="client", client_id=None, p=p, g=g, A=A, B=B, shared=shared, enc_key=enc_key, mac_key=mac_key)
        print(f"[client] handshake complete (p={p}, g={g})")

    def send_data(self, text: str) -> None:
        if self.sock is None:
            raise RuntimeError("not connected")
        if self.session is None:
            raise RuntimeError("no active session; run 'handshake' first")

        ciphertext_b64, mac_b64 = self.session.channel.seal({"type": "DATA", "text": text})
        out = {"type": "SECURE", "ciphertext": ciphertext_b64}
        if mac_b64 is not None:
            out["mac"] = mac_b64
        send_json(self.sock, out)
        print("[client] sent")

    def end_session(self) -> None:
        if self.sock is None:
            raise RuntimeError("not connected")
        if self.session is None:
            print("[client] no active session")
            return

        ciphertext_b64, mac_b64 = self.session.channel.seal({"type": "END_SESSION"})
        out = {"type": "SECURE", "ciphertext": ciphertext_b64}
        if mac_b64 is not None:
            out["mac"] = mac_b64
        send_json(self.sock, out)
        self.session = None
        print("[client] EndSession sent - session reset")

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        self.session = None


def repl(client: MiniTLSClient) -> None:
    help_text = (
        "Commands:\n"
        "  connect                      - open TCP connection\n"
        "  handshake [p] [g]            - start new session (DH), optional ints\n"
        "  send <text>                  - send encrypted DATA\n"
        "  end                          - send encrypted EndSession\n"
        "  quit                         - close\n"
    )
    print(help_text)

    while True:
        try:
            line = input("client> ").strip()
        except EOFError:
            line = "quit"

        if not line:
            continue

        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()

        try:
            if cmd == "connect":
                client.connect()

            elif cmd == "handshake":
                p = g = None
                rest = parts[1] if len(parts) == 2 else ""
                if rest:
                    nums = rest.split()
                    if len(nums) >= 1:
                        p = int(nums[0])
                    if len(nums) >= 2:
                        g = int(nums[1])
                client.start_session(p=p, g=g)

            elif cmd == "send" and len(parts) == 2:
                client.send_data(parts[1])

            elif cmd == "end":
                client.end_session()

            elif cmd == "quit":
                client.close()
                break

            else:
                print(help_text)

        except Exception as e:
            print(f"[client] error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mini TLS-like client")
    parser.add_argument("--host", default="server")
    parser.add_argument("--port", type=int, default=12345)
    parser.add_argument("--no-mac", action="store_true", help="disable MAC (variant W3-like)")
    args = parser.parse_args()

    client = MiniTLSClient(args.host, args.port, use_mac=not args.no_mac)
    repl(client)


if __name__ == "__main__":
    main()
