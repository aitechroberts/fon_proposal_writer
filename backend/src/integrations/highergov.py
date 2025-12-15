# backend/src/integrations/highergov.py
"""HigherGov integration module - re-exports from old_highergov."""

from .old_highergov import ingest_highergov_opportunity

__all__ = ["ingest_highergov_opportunity"]

