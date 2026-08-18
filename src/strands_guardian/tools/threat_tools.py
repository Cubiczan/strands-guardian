from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import httpx

from ..models.schemas import ThreatIntelResult

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.environ.get("SERPAPI_API_KEY", "")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY", "")

# --- Mock threat intel for demo ---
MOCK_THREAT_INTEL: dict[str, list[dict]] = {
    "198.51.100.12:502": [
        {
            "title": "ICS-CERT Advisory: Schneider Electric Modicon M580 Vulnerabilities",
            "url": "https://www.cisa.gov/news-events/ics-cert-advisories",
            "snippet": "Multiple vulnerabilities in Schneider Electric Modicon M580 PLCs could allow remote code execution via Modbus TCP protocol manipulation.",
            "source": "serpapi",
            "published_date": (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "relevance_score": 0.92,
        },
        {
            "title": "Chinese APT Group Volt Typhoon Targeting US Energy Infrastructure",
            "url": "https://www.mandiant.com/resources/blog/volt-typhoon",
            "snippet": "FBI confirms Volt Typhoon has pre-positioned on US critical infrastructure networks including electric grid operators in the Southeast.",
            "source": "tavily",
            "published_date": (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "relevance_score": 0.95,
        },
    ],
    "203.0.113.45:102": [
        {
            "title": "Siemens S7-1500 PLCs Found Exposed on Public Internet Across 12 States",
            "url": "https://www.theregister.com/2026/08/siemens-s7-exposed",
            "snippet": "Security researchers found over 200 Siemens S7-1500 PLCs accessible without authentication, many belonging to water and power utilities.",
            "source": "serpapi",
            "published_date": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "relevance_score": 0.88,
        },
    ],
    "192.0.2.88:20000": [
        {
            "title": "DNP3 Protocol Vulnerability CVE-2025-41877 Actively Exploited",
            "url": "https://nvd.nist.gov/vuln/detail/CVE-2025-41877",
            "snippet": "CISA adds CVE-2025-41877 to Known Exploited Vulnerabilities catalog. Affects DNP3 implementations used in power grid SCADA systems.",
            "source": "tavily",
            "published_date": (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "relevance_score": 0.97,
        },
    ],
    "198.51.100.201:44818": [
        {
            "title": "Rockwell Automation ControlLogix Firmware Update Patches Critical RCE",
            "url": "https://rockwellautomation.custhelp.com/app/answers/detail/a_id/1138794",
            "snippet": "Rockwell Automation releases firmware v34 for ControlLogix addressing multiple critical vulnerabilities including remote code execution.",
            "source": "serpapi",
            "published_date": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "relevance_score": 0.75,
        },
    ],
    "203.0.113.77:47808": [
        {
            "title": "BACnet Protocol Used in Attack Chain Against US Hospital HVAC Systems",
            "url": "https://www.darkreading.com/ics-ot/bacnet-attack-hospital-hvac",
            "snippet": "Attackers exploited exposed BACnet devices to gain access to hospital building automation systems, disrupting HVAC during peak summer.",
            "source": "tavily",
            "published_date": (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d"),
            "relevance_score": 0.72,
        },
    ],
}


async def search_threat_intel(
    ip: str,
    port: int,
    protocol: str,
    vendor: Optional[str] = None,
    product: Optional[str] = None,
    _use_mock: bool = False,
) -> list[dict]:
    """Search for threat intelligence about an ICS asset.

    Uses SerpApi (primary) and Tavily (fallback) to find dated,
    cited headlines and snippets relevant to the asset.

    Args:
        ip: Asset IP address.
        port: Asset port number.
        protocol: ICS protocol name (e.g. "Modbus TCP").
        vendor: Optional vendor name.
        product: Optional product name.
        _use_mock: Force mock data.

    Returns:
        List of dicts with threat intel results.
    """
    asset_key = f"{ip}:{port}"

    if _use_mock or (not SERPAPI_KEY and not TAVILY_KEY):
        logger.info("Using mock threat intel for %s", asset_key)
        results = MOCK_THREAT_INTEL.get(asset_key, [])
        return [
            {
                "title": r["title"],
                "url": r["url"],
                "snippet": r["snippet"],
                "source": r["source"],
                "published_date": r.get("published_date"),
                "relevance_score": r.get("relevance_score", 0.0),
            }
            for r in results
        ]

    all_results: list[ThreatIntelResult] = []

    # Build search queries
    queries = [
        f'"{protocol}" vulnerability SCADA ICS {ip}',
        f'"{vendor}" "{product}" exploit security' if vendor and product else None,
        f'critical infrastructure cyber attack {protocol} 2025 2026',
    ]
    queries = [q for q in queries if q]

    # Try SerpApi first
    if SERPAPI_KEY:
        async with httpx.AsyncClient(timeout=30) as c:
            for q in queries[:2]:  # Limit to 2 queries
                try:
                    params = {
                        "q": q,
                        "api_key": SERPAPI_KEY,
                        "engine": "google_news",
                        "num": 5,
                        "tbs": "qdr:m",  # past month
                    }
                    resp = await c.get("https://serpapi.com/search", params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    for news in data.get("news_results", []):
                        all_results.append(
                            ThreatIntelResult(
                                title=news.get("title", ""),
                                url=news.get("link", ""),
                                snippet=news.get("snippet", ""),
                                source="serpapi",
                                published_date=news.get("date"),
                                relevance_score=0.8,
                            )
                        )
                except Exception as e:
                    logger.warning("SerpApi search failed: %s", e)

    # Fallback to Tavily
    if not all_results and TAVILY_KEY:
        async with httpx.AsyncClient(timeout=30) as c:
            for q in queries[:1]:
                try:
                    resp = await c.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": TAVILY_KEY,
                            "query": q,
                            "max_results": 5,
                            "include_answer": False,
                            "search_depth": "advanced",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    for r in data.get("results", []):
                        all_results.append(
                            ThreatIntelResult(
                                title=r.get("title", ""),
                                url=r.get("url", ""),
                                snippet=r.get("content", ""),
                                source="tavily",
                                published_date=r.get("published_date"),
                                relevance_score=r.get("score", 0.0),
                            )
                        )
                except Exception as e:
                    logger.warning("Tavily search failed: %s", e)

    return [
        {
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet,
            "source": r.source,
            "published_date": r.published_date,
            "relevance_score": r.relevance_score,
        }
        for r in all_results
    ]
