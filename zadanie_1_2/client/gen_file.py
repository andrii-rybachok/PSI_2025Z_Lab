import os
import sys
import random

FILE_SIZE = 10000


def generate_file(filename):
    try:
        data = os.urandom(FILE_SIZE)
    except NotImplementedError:

        data = bytes(random.getrandbits(8) for _ in range(FILE_SIZE))

    try:
        with open(filename, "wb") as f:
            f.write(data)
    except OSError as e:
        print("Bląd zapisu do pliku %s: %s" % (filename, e), file=sys.stderr)
        sys.exit(1)

    print("Utworzono plik %s o rozmiarze %d bajtow." % (filename, FILE_SIZE))


def main():
    if len(sys.argv) >= 2:

        filename = sys.argv[1]
        
    else:
        filename = "random.bin"

    generate_file(filename)


if __name__ == "__main__":
    main()
