import socket
import sys

HOST = "127.0.0.1"
BUFSIZE = 256


def main():
    if len(sys.argv) < 2:
        port = 8000
        print("brak portu, uzywam", port)
    else:
        port = int(sys.argv[1])

    print("serwer", HOST, port)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, port))

        s.listen(5)
        while True:
            conn, addr = s.accept()
            with conn:
                print("polaczenie", addr)

                data = b""
                while data.count(b"\n") < 3:
                    chunk = conn.recv(BUFSIZE)
                    if not chunk:
                        break
                    data += chunk

                if data.count(b"\n") < 3:
                    print("za malo danych")
                    continue

                parts = data.decode("utf-8").splitlines()
                a_str = parts[0]
                op_str = parts[1]
                b_str = parts[2]

                a = int(a_str)
                b = int(b_str)
                res = a * b

                print("wyr:", f"{a} {op_str} {b} = {res}")

                msg = (str(res) + "\n").encode("utf-8")
                conn.sendall(msg)


if __name__ == "__main__":
    main()
