import argparse
import socket
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .crypto import dh_generate_private, dh_public, dh_shared, kdf
from .keylog import log_keys
from .protocol import (
    make_server_hello,
    parse_int_field,
    recv_json,
    send_json,
)
from .secure_channel import SecureChannel


@dataclass
class ClientState:
    client_id: int
    addr: Tuple[str, int]
    sock: socket.socket
    lock: threading.Lock
    channel: Optional[SecureChannel] = None
    dh_p: Optional[int] = None


class MiniTLSServer:
    def __init__(self, host: str, port: int, max_clients: int, use_mac: bool = True):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.use_mac = use_mac

        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._clients: Dict[int, ClientState] = {}
        self._clients_lock = threading.Lock()
        self._next_id = 1
        self._running = threading.Event()
        self._running.set()

    def start(self) -> None:
        self._server_sock.bind((self.host, self.port))
        self._server_sock.listen()
        print(f"[server] listening on {self.host}:{self.port} (max_clients={self.max_clients})")

        threading.Thread(target=self._accept_loop, daemon=True).start()
        self._admin_loop()

    def _accept_loop(self) -> None:
        while self._running.is_set():
            try:
                client_sock, addr = self._server_sock.accept()
            except OSError:
                break

            with self._clients_lock:
                if len(self._clients) >= self.max_clients:
                    # simplest behaviour: refuse
                    client_sock.close()
                    continue
                cid = self._next_id
                self._next_id += 1
                state = ClientState(client_id=cid, addr=addr, sock=client_sock, lock=threading.Lock())
                self._clients[cid] = state

            print(f"[server] client#{cid} connected from {addr[0]}:{addr[1]}")
            threading.Thread(target=self._client_loop, args=(state,), daemon=True).start()

    def _client_loop(self, state: ClientState) -> None:
        sock = state.sock
        try:
            while self._running.is_set():
                msg = recv_json(sock)
                mtype = msg.get("type")

                if state.channel is None:
                    # Expect ClientHello plaintext
                    if mtype != "CLIENT_HELLO":
                        print(f"[server] client#{state.client_id} unexpected plaintext type={mtype}; closing")
                        break

                    p = parse_int_field(msg, "p")
                    g = parse_int_field(msg, "g")
                    A = parse_int_field(msg, "A")

                    b = dh_generate_private(p)
                    B = dh_public(g, b, p)
                    shared = dh_shared(A, b, p)
                    enc_key, mac_key = kdf(shared)
                    state.channel = SecureChannel(enc_key, mac_key, use_mac=self.use_mac)
                    state.dh_p = p

                    # For the final report: store keys so you can manually decrypt
                    # payload captured in Wireshark.
                    log_keys(
                        role="server",
                        client_id=state.client_id,
                        p=p,
                        g=g,
                        A=A,
                        B=B,
                        shared=shared,
                        enc_key=enc_key,
                        mac_key=mac_key,
                    )
                    send_json(sock, make_server_hello(B))
                    print(f"[server] client#{state.client_id} handshake complete (p={p})")
                    continue

                # After handshake: everything must be SECURE
                if mtype != "SECURE":
                    print(f"[server] client#{state.client_id} non-secure message after handshake; ignoring")
                    continue

                ciphertext = msg.get("ciphertext")
                mac = msg.get("mac")
                if not isinstance(ciphertext, str):
                    print(f"[server] client#{state.client_id} malformed secure message")
                    continue

                try:
                    inner = state.channel.open(ciphertext, mac if isinstance(mac, str) else None)
                except Exception as e:
                    print(f"[server] client#{state.client_id} secure open failed: {e}")
                    continue

                inner_type = inner.get("type")
                if inner_type == "DATA":
                    text = inner.get("text")
                    print(f"[server] client#{state.client_id} DATA: {text}")
                elif inner_type == "END_SESSION":
                    print(f"[server] client#{state.client_id} END_SESSION received -> session reset")
                    state.channel = None
                    state.dh_p = None
                else:
                    print(f"[server] client#{state.client_id} unknown inner type: {inner_type}")

        except (ConnectionError, OSError):
            pass
        finally:
            self._drop_client(state.client_id)

    def _drop_client(self, client_id: int) -> None:
        with self._clients_lock:
            state = self._clients.pop(client_id, None)
        if state is not None:
            try:
                state.sock.close()
            except OSError:
                pass
            print(f"[server] client#{client_id} disconnected")

    def _send_end_session(self, state: ClientState) -> None:
        if state.channel is None:
            print(f"[server] client#{state.client_id} has no active session")
            return
        ciphertext_b64, mac_b64 = state.channel.seal({"type": "END_SESSION"})
        out = {"type": "SECURE", "ciphertext": ciphertext_b64}
        if mac_b64 is not None:
            out["mac"] = mac_b64
        with state.lock:
            send_json(state.sock, out)
        state.channel = None
        state.dh_p = None
        print(f"[server] END_SESSION sent to client#{state.client_id} - session reset")

    def _admin_loop(self) -> None:
        help_text = (
            "Commands:\n"
            "  list                 - show connected clients\n"
            "  end <id>              - send encrypted EndSession to client\n"
            "  kick <id>             - close TCP connection\n"
            "  quit                  - stop server\n"
        )
        print(help_text)

        while self._running.is_set():
            try:
                line = input("server> ").strip()
            except EOFError:
                line = "quit"

            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()

            if cmd == "list":
                with self._clients_lock:
                    if not self._clients:
                        print("[server] no clients")
                        continue
                    for cid, st in self._clients.items():
                        session = "ON" if st.channel is not None else "OFF"
                        print(f"  client#{cid} {st.addr[0]}:{st.addr[1]} session={session}")

            elif cmd == "end" and len(parts) == 2:
                try:
                    cid = int(parts[1])
                except ValueError:
                    print("[server] invalid id")
                    continue
                with self._clients_lock:
                    st = self._clients.get(cid)
                if st is None:
                    print("[server] no such client")
                else:
                    try:
                        self._send_end_session(st)
                    except Exception as e:
                        print(f"[server] failed to send EndSession: {e}")

            elif cmd == "kick" and len(parts) == 2:
                try:
                    cid = int(parts[1])
                except ValueError:
                    print("[server] invalid id")
                    continue
                self._drop_client(cid)

            elif cmd == "quit":
                print("[server] stopping...")
                self._running.clear()
                try:
                    self._server_sock.close()
                except OSError:
                    pass
                with self._clients_lock:
                    ids = list(self._clients.keys())
                for cid in ids:
                    self._drop_client(cid)
                break

            else:
                print(help_text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mini TLS-like server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=12345)
    parser.add_argument("--max-clients", type=int, required=True, help="maximum concurrent clients")
    parser.add_argument("--no-mac", action="store_true", help="disable MAC (variant W3-like)")
    args = parser.parse_args()

    srv = MiniTLSServer(args.host, args.port, args.max_clients, use_mac=not args.no_mac)
    srv.start()


if __name__ == "__main__":
    main()
