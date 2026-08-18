from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from ..models.schemas import Priority

logger = logging.getLogger(__name__)


def _score_priority(
    threat_count: int,
    kev_count: int,
    mitre_count: int,
    geo_severe_count: int,
    has_kev_ransomware: bool = False,
) -> tuple[Priority, float]:
    """Compute P1/P2/P3 priority from evidence counts."""
    score = 0.0
    score += min(threat_count, 5) * 8
    score += kev_count * 25
    score += mitre_count * 10
    score += geo_severe_count * 15
    if has_kev_ransomware:
        score += 30

    if score >= 60 or has_kev_ransomware:
        return Priority.P1, min(score, 100)
    elif score >= 30:
        return Priority.P2, min(score, 100)
    else:
        return Priority.P3, min(score, 100)


def generate_dossier(
    asset: dict,
    threat_intel: list[dict],
    mitre_mappings: list[dict],
    cisa_kev: list[dict],
    geo_events: list[dict],
    output_format: str = "markdown",
) -> str:
    """Generate a SOC-ready dossier for an asset.

    Args:
        asset: Asset dict from discover_ics_assets.
        threat_intel: List of threat intel dicts.
        mitre_mappings: List of ATT&CK mapping dicts.
        cisa_kev: List of CISA KEV entry dicts.
        geo_events: List of geo-event dicts.
        output_format: "markdown", "json", or "csv".

    Returns:
        Formatted dossier string.
    """
    # Calculate priority
    geo_severe = sum(1 for e in geo_events if e.get("severity") in ("extreme", "severe"))
    has_ransomware = any(e.get("known_ransomware_use") for e in cisa_kev)
    priority, score = _score_priority(
        threat_count=len(threat_intel),
        kev_count=len(cisa_kev),
        mitre_count=len(mitre_mappings),
        geo_severe_count=geo_severe,
        has_kev_ransomware=has_ransomware,
    )

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    display = asset.get("display_name", f"{asset['ip']}:{asset['port']}")

    if output_format == "json":
        return json.dumps(
            {
                "asset": asset,
                "priority": priority.value,
                "priority_score": score,
                "threat_intel": threat_intel,
                "mitre_mappings": mitre_mappings,
                "cisa_kev": cisa_kev,
                "geo_events": geo_events,
                "generated_at": ts,
            },
            indent=2,
        )

    if output_format == "csv":
        lines = ["asset_id,ip,port,protocol,priority,score,kev_matches,mitre_techniques,geo_events_nearby"]
        lines.append(
            f"{asset.get('asset_id','')},{asset['ip']},{asset['port']},"
            f"{asset['protocol']},{priority.value},{score:.1f},"
            f"{len(cisa_kev)},{len(mitre_mappings)},{len(geo_events)}"
        )
        return "\n".join(lines)

    # Default: Markdown
    md = []
    md.append(f"# SOC Dossier: {display}")
    md.append(f"**Priority:** {priority.value} (score: {score:.1f}/100)")
    md.append(f"**Generated:** {ts} UTC  ")
    md.append(f"**Format:** Automated by Strands Guardian Agent")
    md.append("")

    # Asset details
    md.append("## Asset Details")
    md.append(f"| Field | Value |")
    md.append(f"|-------|-------|")
    md.append(f"| IP | `{asset['ip']}` |")
    md.append(f"| Port | {asset['port']} |")
    md.append(f"| Protocol | {asset['protocol']} |")
    md.append(f"| Vendor | {asset.get('vendor', 'Unknown')} |")
    md.append(f"| Product | {asset.get('product', 'Unknown')} |")
    md.append(f"| Firmware | {asset.get('firmware', 'Unknown')} |")
    md.append(f"| Location | {asset.get('location', 'Unknown')} |")
    md.append("")

    # Threat Intelligence
    md.append("## Threat Intelligence")
    if threat_intel:
        for i, ti in enumerate(threat_intel, 1):
            md.append(f"### {i}. {ti['title']}")
            md.append(f"- **Source:** {ti['source'].upper()} | **Date:** {ti.get('published_date', 'N/A')}")
            md.append(f"- **Relevance:** {ti.get('relevance_score', 0):.0%}")
            md.append(f"> {ti['snippet']}")
            md.append(f"> [View]({ti['url']})")
            md.append("")
    else:
        md.append("No recent threat intelligence found for this asset.")
        md.append("")

    # MITRE ATT&CK
    md.append("## MITRE ATT&CK Mapping")
    if mitre_mappings:
        md.append(f"| Technique | Name | Tactic | Confidence |")
        md.append(f"|-----------|------|--------|------------|")
        for m in mitre_mappings:
            conf_bar = "*" * int(m["confidence"] * 10)
            md.append(
                f"| [{m['technique_id']}]({m.get('att&ck_url', '#')}) "
                f"| {m['technique_name']} | {m['tactic']} | {m['confidence']:.0%} {conf_bar} |"
            )
        md.append("")
        for m in mitre_mappings:
            md.append(f"**{m['technique_id']} — {m['rationale']}**")
            if m.get("evidence_snippet"):
                md.append(f"> {m['evidence_snippet']}")
            md.append("")
    else:
        md.append("No ATT&CK techniques mapped for this protocol.")
        md.append("")

    # CISA KEV
    md.append("## CISA Known Exploited Vulnerabilities")
    if cisa_kev:
        for kev in cisa_kev:
            rwn = " \U0001f534 **KNOWN RANSOMWARE USE**" if kev.get("known_ransomware_use") else ""
            md.append(f"- **{kev['cve_id']}** — {kev['vulnerability_name']}{rwn}")
            md.append(f"  - Product: {kev['product']}")
            md.append(f"  - Added: {kev['date_added']} | Due: {kev['due_date']}")
            if kev.get("description"):
                md.append(f"  - {kev['description']}")
        md.append("")
    else:
        md.append("No CISA KEV matches found.")
        md.append("")

    # Geo Proximity
    md.append("## Geo Situational Awareness")
    if geo_events:
        md.append(f"| Event | Type | Severity | Distance | Bearing | Source |")
        md.append(f"|-------|------|----------|----------|---------|--------|")
        for e in geo_events:
            md.append(
                f"| {e['title'][:50]} | {e['event_type']} "
                f"| {e['severity']} | {e['distance_km']} km | {e['bearing_label']} ({e['bearing_deg']}\u00b0) "
                f"| {e['source']} |"
            )
        md.append("")
    else:
        md.append("No geo-events detected within search radius.")
        md.append("")

    # Priority Assessment
    md.append("## Priority Assessment")
    md.append(f"**{priority.value}** — Score: {score:.1f}/100")
    md.append("")
    md.append("**Scoring factors:**")
    md.append(f"- Threat intel hits: {len(threat_intel)} (\u00d78 = {len(threat_intel)*8})")
    md.append(f"- CISA KEV matches: {len(cisa_kev)} (\u00d725 = {len(cisa_kev)*25})")
    md.append(f"- ATT&CK techniques: {len(mitre_mappings)} (\u00d710 = {len(mitre_mappings)*10})")
    md.append(f"- Severe/nearby geo-events: {geo_severe} (\u00d715 = {geo_severe*15})")
    if has_ransomware:
        md.append(f"- **KEV ransomware flag: +30 (CRITICAL BOOST)**")
    md.append("")

    if priority == Priority.P1:
        md.append("> **\u26a0\ufe0f ACTION REQUIRED** — This asset has critical findings requiring immediate attention.")
    elif priority == Priority.P2:
        md.append("> **\u26a1 HIGH** — This asset has significant findings that should be investigated within 24 hours.")
    else:
        md.append("> **\u2139\ufe0f MEDIUM** — This asset has moderate exposure. Monitor and re-assess during next cycle.")

    return "\n".join(md)
