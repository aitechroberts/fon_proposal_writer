# highergov.py
# -*- coding: utf-8 -*-
"""
HigherGov API integration: resolve user-supplied keys (HigherGov URL with searchID,
SAM-style solicitation numbers like "RFQ1781397", or numeric SAM notice IDs) to an
Opportunity via the list endpoint, then pivot to the Document endpoint to download files.

Env vars (set via .env or your config system):
  - HIGHERGOV_API_KEY=...
  - HIGHERGOV_BASE=https://www.highergov.com
  - HIGHERGOV_API_PREFIX=/api-external
  - JOB_SAMPLE_RATE=0.1              # (optional) used elsewhere for tracing head-sampling

References:
- API overview & usage notes incl. 60-min expiry of document download_url. :contentReference[oaicite:1]{index=1}
- Live OpenAPI UI (Opportunity list & Document list endpoints). :contentReference[oaicite:2]{index=2}
"""
from __future__ import annotations

import os
import re
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse, parse_qs

import requests


# ---------------------------
# Configuration / Endpoints
# ---------------------------

BASE = os.getenv("HIGHERGOV_BASE", "https://www.highergov.com").rstrip("/")
API_PREFIX = os.getenv("HIGHERGOV_API_PREFIX", "/api-external").rstrip("/")
API_KEY = os.getenv("HIGHERGOV_API_KEY", "")

OPPORTUNITY_EP = f"{BASE}{API_PREFIX}/opportunity/"
DOCUMENT_EP = f"{BASE}{API_PREFIX}/document/"


# ---------------------------
# Errors
# ---------------------------

class HigherGovError(RuntimeError):
    """Generic HigherGov client error."""


class HigherGovNotFound(HigherGovError):
    """No opportunity found for the provided key/filters."""


class HigherGovAuthError(HigherGovError):
    """API key missing or invalid."""


# ---------------------------
# HTTP helpers
# ---------------------------

def _json_or_error(resp: requests.Response, url: str) -> Dict[str, Any]:
    try:
        data = resp.json()
    except Exception:
        raise HigherGovError(f"Non-JSON response {resp.status_code} from {url}")
    if resp.status_code == 401 or resp.status_code == 403:
        raise HigherGovAuthError(f"{resp.status_code} auth error: {data}")
    if resp.status_code != 200:
        raise HigherGovError(f"{resp.status_code} error: {data}")
    return data


