# PSI – Laboratorium 2 (TCP)

Repozytorium zawiera rozwiązanie zadania z komunikacji TCP z laboratoriów PSI.  
Zaimplementowano prosty system klient–serwer, który oblicza wynik działania `a * b`:

- **klient TCP w C** (`client_tcp.c`)
- **serwer TCP w Pythonie** (`server_tcp.py`)

Klient łączy się z serwerem, pyta użytkownika o:
1. pierwszą liczbę (`a`),
2. operator (`op`, np. `*`),
3. drugą liczbę (`b`),

a następnie wysyła te trzy linie do serwera.  
Serwer odczytuje dane, oblicza wynik, wypisuje działanie u siebie i odsyła wynik do klienta.  
Klient wyświetla otrzymany wynik na ekranie.

## Wymagania

- kompilator C (np. `gcc` lub `clang`),
- Python 3.

Testowane na macOS (powinno działać również na Linuxie).

## Kompilacja klienta

```bash
gcc client_tcp.c -o client_tcp