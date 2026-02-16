# Regression Lab (Django + DRF)

This repo is a small, intentionally imperfect Django/DRF service used for hiring screens.
It includes:
- A **real regression bug** (one feature breaks unrelated behavior)
- A **slow endpoint** that needs performance work
- A tiny front-end page (vanilla JS) to poke endpoints quickly

## Quick start

**Prereqs:** Python 3.10+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Seed data

Option A (UI button): `Seed sample data`

Option B (curl):

```bash
curl -X POST http://127.0.0.1:8000/api/dev/seed/ \
  -H "Content-Type: application/json" \
  -d '{"customers":200,"orders_per_customer":8,"items_per_order":4}'
```

## Run tests

```bash
python manage.py test
```

Note: One test is expected to fail initially because the repo contains an intentional regression bug.


## Notes
- Fixed routing so `/api/orders/summary/` works.
- Made the seeder resilient to deleted customers by using max(id) instead of count().
