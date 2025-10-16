#!/usr/bin/env python3
"""
HigherGov quick test using searchID (preferred workflow).

Usage:
  python scripts/test_highergov_quick.py <searchID-or-url> [--days 180] [--page-size 5] [--source sam] [--list-docs]

Examples:
  # raw searchID copied from the HigherGov URL
  python scripts/test_highergov_quick.py C7qcfx_hxvUqRbQhIpheO

  # full HigherGov URL (script extracts ?searchID=...)
  python scripts/test_highergov_quick.py "https://www.highergov.com/contract-opportunity/?searchID=C7qcfx_hxvUqRbQhIpheO"

Env:
  HIGHERGOV_API_KEY must be set (e.g., via .env)
"""
from __future__ import annotations

import os
import sys
import re
import argparse
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs

import requests

try:
    import dotenv  # optional convenience
    dotenv.load_dotenv()
except Exception:
    pass


BASE = os.getenv("HIGHERGOV_BASE", "https://www.highergov.com").rstrip("/")
API_PREFIX = os.getenv("HIGHERGOV_API_PREFIX", "/api-external").rstrip("/")
OPPORTUNITY_EP = f"{BASE}{API_PREFIX}/opportunity/"
DOCUMENT_EP = f"{BASE}{API_PREFIX}/document/"

DEFAULT_SOURCE = "sam"
TIMEOUT = 30


def iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()


def extract_search_id(arg: str) -> str | None:
    """Return searchID if arg is a HigherGov URL; otherwise return arg as-is if it *looks* like a searchID."""
    if "highergov.com" in arg:
        try:
            qs = parse_qs(urlparse(arg).query)
            return (qs.get("searchID") or qs.get("searchId") or [None])[0]
        except Exception:
            return None
    # Heuristic: searchIDs are short URL-safe tokens (letters, digits, _ -)
    if re.fullmatch(r"[A-Za-z0-9_\-]{8,}", arg):
        return arg
    return None


def get_api_key() -> str:
    key = os.getenv("HIGHERGOV_API_KEY")
    if not key:
        raise SystemExit("❌ HIGHERGOV_API_KEY not set (create .env or export the var).")
    return key


def call_opportunity_search(api_key: str, search_id: str, source_type: str, captured_since: str, page_size: int) -> dict:
    params = {
        "api_key": api_key,
        "search_id": search_id,
        "source_type": source_type,   # recommended with search_id
        "captured_date": captured_since,  # recommended with search_id
        "page_size": page_size,
    }
    r = requests.get(OPPORTUNITY_EP, params=params, timeout=TIMEOUT)
    try:
        data = r.json()
    except Exception:
        raise SystemExit(f"❌ Non-JSON response ({r.status_code}): {r.text[:200]}")
    if r.status_code != 200:
        raise SystemExit(f"❌ HTTP {r.status_code}: {data}")
    return data


def call_document_list(api_key: str, document_path: str) -> dict:
    # document_path may be a full URL or a relative /api-external/... path
    if document_path.startswith("http"):
        url = document_path
        params = {"api_key": api_key}
    else:
        url = f"{BASE}{document_path}"
        params = {"api_key": api_key}
    r = requests.get(url, params=params, timeout=TIMEOUT)
    try:
        data = r.json()
    except Exception:
        raise SystemExit(f"❌ Non-JSON response from Document endpoint ({r.status_code}): {r.text[:200]}")
    if r.status_code != 200:
        raise SystemExit(f"❌ Document endpoint HTTP {r.status_code}: {data}")
    return data


def pretty_print_opportunity(first: dict) -> None:
    fields = [
        ("title", "Title"),
        ("solicitation_number", "Solicitation #"),
        ("agency_name", "Agency"),
        ("posted_date", "Posted"),
        ("close_date", "Close"),
        ("source_type", "Source"),
    ]
    for k, label in fields:
        v = first.get(k, "—")
        print(f"  {label}: {v}")


def main():
    parser = argparse.ArgumentParser(description="Quick test of HigherGov Opportunity API using searchID.")
    parser.add_argument("searchid_or_url", help="HigherGov searchID (e.g., C7qcfx_hxvUqRbQhIpheO) or full URL containing ?searchID=")
    parser.add_argument("--days", type=int, default=180, help="Captured date window (days back). Default: 180")
    parser.add_argument("--page-size", type=int, default=5, help="How many records to return (preview). Default: 5")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help=f"source_type filter. Default: {DEFAULT_SOURCE}")
    parser.add_argument("--list-docs", action="store_true", help="Also call the document list endpoint to preview filenames.")
    args = parser.parse_args()

    api_key = get_api_key()

    search_id = extract_search_id(args.searchid_or_url)
    if not search_id:
        raise SystemExit("❌ Could not determine a valid searchID. Paste the raw searchID (e.g., C7qcfx_hxvUqRbQhIpheO) or a HigherGov URL with ?searchID=...")

    captured_since = iso_days_ago(args.days)

    print("🧪 HigherGov SearchID Quick Test")
    print("=" * 60)
    print(f"search_id:        {search_id}")
    print(f"source_type:      {args.source}")
    print(f"captured_date >=  {captured_since}")
    print(f"page_size:        {args.page_size}")
    print("=" * 60)

    # 1) Query Opportunity list using search_id (+ source_type + captured_date) — recommended by docs
    #    Ref: docs.highergov.com/import-and-export/api (Using the search_id Parameter)
    try:
        data = call_opportunity_search(
            api_key=api_key,
            search_id=search_id,
            source_type=args.source,
            captured_since=captured_since,
            page_size=args.page_size,
        )
    except SystemExit as e:
        print(e)
        sys.exit(1)

    count = data.get("count")
    results = data.get("results") or []
    print(f"\n✅ Opportunity endpoint OK — count={count}, returned={len(results)}")

    if not results:
        print("\n⚠️  No results. Try:\n  • Increasing --days (e.g., --days 365)\n  • Verifying the searchID from the HigherGov URL\n  • Adjusting --source (sam / sled / etc.)")
        sys.exit(2)

    # Show first hit
    first = results[0]
    print("\n— First result —")
    pretty_print_opportunity(first)

    doc_path = first.get("document_path")
    print(f"\nDocument path: {doc_path or '—'}")
    if not doc_path:
        print("⚠️  No document_path on this record. It may not have downloadable documents.")
    elif args.list_docs:
        # 2) Optionally show file list (filenames only). Download URLs are short-lived per docs.
        #    The docs recommend downloading promptly after retrieving them.
        try:
            doc_idx = call_document_list(api_key, doc_path)
            docs = doc_idx.get("results") or doc_idx.get("documents") or []
            if not docs:
                print("\n📄 No documents found on the document endpoint.")
            else:
                print("\n📄 Documents (first few):")
                for f in docs[:10]:
                    fname = f.get("file_name") or f.get("name") or "(unnamed)"
                    print(f"  - {fname}")
                if len(docs) > 10:
                    print(f"  … and {len(docs) - 10} more")
        except SystemExit as e:
            print(e)
            sys.exit(3)

    print("\n🎉 Done.")


if __name__ == "__main__":
    main()
