"""Rolling per-model LLM request counters.

Deliberately Redis rather than a Postgres table: this increments on the hot
path of every LLM call, and it answers a *rolling* "last hour / last day"
question that self-expiring keys handle for free. A table would need a
migration, a write per call, and its own cleanup sweep in the beat schedule
to say the same thing. The tradeoff is that counters don't survive a Redis
flush -- acceptable for a diagnostics panel, and it's the same Redis Celery
already can't run without.

Counts are per *model*, not per provider, since that's what the Settings
panel lists and what a deployment actually changes when tuning cost. Only
requests that came back successfully are recorded -- "handled" shouldn't
include a call the model never answered.

Buckets are one minute wide, which is what makes both windows genuinely
rolling: the last hour is the newest 60 buckets, the last day the newest
1440, rather than "whatever has accumulated in the current clock hour".
"""

import logging
import time
from functools import lru_cache

import redis as redis_lib

from app.config import get_settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "shoebill:llm:req"
_HOUR_MINUTES = 60
_DAY_MINUTES = 24 * 60
# A full day of lookback plus slack, so the oldest bucket a query asks for
# is still alive when it asks.
_BUCKET_TTL_SECONDS = 25 * 3600


@lru_cache(maxsize=1)
def _client() -> redis_lib.Redis:
    return redis_lib.from_url(
        get_settings().redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True,
    )


def _bucket(now: float | None = None) -> int:
    return int((now if now is not None else time.time()) // 60)


def _key(model: str, minute: int) -> str:
    return f"{_KEY_PREFIX}:{model}:{minute}"


def record_request(model: str, count: int = 1) -> None:
    """Record `count` successful requests against `model`. Best-effort:
    telemetry must never be the reason an LLM call fails, so every error
    here is swallowed."""
    if not model or count <= 0:
        return
    try:
        key = _key(model, _bucket())
        pipe = _client().pipeline()
        pipe.incrby(key, count)
        pipe.expire(key, _BUCKET_TTL_SECONDS)
        pipe.execute()
    except Exception:
        logger.debug("Could not record LLM request count for %s", model, exc_info=True)


def request_counts(models: list[str]) -> dict[str, dict[str, int]]:
    """{model: {"hour": n, "day": n}} over rolling windows ending now.

    Zeros (not an error) when Redis is unreachable -- this feeds a settings
    panel that already reports Redis health separately, so failing the whole
    response over missing telemetry would be the wrong trade.
    """
    out = {m: {"hour": 0, "day": 0} for m in models if m}
    if not out:
        return out

    now = _bucket()
    minutes = [now - i for i in range(_DAY_MINUTES)]
    try:
        client = _client()
    except Exception:
        logger.debug("Could not reach Redis for LLM request counts", exc_info=True)
        return out

    for model in out:
        try:
            raw = client.mget([_key(model, minute) for minute in minutes])
        except Exception:
            logger.debug("Could not read LLM request counts for %s", model, exc_info=True)
            continue
        values = [int(v) if v else 0 for v in raw]
        out[model]["day"] = sum(values)
        out[model]["hour"] = sum(values[:_HOUR_MINUTES])
    return out
