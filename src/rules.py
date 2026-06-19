"""Parametri normativi vigenti per il calcolo dei rimborsi spese."""

MASSIMALI_GIORNALIERI_2025 = {
    "trasferta_italia": 46.48,
    "trasferta_estero": 77.47,
    "pasto": 8.00,
}

MASSIMALE_KM_2025 = 0.42
MASSIMALE_NOTTE_2025 = 150.00
PLAFOND_MENSILE_2025 = 1200.00

MASSIMALI_GIORNALIERI_2026 = {
    "trasferta_italia": 50.00,
    "trasferta_estero": 85.00,
    "pasto": 10.00,
}

MASSIMALE_KM_2026 = 0.45
MASSIMALE_NOTTE_2026 = 170.00
PLAFOND_MENSILE_2026 = 1400.00
MASSIMALE_LAVORO_AGILE_2026 = 3.50
MAX_GIORNI_LAVORO_AGILE_MENSILE = 12

MASSIMALI_GIORNALIERI = MASSIMALI_GIORNALIERI_2026
MASSIMALE_KM = MASSIMALE_KM_2026
MASSIMALE_NOTTE = MASSIMALE_NOTTE_2026
PLAFOND_MENSILE = PLAFOND_MENSILE_2026

CATEGORIE = {
    "trasferta_italia": "Trasferta in Italia",
    "trasferta_estero": "Trasferta all'estero",
    "pasto": "Rimborso pasto",
    "chilometrico": "Rimborso chilometrico",
    "alloggio": "Rimborso alloggio",
    "lavoro_agile": "Indennità lavoro agile",
}

CATEGORIE_A_GIORNATE = ("trasferta_italia", "trasferta_estero", "pasto")

RIFERIMENTO_NORMATIVO = "Circolare MEF n. 18/2026"
RIFERIMENTO_NORMATIVO_2025 = "Circolare MEF n. 41/2024"
