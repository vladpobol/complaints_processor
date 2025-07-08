from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, List, Tuple

import httpx

BASE_URL = "http://localhost:8000"  # override via CLI arg

# Allowed sentiment values according to API spec
ALLOWED_SENTIMENTS = {"positive", "negative", "neutral", "unknown"}

# Test cases: (text, expected_category)
TEST_CASES: List[Tuple[str, str]] = [
    ("Сайт не открывается, ошибка 500", "technical"),
    ("Деньги списали дважды", "payment"),
    ("Спасибо, всё отлично", "other"),
]


def parse_base_url() -> str:
    """Return base url from CLI arg or default."""
    if len(sys.argv) > 1:
        return sys.argv[1].rstrip("/")
    return BASE_URL


async def main() -> None:  # noqa: D401
    base_url = parse_base_url()
    async with httpx.AsyncClient(base_url=base_url, timeout=20) as client:
        created_ids: List[int] = []

        # 1) Create complaints for each test case and assert response fields
        for text, expected_category in TEST_CASES:
            print(f"Creating complaint expecting category '{expected_category}'…")
            resp = await client.post("/complaints", json={"text": text})
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

            # Basic field assertions
            assert data["text"] == text, "Stored text mismatch"
            assert data["status"] == "open", "Status should be open at creation"
            assert data["category"] == expected_category, (
                f"Category mismatch: expected {expected_category}, got {data['category']}"
            )
            assert (
                data["sentiment"] in ALLOWED_SENTIMENTS
            ), f"Unexpected sentiment {data['sentiment']}"

            created_ids.append(data["id"])
            print("Created OK:", json.dumps(data, ensure_ascii=False, indent=2))

        # 2) Verify list endpoint with status filter returns all created items
        print("\nListing open complaints…")
        resp = await client.get("/complaints", params={"status": "open"})
        resp.raise_for_status()
        open_list = resp.json()
        open_ids = {c["id"] for c in open_list}
        assert set(created_ids).issubset(open_ids), "Not all open complaints returned"
        print(json.dumps(open_list, ensure_ascii=False, indent=2))

        # 4) Close all complaints and assert status change
        print("\nClosing complaints…")
        for cid in created_ids:
            resp = await client.patch(f"/complaints/{cid}", json={"status": "closed"})
            resp.raise_for_status()
            closed = resp.json()
            assert closed["status"] == "closed", "Failed to close complaint"
            print(f"Closed id={cid}")

        # 5) Ensure no created complaints remain open
        print("\nVerifying no open complaints remain…")
        resp = await client.get("/complaints", params={"status": "open"})
        resp.raise_for_status()
        remaining_open = {c["id"] for c in resp.json()}
        assert not (set(created_ids) & remaining_open), "Some complaints are still open"

    print("\n✅ Comprehensive smoke test finished successfully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as exc:  # noqa: BLE001
        print("❌ Smoke test failed:", exc)
        sys.exit(1) 