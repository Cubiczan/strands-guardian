from __future__ import annotations

import csv
import io
import logging
from typing import Optional

import httpx

from ..models.schemas import GeoEvent, GeoEventType, Severity
from ..utils.cache import TimedCache

logger = logging.getLogger(__name__)
_cache = TimedCache(default_ttl=900.0)

FIRMS_CSV_URL = (
    "https://firms.modaps.eosdis.nasa.gov/data/active_fire/c6/csv/"
    "VIIRS_SNPP_NRT_USA_contiguous_and_Hawaii.csv"
)


async def fetch_firms_fires(
    map_key: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
    _use_cache: bool = True,
) -> list[GeoEvent]:
    """Fetch NASA FIRMS VIIRS active fire pixels for the continental US."""
    cache_key = "firms:us_contiguous"
    if _use_cache:
        hit = _cache.get(cache_key)
        if hit is not None:
            return hit

    events: list[GeoEvent] = []
    if not map_key:
        logger.info("FIRMS_MAP_KEY not set; skipping FIRMS feed")
        return events

    try:
        url = f"{FIRMS_CSV_URL}?MAP_KEY={map_key}"
        c = client or httpx.AsyncClient(timeout=30)
        resp = await c.get(url)
        resp.raise_for_status()

        reader = csv.DictReader(io.StringIO(resp.text))
        for row in reader:
            try:
                lat = float(row.get("latitude", 0))
                lon = float(row.get("longitude", 0))
                frp = float(row.get("frp", 0))

                sev = Severity.MINOR
                if frp >= 150:
                    sev = Severity.EXTREME
                elif frp >= 80:
                    sev = Severity.SEVERE
                elif frp >= 30:
                    sev = Severity.MODERATE

                events.append(
                    GeoEvent(
                        event_type=GeoEventType.WILDFIRE,
                        title=f"Active fire (FRP={frp:.0f})",
                        description=f"VIIRS SNPP NRT fire pixel, FRP={frp:.1f} MW",
                        latitude=lat,
                        longitude=lon,
                        severity=sev,
                        source="NASA FIRMS",
                        timestamp=row.get("acq_date", ""),
                    )
                )
            except (ValueError, TypeError):
                continue

    except Exception as e:
        logger.warning("FIRMS fetch failed: %s", e)

    _cache.set(cache_key, events)
    return events
