from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Priority(str, Enum):
    P1 = "P1 - CRITICAL"
    P2 = "P2 - HIGH"
    P3 = "P3 - MEDIUM"


class Severity(str, Enum):
    EXTREME = "extreme"
    SEVERE = "severe"
    MODERATE = "moderate"
    MINOR = "minor"
    INFO = "info"


class GeoEventType(str, Enum):
    WILDFIRE = "wildfire"
    FLOOD = "flood"
    STORM = "storm"
    EARTHQUAKE = "earthquake"
    WEATHER_ALERT = "weather_alert"
    NEWS = "news"


@dataclass
class ICSAsset:
    """Represents a discovered ICS/SCADA asset."""
    ip: str
    port: int
    protocol: str
    service_name: str
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "US"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    firmware: Optional[str] = None
    vendor: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    last_seen: Optional[str] = None
    cert_fingerprint: Optional[str] = None

    @property
    def asset_id(self) -> str:
        raw = f"{self.ip}:{self.port}:{self.protocol}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    @property
    def display_name(self) -> str:
        loc = f" ({self.city}, {self.state})" if self.city and self.state else ""
        return f"{self.ip}:{self.port} [{self.protocol}]{loc}"


@dataclass
class MitreMapping:
    """MITRE ATT&CK technique mapping for an asset."""
    technique_id: str
    technique_name: str
    tactic: str
    confidence: float  # 0.0 - 1.0
    rationale: str
    evidence_snippet: Optional[str] = None
    sub_technique_of: Optional[str] = None
    ics_matrix: bool = True


@dataclass
class CisaKevEntry:
    """CISA Known Exploited Vulnerabilities entry."""
    cve_id: str
    product: str
    vulnerability_name: str
    date_added: str
    due_date: str
    description: Optional[str] = None
    known_ransomware_use: bool = False


@dataclass
class ThreatIntelResult:
    """A single threat intelligence search result."""
    title: str
    url: str
    snippet: str
    source: str  # "serpapi" or "tavily"
    published_date: Optional[str] = None
    relevance_score: float = 0.0


@dataclass
class ThreatBrief:
    """Complete threat assessment for a single asset."""
    asset: ICSAsset
    priority: Priority
    priority_score: float
    threat_intel: list[ThreatIntelResult] = field(default_factory=list)
    mitre_mappings: list[MitreMapping] = field(default_factory=list)
    cisa_kev_matches: list[CisaKevEntry] = field(default_factory=list)
    nvd_matches: list[dict] = field(default_factory=list)
    geo_proximity: list[ProximityResult] = field(default_factory=list)
    summary: str = ""
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class GeoEvent:
    """A geo-located event (disaster, fire, quake, weather, news)."""
    event_type: GeoEventType
    title: str
    description: str
    latitude: float
    longitude: float
    severity: Severity
    source: str
    event_id: Optional[str] = None
    timestamp: Optional[str] = None
    radius_km: Optional[float] = None
    details_url: Optional[str] = None


@dataclass
class ProximityResult:
    """Result of proximity calculation between an asset and a geo event."""
    event: GeoEvent
    distance_km: float
    bearing_deg: float
    bearing_label: str  # e.g. "N", "NE", "E", "SE", etc.
    threat_relevance: str  # agent-assessed relevance


@dataclass
class Dossier:
    """Complete SOC-ready dossier for an asset."""
    asset: ICSAsset
    brief: ThreatBrief
    format: str = "markdown"  # markdown, pdf, csv, json, stix
    content: str = ""
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
