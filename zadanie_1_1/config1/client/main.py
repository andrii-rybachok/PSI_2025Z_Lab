import socket
import sys
import math
import time

sizes = []
times = []
MAX_SIZE = 65507

SERVER_PORT = int(sys.argv[1] if len(sys.argv) > 1 else 63823)
HOST = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
ACK_MSG = b"ACK"

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(10)
    for i in range(1, 17):
        data_size = math.pow(2, i) - 1
        if data_size > MAX_SIZE:
            data_size = MAX_SIZE
        send_data = b"x" * int(data_size)
        start_time = time.time()
        try:
            s.sendto(send_data, (HOST, SERVER_PORT))
            data = s.recvfrom(1024)
            end_time = time.time()
            if data[0] == ACK_MSG:
                rtt = (end_time - start_time) * 1000  # w ms
                print(f"{int(data_size)} bajtów OK, RTT = {rtt:.3f} ms")
                sizes.append(int(data_size))
                times.append(rtt)
            else:
                print("Niepoprawna odpowiedź")
                break
        except socket.timeout:
            print(f"Timeout przy rozmiarze {int(data_size)} bajtów – przekroczony maksymalny rozmiar datagramu")
            break

print("\nPodsumowanie (Rozmiar bajtów : RTT ms):")
for size, rtt in zip(sizes, times):
    print(f"{size} : {rtt:.3f}")

print("\nClient finished.")
