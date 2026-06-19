"""Regole di validazione delle richieste di rimborso."""

from datetime import date, timedelta

from src import rules


def _date_range(r):
    """Insieme delle date coperte da una richiesta (per categorie a giornate)."""
    inizio = date.fromisoformat(r["data"])
    giorni = r.get("giorni") or 1
    return {inizio + timedelta(days=i) for i in range(giorni)}


def valida(richiesta, richieste_esistenti=None):
    """Restituisce (True, "") se la richiesta è valida, altrimenti (False, motivazione)."""
    if not richiesta.get("dipendente"):
        return False, "dipendente mancante"

    categoria = richiesta.get("categoria")
    if categoria not in rules.CATEGORIE:
        return False, "categoria non riconosciuta"

    importo = richiesta.get("importo")
    if importo is None or importo <= 0:
        return False, "importo non positivo"

    try:
        date.fromisoformat(richiesta.get("data") or "")
    except ValueError:
        return False, "data mancante o non valida"

    if categoria == "lavoro_agile":
        if (richiesta.get("data") or "")[:4] < "2026":
            return False, "categoria non riconosciuta"
        giorni = richiesta.get("giorni")
        if not giorni or giorni <= 0:
            return False, "numero di giornate non valido"

    if categoria in rules.CATEGORIE_A_GIORNATE:
        giorni = richiesta.get("giorni")
        if not giorni or giorni <= 0:
            return False, "numero di giornate non valido"

    if categoria == "chilometrico":
        km = richiesta.get("km")
        if not km or km <= 0:
            return False, "numero di chilometri non valido"

    if categoria == "alloggio":
        notti = richiesta.get("notti")
        if not notti or notti <= 0:
            return False, "numero di notti non valido"

    if richieste_esistenti and (richiesta.get("data") or "")[:4] >= "2026":
        if categoria in ("lavoro_agile", "trasferta_italia", "trasferta_estero"):
            categorie_incompatibili = (
                {"trasferta_italia", "trasferta_estero"}
                if categoria == "lavoro_agile"
                else {"lavoro_agile"}
            )
            date_richiesta = _date_range(richiesta)
            for r in richieste_esistenti:
                if (
                    r["stato"] == "valida"
                    and r["dipendente"] == richiesta["dipendente"]
                    and r["categoria"] in categorie_incompatibili
                ):
                    if date_richiesta & _date_range(r):
                        return False, "incompatibilità lavoro agile / trasferta"

    return True, ""
