from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Strands Agents SDK; graceful fallback for demo mode
try:
    from strands import Agent
    from strands.tools import tool

    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False
    logger.warning(
        "strands-agents SDK not installed. Running in standalone/demo mode. "
        "Install with: pip install strands-agents"
    )

from .tools.censys_tools import discover_ics_assets
from .tools.threat_tools import search_threat_intel
from .tools.mitre_tools import map_mitre_attack, check_cisa_kev
from .tools.geo_tools import get_geo_events
from .tools.dossier_tools import generate_dossier
from .tools.alert_tools import send_alert

SYSTEM_PROMPT = """\
You are Strands Guardian, an autonomous cyber-physical threat intelligence agent.
Your mission is to discover, analyze, and assess threats to US critical infrastructure 
by fusing ICS/SCADA asset discovery with OSINT, MITRE ATT&CK mapping, CISA KEV 
enrichment, and real-time geo-event feeds.

## Your Capabilities
- **discover_ics_assets**: Find exposed ICS/SCADA devices via Censys
- **search_threat_intel**: Search OSINT news for threat context per asset
- **map_mitre_attack**: Map asset protocols to MITRE ATT&CK ICS techniques
- **check_cisa_kev**: Check CISA Known Exploited Vulnerabilities catalog
- **get_geo_events**: Aggregate GDACS, NASA FIRMS, USGS, NOAA feeds near an asset
- **generate_dossier**: Produce a SOC-ready intelligence dossier
- **send_alert**: Notify responders for P1 findings

## Operating Procedure
1. Use discover_ics_assets to find exposed ICS devices in the requested scope
2. For EACH asset, run the full analysis pipeline:
   a. search_threat_intel for the asset
   b. map_mitre_attack for the protocol
   c. check_cisa_kev for vendor/product
   d. get_geo_events near the asset location
3. Synthesize all findings and generate_dossier for each asset
4. If any dossier is P1, call send_alert immediately
5. Report a final summary of all assets analyzed and their priorities

## Rules
- Always cite sources with dates for every intelligence finding
- Be specific about distances, bearings, and severity levels
- Prioritize P1 findings — alert first, analyze second
- Use mock data when API keys are not configured
- Be thorough: every asset gets the full pipeline
"""


# ── Standalone tool wrappers (used when Strands SDK is not installed) ──

def _parse_asset_from_dict(d: dict) -> dict:
    return d


def _run_standalone(
    region: str = "US",
    protocols: Optional[list[str]] = None,
    radius_km: float = 200.0,
    output_dir: str = "./dossiers",
    mock: bool = True,
) -> str:
    """Run the full pipeline without Strands SDK (demo/CI mode)."""
    import subprocess

    async def _pipeline():
        print("\n" + "=" * 70)
        print("  STRANDS GUARDIAN — Autonomous ICS Threat Intelligence Agent")
        print("=" * 70)
        print(f"  Scope: {region} | Radius: {radius_km}km | Mode: {'MOCK' if mock else 'LIVE'}")
        print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        # Step 1: Discover assets
        print("\U0001f50d Step 1: Discovering ICS/SCADA assets...")
        assets = await discover_ics_assets(
            region=region, protocols=protocols, _use_mock=mock
        )
        print(f"  Found {len(assets)} exposed ICS asset(s)\n")
        for a in assets:
            print(f"  • {a['display_name']}")
        print()

        # Step 2-4: Analyze each asset
        results = []
        for i, asset in enumerate(assets, 1):
            ip, port = asset["ip"], asset["port"]
            protocol = asset["protocol"]
            lat = asset.get("latitude")
            lon = asset.get("longitude")
            vendor = asset.get("vendor")
            product = asset.get("product")

            print(f"\U0001f9ea Step 2: Analyzing [{i}/{len(assets)}] {asset['display_name']}")
            print(f"  ├─ Threat intelligence search...")
            intel = await search_threat_intel(
                ip=ip, port=port, protocol=protocol,
                vendor=vendor, product=product, _use_mock=mock,
            )
            print(f"  ├─ Found {len(intel)} threat intel result(s)")

            print(f"  ├─ Mapping MITRE ATT&CK techniques...")
            mitre = await map_mitre_attack(
                protocol=protocol, vendor=vendor, product=product
            )
            print(f"  ├─ Mapped {len(mitre)} ATT&CK technique(s)")

            print(f"  ├─ Checking CISA KEV catalog...")
            kev = await check_cisa_kev(
                vendor=vendor, product=product, _use_mock=mock
            )
            kev_str = f"{len(kev)} match(es)" if kev else "No matches"
            if any(k.get("known_ransomware_use") for k in kev):
                kev_str += " ⚠\ufe0f RANSOMWARE FLAG"
            print(f"  ├─ {kev_str}")

            geo = []
            if lat is not None and lon is not None:
                print(f"  ├─ Fetching geo-events within {radius_km}km...")
                geo = await get_geo_events(
                    latitude=lat, longitude=lon,
                    radius_km=radius_km, _use_mock=mock,
                )
                print(f"  ├─ {len(geo)} nearby geo-event(s)")
                for g in geo:
                    print(f"  │     • {g['title'][:55]} ({g['distance_km']}km {g['bearing_label']}) [{g['severity']}]")
            else:
                print(f"  └─ No coordinates — skipping geo-fusion")

            # Step 3: Generate dossier
            print(f"\U0001f4cb Generating dossier...")
            dossier_md = generate_dossier(
                asset=asset,
                threat_intel=intel,
                mitre_mappings=mitre,
                cisa_kev=kev,
                geo_events=geo,
            )

            # Extract priority from dossier
            priority = "P3"
            for line in dossier_md.split("\n"):
                if "**Priority:**" in line:
                    for p in ["P1 - CRITICAL", "P2 - HIGH", "P3 - MEDIUM"]:
                        if p in line:
                            priority = p
                            break

            print(f"  └─ Priority: {priority}")

            # Step 4: Alert if P1
            if "P1" in priority:
                print(f"\U0001f6a8 P1 CRITICAL — Sending alert!")
                alert_result = send_alert(
                    message=f"Critical findings on {asset['display_name']}. "
                            f"See dossier for details.",
                    priority=priority,
                    asset_ip=ip,
                    asset_port=port,
                    _use_mock=True,
                )
                print(f"  Alert status: {alert_result.get('mock', 'sent')}")

            # Save dossier
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            safe_name = f"{ip}_{port}".replace(".", "_")
            md_file = out_path / f"dossier_{safe_name}.md"
            json_file = out_path / f"dossier_{safe_name}.json"

            md_file.write_text(dossier_md, encoding="utf-8")

            # Also save JSON
            dossier_json = generate_dossier(
                asset=asset, threat_intel=intel, mitre_mappings=mitre,
                cisa_kev=kev, geo_events=geo, output_format="json",
            )
            json_file.write_text(dossier_json, encoding="utf-8")

            print(f"  Saved: {md_file.name}, {json_file.name}")
            results.append({"asset": asset, "priority": priority})
            print()

        # Summary
        print("\n" + "=" * 70)
        print("  ANALYSIS COMPLETE")
        print("=" * 70)
        p1 = sum(1 for r in results if "P1" in r["priority"])
        p2 = sum(1 for r in results if "P2" in r["priority"])
        p3 = sum(1 for r in results if "P3" in r["priority"])
        print(f"  Assets analyzed: {len(results)}")
        print(f"  P1 CRITICAL: {p1}  |  P2 HIGH: {p2}  |  P3 MEDIUM: {p3}")
        print(f"  Dossiers saved to: {Path(output_dir).resolve()}")
        print(f"  Completed: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)

        return results

    return asyncio.run(_pipeline())


# ── Strands SDK Agent Creation ──

def create_guardian_agent(
    model_id: Optional[str] = None,
    mock: bool = True,
) -> "Agent":
    """Create and return a Strands Agent pre-loaded with Guardian tools.

    Args:
        model_id: Bedrock model ID (e.g. "us.anthropic.claude-sonnet-4-20250514").
                  Falls back to STRANDS_MODEL_ID env var or default.
        mock: Use mock data for demo.

    Returns:
        Configured Strands Agent instance.
    """
    if not STRANDS_AVAILABLE:
        raise RuntimeError(
            "strands-agents SDK is required for agent mode. "
            "Install with: pip install strands-agents"
        )

    _model = model_id or os.environ.get(
        "STRANDS_MODEL_ID",
        "us.anthropic.claude-sonnet-4-20250514",
    )

    agent = Agent(
        model=_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            _wrap_tool(discover_ics_assets, mock),
            _wrap_tool(search_threat_intel, mock),
            _wrap_tool(map_mitre_attack, mock),
            _wrap_tool(check_cisa_kev, mock),
            _wrap_tool(get_geo_events, mock),
            _wrap_tool(generate_dossier, mock),
            _wrap_tool(send_alert, mock),
        ],
    )
    return agent


