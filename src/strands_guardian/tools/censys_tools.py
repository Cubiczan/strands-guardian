from __future__ import annotations

import json
import logging
import os
from typing import Optional

import httpx

from ..models.schemas import ICSAsset

logger = logging.getLogger(__name__)

CENSYS_API_URL = "https://search.censys.io/api/v3"
CENSYS_TOKEN_ID = os.environ.get("CENSYS_API_ID", "")
CENSYS_TOKEN_SECRET = os.environ.get("CENSYS_API_SECRET", "")

# Known ICS/SCADA protocols to query
ICS_QUERIES = [
    {"service": "Modbus", "query": "services.modbus AND location.country_code:US"},
    {"service": "Siemens S7", "query": "services.s7comm AND location.country_code:US"},
    {"service": "DNP3", "query": "services.dnp3 AND location.country_code:US"},
    {"service": "EtherNet/IP", "query": "services.enip AND location.country_code:US"},
    {"service": "IEC 104", "query": "services.iec_60870_5_104 AND location.country_code:US"},
    {"service": "BACnet", "query": "services.bacnet AND location.country_code:US"},
]

# --- Mock data for demo / no-key mode ---
MOCK_ASSETS = [
    ICSAsset(ip="198.51.100.12", port=502, protocol="Modbus TCP", service_name="modbus",
              city="Houston", state="TX", country="US", latitude=29.76, longitude=-95.37,
              vendor="Schneider Electric", product="Modicon M580", firmware="v3.60"),
    ICSAsset(ip="203.0.113.45", port=102, protocol="Siemens S7", service_name="s7comm",
              city="Atlanta", state="GA", country="US", latitude=33.75, longitude=-84.39,
              vendor="Siemens", product="S7-1500", firmware="v2.9"),
    ICSAsset(ip="192.0.2.88", port=20000, protocol="DNP3", service_name="dnp3",
              city="Chattanooga", state="TN", country="US", latitude=35.05, longitude=-85.31,
              vendor="Triangle MicroWorks", product="DNP3 Outstation Simulator", firmware="v5.1"),
    ICSAsset(ip="198.51.100.201", port=44818, protocol="EtherNet/IP", service_name="enip",
              city="Charlotte", state="NC", country="US", latitude=35.23, longitude=-80.84,
              vendor="Rockwell Automation", product="ControlLogix", firmware="v33.11"),
    ICSAsset(ip="203.0.113.77", port=47808, protocol="BACnet", service_name="bacnet",
              city="Nashville", state="TN", country="US", latitude=36.16, longitude=-86.78,
              vendor="Johnson Controls", product="Metasys N2", firmware="v14.2"),
]


def _build_censys_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def discover_ics_assets(
    region: str = "US",
    protocols: Optional[list[str]] = None,
    max_per_protocol: int = 10,
    _use_mock: bool = False,
) -> list[dict]:
    """Discover exposed ICS/SCADA assets via Censys API v3.

    Args:
        region: Country code to scope discovery.
        protocols: Optional list of protocol names to filter. None = all.
        max_per_protocol: Max results per protocol query.
        _use_mock: Force use of mock data (for demo).

    Returns:
        List of dicts with asset details.
    """
    if _use_mock or not CENSYS_TOKEN_ID:
        logger.info("Using mock ICS asset data")
        assets = MOCK_ASSETS
        if protocols:
            assets = [a for a in assets if a.protocol in protocols]
        return [_asset_to_dict(a) for a in assets[:max_per_protocol * len(ICS_QUERIES)]]

    all_assets: list[ICSAsset] = []
    queries = ICS_QUERIES
    if protocols:
        queries = [q for q in queries if q["service"] in protocols]

    async with httpx.AsyncClient(auth=(CENSYS_TOKEN_ID, CENSYS_TOKEN_SECRET), timeout=60) as c:
        for q in queries:
            try:
                resp = await c.post(
                    f"{CENSYS_API_URL}/hosts/search",
                    headers=_build_censys_headers(),
                    json={
                        "q": q["query"],
                        "per_page": max_per_protocol,
                        "virtual_hosts": "EXCLUDE",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                for hit in data.get("result", {}).get("hits", []):
                    ip = hit.get("ip", "")
                    services = hit.get("services", {})
                    for port_str, svc in services.items():
                        if port_str == q["service"].lower() or q["service"].lower() in str(svc).lower():
                            port = int(port_str)
                            loc = hit.get("location", {})
                            all_assets.append(
                                ICSAsset(
                                    ip=ip,
                                    port=port,
                                    protocol=q["service"],
                                    service_name=q["service"].lower(),
                                    city=loc.get("city"),
                                    state=loc.get("province"),
                                    country=loc.get("country", "US"),
                                    latitude=loc.get("coordinates", {}).get("latitude"),
                                    longitude=loc.get("coordinates", {}).get("longitude"),
                                )
                            )
                            break
            except Exception as e:
                logger.warning("Censys query for %s failed: %s", q["service"], e)

    return [_asset_to_dict(a) for a in all_assets]


def _asset_to_dict(a: ICSAsset) -> dict:
    return {
        "asset_id": a.asset_id,
        "ip": a.ip,
        "port": a.port,
        "protocol": a.protocol,
        "service_name": a.service_name,
        "location": a.location or f"{a.city}, {a.state}" if a.city and a.state else "Unknown",
        "city": a.city,
        "state": a.state,
        "country": a.country,
        "latitude": a.latitude,
        "longitude": a.longitude,
        "vendor": a.vendor,
        "product": a.product,
        "firmware": a.firmware,
        "last_seen": a.last_seen,
        "display_name": a.display_name,
    }
