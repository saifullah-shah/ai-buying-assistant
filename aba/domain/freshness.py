"""Deterministic freshness policy for seller offers.

Key design points (see PROJECT_BRIEF §12: "Show current prices with source and observation
time. Apply a freshness policy and recheck where supported before describing an offer as
current."):

- ``freshness()`` is pure — it accepts ``now`` as an injected parameter so tests do not
  depend on the wall clock.
- Returns one of ``FRESH`` / ``STALE`` / ``UNKNOWN``.
- ``STALE`` when the offer's ``observed_at`` is older than the configured TTL.
- ``UNKNOWN`` when ``observed_at`` is absent or unparseable (naive datetime is already
  rejected at the model level, but we guard here too).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum


class FreshnessStatus(Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


def freshness(
    observed_at: datetime,
    *,
    now: datetime | None = None,
    ttl_seconds: int = 86_400,  # 24 hours default
) -> FreshnessStatus:
    """Determine whether an offer's price observation is fresh.

    Args:
        observed_at: The offer's ``observed_at`` datetime (must be timezone-aware UTC).
        now: The "current" time for comparison.  Defaults to ``datetime.now(timezone.utc)``.
            Inject a fixed time to make tests deterministic.
        ttl_seconds: How old an observation can be before it is considered stale.
            Default 24 hours (86_400 seconds).

    Returns:
        ``FreshnessStatus.FRESH`` if ``now - observed_at <= ttl_seconds``,
        ``FreshnessStatus.STALE`` if older, and ``FreshnessStatus.UNKNOWN`` if
        ``observed_at`` is None or lacks timezone info.
    """
    ref_time = now if now is not None else datetime.now(timezone.utc)

    if observed_at is None:
        return FreshnessStatus.UNKNOWN

    # observed_at should already be validated as tz-aware by the model, but guard anyway.
    if observed_at.tzinfo is None:
        return FreshnessStatus.UNKNOWN

    age = (ref_time - observed_at).total_seconds()
    if age <= 0:
        # observed_at is in the future — treat as fresh (or UNKNOWN depending on policy);
        # here we choose FRESH because the observation is "newer than now".
        return FreshnessStatus.FRESH

    if age <= ttl_seconds:
        return FreshnessStatus.FRESH
    return FreshnessStatus.STALE