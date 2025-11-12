# Zadanie 1.1 – Komunikacja UDP

## Uruchomienie 
### Konfiguracja 1
#### Serwer
- docker build -t z35_zad1_serverc .
- docker run --network-alias serverc --name z35_zad1_serverc_kont --network z35_network z35_zad1_serverc
#### Klient
- docker build -t z35_zad1_clientp
- docker run -it --name z35_zad1_clientp_kont --network z35_network z35_zad1_clientp 12345 serverc
<p>Aby wypisać logi z serweru należy użyć komendy: <strong>docker logs z35_zad1_serverc_kont</strong></p>

### Konfiguracja 2
#### Serwer
- docker build -t z35_zad1_serverp .
- docker run --network-alias serverp --name z35_zad1_serverp_kont --network z35_network z35_zad1_serverp
#### Klient
- docker build -t z35_zad1_clientc .
- docker run -it --name z35_zad1_clientc_kont --network z35_network z35_zad1_clientc serverp 12345
<p>Aby wypisać logi z serweru należy użyć komendy: <strong>docker logs z35_zad1_serverp_kont</strong></p>
