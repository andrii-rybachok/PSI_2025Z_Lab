import socket
import sys
from socket import *

HOST = '0.0.0.0'
SERVER_PORT = int(sys.argv[1] if len(sys.argv) > 1 else 12345)
BUFFER_SIZE = 65507
REPLY = b"ACK"

# Utworzenie gniazda UDP
sock = socket(AF_INET, SOCK_DGRAM)
sock.bind((HOST, SERVER_PORT))

print(f"Serwer UDP nasłuchuje na {HOST}:{SERVER_PORT}...")

while True:
    data, addr = sock.recvfrom(BUFFER_SIZE)
    print(f"Odebrano {len(data)} bajtów od {addr}")
    sock.sendto(REPLY, addr)