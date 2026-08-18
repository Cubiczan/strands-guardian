from __future__ import annotations

import logging
from typing import Optional

import httpx

from ..models.schemas import GeoEvent, GeoEventType, Severity
from ..utils.cache import TimedCache

logger = logging.getLogger(__name__)
_cache = TimedCache(default_ttl=900.0)

USGS_GEOJSON_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/"
    "4.5_week.geojson"
)


async def fetch_usgs_earthquakes(
    min_magnitude: float = 4.5,
    client: Optional[httpx.AsyncClient] = None,
    _use_cache: bool = True,
) -> list[GeoEvent]:
    """Fetch USGS earthquakes >= min_magnitude, past 7 days."""
    cache_key = f"usgs:m{min_magnitude}"
    if _use_cache:
        hit = _cache.get(cache_key)
        if hit is not None:
            return hit

    events: list[GeoEvent] = []
    try:
        c = client or httpx.AsyncClient(timeout=30)
        resp = await c.get(USGS_GEOJSON_URL)
        resp.raise_for_status()
        data = resp.json()

        for f in data.get("features", []):
            props = f.get("properties", [])
            mag = props.get("mag", 0)
            if mag < min_magnitude:
                continue

            coords = f.get("geometry", {}).get("coordinates", [0, 0, 0])
            lon, lat, depth = coords[0], coords[1], coords[2]

            sev = Severity.MODERATE
            if mag >= 7.0:
                sev = Severity.EXTREME
            elif mag >= 5.5:
                sev = Severity.SEVERE

            events.append(
                GeoEvent(
                    event_type=GeoEventType.EARTHQUAKE,
                    title=props.get("place", f"M{mag:.1f} earthquake"),
                    description=f"Magnitude {mag:.1f} at depth {depth:.1f}km. {props.get('place', '')}",
                    latitude=lat,
                    longitude=lon,
                    severity=sev,
                    source="USGS",
                    event_id=f.get("id"),
                    timestamp=props.get("time"),
                    details_url=props.get("url"),
                )
            )

    except Exception as e:
        logger.warning("USGS fetch failed: %s", e)

    _cache.set(cache_key, events)
    return events
