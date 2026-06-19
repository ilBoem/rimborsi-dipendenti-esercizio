import pytest

from src import storage
from src.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "PERCORSO_DATI", tmp_path / "richieste.json")
    app.config["TESTING"] = True
    return app.test_client()


def nuova_richiesta_pasto(client, **campi):
    dati = {
        "dipendente": "Maria Rossi",
        "data": "2025-10-06",
        "categoria": "pasto",
        "importo": "24.00",
        "giorni": "3",
    }
    dati.update(campi)
    return client.post("/nuova", data=dati)


def test_home_reindirizza_a_elenco(client):
    risposta = client.get("/")
    assert risposta.status_code == 302
    assert "/richieste" in risposta.headers["Location"]


def test_pagine_principali_raggiungibili(client):
    for percorso in ("/richieste", "/nuova", "/riepilogo", "/normativa"):
        assert client.get(percorso).status_code == 200


def test_registrazione_richiesta_valida(client):
    risposta = nuova_richiesta_pasto(client)
    assert risposta.status_code == 200
    assert "registrata" in risposta.get_data(as_text=True)

    richieste = storage.carica()
    assert len(richieste) == 1
    assert richieste[0]["stato"] == "valida"
    assert richieste[0]["quota_esente"] == 24.0
    assert richieste[0]["quota_imponibile"] == 0.0


def test_registrazione_richiesta_respinta(client):
    risposta = nuova_richiesta_pasto(client, importo="-10")
    assert "respinta" in risposta.get_data(as_text=True)
    assert "importo non positivo" in risposta.get_data(as_text=True)

    richieste = storage.carica()
    assert richieste[0]["stato"] == "respinta"
    assert richieste[0]["quota_esente"] == 0.0


def test_eccedenza_oltre_massimale_diventa_imponibile(client):
    nuova_richiesta_pasto(client, importo="30.00", giorni="3")
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 24.0
    assert richieste[0]["quota_imponibile"] == 6.0


def test_plafond_mensile_condiviso_tra_richieste(client):
    nuova_richiesta_pasto(
        client, categoria="alloggio", notti="8", importo="1150.00", giorni=""
    )
    nuova_richiesta_pasto(client, importo="80.00", giorni="10")
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 1150.0
    # Capienza residua: 1200 - 1150 = 50, quindi del pasto sono esenti solo 50.
    assert richieste[1]["quota_esente"] == 50.0
    assert richieste[1]["quota_imponibile"] == 30.0


def test_elenco_filtra_per_dipendente(client):
    nuova_richiesta_pasto(client, dipendente="Maria Rossi")
    nuova_richiesta_pasto(client, dipendente="Luca Bianchi")
    testo = client.get("/richieste?dipendente=Luca+Bianchi").get_data(as_text=True)
    assert "Luca Bianchi" in testo
    assert "Maria Rossi" not in testo.split("</thead>")[1].split("Clicca")[0]


def test_riepilogo_mostra_totali(client):
    nuova_richiesta_pasto(client)
    nuova_richiesta_pasto(client, importo="16.00", giorni="2")
    testo = client.get("/riepilogo").get_data(as_text=True)
    assert "Maria Rossi" in testo
    assert "40.00" in testo


def test_normativa_mostra_massimali_vigenti(client):
    testo = client.get("/normativa").get_data(as_text=True)
    assert "50.00" in testo
    assert "85.00" in testo
    assert "1400.00" in testo


def test_normativa_mostra_entrambe_le_normative(client):
    testo = client.get("/normativa").get_data(as_text=True)
    assert "46.48" in testo
    assert "77.47" in testo
    assert "1200.00" in testo
    assert "50.00" in testo
    assert "85.00" in testo
    assert "1400.00" in testo


def test_richiesta_2026_usa_nuovi_massimali(client):
    nuova_richiesta_pasto(
        client, data="2026-01-15", categoria="pasto", importo="30.00", giorni="3"
    )
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 30.0
    assert richieste[0]["quota_imponibile"] == 0.0


