## Zadanie 1.1 – Komunikacja UDP

### Konfiguracja 1
#### Serwer
- docker run --network-alias serverc --name z35_zad1_serverc_kont --network z35_network z35_zad1_serverc
#### Klient
- docker run -it --name z35_zad1_clientp_kont --network z35_network z35_zad1_clientp 12345 serverc
<p>Aby wypisać logi z serweru należy użyć komendy: <strong>docker logs z35_zad1_serverc_kont</strong></p>

### Konfiguracja 2
#### Serwer
- docker run --network-alias serverp --name z35_zad1_serverp_kont --network z35_network z35_zad1_serverp
#### Klient
- docker run -it --name z35_zad1_clientc_kont --network z35_network z35_zad1_clientc serverp 12345
<p>Aby wypisać logi z serweru należy użyć komendy: <strong>docker logs z35_zad1_serverp_kont</strong></p>
