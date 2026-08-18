"""Strands Guardian — Autonomous ICS/SCADA Threat Intelligence Agent.

Built with Strands Agents SDK, fuses Censys ICS discovery, OSINT news,
MITRE ATT&CK mapping, CISA KEV enrichment, and live geo-event feeds
into SOC-ready intelligence dossiers for US critical infrastructure.
"""

__version__ = "0.1.0"

from .agent import create_guardian_agent, run_guardian

__all__ = ["create_guardian_agent", "run_guardian"]
