from src import validator


def richiesta(**campi):
    base = {
        "dipendente": "Maria Rossi",
        "data": "2025-10-06",
        "categoria": "pasto",
        "importo": 10.0,
        "giorni": 1,
        "km": None,
        "notti": None,
    }
    base.update(campi)
    return base


def test_richiesta_valida():
    assert validator.valida(richiesta()) == (True, "")


def test_dipendente_mancante():
    ok, motivazione = validator.valida(richiesta(dipendente=""))
    assert not ok
    assert motivazione == "dipendente mancante"


def test_categoria_non_riconosciuta():
    ok, motivazione = validator.valida(richiesta(categoria="parcheggio"))
    assert not ok
    assert motivazione == "categoria non riconosciuta"


def test_importo_zero():
    ok, motivazione = validator.valida(richiesta(importo=0))
    assert not ok
    assert motivazione == "importo non positivo"


def test_importo_negativo():
    ok, motivazione = validator.valida(richiesta(importo=-5.0))
    assert not ok
    assert motivazione == "importo non positivo"


def test_importo_mancante():
    ok, motivazione = validator.valida(richiesta(importo=None))
    assert not ok
    assert motivazione == "importo non positivo"


def test_data_mancante():
    ok, motivazione = validator.valida(richiesta(data=""))
    assert not ok
    assert motivazione == "data mancante o non valida"


def test_data_non_valida():
    ok, motivazione = validator.valida(richiesta(data="06/10/2025"))
    assert not ok
    assert motivazione == "data mancante o non valida"


def test_giornate_mancanti_per_trasferta():
    ok, motivazione = validator.valida(
        richiesta(categoria="trasferta_italia", giorni=None)
    )
    assert not ok
    assert motivazione == "numero di giornate non valido"


def test_giornate_zero_per_pasto():
    ok, motivazione = validator.valida(richiesta(categoria="pasto", giorni=0))
    assert not ok
    assert motivazione == "numero di giornate non valido"


def test_chilometri_non_validi():
    ok, motivazione = validator.valida(
        richiesta(categoria="chilometrico", km=0)
    )
    assert not ok
    assert motivazione == "numero di chilometri non valido"


def test_notti_non_valide():
    ok, motivazione = validator.valida(
        richiesta(categoria="alloggio", notti=None)
    )
    assert not ok
    assert motivazione == "numero di notti non valido"


def test_chilometrico_valido():
    assert validator.valida(
        richiesta(categoria="chilometrico", km=120, giorni=None)
    ) == (True, "")


def test_alloggio_valido():
    assert validator.valida(
        richiesta(categoria="alloggio", notti=3, giorni=None)
    ) == (True, "")


def test_lavoro_agile_valido_2026():
    ok, _ = validator.valida(richiesta(data="2026-03-01", categoria="lavoro_agile", giorni=5))
    assert ok


def test_lavoro_agile_respinto_data_2025():
    ok, motivazione = validator.valida(richiesta(data="2025-12-01", categoria="lavoro_agile", giorni=3))
    assert not ok
    assert motivazione == "categoria non riconosciuta"


def test_lavoro_agile_giornate_zero():
    ok, motivazione = validator.valida(richiesta(data="2026-03-01", categoria="lavoro_agile", giorni=0))
    assert not ok
    assert motivazione == "numero di giornate non valido"


def _richiesta_valida_archiviata(categoria, data, giorni):
    """Helper: richiesta già archviata (valida) per i test di incompatibilità."""
    return {
        "dipendente": "Maria Rossi",
        "data": data,
        "categoria": categoria,
        "importo": 50.0,
        "giorni": giorni,
        "km": None,
        "notti": None,
        "stato": "valida",
        "quota_esente": 50.0,
        "quota_imponibile": 0.0,
        "dettaglio": {},
    }


def test_incompatibilita_lavoro_agile_su_trasferta():
    # trasferta_italia 2026-03-04 per 3gg copre 04, 05, 06
    # lavoro_agile richiesto 2026-03-05 per 2gg copre 05, 06 → sovrapposizione
    esistenti = [_richiesta_valida_archiviata("trasferta_italia", "2026-03-04", 3)]
    ok, motivazione = validator.valida(
        richiesta(data="2026-03-05", categoria="lavoro_agile", giorni=2),
        richieste_esistenti=esistenti,
    )
    assert not ok
    assert motivazione == "incompatibilità lavoro agile / trasferta"


def test_incompatibilita_trasferta_su_lavoro_agile():
    # lavoro_agile valido 2026-03-06 per 1gg
    # trasferta_estero richiesta 2026-03-05 per 3gg copre 05, 06, 07 → sovrapposizione
    esistenti = [_richiesta_valida_archiviata("lavoro_agile", "2026-03-06", 1)]
    ok, motivazione = validator.valida(
        richiesta(data="2026-03-05", categoria="trasferta_estero", giorni=3),
        richieste_esistenti=esistenti,
    )
    assert not ok
    assert motivazione == "incompatibilità lavoro agile / trasferta"


def test_nessuna_incompatibilita_date_non_sovrapposte():
    # trasferta 2026-03-31, lavoro_agile 2026-04-01 → nessuna sovrapposizione
    esistenti = [_richiesta_valida_archiviata("trasferta_italia", "2026-03-31", 1)]
    ok, _ = validator.valida(
        richiesta(data="2026-04-01", categoria="lavoro_agile", giorni=1),
        richieste_esistenti=esistenti,
    )
    assert ok