def _get(url: str, params: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
    # HigherGov expects API key as query param
    p = dict(params or {})
    p.setdefault("api_key", API_KEY)
    r = requests.get(url, params=p, timeout=timeout)
    return _json_or_error(r, url)


# ---------------------------
# Utility helpers
# ---------------------------

_SAFE_CHARS = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_filename(name: str) -> str:
    """Sanitize filenames for filesystem portability."""
    name = _SAFE_CHARS.sub("_", name).strip("_")
    return name[:180] or "file"


def _captured_date_since(days: int = 180) -> str:
    """ISO date (UTC) used to scope recency for list queries."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()


def _is_pure_digits(s: str) -> bool:
    return s.isdigit()


def _maybe_extract_search_id(user_key: str) -> Optional[str]:
    """If a HigherGov URL with ?searchID=... is pasted, extract it."""
    if "highergov.com" not in user_key:
        return None
    try:
        qs = parse_qs(urlparse(user_key).query)
        return (qs.get("searchID") or qs.get("searchId") or [None])[0]
    except Exception:
        return None


# ---------------------------
# Core lookup
# ---------------------------

def fetch_opportunity_record(user_key: str,
                             *,
                             source_type: str = "sam",
                             captured_days: int = 180) -> Dict[str, Any]:
    """
    Resolve a user-supplied key to a single Opportunity record using the list endpoint.

    Behavior:
      1) If user_key is a HigherGov URL with ?searchID=..., prefer search_id (scoped by source_type & recency).
      2) Else attempt filter-based lookup:
           - alphanumeric (e.g., RFQ1781397)  -> solicitation_number
           - pure digits (e.g., 1781397)      -> notice_id
           - also try sam_notice_id
         All attempts include source_type=<source_type> and captured_date since <captured_days> days ago.
    Returns:
      The first record from the API.
    Raises:
      HigherGovNotFound | HigherGovAuthError | HigherGovError
    """
    if not API_KEY:
        raise HigherGovAuthError("HIGHERGOV_API_KEY not set")

    key = (user_key or "").strip()
    if not key:
        raise HigherGovError("Empty opportunity key")

    base = {
        "api_key": API_KEY,
        "page_size": 1,
        "captured_date": _captured_date_since(captured_days),
    }

    # 1) search_id path (best-practice for reproducing UI finds)  :contentReference[oaicite:3]{index=3}
    search_id = _maybe_extract_search_id(key)
    if search_id:
        params = dict(base)
        params.update({"search_id": search_id, "source_type": source_type})
        data = _get(OPPORTUNITY_EP, params)
        results = data.get("results") or []
        if results:
            return results[0]

    # 2) Filter-based lookups on Opportunity list
    attempts: List[Dict[str, Any]] = []

    if _is_pure_digits(key):
        # Numeric SAM notice id
        attempts.append({"notice_id": key, "source_type": source_type})
        attempts.append({"sam_notice_id": key, "source_type": source_type})
    else:
        # Likely a solicitation number (RFQ..., N00..., 36C..., etc.)
        attempts.append({"solicitation_number": key, "source_type": source_type})
        # Sometimes users paste with spaces or dashes; try a compacted variant
        compact = re.sub(r"[\s\-]+", "", key)
        if compact != key:
            attempts.append({"solicitation_number": compact, "source_type": source_type})

    # You can optionally add a very narrow keyword as a last resort:
    # attempts.append({"q": key, "source_type": source_type})

    for attempt in attempts:
        params = dict(base)
        params.update(attempt)
        data = _get(OPPORTUNITY_EP, params)
        results = data.get("results") or []
        if results:
            return results[0]

    raise HigherGovNotFound(
        f"No opportunity found for '{user_key}'. "
        f"Tried search_id (if present) and SAM-scoped filters."
    )


def fetch_document_index(document_path: str) -> Dict[str, Any]:
    """
    Retrieve the document index for an opportunity via its document_path.
    The response should contain one or more file objects with a time-limited 'download_url'
    (HigherGov notes these links expire ~60 minutes after issuance). :contentReference[oaicite:4]{index=4}
    """
    if not API_KEY:
        raise HigherGovAuthError("HIGHERGOV_API_KEY not set")

    # document_path is typically a fully formed path (with its own query). Always pass api_key.
    if document_path.startswith("http"):
        url = document_path
        params: Dict[str, Any] = {}
    else:
        url = f"{BASE}{document_path}"
        params = {}

    return _get(url, params)


def download_opportunity_files(user_key: str,
                               target_dir: Path,
                               *,
                               source_type: str = "sam",
                               captured_days: int = 180,
                               chunk_size: int = 1024 * 256) -> List[Path]:
    """
    Resolve the opportunity (via user_key), fetch its document index, and download each file.
    Returns the list of saved file paths.
    """
    rec = fetch_opportunity_record(user_key, source_type=source_type, captured_days=captured_days)
    doc_path = rec.get("document_path")
    if not doc_path:
        raise HigherGovError(f"Opportunity has no document_path: {user_key}")

    idx = fetch_document_index(doc_path)
    files = idx.get("results") or idx.get("documents") or []

    saved: List[Path] = []
    target_dir.mkdir(parents=True, exist_ok=True)

    for i, f in enumerate(files, 1):
        url = f.get("download_url")
        if not url:
            continue
        name = f.get("file_name") or f.get("name") or f"file_{i}"
        fname = _safe_filename(name)
        # If no extension on the name, attempt to infer from the URL path
        if "." not in Path(fname).name:
            inferred_ext = Path(url.split("?", 1)[0]).suffix
            if inferred_ext:
                fname = f"{fname}{inferred_ext}"

        out = target_dir / fname

        # Stream to disk
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(out, "wb") as fp:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        fp.write(chunk)

        saved.append(out)

    if not saved:
        # The docs stress that download_url is short-lived; users might have delayed. :contentReference[oaicite:5]{index=5}
        raise HigherGovError(
            "No files downloaded from document index. Links may have expired; "
            "refresh the Document endpoint and retry within ~60 minutes."
        )
    return saved


def ingest_highergov_opportunity(user_key: str,
                                 *,
                                 inputs_root: Path = Path("data/inputs"),
                                 source_type: str = "sam",
                                 captured_days: int = 180) -> List[Path]:
    """
    High-level helper: downloads all files for an opportunity into data/inputs/<job_id>/
    where <job_id> is the user_key (sanitized). Returns list of saved paths.
    """
    job_id = _safe_filename(user_key)
    target = inputs_root / job_id
    return download_opportunity_files(
        user_key, target, source_type=source_type, captured_days=captured_days
    )
