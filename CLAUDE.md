# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Development
flask --app src.app run              # Start app on http://127.0.0.1:5000
pytest                               # Run all tests
pytest tests/test_calculator.py      # Run single test file
pytest tests/test_calculator.py::test_nome  # Run single test
pytest -v                            # Verbose output

# Code structure
pytest --collect-only                # List all tests
```

## Project Architecture

This is a Flask web application for managing employee expense reimbursements according to Italian tax regulations (MEF Circular 41/2024).

### Request Flow

1. **User submits form** → `POST /nuova`
2. **Validation** (`validator.py`):
   - Required fields: employee, category, amount, date
   - Category-specific: days/km/nights based on type
   - Returns `(bool, reason)` tuple
3. **Calculation** (`calculator.py`):
   - Computes theoretical maximum based on daily rates × quantity
   - Applies monthly cap (€1,200 per employee per month)
   - Returns: (tax-exempt_amount, taxable_amount, details_dict)
4. **Storage** (`storage.py`):
   - Saves request to `data/richieste.json`
   - Sets state: "valida" (valid) or "respinta" (rejected)
5. **Response**: User sees calculation details or error message

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `app.py` | Flask routes, form handling, view rendering |
| `rules.py` | **Normative parameters** — daily rates, km rate, night rate, monthly cap |
| `calculator.py` | Tax-exempt vs. taxable amount split logic |
| `validator.py` | Input validation rules per category |
| `storage.py` | JSON persistence, monthly cap tracking per employee |
| `templates/` | Jinja2 HTML forms and pages |

### Key Concepts

**Categories** (6 types, each with different unit):
- `trasferta_italia`, `trasferta_estero`, `pasto` → per day
- `chilometrico` → per km
- `alloggio` → per night

**Calculation Rules**:
```
theoretical_max = unit_rate × quantity
exempt_proposed = min(amount, theoretical_max)
month_capacity = max(1200 - already_exempt_this_month, 0)
exempt_final = min(exempt_proposed, month_capacity)
taxable = amount - exempt_final
```

The **most restrictive limit wins**: rate limit, amount limit, or monthly cap.

## Fixed Amounts & Normative Parameters

All monetary limits are defined in `src/rules.py`. These are sourced from MEF Circular 41/2024:

| Parameter | Value | Type | Unit |
|-----------|-------|------|------|
| **Daily allowances** | | | |
| Travel in Italy | € 46.48 | Daily max | Per day |
| Travel abroad | € 77.47 | Daily max | Per day |
| Meal | € 8.00 | Daily max | Per day |
| **Usage-based rates** | | | |
| Mileage | € 0.42 | Rate | Per km |
| Lodging | € 150.00 | Daily max | Per night |
| **Caps** | | | |
| Monthly per employee | € 1,200.00 | Hard cap | Per calendar month |

All amounts use 2 decimal places (rounded to cents). The calculation applies the most restrictive limit: if an employee has already used €800 of their €1,200 monthly cap and submits a €500 request, only €400 is tax-exempt.

## Where to Change Things

| Need | File |
|------|------|
| Add/update tax rates | `src/rules.py` (MASSIMALI_* constants) |
| Add validation rule | `src/validator.py` (in `valida()` function) |
| Change calculation logic | `src/calculator.py` (in `calcola()` function) |
| Add a web page | `src/templates/` + route in `src/app.py` |
| Adjust monthly cap | `src/rules.py` (PLAFOND_MENSILE constant) |

## Data Structure

Requests stored as JSON objects in `data/richieste.json`:
```json
{
  "id": 1,
  "dipendente": "Maria Rossi",
  "data": "2025-01-15",
  "categoria": "trasferta_italia",
  "importo": 100.00,
  "giorni": 2,
  "km": null,
  "notti": null,
  "stato": "valida",
  "quota_esente": 92.96,
  "quota_imponibile": 7.04,
  "dettaglio": {
    "massimale_teorico": 92.96,
    "esente_teorica": 92.96,
    "capienza_plafond": 1200.00
  }
}
```

## Testing

- **calculator**: Tests the split logic with various amounts and categories
- **validator**: Tests rejection/acceptance of malformed requests
- **app**: Tests Flask routes with a test client and isolated JSON storage

Tests use `monkeypatch` to isolate storage (each test gets a temp JSON file).

## Code Style

This project follows these conventions:

**Language & Naming**:
- All code, variable names, docstrings, and comments are in **Italian** (project context: Italian tax law, Italian HR audience)
- Variables use snake_case: `quota_esente`, `gia_riconosciuta`, `categoria`

**Functions & Docstrings**:
- Keep docstrings concise (1–2 sentences) in English or Italian describing what, not how
- Return tuples for multiple values: `(bool, reason)` from validators, `(exempt, taxable, details)` from calculator
- Early returns for validation failures; avoid deep nesting

**Imports**:
```python
import json
from datetime import date
from pathlib import Path

from flask import Flask, request

from src import calculator, rules
```
Order: stdlib, third-party, local (src/). No wildcard imports.

**Data Structures**:
- Use dictionaries for request objects (not dataclasses or Pydantic models) — simple and JSON-compatible
- Float amounts rounded to 2 decimal places: `round(value, 2)`
- Dates stored as ISO strings: `"2025-01-15"`

**Comments**:
- Minimal comments; code should be self-explanatory via naming
- Add a comment only when the WHY is non-obvious (e.g., a regulatory constraint or subtle invariant)

**Type Hints**:
- Not used in this project. When adding code, match existing style (no type hints needed).

**Flask Routes**:
- Use `@app.get()` / `@app.post()` decorators (not `@app.route()`)
- Keep route logic lightweight; delegate to module functions (`validator.valida()`, `calculator.calcola()`, etc.)
- Return template renders with context dict, not raw JSON (except for data endpoints, of which there are none yet)

**Boundaries** Do not touch the stored requests in data/.
