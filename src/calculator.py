"""Calcolo della quota esente e della quota imponibile di una richiesta."""

from src import rules


def _regole_per_anno(anno: int) -> dict:
    """Restituisce il set di parametri normativi per l'anno dato."""
    if anno >= 2026:
        return {
            "massimali_giornalieri": rules.MASSIMALI_GIORNALIERI_2026,
            "massimale_km": rules.MASSIMALE_KM_2026,
            "massimale_notte": rules.MASSIMALE_NOTTE_2026,
            "plafond_mensile": rules.PLAFOND_MENSILE_2026,
            "massimale_lavoro_agile": rules.MASSIMALE_LAVORO_AGILE_2026,
            "riduzione_progressiva_estero": True,
        }
    return {
        "massimali_giornalieri": rules.MASSIMALI_GIORNALIERI_2025,
        "massimale_km": rules.MASSIMALE_KM_2025,
        "massimale_notte": rules.MASSIMALE_NOTTE_2025,
        "plafond_mensile": rules.PLAFOND_MENSILE_2025,
        "riduzione_progressiva_estero": False,
    }


def massimale_teorico(richiesta, regole, giorni_la_ammessi=0):
    """Massimale di esenzione applicabile alla richiesta, in base alla categoria."""
    categoria = richiesta["categoria"]
    if categoria == "lavoro_agile":
        return round(regole["massimale_lavoro_agile"] * giorni_la_ammessi, 2)
    if categoria in rules.CATEGORIE_A_GIORNATE:
        giorni = richiesta["giorni"]
        if categoria == "trasferta_estero" and regole["riduzione_progressiva_estero"] and giorni > 5:
            g1 = min(giorni, 5)
            g2 = min(max(giorni - 5, 0), 5)
            g3 = max(giorni - 10, 0)
            return round(g1 * 85.00 + g2 * 76.50 + g3 * 68.00, 2)
        return round(regole["massimali_giornalieri"][categoria] * giorni, 2)
    if categoria == "chilometrico":
        return round(regole["massimale_km"] * richiesta["km"], 2)
    if categoria == "alloggio":
        return round(regole["massimale_notte"] * richiesta["notti"], 2)
    raise ValueError(f"categoria non gestita: {categoria}")


def calcola(richiesta, esente_gia_riconosciuta, giorni_la_gia_rimborsati=0):
    """Restituisce (quota_esente, quota_imponibile, dettaglio).

    `esente_gia_riconosciuta` è la quota esente già riconosciuta al dipendente
    nel mese della richiesta, ai fini del plafond mensile.
    `giorni_la_gia_rimborsati` è il numero di giornate di lavoro agile già ammesse
    nel mese (usato solo per categoria lavoro_agile).
    """
    anno = int(richiesta["data"][:4])
    regole = _regole_per_anno(anno)
    importo = richiesta["importo"]
    categoria = richiesta["categoria"]
    giorni_ammessi = None
    if categoria == "lavoro_agile":
        giorni_ammessi = min(
            richiesta["giorni"],
            max(0, rules.MAX_GIORNI_LAVORO_AGILE_MENSILE - giorni_la_gia_rimborsati),
        )
        teorico = massimale_teorico(richiesta, regole, giorni_la_ammessi=giorni_ammessi)
    else:
        teorico = massimale_teorico(richiesta, regole)
    esente_teorica = min(importo, teorico)
    capienza = max(regole["plafond_mensile"] - esente_gia_riconosciuta, 0.0)
    esente = round(min(esente_teorica, capienza), 2)
    imponibile = round(importo - esente, 2)
    dettaglio = {
        "massimale_teorico": teorico,
        "esente_teorica": round(esente_teorica, 2),
        "capienza_plafond": round(capienza, 2),
    }
    if giorni_ammessi is not None:
        dettaglio["giorni_ammessi"] = giorni_ammessi
    return esente, imponibile, dettaglio
