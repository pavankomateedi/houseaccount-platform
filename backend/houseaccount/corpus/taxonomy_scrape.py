"""Optional one-time fetch of TaskRabbit's *public category list only*.

Per the project decisions: we scrape only the public service-category taxonomy
(not message data), one time, and we COMMIT a synthetic fallback so the build is
fully reproducible offline and never depends on a live request at run/test time.

Run manually with ``python -m houseaccount.corpus.taxonomy_scrape`` to attempt a
refresh; on any failure the committed ``data/taxonomy.json`` is left untouched.
This is intentionally not invoked by the app, the generator, or the tests.
"""

from __future__ import annotations

import re

import httpx

# TaskRabbit exposes its service categories on its public services page. We only
# read category *names* — never user content. If this DOM/endpoint changes or is
# blocked, we fall back to the committed taxonomy.
_SERVICES_URL = "https://www.taskrabbit.com/services"
_TIMEOUT = 8.0


def fetch_public_categories() -> list[str]:
    """Best-effort fetch of public category labels. Raises on any failure."""
    resp = httpx.get(_SERVICES_URL, timeout=_TIMEOUT, follow_redirects=True)
    resp.raise_for_status()
    # Categories appear as link/heading text; extract candidate labels heuristically.
    candidates = re.findall(r">([A-Z][A-Za-z &/]{3,40})<", resp.text)
    cleaned = sorted({c.strip() for c in candidates if " " in c or c.isalpha()})
    if not cleaned:
        raise RuntimeError("no categories parsed from TaskRabbit services page")
    return cleaned


def main() -> None:
    try:
        cats = fetch_public_categories()
    except Exception as exc:  # noqa: BLE001 — any failure must degrade gracefully
        print(f"[taxonomy_scrape] live fetch failed ({exc}); keeping committed fallback.")
        return
    print(f"[taxonomy_scrape] fetched {len(cats)} public categories from TaskRabbit:")
    for c in cats:
        print(f"  - {c}")
    print(
        "\nReview these against data/taxonomy.json. Mapping to canonical service "
        "keys is left manual on purpose — the committed list stays the source of truth."
    )


if __name__ == "__main__":
    main()
