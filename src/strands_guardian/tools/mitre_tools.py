from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

ATTACK_REST_URL = "https://attack.mitre.org/api/v1"
CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

# --- ATT&CK ICS protocol-to-technique mapping ---
PROTOCOL_TECHNIQUE_MAP: dict[str, list[dict]] = {
    "modbus": [
        {
            "technique_id": "T0881",
            "technique_name": "Manipulation of Control",
            "tactic": "Inhibit Response Function",
            "confidence": 0.90,
            "rationale": "Modbus TCP lacks authentication; an attacker with network access can write to any register, manipulating PLC control logic.",
            "evidence_snippet": "Asset exposes Modbus TCP (port 502) without TLS or authentication wrapper.",
            "ics_matrix": True,
        },
        {
            "technique_id": "T0882",
            "technique_name": "Manipulation of View",
            "tactic": "Inhibit Response Function",
            "confidence": 0.85,
            "rationale": "Attacker can spoof sensor readings via Modbus register writes, causing operators to make decisions on falsified data.",
            "evidence_snippet": "Read/write registers accessible on exposed Modbus endpoint.",
            "ics_matrix": True,
        },
    ],
    "siemens s7": [
        {
            "technique_id": "T0885",
            "technique_name": "Remote System Discovery",
            "tactic": "Discovery",
            "confidence": 0.92,
            "rationale": "S7comm protocol allows unauthenticated enumeration of PLC device info, project names, and module configuration.",
            "evidence_snippet": "Siemens S7 port 102 accessible; S7comm handshake does not require credentials.",
            "ics_matrix": True,
        },
        {
            "technique_id": "T0881",
            "technique_name": "Manipulation of Control",
            "tactic": "Inhibit Response Function",
            "confidence": 0.88,
            "rationale": "S7 protocol allows PLC program upload/download and memory writes without authentication on exposed devices.",
            "evidence_snippet": "S7-1500 PLC with public-facing port 102 accepts unauthenticated connections.",
            "ics_matrix": True,
        },
    ],
    "dnp3": [
        {
            "technique_id": "T0883",
            "technique_name": "Loss of Protection",
            "tactic": "Impair Process Control",
            "confidence": 0.87,
            "rationale": "DNP3 outstation spoofing can cause the master station to lose visibility into field device states, impairing protective relay coordination.",
            "evidence_snippet": "DNP3 outstation on port 20000 is publicly reachable.",
            "ics_matrix": True,
        },
        {
            "technique_id": "T0856",
            "technique_name": "Modbus Function Code Probe",
            "tactic": "Discovery",
            "confidence": 0.80,
            "rationale": "DNP3 devices responding to unsolicited responses can leak internal addressing and point configuration.",
            "ics_matrix": True,
        },
    ],
    "ethernet/ip": [
        {
            "technique_id": "T0885",
            "technique_name": "Remote System Discovery",
            "tactic": "Discovery",
            "confidence": 0.85,
            "rationale": "EtherNet/IP CIP Identity requests enumerate device vendor, product, revision, and serial number without authentication.",
            "evidence_snippet": "EtherNet/IP port 44818 responds to CIP Identity requests.",
            "ics_matrix": True,
        },
        {
            "technique_id": "T0881",
            "technique_name": "Manipulation of Control",
            "tactic": "Inhibit Response Function",
            "confidence": 0.82,
            "rationale": "CIP messaging allows forward-open sessions to manipulate controller tags and execute ladder logic modifications.",
            "evidence_snippet": "ControlLogix controller accessible via public EtherNet/IP port.",
            "ics_matrix": True,
        },
    ],
    "iec 104": [
        {
            "technique_id": "T0881",
            "technique_name": "Manipulation of Control",
            "tactic": "Inhibit Response Function",
            "confidence": 0.88,
            "rationale": "IEC 60870-5-104 ASDU messages can spoof telemetry or issue control commands to RTUs without built-in authentication.",
            "evidence_snippet": "IEC 104 port accessible; protocol lacks authentication mechanisms.",
            "ics_matrix": True,
        },
    ],
    "bacnet": [
        {
            "technique_id": "T0885",
            "technique_name": "Remote System Discovery",
            "tactic": "Discovery",
            "confidence": 0.83,
            "rationale": "BACnet Who-Is/I-Am requests enumerate all building automation devices, revealing system topology.",
            "evidence_snippet": "BACnet device on port 47808 responds to broadcast Who-Is requests.",
            "ics_matrix": True,
        },
        {
            "technique_id": "T0882",
            "technique_name": "Manipulation of View",
            "tactic": "Inhibit Response Function",
            "confidence": 0.78,
            "rationale": "BACnet Write Property service can alter sensor setpoints and alarm thresholds without authentication on exposed devices.",
            "evidence_snippet": "BACnet port 47808 publicly accessible; Write Property confirmed.",
            "ics_matrix": True,
        },
    ],
}

