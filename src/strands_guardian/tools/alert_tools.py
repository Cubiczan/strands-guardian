from __future__ import annotations

import json
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
WEBHOOK_URL = os.environ.get("GUARDIAN_WEBHOOK_URL", "")


def send_alert(
    message: str,
    priority: str = "P2",
    asset_ip: str = "",
    asset_port: int = 0,
    _use_mock: bool = False,
) -> dict:
    """Send a P1/P2 alert to configured notification channels.

    Args:
        message: Alert message content.
        priority: Priority level (P1, P2, P3).
        asset_ip: Asset IP for context.
        asset_port: Asset port for context.
        _use_mock: Log alert without sending.

    Returns:
        Dict with delivery status.
    """
    emoji = {
        "P1 - CRITICAL": ":red_circle: *CRITICAL*",
        "P2 - HIGH": ":large_orange_diamond: *HIGH*",
        "P3 - MEDIUM": ":white_circle: *MEDIUM*",
    }.get(priority, priority)

    full_msg = (
        f"{emoji} *Strands Guardian Alert*\n"
        f"*Asset:* `{asset_ip}:{asset_port}`\n"
        f"*Priority:* {priority}\n\n"
        f"{message}"
    )

    results: dict[str, str] = {}

    if _use_mock or not SLACK_WEBHOOK_URL:
        logger.info("[MOCK ALERT] %s", full_msg)
        results["mock"] = "Alert logged (no webhook configured)"
        results["message_preview"] = full_msg[:200]
        return results

    # Send to Slack
    if SLACK_WEBHOOK_URL:
        try:
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                _post_webhook(SLACK_WEBHOOK_URL, {"text": full_msg})
            )
            results["slack"] = "delivered"
        except Exception as e:
            results["slack"] = f"failed: {e}"

    # Send to generic webhook
    if WEBHOOK_URL:
        try:
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                _post_webhook(
                    WEBHOOK_URL,
                    {
                        "priority": priority,
                        "asset_ip": asset_ip,
                        "asset_port": asset_port,
                        "message": message,
                    },
                )
            )
            results["webhook"] = "delivered"
        except Exception as e:
            results["webhook"] = f"failed: {e}"

    return results


async def _post_webhook(url: str, payload: dict) -> None:
    async with httpx.AsyncClient(timeout=15) as c:
        resp = await c.post(url, json=payload)
        resp.raise_for_status()
