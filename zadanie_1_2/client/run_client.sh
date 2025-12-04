#!/bin/sh
set -e

echo "[client] Generuję plik /tmp/random.bin..."
python gen_file.py /tmp/random.bin

echo "[client] Start klienta UDP..."
python client.py server 9000 /tmp/random.bin
