#!/usr/bin/env python3
"""Generate Strands Guardian thumbnail for Devpost/YouTube."""

from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1920, 1080

def get_font(size, bold=False):
    """Try multiple font paths."""
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# Background gradient (dark blue → near-black)
img = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(img)
for y in range(H):
    t = y / H
    r = int(10 + 15 * t)
    g = int(15 + 25 * t)
    b = int(45 - 15 * t)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Accent bar at top
for y in range(4):
    draw.line([(0, y), (W, y)], fill=(0, 180, 255))

# Subtle grid pattern
for x in range(0, W, 80):
    draw.line([(x, 0), (x, H)], fill=(255, 255, 255, 8), width=1)
for y in range(0, H, 80):
    draw.line([(0, y), (W, y)], fill=(255, 255, 255, 8), width=1)

# Shield icon (simplified)
shield_cx, shield_cy = 280, 400
shield_size = 120
shield_points = [
    (shield_cx, shield_cy - shield_size),
    (shield_cx + shield_size * 0.85, shield_cy - shield_size * 0.5),
    (shield_cx + shield_size * 0.85, shield_cy + shield_size * 0.3),
    (shield_cx, shield_cy + shield_size),
    (shield_cx - shield_size * 0.85, shield_cy + shield_size * 0.3),
    (shield_cx - shield_size * 0.85, shield_cy - shield_size * 0.5),
]
draw.polygon(shield_points, fill=(0, 180, 255), outline=(100, 220, 255), width=3)

# Lock icon inside shield
lock_cx, lock_cy = shield_cx, shield_cy + 10
# Lock body
draw.rounded_rectangle([lock_cx - 25, lock_cy - 10, lock_cx + 25, lock_cy + 30], radius=5, fill=(10, 15, 35))
# Lock shackle
draw.arc([lock_cx - 18, lock_cy - 45, lock_cx + 18, lock_cy - 5], 180, 0, fill=(100, 220, 255), width=4)

# Title
font_title = get_font(72, bold=True)
font_sub = get_font(36)
font_small = get_font(28)
font_tag = get_font(24, bold=True)

# Strands Guardian title
title = "STRANDS GUARDIAN"
bbox = draw.textbbox((0, 0), title, font=font_title)
tw = bbox[2] - bbox[0]
draw.text(((W - tw) // 2, 150), title, fill=(0, 200, 255), font=font_title)

# Subtitle
subtitle = "Autonomous ICS/SCADA Threat Intelligence Agent"
bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
sw = bbox[2] - bbox[0]
draw.text(((W - sw) // 2, 250), subtitle, fill=(200, 210, 230), font=font_sub)

# Tagline
tagline = "Censys  |  MITRE ATT&CK  |  CISA KEV  |  Live Geo-Events"
bbox = draw.textbbox((0, 0), tagline, font=font_small)
tw2 = bbox[2] - bbox[0]
draw.text(((W - tw2) // 2, 320), tagline, fill=(140, 160, 190), font=font_small)

# Feature boxes
features = [
    ("\U0001f50d", "Discover", "Censys ICS/SCADA\nasset discovery"),
    ("\U0001f9ea", "Analyze", "OSINT + ATT&CK\n+ KEV mapping"),
    ("\U0001f30d", "Geo-Fuse", "GDACS, FIRMS,\nUSGS, NOAA"),
    ("\U0001f4cb", "Dossier", "SOC-ready MD/PDF\nJSON/STIX 2.1"),
]
box_w = 320
box_h = 180
start_x = (W - (box_w * 4 + 40 * 3)) // 2
box_y = 480

for i, (icon, title, desc) in enumerate(features):
    x = start_x + i * (box_w + 40)
    # Box background
    draw.rounded_rectangle([x, box_y, x + box_w, box_y + box_h], radius=12, fill=(20, 30, 55), outline=(0, 120, 200), width=2)
    # Accent dot
    draw.ellipse([x + 15, box_y + 15, x + 27, box_y + 27], fill=(0, 200, 255))
    # Title
    draw.text((x + 40, box_y + 12), title, fill=(0, 200, 255), font=get_font(26, bold=True))
    # Description lines
    lines = desc.split("\n")
    for j, line in enumerate(lines):
        draw.text((x + 20, box_y + 60 + j * 35), line, fill=(180, 195, 220), font=get_font(22))

# Bottom bar
bar_y = H - 80
for y in range(3):
    draw.line([(0, bar_y - 3 + y), (W, bar_y - 3 + y)], fill=(0, 180, 255))

# Built with Strands Agents SDK
built_text = "Built with Strands Agents SDK  |  Amazon Bedrock  |  AWS"
bbox = draw.textbbox((0, 0), built_text, font=font_small)
bw = bbox[2] - bbox[0]
draw.text(((W - bw) // 2, bar_y + 10), built_text, fill=(120, 140, 170), font=font_small)

# Hackathon tag
tag = "AGENTS FOR HUMANS HACKATHON 2026"
bbox = draw.textbbox((0, 0), tag, font=font_tag)
tagw = bbox[2] - bbox[0]
draw.rounded_rectangle(
    [W - tagw - 40, 380, W - 10, 380 + 40],
    radius=8, fill=(0, 180, 255)
)
draw.text((W - tagw - 20, 385), tag, fill=(255, 255, 255), font=font_tag)

# Save
out = "/home/z/my-project/strands-guardian/assets/thumbnail.png"
img.save(out, "PNG")
print(f"Thumbnail saved: {out} ({os.path.getsize(out)} bytes)")
