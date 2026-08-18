from __future__ import annotations

import logging
from typing import Optional

import httpx

from ..models.schemas import GeoEvent, GeoEventType, Severity
from ..utils.cache import TimedCache

logger = logging.getLogger(__name__)
_cache = TimedCache(default_ttl=900.0)

NOAA_CAP_URL = "https://api.weather.gov/alerts/active?area=US"


async def fetch_noaa_alerts(
    client: Optional[httpx.AsyncClient] = None,
    _use_cache: bool = True,
) -> list[GeoEvent]:
    """Fetch active NOAA/NWS CAP weather alerts for the US."""
    cache_key = "noaa:us_alerts"
    if _use_cache:
        hit = _cache.get(cache_key)
        if hit is not None:
            return hit

    events: list[GeoEvent] = []
    try:
        c = client or httpx.AsyncClient(timeout=30)
        resp = await c.get(
            NOAA_CAP_URL,
            headers={"Accept": "application/geo+json", "User-Agent": "StrandsGuardian/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()

        for f in data.get("features", []):
            props = f.get("properties", {})
            geom = f.get("geometry", {})

            # Try to extract centroid from polygon
            lat, lon = None, None
            if geom and geom.get("type") == "Polygon":
                coords = geom.get("coordinates", [[]])[0]
                if coords:
                    n = len(coords)
                    lat = sum(p[1] for p in coords) / n
                    lon = sum(p[0] for p in coords) / n
            elif geom and geom.get("type") == "Point":
                lon, lat = geom.get("coordinates", [0, 0])[:2]

            if lat is None or lon is None:
                continue

            severity_str = props.get("severity", "unknown").lower()
            sev_map = {
                "extreme": Severity.EXTREME,
                "severe": Severity.SEVERE,
                "moderate": Severity.MODERATE,
                "minor": Severity.MINOR,
            }
            sev = sev_map.get(severity_str, Severity.INFO)

            events.append(
                GeoEvent(
                    event_type=GeoEventType.WEATHER_ALERT,
                    title=props.get("event", "Weather Alert"),
                    description=props.get("headline", props.get("description", ""))[:500],
                    latitude=lat,
                    longitude=lon,
                    severity=sev,
                    source="NOAA/NWS",
                    event_id=props.get("id"),
                    timestamp=props.get("sent"),
                    details_url=props.get("@id"),
                )
            )

    except Exception as e:
        logger.warning("NOAA fetch failed: %s", e)

    _cache.set(cache_key, events)
    return events
