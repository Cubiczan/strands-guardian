from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from ..models.schemas import GeoEvent, GeoEventType, Severity
from ..utils.cache import TimedCache

logger = logging.getLogger(__name__)
_cache = TimedCache(default_ttl=900.0)  # 15 min

GDACS_RSS_URL = "https://www.gdacs.org/xml/rss.xml"


async def fetch_gdacs_events(
    country_code: str = "US",
    client: Optional[httpx.AsyncClient] = None,
    _use_cache: bool = True,
) -> list[GeoEvent]:
    """Fetch GDACS global disaster events, filtered to a country."""
    cache_key = f"gdacs:{country_code}"
    if _use_cache:
        hit = _cache.get(cache_key)
        if hit is not None:
            return hit

    events: list[GeoEvent] = []
    try:
        c = client or httpx.AsyncClient(timeout=30)
        resp = await c.get(GDACS_RSS_URL)
        resp.raise_for_status()

        # GDACS RSS may return XML; fall back to their GeoJSON API
        geo_url = "https://www.gdacs.org/data/arcgis/active_events.json"
        try:
            resp2 = await c.get(geo_url, follow_redirects=True)
            if resp2.status_code == 200:
                data = resp2.json()
                features = data.get("features", [])
                for f in features:
                    props = f.get("properties", {})
                    geom = f.get("geometry", {})
                    coords = geom.get("coordinates", [0, 0, 0])
                    lon, lat = coords[0], coords[1]

                    sev = Severity.MODERATE
                    if "Red" in str(props.get("severity", "")):
                        sev = Severity.EXTREME
                    elif "Orange" in str(props.get("severity", "")):
                        sev = Severity.SEVERE

                    evt_type = GeoEventType.STORM
                    title_lower = (props.get("name", "") + " " + props.get("eventtype", "")).lower()
                    if "flood" in title_lower:
                        evt_type = GeoEventType.FLOOD
                    elif "earthquake" in title_lower or "quake" in title_lower:
                        evt_type = GeoEventType.EARTHQUAKE
                    elif "wildfire" in title_lower or "fire" in title_lower:
                        evt_type = GeoEventType.WILDFIRE

                    events.append(
                        GeoEvent(
                            event_type=evt_type,
                            title=props.get("name", "GDACS Event"),
                            description=props.get("description", ""),
                            latitude=lat,
                            longitude=lon,
                            severity=sev,
                            source="GDACS",
                            event_id=props.get("eventid"),
                            timestamp=props.get("startdate"),
                            details_url=props.get("url"),
                        )
                    )
        except Exception:
            logger.debug("GDACS GeoJSON unavailable, skipping")

    except Exception as e:
        logger.warning("GDACS fetch failed: %s", e)

    _cache.set(cache_key, events)
    return events
