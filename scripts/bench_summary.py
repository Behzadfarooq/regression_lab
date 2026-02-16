import os
import sys
import time
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "regression_lab.settings")

    import django

    django.setup()

    from django.db import connection
    from django.test import Client
    from django.test.utils import CaptureQueriesContext

    c = Client()

    t0 = time.perf_counter()
    with CaptureQueriesContext(connection) as q:
        r = c.get("/api/orders/summary/?limit=50")

    ms = (time.perf_counter() - t0) * 1000
    print(
        "summary_status=",
        r.status_code,
        "ms=",
        round(ms, 2),
        "queries=",
        len(q),
    )


if __name__ == "__main__":
    main()
