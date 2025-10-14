# src/extraction/modules.py
from __future__ import annotations

import json
import logging
import re
import time
import os
from typing import Dict, List, Any

import dspy
from .signatures import ExtractReqs, ClassifyReq, GroundReq, BatchClassifyReq, BatchGroundReq

logger = logging.getLogger(__name__)

LOG_LLM = os.getenv("LOG_LLM", "0") in ("1","true","TRUE","yes","YES")
RAW_DIR = os.getenv("RAW_DUMP_DIR", "raw_llm")

def _flatten_dict(d: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
    """Recursively flatten nested dictionaries."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            # Flatten nested dict into parent level
            items.extend(_flatten_dict(v, '').items())
        else:
            items.append((k, v))
    return dict(items)

def _dump_raw(name: str, idx: int, payload: Any) -> None:
    if not LOG_LLM:
        return
    try:
        os.makedirs(RAW_DIR, exist_ok=True)
        p = os.path.join(RAW_DIR, f"{name}_{idx:06d}.txt")
        with open(p, "w", encoding="utf-8") as f:
            if isinstance(payload, (dict, list)):
                f.write(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                f.write(str(payload))
    except Exception as e:
        logger.warning("Failed to write raw dump %s: %s", name, e)

# -------------- Robust JSON helpers --------------
def _extract_json(text: str):
    if not text: raise ValueError("empty response")
    m = re.search(r"```json\s*(.+?)\s*```", text, flags=re.S|re.I)
    if m: return json.loads(m.group(1))
    m = re.search(r"```\s*(.+?)\s*```", text, flags=re.S)
    if m:
        try: return json.loads(m.group(1))
        except Exception: pass
    start = None
    for i,ch in enumerate(text):
        if ch in "{[": start = i; break
    if start is not None:
        for end in (text.rfind("}"), text.rfind("]")):
            if end != -1 and end > start:
                cand = text[start:end+1]
                try: return json.loads(cand)
                except Exception: pass
    raise ValueError("could not parse JSON from response")

def _safe_loads(s: str):
    try: return json.loads(s)
    except Exception: return _extract_json(s)

# -------------- Single-item modules (unchanged signatures) --------------
class Extractor(dspy.Module):
    """Extract requirements from a text chunk (single call per chunk)."""
    def __init__(self, retries: int = 2, retry_sleep: float = 0.5):
        super().__init__()
        self.pred = dspy.Predict(ExtractReqs)
        self.retries = retries
        self.retry_sleep = retry_sleep
        self._ctr = 0

    def forward(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        self._ctr += 1
        out = None
        try:
            out = self.pred(chunk_text=chunk["text"])
            raw = getattr(out, "requirements_json", None)
            _dump_raw("extract_requirements_json_raw", self._ctr, raw)
            result = _safe_loads(raw or "[]")
            if not isinstance(result, list):
                logger.warning("Extractor returned non-list: %s", type(result))
                return []
            logger.info("Extractor OK: %d items", len(result))
            return result
        except Exception as e:
            logger.error("Extractor parse fail: %s", e)
            if out is not None:
                logger.debug("Extractor raw field: %r", getattr(out, "requirements_json", None))

        # retries
        for r in range(self.retries):
            try:
                retry_text = (
                    chunk["text"]
                    + "\n\nReturn ONLY a JSON array of requirement objects. "
                      "Use strictly valid JSON (double-quoted keys/strings). No prose."
                )
                out = self.pred(chunk_text=retry_text)
                raw = getattr(out, "requirements_json", None)
                _dump_raw("extract_requirements_json_retry_raw", self._ctr, raw)
                result = _safe_loads(raw or "[]")
                if isinstance(result, list):
                    logger.info("Extractor retry %d OK: %d items", r + 1, len(result))
                    return result
            except Exception as e:
                logger.error("Extractor retry %d fail: %s", r + 1, e)
                time.sleep(self.retry_sleep)

        logger.warning("Extractor giving up for this chunk")
        return []

class Classifier(dspy.Module):
    """Classify and normalize a requirement object (single item)."""
    def __init__(self):
        super().__init__()
        self.pred = dspy.Predict(ClassifyReq)
        self._ctr = 0

    def forward(self, req: Dict[str, Any]) -> Dict[str, Any]:
        self._ctr += 1
        try:
            out = self.pred(req_json=json.dumps(req, ensure_ascii=False))
            raw = getattr(out, "classified_json", None)
            _dump_raw("classify_classified_json_raw", self._ctr, raw)
            result = _safe_loads(raw or "{}")
            if not isinstance(result, dict):
                logger.warning("Classifier returned non-dict: %s", type(result))
                return req
            logger.debug("Classifier OK")
            return result
        except Exception as e:
            logger.error("Classifier parse fail: %s", e)
            return req

class Grounder(dspy.Module):
    """Ground a requirement with evidence from source chunk (single item)."""
    def __init__(self, retries: int = 2, retry_sleep: float = 0.5):
        super().__init__()
        self.pred = dspy.Predict(GroundReq)
        self.retries = retries
        self.retry_sleep = retry_sleep
        self._ctr = 0

    def forward(self, chunk: Dict[str, Any], req: Dict[str, Any]) -> Dict[str, Any]:
        self._ctr += 1
        try:
            out = self.pred(
                chunk_text=chunk.get("text", ""),
                req_json=json.dumps(req, ensure_ascii=False),
            )
            raw = getattr(out, "grounded_json", None)
            _dump_raw("ground_grounded_json_raw", self._ctr, raw)
            result = _safe_loads(raw or "{}")
            if not isinstance(result, dict):
                logger.warning("Grounder returned non-dict: %s", type(result))
                return req
            logger.debug("Grounder OK")
            return result
        except Exception as e:
            logger.error("Grounder parse fail: %s", e)

        for r in range(self.retries):
            try:
                retry_text = (
                    chunk.get("text", "")
                    + "\n\nReturn ONLY a JSON object for the grounded requirement. "
                      "Use strictly valid JSON (double-quoted keys/strings). No prose."
                )
                out = self.pred(
                    chunk_text=retry_text,
                    req_json=json.dumps(req, ensure_ascii=False),
                )
                raw = getattr(out, "grounded_json", None)
                _dump_raw("ground_grounded_json_retry_raw", self._ctr, raw)
                result = _safe_loads(raw or "{}")
                if isinstance(result, dict):
                    logger.info("Grounder retry %d OK", r + 1)
                    return result
            except Exception as e:
                logger.error("Grounder retry %d fail: %s", r + 1, e)
                time.sleep(self.retry_sleep)

        logger.warning("Grounder giving up for this item")
        return req


# ---- keep existing imports / helpers at top of file ----
# _dump_raw, _safe_loads, etc.

class BatchClassifier(dspy.Module):
    """Classify N requirements in a single LM call with index echo and stable alignment."""
    def __init__(self, retries: int = 1, retry_sleep: float = 0.4):
        super().__init__()
        self.pred = dspy.Predict(BatchClassifyReq)
        self.retries = retries
        self.retry_sleep = retry_sleep
        self._ctr = 0

    def _run_once(self, reqs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # attach deterministic indices so we can re-align results
        reqs_with_idx = []
        for i, r in enumerate(reqs):
            # IMPORTANT: preserve metadata like _gidx by copying dict
            item = dict(r)
            item.setdefault("_idx", i)   # don't overwrite if already set
            reqs_with_idx.append(item)

        payload = json.dumps(reqs_with_idx, ensure_ascii=False)

        # strong instruction: same length/order, echo _idx
        prompt_payload = (
            payload
            + "\n\nInstructions: For each input object, return ONE classified object in the SAME order, "
              "and include the `_idx` field UNCHANGED so we can match them back. "
              "Return ONLY a JSON array. No prose."
        )

        out = self.pred(reqs_json=prompt_payload)
        raw = getattr(out, "classified_json", None)
        _dump_raw("batch_classify_raw", self._ctr, raw)
        result = _safe_loads(raw or "[]")
        if not isinstance(result, list):
            raise ValueError("BatchClassifier: model returned non-list")

        # Build result-by-idx map
        by_idx = {}
        for j, obj in enumerate(result):
            if isinstance(obj, dict) and "_idx" in obj:
                by_idx[int(obj["_idx"])] = obj
            else:
                # Fallback: if _idx missing, map by position
                by_idx[j] = obj if isinstance(obj, dict) else {}

        # Re-align and MERGE: original first, then model fields overwrite/add
        merged = []
        for i, orig in enumerate(reqs_with_idx):
            classified = by_idx.get(i, {})
            # FLATTEN any nested dicts before merging
            classified = _flatten_dict(classified)
            merged_item = dict(orig)
            merged_item.update(classified)
            # ensure _idx remains the current i
            merged_item["_idx"] = i
            merged.append(merged_item)

        return merged

    def forward(self, reqs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self._ctr += 1
        try:
            return self._run_once(reqs)
        except Exception as e:
            logger.error("BatchClassifier parse fail: %s", e)

        # single retry with the same instruction (model sometimes needs two shots)
        time.sleep(self.retry_sleep)
        try:
            out = self._run_once(reqs)
            logger.info("BatchClassifier retry OK")
            return out
        except Exception as e:
            logger.error("BatchClassifier retry fail: %s", e)
            # FINAL FALLBACK: return EMPTY to signal total failure
            logger.warning(f"BatchClassifier SKIPPING {len(reqs)} items due to parse failures")
            return []


class BatchGrounder(dspy.Module):
    """Ground N requirements for a single chunk in one call with index echo and stable alignment."""
    def __init__(self, retries: int = 1, retry_sleep: float = 0.4):
        super().__init__()
        self.pred = dspy.Predict(BatchGroundReq)
        self.retries = retries
        self.retry_sleep = retry_sleep
        self._ctr = 0

    def _run_once(self, chunk: Dict[str, Any], reqs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # attach indices for alignment
        reqs_with_idx = []
        for i, r in enumerate(reqs):
            item = dict(r)
            item.setdefault("_idx", i)
            reqs_with_idx.append(item)

        payload = json.dumps(reqs_with_idx, ensure_ascii=False)

        prompt_payload = (
            "Use the provided chunk_text to ground each requirement (provide page/quote/section if applicable). "
            "For EVERY input object, return ONE grounded object in the SAME order and include `_idx` unchanged. "
            "Return ONLY a JSON array. No prose.\n\n"
            + payload
        )

        out = self.pred(chunk_text=chunk.get("text", ""), reqs_json=prompt_payload)
        raw = getattr(out, "grounded_json", None)
        _dump_raw("batch_ground_raw", self._ctr, raw)
        result = _safe_loads(raw or "[]")
        if not isinstance(result, list):
            raise ValueError("BatchGrounder: model returned non-list")

        # Build result-by-idx map
        by_idx = {}
        for j, obj in enumerate(result):
            if isinstance(obj, dict) and "_idx" in obj:
                by_idx[int(obj["_idx"])] = obj
            else:
                by_idx[j] = obj if isinstance(obj, dict) else {}

        # Re-align & MERGE to preserve metadata (e.g., _gidx)
        merged = []
        for i, orig in enumerate(reqs_with_idx):
            grounded = by_idx.get(i, {})
            grounded = _flatten_dict(grounded)
            merged_item = dict(orig)
            merged_item.update(grounded)
            merged_item["_idx"] = i
            merged.append(merged_item)

        return merged

    def forward(self, chunk: Dict[str, Any], reqs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self._ctr += 1
        try:
            return self._run_once(chunk, reqs)
        except Exception as e:
            logger.error("BatchGrounder parse fail: %s", e)

        # retry once
        time.sleep(self.retry_sleep)
        try:
            out = self._run_once(chunk, reqs)
            logger.info("BatchGrounder retry OK")
            return out
        except Exception as e:
            logger.error("BatchGrounder retry fail: %s", e)
            # FINAL FALLBACK: return EMPTY to signal total failure
            logger.warning(f"BatchGrounder SKIPPING {len(reqs)} items due to parse failures")
            return []

