# Mini TLS (PSI) – TCP + Diffie-Hellman + XOR + Encrypt-then-MAC

Projekt realizuje wymagania z opisu zadania. Zgodnie z uwagami:

- **`EndSession` jest szyfrowane** (idzie jako zaszyfrowany typ wewnętrzny), więc odbiorca rozpoznaje je dopiero po odszyfrowaniu.
- **Brak hardcodowania parametrów Diffie-Hellmana po stronie serwera** – klient wysyła `p`, `g` oraz `A` w `ClientHello`.
- **Nonce zostały pominięte** dla prostoty (nie są potrzebne do spełnienia minimalnych wymagań).

## Struktura wiadomości

### 1) Nieszyfrowane (handshake)

**ClientHello** (jawne):
```json
{ "type": "CLIENT_HELLO", "p": 7919, "g": 5, "A": 1234 }
```

**ServerHello** (jawne):
```json
{ "type": "SERVER_HELLO", "B": 5678 }
```

### 2) Szyfrowane (po handshake)

Wszystko po handshake ma postać **SECURE**:
```json
{ "type": "SECURE", "ciphertext": "...base64...", "mac": "...base64..." }
```

W środku jest zaszyfrowany JSON, np.:

- DATA:
```json
{ "type": "DATA", "text": "Hello" }
```

- END_SESSION:
```json
{ "type": "END_SESSION" }
```

## Algorytmy

- **Wymiana kluczy:** Diffie–Hellman na małych `int`.
- **KDF:** SHA-256 z sekretu DH -> `enc_key` i `mac_key`.
- **Szyfrowanie:** XOR z powtarzanym `enc_key` (prosty odpowiednik OTP – zgodnie z zaleceniem prostoty).
- **Integralność i autentyczność:** Encrypt-then-MAC (HMAC-SHA256 po ciphertext).

## Klucze do sprawozdania końcowego (Wireshark)

Po udanym handshake obie strony dopisują użyte klucze do plików w katalogu `keys/`:

- `keys/server_<id>.log` (dla każdego klienta osobno)
- `keys/client.log`

To jest celowo „niebezpieczne”, ale upraszcza dowód działania protokołu w sprawozdaniu końcowym.

Przykład ręcznego odszyfrowania (np. na podstawie wartości z Wireshark):

```bash
python -m app.manual_decrypt \
  --enc-key-hex <enc_key_hex_z_pliku_log> \
  --ciphertext-b64 <ciphertext_z_wireshark>
```

## Uruchomienie w Docker

### Serwer
W jednym terminalu:
```bash
MAX_CLIENTS=5 PORT=12345 docker compose up --build server
```

### Klient
W drugim terminalu (możesz uruchomić kilka razy dla wielu klientów):
```bash
docker compose run --rm client
```

W kliencie dostępne są komendy:
- `connect`
- `handshake [p] [g]` (bez parametrów klient losuje małe p i g)
- `send <tekst>`
- `end`
- `quit`

Na serwerze:
- `list`
- `end <id>` (wysyła zaszyfrowane EndSession do wybranego klienta)
- `kick <id>`
- `quit`

## Uruchomienie lokalne (bez Dockera)

```bash
python -m app.server --max-clients 5
python -m app.client --host 127.0.0.1
```
