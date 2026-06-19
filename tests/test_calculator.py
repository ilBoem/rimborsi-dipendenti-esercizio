from src import calculator, rules


def richiesta(**campi):
    base = {
        "dipendente": "Maria Rossi",
        "data": "2026-03-01",
        "categoria": "pasto",
        "importo": 10.0,
        "giorni": 1,
        "km": None,
        "notti": None,
    }
    base.update(campi)
    return base


class TestMassimaleTeorico:
    def test_trasferta_italia_2026(self):
        r = richiesta(categoria="trasferta_italia", giorni=4)
        regole = calculator._regole_per_anno(2026)
        assert calculator.massimale_teorico(r, regole) == 200.0

    def test_trasferta_estero_2026(self):
        r = richiesta(categoria="trasferta_estero", giorni=3)
        regole = calculator._regole_per_anno(2026)
        assert calculator.massimale_teorico(r, regole) == 255.0

    def test_pasto_2026(self):
        r = richiesta(categoria="pasto", giorni=5)
        regole = calculator._regole_per_anno(2026)
        assert calculator.massimale_teorico(r, regole) == 50.0

    def test_chilometrico_2026(self):
        r = richiesta(categoria="chilometrico", km=250)
        regole = calculator._regole_per_anno(2026)
        assert calculator.massimale_teorico(r, regole) == 112.5

    def test_alloggio_2026(self):
        r = richiesta(categoria="alloggio", notti=2)
        regole = calculator._regole_per_anno(2026)
        assert calculator.massimale_teorico(r, regole) == 340.0

    def test_trasferta_italia_2025(self):
        r = richiesta(data="2025-10-06", categoria="trasferta_italia", giorni=4)
        regole = calculator._regole_per_anno(2025)
        assert calculator.massimale_teorico(r, regole) == 185.92

    def test_pasto_2025(self):
        r = richiesta(data="2025-10-06", categoria="pasto", giorni=5)
        regole = calculator._regole_per_anno(2025)
        assert calculator.massimale_teorico(r, regole) == 40.0

    def test_lavoro_agile_2026_base(self):
        r = richiesta(categoria="lavoro_agile", giorni=6)
        regole = calculator._regole_per_anno(2026)
        assert calculator.massimale_teorico(r, regole, giorni_la_ammessi=6) == 21.0

    def test_trasferta_estero_2026_6gg_progressiva(self):
        # (5×85) + (1×76,50) = 501,50 — Caso 6.2 circolare
        r = richiesta(categoria="trasferta_estero", giorni=6)
        regole = calculator._regole_per_anno(2026)
        assert calculator.massimale_teorico(r, regole) == 501.50

    def test_trasferta_estero_2026_12gg_progressiva(self):
        # (5×85) + (5×76,50) + (2×68) = 943,50 — esempio circolare Sezione 4
        r = richiesta(categoria="trasferta_estero", giorni=12)
        regole = calculator._regole_per_anno(2026)
        assert calculator.massimale_teorico(r, regole) == 943.50

    def test_trasferta_estero_2026_5gg_no_riduzione(self):
        # 5 gg esatte: nessuna riduzione progressiva — Caso 6.3 circolare
        r = richiesta(categoria="trasferta_estero", giorni=5)
        regole = calculator._regole_per_anno(2026)
        assert calculator.massimale_teorico(r, regole) == 425.0

    def test_trasferta_estero_2025_no_riduzione(self):
        # 2025: massimale piatto 77,47 × 6 = 464,82 (nessuna riduzione progressiva)
        r = richiesta(data="2025-10-06", categoria="trasferta_estero", giorni=6)
        regole = calculator._regole_per_anno(2025)
        assert calculator.massimale_teorico(r, regole) == round(77.47 * 6, 2)


class TestCalcola:
    def test_importo_sotto_massimale_tutto_esente_2026(self):
        r = richiesta(categoria="pasto", giorni=5, importo=35.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 35.0
        assert imponibile == 0.0

    def test_importo_sopra_massimale_eccedenza_imponibile_2026(self):
        r = richiesta(categoria="trasferta_italia", giorni=2, importo=120.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 100.0
        assert imponibile == 20.0

    def test_plafond_incapiente_limita_la_quota_esente_2026(self):
        r = richiesta(categoria="alloggio", notti=2, importo=300.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1300.0)
        assert esente == 100.0
        assert imponibile == 200.0

    def test_plafond_esaurito_tutto_imponibile_2026(self):
        r = richiesta(categoria="pasto", giorni=1, importo=10.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1400.0)
        assert esente == 0.0
        assert imponibile == 10.0

    def test_dettaglio_del_calcolo_2026(self):
        r = richiesta(categoria="trasferta_estero", giorni=2, importo=200.0)
        _, _, dettaglio = calculator.calcola(r, esente_gia_riconosciuta=1300.0)
        assert dettaglio == {
            "massimale_teorico": 170.0,
            "esente_teorica": 170.0,
            "capienza_plafond": 100.0,
        }

    def test_regime_transitorio_massimali_2025(self):
        r = richiesta(data="2025-12-01", categoria="trasferta_italia", giorni=2, importo=120.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 92.96
        assert imponibile == 27.04

    def test_regime_transitorio_plafond_2025(self):
        r = richiesta(data="2025-12-01", categoria="alloggio", notti=2, importo=300.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1100.0)
        assert esente == 100.0
        assert imponibile == 200.0

    def test_plafond_2026_capienza_aumentata(self):
        r = richiesta(categoria="pasto", giorni=3, importo=30.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1350.0)
        assert esente == 30.0
        assert imponibile == 0.0

    def test_lavoro_agile_limite_parziale(self):
        # 6gg richiesti, 10 già rimborsati → giorni_ammessi=2 → massimale=7,00
        r = richiesta(categoria="lavoro_agile", giorni=6, importo=21.0)
        esente, imponibile, dettaglio = calculator.calcola(r, esente_gia_riconosciuta=0.0, giorni_la_gia_rimborsati=10)
        assert dettaglio["giorni_ammessi"] == 2
        assert dettaglio["massimale_teorico"] == 7.0
        assert esente == 7.0
        assert imponibile == 14.0

    def test_lavoro_agile_limite_esaurito(self):
        # Già 12gg nel mese → giorni_ammessi=0 → tutto imponibile — Caso 6.4 circolare
        r = richiesta(categoria="lavoro_agile", giorni=3, importo=10.50)
        esente, imponibile, dettaglio = calculator.calcola(r, esente_gia_riconosciuta=0.0, giorni_la_gia_rimborsati=12)
        assert dettaglio["giorni_ammessi"] == 0
        assert esente == 0.0
        assert imponibile == 10.50