# --- Mock CISA KEV data ---
MOCK_KEV: list[dict] = [
    {
        "cve_id": "CVE-2025-41877",
        "product": "DNP3 Implementations (Various)",
        "vulnerability_name": "DNP3 Outstation Response Spoofing",
        "date_added": "2025-07-15",
        "due_date": "2026-01-15",
        "description": "Improper input validation in DNP3 outstation implementations allows remote attackers to spoof responses.",
        "known_ransomware_use": True,
    },
    {
        "cve_id": "CVE-2024-29041",
        "product": "Schneider Electric Modicon M580",
        "vulnerability_name": "Modicon M580 Buffer Overflow",
        "date_added": "2024-11-20",
        "due_date": "2025-05-20",
        "description": "Stack-based buffer overflow in Schneider Electric Modicon M580 web server allows remote code execution.",
        "known_ransomware_use": False,
    },
    {
        "cve_id": "CVE-2024-89012",
        "product": "Siemens S7-1500 PLC Firmware",
        "vulnerability_name": "S7-1500 Unauthenticated Memory Access",
        "date_added": "2025-02-28",
        "due_date": "2025-08-28",
        "description": "Siemens S7-1500 PLCs allow unauthenticated read/write access to memory regions via S7comm protocol.",
        "known_ransomware_use": False,
    },
]


async def map_mitre_attack(
    protocol: str,
    vendor: Optional[str] = None,
    product: Optional[str] = None,
    services: Optional[list[str]] = None,
) -> list[dict]:
    """Map an ICS asset's protocol against MITRE ATT&CK ICS matrix.

    Args:
        protocol: ICS protocol name (e.g. "Modbus TCP").
        vendor: Optional vendor for additional mapping.
        product: Optional product for additional mapping.
        services: Optional list of detected service banners.

    Returns:
        List of MITRE ATT&CK technique mappings.
    """
    proto_lower = protocol.lower()
    mappings = PROTOCOL_TECHNIQUE_MAP.get(proto_lower, [])

    # Cross-reference with live ATT&CK API if available
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            for m in mappings:
                tid = m["technique_id"]
                resp = await c.get(
                    f"{ATTACK_REST_URL}/techniques/{tid}",
                    headers={"Accept": "application/json"},
                )
                if resp.status_code == 200:
                    tech = resp.json()
                    m["att&ck_url"] = f"https://attack.mitre.org/techniques/{tid}"
                    # Enrich with official description
                    if tech.get("description"):
                        m["att&ck_description"] = tech["description"][:300]
    except Exception as e:
        logger.debug("ATT&CK API enrichment failed: %s", e)

    return [
        {
            "technique_id": m["technique_id"],
            "technique_name": m["technique_name"],
            "tactic": m["tactic"],
            "confidence": m["confidence"],
            "rationale": m["rationale"],
            "evidence_snippet": m.get("evidence_snippet"),
            "sub_technique_of": m.get("sub_technique_of"),
            "ics_matrix": m.get("ics_matrix", True),
            "att&ck_url": m.get("att&ck_url"),
        }
        for m in mappings
    ]


async def check_cisa_kev(
    vendor: Optional[str] = None,
    product: Optional[str] = None,
    firmware: Optional[str] = None,
    _use_mock: bool = False,
) -> list[dict]:
    """Check CISA Known Exploited Vulnerabilities catalog for matches.

    Args:
        vendor: Vendor name to search.
        product: Product name to search.
        firmware: Firmware version string.
        _use_mock: Force mock data.

    Returns:
        List of matching KEV entries.
    """
    if _use_mock:
        matches = []
        for entry in MOCK_KEV:
            if vendor and vendor.lower() in entry["product"].lower():
                matches.append(entry)
            elif product and product.lower() in entry["product"].lower():
                matches.append(entry)
        return matches

    # Live CISA KEV check
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            resp = await c.get(CISA_KEV_URL)
            resp.raise_for_status()
            data = resp.json()
            vulnerabilities = data.get("vulnerabilities", [])

            matches = []
            for v in vulnerabilities:
                prod = v.get("product", "")
                if vendor and vendor.lower() in prod.lower():
                    matches.append(v)
                elif product and product.lower() in prod.lower():
                    matches.append(v)
            return matches
    except Exception as e:
        logger.warning("CISA KEV check failed: %s", e)
        return []
