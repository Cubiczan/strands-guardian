from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

from ..feeds import fetch_gdacs_events, fetch_firms_fires, fetch_usgs_earthquakes, fetch_noaa_alerts
from ..models.schemas import GeoEvent, ProximityResult
from ..utils.haversine import haversine_km, bearing_degrees, bearing_label

logger = logging.getLogger(__name__)

# --- Mock geo events for demo ---
MOCK_GEO_EVENTS: list[dict] = [
    {
        "event_type": "weather_alert",
        "title": "Severe Thunderstorm Warning",
        "description": "Severe thunderstorms capable of producing damaging winds and large hail. Move to an interior room.",
        "latitude": 30.05,
        "longitude": -95.20,
        "severity": "severe",
        "source": "NOAA/NWS",
        "timestamp": "2026-08-17T14:00:00Z",
    },
    {
        "event_type": "wildfire",
        "title": "Active Fire Cluster (FRP=187)",
        "description": "VIIRS SNPP NRT: Active fire pixel cluster with high Fire Radiative Power, indicating intense wildfire activity.",
        "latitude": 34.10,
        "longitude": -84.50,
        "severity": "extreme",
        "source": "NASA FIRMS",
        "timestamp": "2026-08-17T12:30:00Z",
    },
    {
        "event_type": "earthquake",
        "title": "M4.7 earthquake - 12km WSW of Cleveland, Tennessee",
        "description": "Magnitude 4.7 at depth 8.2km. Light to moderate shaking reported across eastern Tennessee.",
        "latitude": 35.10,
        "longitude": -85.00,
        "severity": "moderate",
        "source": "USGS",
        "timestamp": "2026-08-17T08:15:00Z",
    },
    {
        "event_type": "news",
        "title": "Volt Typhoon APT Activity Reported in Southeast US Energy Sector",
        "description": "FBI and CISA jointly warn of Chinese state-sponsored APT targeting electric grid operators in Georgia, Tennessee, and the Carolinas.",
        "latitude": 33.75,
        "longitude": -84.39,
        "severity": "severe",
        "source": "Intelligence Feed",
        "timestamp": "2026-08-16T18:00:00Z",
    },
]


async def get_geo_events(
    latitude: float,
    longitude: float,
    radius_km: float = 200.0,
    _use_mock: bool = False,
) -> list[dict]:
    """Aggregate geo-events from all feeds near a location.

    Fetches from GDACS, NASA FIRMS, USGS, and NOAA, then
    filters to events within the specified radius.

    Args:
        latitude: Center latitude.
        longitude: Center longitude.
        radius_km: Search radius in kilometers.
        _use_mock: Force mock data.

    Returns:
        List of geo-event dicts within radius.
    """
    if _use_mock:
        events = []
        for e in MOCK_GEO_EVENTS:
            evt = e.copy()
            if isinstance(evt.get("event_type"), str):
                from ..models.schemas import GeoEventType
                evt["event_type"] = GeoEventType(evt["event_type"])
            if isinstance(evt.get("severity"), str):
                from ..models.schemas import Severity
                evt["severity"] = Severity(evt["severity"])
            events.append(GeoEvent(**evt))
    else:
        async with httpx.AsyncClient(timeout=30) as c:
            coros = [
                fetch_gdacs_events(client=c),
                fetch_firms_fires(client=c),
                fetch_usgs_earthquakes(client=c),
                fetch_noaa_alerts(client=c),
            ]
            results = await asyncio.gather(*coros, return_exceptions=True)
            events: list[GeoEvent] = []
            for r in results:
                if isinstance(r, list):
                    events.extend(r)
                elif isinstance(r, Exception):
                    logger.warning("Geo feed error: %s", r)

    # Filter by radius
    nearby = []
    for evt in events:
        dist = haversine_km(latitude, longitude, evt.latitude, evt.longitude)
        if dist <= radius_km:
            bear = bearing_degrees(latitude, longitude, evt.latitude, evt.longitude)
            nearby.append(
                {
                    "event_type": evt.event_type.value,
                    "title": evt.title,
                    "description": evt.description,
                    "latitude": evt.latitude,
                    "longitude": evt.longitude,
                    "severity": evt.severity.value,
                    "source": evt.source,
                    "distance_km": round(dist, 1),
                    "bearing_deg": round(bear, 1),
                    "bearing_label": bearing_label(bear),
                    "timestamp": evt.timestamp,
                    "details_url": evt.details_url,
                }
            )

    # Sort by severity then distance
    sev_order = {"extreme": 0, "severe": 1, "moderate": 2, "minor": 3, "info": 4}
    nearby.sort(key=lambda e: (sev_order.get(e["severity"], 5), e["distance_km"]))
    return nearby


def calculate_proximity(
    asset_lat: float,
    asset_lon: float,
    event_lat: float,
    event_lon: float,
) -> dict:
    """Calculate haversine distance and compass bearing between asset and event.

    Args:
        asset_lat: Asset latitude.
        asset_lon: Asset longitude.
        event_lat: Event latitude.
        event_lon: Event longitude.

    Returns:
        Dict with distance_km, bearing_deg, bearing_label.
    """
    dist = haversine_km(asset_lat, asset_lon, event_lat, event_lon)
    bear = bearing_degrees(asset_lat, asset_lon, event_lat, event_lon)
    return {
        "distance_km": round(dist, 1),
        "bearing_deg": round(bear, 1),
        "bearing_label": bearing_label(bear),
    }
