# Take-home Assignment — Regression + Performance (Django/JS/AWS)

**Timebox:** 2–3 hours (hard stop).  
**Goal:** show practical engineering judgment: fix regressions safely, add a feature without breaking things, and improve performance with evidence.

You are given a small Django + DRF service. It has:
- An **intentional regression bug**
- An **intentionally slow summary endpoint**
- A minimal UI to trigger behaviors quickly

## What to submit
- A link to your repo (GitHub) OR a zip of your solution
- A short `SOLUTION.md` that includes:
  - Root cause analysis (what broke and why)
  - What you changed, and why it’s safe
  - Evidence of performance improvements (before/after)
  - Any tradeoffs / follow-ups you would do in production

## Part A — Fix the regression bug (must-have)
**Repro:** cancel an order via:

- UI: “Cancel an order”
- API: `POST /api/orders/<id>/cancel/`

**Observed:** a customer-related endpoint starts failing unexpectedly.  
**Your tasks:**
1) Identify the root cause (write it down in `SOLUTION.md`)
2) Fix it in a minimal, safe way
3) Add/adjust tests so this regression can’t happen again  
   - A test already exists (`orders/tests/test_regression_bug.py`) and currently fails.

**Success criteria:**
- All tests pass
- Cancelling an order does not break customer endpoints

## Part B — Add a small feature safely (must-have)
Add **one** small feature that forces you to touch existing logic without creating regressions.

Choose **one**:
1) **Customer Orders endpoint:** `GET /api/customers/<id>/orders/`  
   Return the customer’s orders with items, with attention to query efficiency.
2) **Search + filter:** add filters to `GET /api/orders/`  
   - support: `status=paid|draft|shipped|cancelled`, `email=<customer email contains>`
   - ensure it doesn't re-introduce N+1 issues
3) **Soft-delete orders:** add `is_deleted` and hide from lists by default, but keep retrievable by id.

**Success criteria:**
- Feature works and is tested
- You don’t break existing behavior
- You don’t “rewrite the whole app” to do it

## Part C — Improve performance (must-have)
Endpoint: `GET /api/orders/summary/?limit=50`

It’s intentionally slow (N+1 queries + Python aggregation).

**Your tasks:**
1) Make it meaningfully faster using Django ORM best practices:
   - `select_related`, `prefetch_related`, aggregation, annotations, etc.
2) Provide evidence:
   - Before/after timing (rough is fine)
   - Before/after query count (ideal)

**Success criteria:**
- Your version is demonstrably faster
- Code is still readable and correct

## Part D — Short system design (15–20 min max)
In `SOLUTION.md`, answer:

> You need to run this on AWS for a small startup that expects growth.
> Describe a simple, production-ready architecture and what you’d monitor.

Include:
- App runtime (ECS/Fargate or Elastic Beanstalk or EC2) and why
- DB (RDS Postgres) and connection concerns
- Cache/queue if relevant (Redis/SQS)
- CI/CD approach
- 5–8 key metrics/alerts (p95 latency, error rate, DB slow queries, queue depth, etc.)

## What we evaluate
- Debugging discipline (repro, isolate, fix)
- Regression prevention (tests + safe changes)
- Performance thinking (evidence-based)
- Clarity of communication (SOLUTION.md)
- Engineering judgment (no overengineering)

Good luck — ship it safely.
