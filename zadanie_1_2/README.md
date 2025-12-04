# Zadanie 1.2

Projekt realizuje prosty, własny protokół niezawodnego przesyłania pliku po UDP.  
Klient (Python) wysyła plik 10000 B w pakietach po 100 B, serwer (C) składa plik, liczy SHA-256 i odsyła hash, a klient porównuje hash lokalny z tym z serwera.

## Jak uruchomić (Docker)

W katalogu głównym repozytorium:

```bash
docker compose up --build
````

Po poprawnym działaniu w logach klienta powinno być coś w stylu:

```text
Local hash : ...
Server hash: ...
Wynik: hashe są identyczne (OK).
```

Serwer w logach pokazuje kolejne pakiety `START/DATA` oraz wyliczony hash.

## Jak uruchomić lokalnie (opcjonalnie)

1. Wygeneruj plik 10000 B:

   ```bash
   python gen_file.py random.bin
   ```

2. Uruchom serwer (C) na porcie 9000:

   ```bash
   gcc -Wall -Wextra -O2 server.c -o server -lssl -lcrypto
   ./server 9000
   ```

3. W drugim terminalu uruchom klienta (Python):

   ```bash
   python client.py 127.0.0.1 9000 random.bin
   ```
