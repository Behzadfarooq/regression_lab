# Solution

## Time spent
- Completed under 6 hours.
- Approximate effort: **3-4 hours**.

## Mental model (brief)
The service has three core entities: **Customer -> Order -> OrderItem**.

- Customer email is unique.
- Orders belong to customers and can be cancelled/archived.
- Order list and summary are business-facing endpoints.

Because these endpoints are connected, a side effect in one place can break unrelated behavior.

## Instability fixed (regression)

### Repro
1. Create a customer and an order.
2. Call `POST /api/orders/<id>/cancel/`.
3. Check the customer endpoint afterward.

Observed before fix: customer could disappear, causing unrelated customer reads to fail.

### Root cause
`orders/signals.py` had a `post_save` signal on `Order` that deleted the related customer when order status became `cancelled`.

- File: `orders/signals.py`
- Problematic behavior (before): cancelling order triggered `instance.customer.delete()`.

### Blast radius
- Customer records could be deleted as a side effect of order cancel.
- Customer endpoints became unreliable (404s / missing records).
- Since `Order.customer` uses `on_delete=CASCADE`, deleting a customer also risks cascading collateral data loss.

### Minimal safe fix
Kept the signal but removed destructive side effect for cancelled orders.

- Before: delete customer on cancelled status.
- After: return early (no-op) when status is cancelled.

This is a small, targeted change with low risk.

### Prevention
Regression test `orders/tests/test_regression_bug.py` now protects this path:

- cancel order via API
- assert response is 200
- assert customer still exists

## Tests added/updated
- Verified `orders/tests/test_regression_bug.py` passes after fix.
- Added `orders/tests/test_order_filters.py` for feature coverage:
  - status filter returns matching non-archived orders
  - email contains filter works
  - combined status + email filter works
  - invalid status returns 400
- Added a summary correctness test in `orders/tests/test_summary_perf.py` to lock paid-only, non-archived totals and descending ranking behavior.
- Full suite passes (`python manage.py test -v 2`).

## Feature shipped safely
Implemented **Option 2** on `GET /api/orders/`:

- `status` filter: `paid|draft|shipped|cancelled`
- `email` filter: case-insensitive contains match on customer email
- Validation for invalid status (returns 400)
- Query efficiency improvement for serialized list/detail responses by using:
  - `select_related("customer")`
  - `prefetch_related("items")`

## Performance evidence (before/after)
Bench method (same local machine):
- Used Django test client + `CaptureQueriesContext` in a one-off script.
- Seed payload benchmarked: `{"customers":50,"orders_per_customer":5,"items_per_order":3}`.
- Summary benchmarked: `GET /api/orders/summary/?limit=50`.

### Before
- Seed: **201**, ~**9236.39 ms**, **2551 queries**
- Summary: **200**, ~**65.56 ms**, **195 queries**

### After
- Seed: **201**, ~**138.36 ms**, **553 queries**
- Summary: **200**, ~**3.5 ms**, **1 query**

### What changed
1. `GET /api/orders/summary/?limit=50`
   - Replaced Python/N+1 loop with ORM aggregation.
   - Used filtered `Count` and `Sum` on paid + non-archived orders.
   - Kept output contract: `customer_id, email, order_count, total_cents` sorted by total desc.

2. `POST /api/dev/seed/`
   - Precomputed each order total in memory once.
   - Created `Order` with `total_cents` directly.
   - Used `bulk_create` for order items per order to avoid per-item save recalculation overhead.
   - Wrapped operation in `transaction.atomic()`.

### Bottlenecks + tradeoffs
- Original seed bottleneck: each `OrderItem.objects.create(...)` triggered model `save()` logic that re-read all order items repeatedly.
- Tradeoff: `bulk_create` bypasses `OrderItem.save()` hooks. We addressed correctness by setting `Order.total_cents` explicitly during seed creation.
- Summary endpoint is now DB-driven; much fewer queries and lower Python work.

## AWS system design
Proposed production setup (small startup, ready to grow):

1. Runtime choice: **ECS Fargate**
   - Why: container-based, no EC2 management, easy horizontal scaling, strong fit for Django API services.
   - Better long-term control than Elastic Beanstalk, less ops burden than EC2.

2. Core architecture
   - Route53 -> ALB -> ECS Fargate service (2+ tasks across AZs)
   - App containers run Django + Gunicorn
   - RDS Postgres (Multi-AZ in production)
   - CloudWatch logs + metrics

3. RDS Postgres connection considerations
   - Use connection pooling (`CONN_MAX_AGE` and/or RDS Proxy/PgBouncer)
   - Keep worker count aligned with DB max connections
   - Set query timeout and monitor slow queries

4. Cache/queue decisions
   - Add Redis (ElastiCache) for hot reads (for example summary caching if traffic increases)
   - Add SQS + worker (Celery/RQ) for async jobs (heavy seed-like jobs, emails, exports)

5. CI/CD (high-level)
   - GitHub Actions: lint + tests
   - Build Docker image, push to ECR
   - Deploy to ECS with rolling update
   - Run migrations as a controlled deployment step before traffic switch

6. Day-one metrics/alerts
   - API p95 latency (global + key endpoints like `/api/orders/summary/`)
   - 5xx error rate
   - Request volume / saturation
   - ECS task CPU + memory + restarts
   - RDS CPU + free storage + active connections
   - DB slow query count / duration
   - Queue depth + age (if SQS is used)
   - Cache hit ratio (if Redis is used)

## Risks / tradeoffs / next steps
### Risks / tradeoffs
- Seed optimization uses `bulk_create` for items, which bypasses model `save()` hooks.
  - Tradeoff accepted for performance in dev seed path.
- Seed email generation is deterministic (`user<id>@example.com`); concurrent seed calls can still collide.
- Summary now depends on `Order.total_cents` being correct.
  - If other future bulk item writes bypass recalculation, totals can drift.

### Next steps
1. Add a concurrency-safe seed strategy (retry on `IntegrityError` or unique suffix/UUID emails).
2. Add endpoint-level performance tests (query count thresholds) for summary and order list.
3. Add DB indexes for common filters (`status`, `is_archived`, `customer_id`, `customer.email`).
4. Protect `/api/dev/seed/` behind a dev-only flag/auth guard to prevent misuse.
5. Add a periodic data consistency check between order items and `Order.total_cents`.

## AI usage
- Used AI to quickly map code paths (models/views/signals/tests) and isolate regression root cause.
- Used AI to propose minimal safe patches first, then validate behavior with tests.
- Used AI to design feature tests for order list filters and invalid input handling.
- Used AI to propose ORM-based performance refactors and benchmark approach (time + query counts).
- Used AI to draft clear `SOLUTION.md` documentation and demo narration structure.
