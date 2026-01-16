import argparse
import base64

from .crypto import xor_stream


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual decrypt helper for Wireshark demo")
    parser.add_argument("--enc-key-hex", required=True, help="enc_key in hex (from keys/*.log)")
    parser.add_argument("--ciphertext-b64", required=True, help="ciphertext field (base64) from SECURE message")
    args = parser.parse_args()

    enc_key = bytes.fromhex(args.enc_key_hex)
    ciphertext = base64.b64decode(args.ciphertext_b64)
    plaintext = xor_stream(ciphertext, enc_key)
    print(plaintext.decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
