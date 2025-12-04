import sys

import socket
import struct
import hashlib

from pathlib import Path

MSG_START = b"S"
MSG_DATA  = b"D"
MSG_ACK   = b"A"
MSG_HASH  = b"H"

CHUNK_SIZE = 100
FILE_SIZE  = 10000
SOCKET_TIMEOUT = 0.5
HASH_TIMEOUT   = 2.0
MAX_RETRIES    = 20
RECV_BUF_SIZE  = 2048


def read_file_bytes(filename):
    try:
        data = Path(filename).read_bytes()
    except OSError as e:
        print("Blad odczytu pliku %s: %s" % (filename, e), file=sys.stderr)
        sys.exit(1)

    if len(data) != FILE_SIZE:
        print("Blad: plik musi mieć dokładnie %d bajtow, a ma %d." %
              (FILE_SIZE, len(data)), file=sys.stderr)
        sys.exit(1)

    return data


def compute_sha256(data):
    return hashlib.sha256(data).digest()


def build_start_packet(file_size, chunk_size):
    return struct.pack("!cIH", MSG_START, file_size, chunk_size)


def build_data_packet(seq, chunk):
    data_len = len(chunk)
    return struct.pack("!cIH", MSG_DATA, seq, data_len) + chunk


def parse_ack_packet(packet):
    if len(packet) < 5:
        raise ValueError("ACK za krótki")

    msg_type, seq = struct.unpack("!cI", packet[:5])
    return msg_type, seq


def parse_hash_packet(packet):
    if len(packet) < 1 + 32:
        raise ValueError("hash jest za krotki")

    msg_type = packet[0:1]
    hash_bytes = packet[1:33]
    return msg_type, hash_bytes


def send_with_ack(sock, addr, packet, expected_seq):
    attempt = 0
    while attempt < MAX_RETRIES:
        attempt += 1
        try:
            sock.sendto(packet, addr)
        except OSError as e:
            raise RuntimeError("Błąd sendto: %s" % e)

        try:
            data, _ = sock.recvfrom(RECV_BUF_SIZE)
        except socket.timeout:
            continue
        except OSError as e:
            raise RuntimeError("Błąd recvfrom: %s" % e)

        try:
            msg_type, seq = parse_ack_packet(data)
        except ValueError:
            continue

        if msg_type != MSG_ACK:
            continue

        if seq == expected_seq:
            return

    raise RuntimeError("Za duzo prob wysłania pakietu seq=%d" % expected_seq)


def wait_for_hash(sock):
    sock.settimeout(HASH_TIMEOUT)

    tries = 0
    while tries < MAX_RETRIES:
        tries += 1
        try:
            data, _ = sock.recvfrom(RECV_BUF_SIZE)

            # print(data)
        except socket.timeout:
            continue
        except OSError as e:
            raise RuntimeError("Błąd recvfrom (hash): %s" % e)

        try:
            msg_type, hash_bytes = parse_hash_packet(data)
        except ValueError:
            continue

        if msg_type != MSG_HASH:
            continue

        if len(hash_bytes) == 32:
            return hash_bytes

    raise RuntimeError("Nie udało odebrać poprawnego hashu od serwera")


def send_file(sock, addr, file_bytes):
    total_size = len(file_bytes)

    start_packet = build_start_packet(total_size, CHUNK_SIZE)
    send_with_ack(sock, addr, start_packet, expected_seq=0)

    seq = 0

    offset = 0
    while offset < total_size:
        chunk = file_bytes[offset:offset + CHUNK_SIZE]
        data_packet = build_data_packet(seq, chunk)
        send_with_ack(sock, addr, data_packet, expected_seq=seq)
        offset += CHUNK_SIZE
        seq += 1

    server_hash = wait_for_hash(sock)
    return server_hash


def main():
    if len(sys.argv) != 4:

        print("Usage: %s <server_host> <server_port> <file>" % sys.argv[0],
              file=sys.stderr)

        sys.exit(1)

    server_host = sys.argv[1]
    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("Blad: port musi byc liczba całkowita.", file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[3]

    file_bytes = read_file_bytes(filename)
    local_hash = compute_sha256(file_bytes)

    addr = (server_host, server_port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(SOCKET_TIMEOUT)

    try:
        server_hash = send_file(sock, addr, file_bytes)
    except RuntimeError as e:
        print("Blad protokolu: %s" % e, file=sys.stderr)
        sock.close()
        sys.exit(1)

    sock.close()

    print("Local hash: %s" % local_hash.hex())
    print("Server hash: %s" % server_hash.hex())

    if local_hash == server_hash:
        print("Hashe są identyczne")
        sys.exit(0)
    else:
        print("Hashe rozne")
        sys.exit(2)


if __name__ == "__main__":
    main()
