#!/usr/bin/env python3
"""Generate architecture diagram for Strands Guardian."""

from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1920, 1080

def get_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def arrow(draw, x1, y1, x2, y2, color, width=2):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    # Arrowhead
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    alen = 12
    draw.polygon([
        (x2, y2),
        (x2 - alen * math.cos(angle - 0.4), y2 - alen * math.sin(angle - 0.4)),
        (x2 - alen * math.cos(angle + 0.4), y2 - alen * math.sin(angle + 0.4)),
    ], fill=color)

img = Image.new("RGB", (W, H), (15, 20, 40))
draw = ImageDraw.Draw(img)

font_title = get_font(28, bold=True)
font_box = get_font(20, bold=True)
font_small = get_font(16)
font_tiny = get_font(14)

# Title
title = "Strands Guardian — Architecture"
bbox = draw.textbbox((0, 0), title, font=get_font(36, bold=True))
draw.text(((W - (bbox[2] - bbox[0])) // 2, 25), title, fill=(0, 200, 255), font=get_font(36, bold=True))

# ── USER PROMPT (top center) ──
ux, uy = W // 2 - 180, 90
rounded_rect(draw, [ux, uy, ux + 360, uy + 60], 10, (0, 100, 180), (0, 180, 255), 2)
draw.text((ux + 30, uy + 17), "User Prompt", fill=(255, 255, 255), font=font_box)

# ── STRANDS AGENT (center) ──
ax, ay = W // 2 - 160, 220
rounded_rect(draw, [ax, ay, ax + 320, ay + 90], 12, (0, 60, 120), (0, 200, 255), 3)
draw.text((ax + 50, ay + 15), "Strands Agent", fill=(0, 220, 255), font=font_title)
draw.text((ax + 25, ay + 55), "(Strands SDK + Amazon Bedrock)", fill=(140, 170, 200), font=font_small)

# Arrow from user to agent
arrow(draw, W // 2, 150, W // 2, 220, (0, 180, 255), 3)

# ── TOOL LAYER (left side) ──
tools = [
    ("discover_ics_assets", "Censys API v3"),
    ("search_threat_intel", "SerpApi / Tavily"),
    ("map_mitre_attack", "MITRE ATT&CK ICS"),
    ("check_cisa_kev", "CISA KEV Catalog"),
    ("get_geo_events", "GDACS / FIRMS / USGS / NOAA"),
    ("generate_dossier", "MD / PDF / JSON / STIX"),
    ("send_alert", "Slack / Webhook"),
]

ty_start = 380
for i, (name, desc) in enumerate(tools):
    ty = ty_start + i * 55
    tw = 340
    rounded_rect(draw, [80, ty, 80 + tw, ty + 45], 8, (25, 40, 65), (0, 140, 200), 1)
    draw.text((95, ty + 4), name, fill=(0, 200, 255), font=font_box)
    draw.text((95, ty + 26), desc, fill=(130, 150, 180), font=font_tiny)

# Arrow from agent to tools
arrow(draw, ax - 10, 265, 420, 400, (0, 140, 200), 2)

# ── DATA SOURCES (right side) ──
sources = [
    ("Censys", "ICS/SCADA Discovery"),
    ("SerpApi + Tavily", "OSINT News Intelligence"),
    ("MITRE ATT&CK", "ICS + Enterprise Matrix"),
    ("CISA KEV", "Known Exploited Vulns"),
    ("GDACS", "Global Disaster Alerts"),
    ("NASA FIRMS", "Active Fire Pixels"),
    ("USGS", "Earthquake Feed"),
    ("NOAA/NWS", "Weather Alerts (CAP)"),
]

sy_start = 350
for i, (name, desc) in enumerate(sources):
    sy = sy_start + i * 50
    sw = 340
    rounded_rect(draw, [W - 80 - sw, sy, W - 80, sy + 40], 8, (35, 25, 45), (140, 80, 200), 1)
    draw.text((W - 65 - sw, sy + 4), name, fill=(200, 150, 255), font=font_box)
    draw.text((W - 65 - sw, sy + 24), desc, fill=(150, 130, 170), font=font_tiny)
    if i < len(tools):
        # Arrow from tool to source
        t_y = ty_start + i * 55 + 22
        s_y = sy + 20
        arrow(draw, 80 + 340, t_y, W - 80 - 340, s_y, (80, 80, 120), 1)

# Arrow from agent to sources
arrow(draw, ax + 330, 265, W - 80 - 340, 380, (140, 80, 200), 2)

# ── OUTPUT (bottom center) ──
outputs = [
    ("SOC Dossier", "Markdown / PDF / CSV"),
    ("JSON Export", "Machine-readable"),
    ("STIX 2.1", "Threat Intel sharing"),
    ("P1 Alert", "Slack / Webhook"),
]

oy = 800
ow = 260
total_w = ow * 4 + 30 * 3
ox_start = (W - total_w) // 2
for i, (name, desc) in enumerate(outputs):
    ox = ox_start + i * (ow + 30)
    color = (180, 40, 40) if "P1" in name else (25, 60, 40)
    border = (255, 80, 80) if "P1" in name else (40, 180, 80)
    rounded_rect(draw, [ox, oy, ox + ow, oy + 55], 8, color, border, 2)
    draw.text((ox + 15, oy + 5), name, fill=(255, 255, 255), font=font_box)
    draw.text((ox + 15, oy + 30), desc, fill=(180, 200, 180), font=font_tiny)

# Arrow from tools to output
arrow(draw, W // 2 - 80, 770, W // 2, 800, (40, 180, 80), 2)

# Label
label = "Output Layer"
bbox = draw.textbbox((0, 0), label, font=font_small)
lw = bbox[2] - bbox[0]
draw.text(((W - lw) // 2, oy - 25), label, fill=(140, 160, 140), font=font_small)

# ── Labels ──
label_agent = "Agent Orchestration"
bbox = draw.textbbox((0, 0), label_agent, font=font_small)
aw = bbox[2] - bbox[0]
draw.text((W // 2 - aw // 2, ay - 20), label_agent, fill=(100, 160, 220), font=font_small)

label_tools = "Tool Registry (@tool)"
bbox = draw.textbbox((0, 0), label_tools, font=font_small)
draw.text((80, ty_start - 25), label_tools, fill=(0, 160, 220), font=font_small)

label_sources = "Data Sources"
bbox = draw.textbbox((0, 0), label_sources, font=font_small)
sw_label = bbox[2] - bbox[0]
draw.text((W - 80 - sw_label, sy_start - 25), label_sources, fill=(180, 130, 255), font=font_small)

out = "/home/z/my-project/strands-guardian/assets/architecture.png"
img.save(out, "PNG")
print(f"Architecture diagram saved: {out} ({os.path.getsize(out)} bytes)")