def test_richiesta_2025_usa_vecchi_massimali(client):
    nuova_richiesta_pasto(
        client, data="2025-12-18", categoria="pasto", importo="24.00", giorni="3"
    )
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 24.0
    assert richieste[0]["quota_imponibile"] == 0.0


def nuova_richiesta_lavoro_agile(client, **campi):
    dati = {
        "dipendente": "Maria Rossi",
        "data": "2026-02-01",
        "categoria": "lavoro_agile",
        "importo": "10.50",
        "giorni": "3",
    }
    dati.update(campi)
    return client.post("/nuova", data=dati)


def test_lavoro_agile_2026_quota_esente(client):
    # 3gg × 3,50 = 10,50 → tutto esente
    risposta = nuova_richiesta_lavoro_agile(client)
    assert risposta.status_code == 200
    richieste = storage.carica()
    assert richieste[0]["stato"] == "valida"
    assert richieste[0]["quota_esente"] == 10.50
    assert richieste[0]["quota_imponibile"] == 0.0
    assert richieste[0]["dettaglio"]["giorni_ammessi"] == 3


def test_lavoro_agile_2025_respinto(client):
    risposta = nuova_richiesta_lavoro_agile(client, data="2025-12-01")
    assert "respinta" in risposta.get_data(as_text=True)
    richieste = storage.carica()
    assert richieste[0]["stato"] == "respinta"
    assert richieste[0]["motivazione"] == "categoria non riconosciuta"


def test_lavoro_agile_limite_mensile_saturato(client):
    # Prima richiesta: 12 gg → saturano il mese
    nuova_richiesta_lavoro_agile(client, giorni="12", importo="42.00")
    # Seconda richiesta: giorni_ammessi=0 → massimale=0 → tutto imponibile
    nuova_richiesta_lavoro_agile(client, giorni="3", importo="10.50")
    richieste = storage.carica()
    assert richieste[0]["dettaglio"]["giorni_ammessi"] == 12
    assert richieste[1]["dettaglio"]["giorni_ammessi"] == 0
    assert richieste[1]["quota_esente"] == 0.0
    assert richieste[1]["quota_imponibile"] == 10.50


def test_incompatibilita_app(client):
    # Prima: trasferta_italia 2026-03-04 per 3gg (valida)
    client.post("/nuova", data={
        "dipendente": "Maria Rossi",
        "data": "2026-03-04",
        "categoria": "trasferta_italia",
        "importo": "100.00",
        "giorni": "3",
    })
    # Seconda: lavoro_agile 2026-03-05 per 2gg (sovrapposizione → respinta)
    risposta = nuova_richiesta_lavoro_agile(client, data="2026-03-05", giorni="2", importo="7.00")
    assert "respinta" in risposta.get_data(as_text=True)
    richieste = storage.carica()
    assert richieste[0]["stato"] == "valida"
    assert richieste[1]["stato"] == "respinta"
    assert richieste[1]["motivazione"] == "incompatibilità lavoro agile / trasferta"


def test_trasferta_estera_6gg_progressiva(client):
    # 6gg 2026: massimale = (5×85) + (1×76,50) = 501,50 → importo 500 → tutto esente
    client.post("/nuova", data={
        "dipendente": "Maria Rossi",
        "data": "2026-03-09",
        "categoria": "trasferta_estero",
        "importo": "500.00",
        "giorni": "6",
    })
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 500.0
    assert richieste[0]["quota_imponibile"] == 0.0
    assert richieste[0]["dettaglio"]["massimale_teorico"] == 501.50


def test_riepilogo_percentuale_plafond_2026(client):
    nuova_richiesta_pasto(
        client,
        data="2026-01-15",
        categoria="alloggio",
        notti="4",
        importo="700.00",
        giorni="",
    )
    testo = client.get("/riepilogo").get_data(as_text=True)
    assert "Maria Rossi" in testo
    assert "49%" in testo