def _wrap_tool(fn, mock: bool):
    """Wrap an async tool function with the Strands @tool decorator."""
    import functools
    import inspect

    @tool
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        kwargs.setdefault("_use_mock", mock)
        if inspect.iscoroutinefunction(fn):
            return await fn(*args, **kwargs)
        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


def run_guardian(
    prompt: str,
    model_id: Optional[str] = None,
    mock: bool = True,
    output_dir: str = "./dossiers",
) -> str:
    """Run Strands Guardian in the appropriate mode.

    If Strands SDK is installed, creates a full agent that autonomously
    orchestrates the tools. Otherwise runs the standalone pipeline.

    Args:
        prompt: Natural language prompt (e.g. "Monitor grid assets in the Southeast US").
        model_id: Bedrock model ID for Strands agent.
        mock: Use mock data for demo.
        output_dir: Directory to save generated dossiers.

    Returns:
        Agent response or pipeline summary.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    if STRANDS_AVAILABLE and not mock:
        agent = create_guardian_agent(model_id=model_id, mock=mock)
        print(f"\U0001f916 Strands Guardian agent initialized (model: {model_id or 'default'})")
        print(f"\U0001f4ac Prompt: {prompt}\n")
        result = agent(prompt)
        return str(result)
    else:
        mode = "MOCK" if mock else "STANDALONE"
        print(f"\U0001f916 Strands Guardian running in {mode} mode")
        print(f"\U0001f4ac Prompt: {prompt}\n")
        return _run_standalone(
            region="US",
            radius_km=200.0,
            output_dir=output_dir,
            mock=mock,
        )


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Strands Guardian — Autonomous ICS Threat Intelligence Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  strands-guardian "Monitor grid assets in the Southeast US"
  strands-guardian --mock --output ./reports "Analyze power grid SCADA"
  strands-guardian --model us.anthropic.claude-sonnet-4-20250514 "Full southeast scan"
        """,
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        default=["Monitor grid assets in the Southeast US"],
        help="Natural language prompt for the agent",
    )
    parser.add_argument("--model", help="Bedrock model ID")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock data")
    parser.add_argument("--live", action="store_true", help="Use live API data")
    parser.add_argument("--output", default="./dossiers", help="Output directory for dossiers")
    parser.add_argument("--version", action="version", version=f"Strands Guardian v0.1.0")

    args = parser.parse_args()
    prompt = " ".join(args.prompt)
    mock = args.mock and not args.live

    run_guardian(
        prompt=prompt,
        model_id=args.model,
        mock=mock,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
