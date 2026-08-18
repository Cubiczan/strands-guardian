#!/usr/bin/env python3
"""Generate 3-minute demo video for Strands Guardian using PIL + FFmpeg.

Creates slide frames, then compiles with FFmpeg into an MP4 video.
"""

import os
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 24
FRAMES_DIR = tempfile.mkdtemp(prefix="sg_frames_")

# Ensure output dir for .gitkeep
os.makedirs(FRAMES_DIR, exist_ok=True)

font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def get_font(size, bold=False):
    return ImageFont.truetype(font_bold if bold else font_reg, size)

def make_bg(color=(12, 16, 36)):
    img = Image.new("RGB", (W, H), color)
    draw = ImageDraw.Draw(img)
    # Subtle grid
    for x in range(0, W, 80):
        draw.line([(x, 0), (x, H)], fill=(255, 255, 255, 6), width=1)
    for y in range(0, H, 80):
        draw.line([(0, y), (W, y)], fill=(255, 255, 255, 6), width=1)
    # Top accent line
    for y in range(3):
        draw.line([(0, y), (W, y)], fill=(0, 180, 255))
    return img, draw

def text_center(draw, text, y, font, fill=(200, 210, 230)):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, fill=fill, font=font)

def save_frame(img, frame_num):
    path = os.path.join(FRAMES_DIR, f"frame_{frame_num:05d}.png")
    img.save(path, "PNG")
    return path

# Track frame counter
frame = [0]

def add_slide(img, duration_sec):
    """Duplicate an image for N seconds of video."""
    n = int(duration_sec * FPS)
    for _ in range(n):
        save_frame(img, frame[0])
        frame[0] += 1

def typewriter(draw, text, x, y, font, fill=(200, 220, 255), char_delay=2):
    """Add frames for typewriter effect."""
    for i, ch in enumerate(text):
        # Create fresh frame for each character
        img, d = make_bg()
        partial = text[:i+1]
        d.text((x, y), partial, fill=fill, font=font)
        for _ in range(char_delay):
            save_frame(img, frame[0])
            frame[0] += 1

# ── SLIDE 1: Title (6 seconds) ──
img, draw = make_bg()
text_center(draw, "STRANDS GUARDIAN", 280, get_font(80, True), (0, 200, 255))
text_center(draw, "Autonomous ICS/SCADA Threat Intelligence Agent", 400, get_font(36))
text_center(draw, "Built with Strands Agents SDK + Amazon Bedrock", 470, get_font(28), (120, 150, 180))
# Hackathon badge
badge = "AGENTS FOR HUMANS HACKATHON 2026"
bbox = draw.textbbox((0, 0), badge, font=get_font(26, True))
bw = bbox[2] - bbox[0]
bx = (W - bw) // 2 - 15
draw.rounded_rectangle([bx, 550, bx + bw + 30, 595], radius=10, fill=(0, 180, 255))
text_center(draw, badge, 555, get_font(26, True), (255, 255, 255))
add_slide(img, 6)

# ── SLIDE 2: The Problem (8 seconds) ──
img, draw = make_bg()
text_center(draw, "THE PROBLEM", 100, get_font(52, True), (255, 100, 100))
problems = [
    "SOC analysts spend 2-3 hours daily correlating ICS threats",
    "Jumping between 6+ tools: Censys, Google, ATT&CK, NOAA...",
    "Exposed SCADA devices get a raw IP and port. No context.",
    "A wildfire 40 miles away turns an exposure into a 5-alarm incident",
    "    and nobody connects the dots in time.",
    "",
    "Every minute of delay = an exploitable window for adversaries.",
]
for i, line in enumerate(problems):
    color = (220, 180, 180) if i < 5 else (255, 200, 100) if i == 6 else (200, 200, 200)
    draw.text((140, 220 + i * 70), line, fill=color, font=get_font(32))
add_slide(img, 8)

# ── SLIDE 3: Who It's For (6 seconds) ──
img, draw = make_bg()
text_center(draw, "WHO IT'S FOR", 100, get_font(52, True), (0, 200, 255))
for i, line in enumerate([
    "SOC analysts at electric utilities and grid operators",
    "CISOs and security teams at critical infrastructure",
    "Infrastructure defenders at DHS CISA, FBI, and partners",
    "Anyone protecting industrial control systems from cyber threats",
]):
    draw.text((200, 240 + i * 80), f"{chr(0x25cf)}  {line}", fill=(180, 200, 220), font=get_font(32))
text_center(draw, "Why it matters: Defenders need automation, not more dashboards.", 650, get_font(28), (255, 200, 100))
add_slide(img, 6)

# ── SLIDE 4: Architecture (10 seconds) ──
arch_img = Image.open("/home/z/my-project/strands-guardian/assets/architecture.png")
if arch_img.size != (W, H):
    arch_img = arch_img.resize((W, H), Image.LANCZOS)
add_slide(arch_img, 10)

# ── SLIDE 5: The Agent in Action — Terminal (45 seconds) ──
terminal_bg = (8, 12, 24)
for line_data in [
    # (text, color, pause_frames)
    ("$ strands-guardian \"Monitor grid assets in the Southeast US\" --mock", (0, 255, 150), 30),
    ("", (0, 0, 0), 8),
    ("strands-agents SDK not installed. Running in standalone/demo mode.", (255, 200, 100), 18),
    ("\U0001f916 Strands Guardian running in MOCK mode", (0, 200, 255), 18),
    ("\U0001f4ac Prompt: Monitor grid assets in the Southeast US", (180, 190, 210), 12),
    ("", (0, 0, 0), 6),
    ("======================================================================", (0, 100, 180), 8),
    ("  STRANDS GUARDIAN \u2014 Autonomous ICS Threat Intelligence Agent", (0, 200, 255), 10),
    ("======================================================================", (0, 100, 180), 8),
    ("  Scope: US | Radius: 200.0km | Mode: MOCK", (180, 190, 210), 10),
    ("", (0, 0, 0), 6),
    ("\U0001f50d Step 1: Discovering ICS/SCADA assets...", (0, 200, 255), 15),
    ("  Found 5 exposed ICS asset(s)", (0, 255, 150), 15),
    ("", (0, 0, 0), 4),
    ("  \u2022 198.51.100.12:502 [Modbus TCP] (Houston, TX)", (180, 200, 220), 8),
    ("  \u2022 203.0.113.45:102 [Siemens S7] (Atlanta, GA)", (180, 200, 220), 8),
    ("  \u2022 192.0.2.88:20000 [DNP3] (Chattanooga, TN)", (180, 200, 220), 8),
    ("  \u2022 198.51.100.201:44818 [EtherNet/IP] (Charlotte, NC)", (180, 200, 220), 8),
    ("  \u2022 203.0.113.77:47808 [BACnet] (Nashville, TN)", (180, 200, 220), 8),
    ("", (0, 0, 0), 6),
    ("\U0001f9ea Analyzing [2/5] 203.0.113.45:102 [Siemens S7] (Atlanta, GA)", (0, 200, 255), 15),
    ("  \u251c\u2500 Found 1 threat intel result(s)", (180, 200, 220), 10),
    ("  \u251c\u2500 Mapped 2 ATT&CK technique(s)", (180, 200, 220), 10),
    ("  \u251c\u2500 1 CISA KEV match(es)", (255, 200, 100), 10),
    ("  \u251c\u2500 3 nearby geo-event(s)", (180, 200, 220), 10),
    ("  \u2502     \u2022 Active Fire Cluster (FRP=187) (40.2km N) [extreme]", (255, 100, 100), 8),
    ("  \u2502     \u2022 Volt Typhoon APT Activity (0.0km N) [severe]", (255, 80, 80), 8),
    ("  \u2502     \u2022 M4.7 earthquake (160.2km N) [moderate]", (255, 200, 100), 8),
    ("", (0, 0, 0), 6),
    ("\U0001f4cb Generating dossier...", (0, 200, 255), 12),
    ("  \u2514\u2500 Priority: P1 - CRITICAL", (255, 60, 60), 18),
    ("", (0, 0, 0), 6),
    ("\U0001f6a8 P1 CRITICAL \u2014 Sending alert!", (255, 60, 60), 20),
    ("  Alert status: Alert logged (no webhook configured)", (180, 200, 220), 12),
    ("  Saved: dossier_203_0_113_45_102.md, .json", (0, 255, 150), 12),
    ("", (0, 0, 0), 6),
    ("======================================================================", (0, 100, 180), 8),
    ("  ANALYSIS COMPLETE", (0, 255, 150), 15),
    ("======================================================================", (0, 100, 180), 8),
    ("  Assets analyzed: 5", (180, 200, 220), 10),
    ("  P1 CRITICAL: 1  |  P2 HIGH: 2  |  P3 MEDIUM: 2", (255, 200, 100), 12),
    ("  Dossiers saved to: ./dossiers/", (0, 255, 150), 10),
    ("======================================================================", (0, 100, 180), 15),
]:
    text, color, pause = line_data
    img, draw = make_bg(terminal_bg)
    # Terminal window chrome
    draw.rounded_rectangle([60, 60, W - 60, H - 60], radius=12, fill=(15, 20, 35), outline=(0, 80, 140), width=1)
    # Terminal dots
    draw.ellipse([80, 72, 96, 88], fill=(255, 80, 80))
    draw.ellipse([104, 72, 120, 88], fill=(255, 200, 50))
    draw.ellipse([128, 72, 144, 88], fill=(80, 255, 80))
    draw.text((160, 73), "strands-guardian \u2014 bash", fill=(100, 120, 150), font=get_font(18))
    # Render accumulated lines up to current
    # For simplicity, render each line as its own "frame group"
    # Actually we need to build up. Let me collect all lines shown so far.
    # Simple approach: show the current line highlighted, with a few previous lines visible
    draw.text((100, 110), text, fill=color, font=get_font(26))
    for _ in range(pause):
        save_frame(img, frame[0])
        frame[0] += 1

# Better terminal approach: build up lines
# Let me redo this properly with cumulative lines
class TerminalVideo:
    def __init__(self):
        self.lines = []  # (text, color)
    
    def render(self, pause_frames):
        img, draw = make_bg((8, 12, 24))
        # Terminal window
        draw.rounded_rectangle([60, 50, W - 60, H - 50], radius=12, fill=(15, 20, 35), outline=(0, 80, 140), width=1)
        # Dots
        draw.ellipse([80, 62, 96, 78], fill=(255, 80, 80))
        draw.ellipse([104, 62, 120, 78], fill=(255, 200, 50))
        draw.ellipse([128, 62, 144, 78], fill=(80, 255, 80))
        draw.text((160, 63), "strands-guardian \u2014 bash", fill=(100, 120, 150), font=get_font(18))
        
        y = 100
        # Show last N lines that fit
        max_lines = 22
        visible = self.lines[-max_lines:]
        for text, color in visible:
            if text == "":
                y += 18
                continue
            draw.text((100, y), text, fill=color, font=get_font(24))
            y += 34
        
        for _ in range(pause_frames):
            save_frame(img, frame[0])
            frame[0] += 1
    
    def add(self, text, color=(180, 200, 220), pause=8):
        self.lines.append((text, color))
        self.render(pause)
    
    def blank(self, pause=4):
        self.lines.append(("", (0,0,0)))
        self.render(pause)

tv = TerminalVideo()
tv.add("$ strands-guardian \"Monitor grid assets in the Southeast US\" --mock", (0, 255, 150), 36)
tv.blank(12)
tv.add("strands-agents SDK not installed. Running in standalone/demo mode.", (255, 200, 100), 18)
tv.add("\U0001f916 Strands Guardian running in MOCK mode", (0, 200, 255), 18)
tv.blank(8)
tv.add("======================================================================", (0, 100, 180), 6)
tv.add("  STRANDS GUARDIAN \u2014 Autonomous ICS Threat Intelligence Agent", (0, 200, 255), 10)
tv.add("======================================================================", (0, 100, 180), 6)
tv.add("  Scope: US | Radius: 200.0km | Mode: MOCK", (180, 190, 210), 10)
tv.blank(6)
tv.add("\U0001f50d Step 1: Discovering ICS/SCADA assets...", (0, 200, 255), 18)
tv.add("  Found 5 exposed ICS asset(s)", (0, 255, 150), 15)
tv.blank(4)
tv.add("  \u2022 198.51.100.12:502 [Modbus TCP] (Houston, TX)", (180, 200, 220), 6)
tv.add("  \u2022 203.0.113.45:102 [Siemens S7] (Atlanta, GA)", (180, 200, 220), 6)
tv.add("  \u2022 192.0.2.88:20000 [DNP3] (Chattanooga, TN)", (180, 200, 220), 6)
tv.add("  \u2022 198.51.100.201:44818 [EtherNet/IP] (Charlotte, NC)", (180, 200, 220), 6)
tv.add("  \u2022 203.0.113.77:47808 [BACnet] (Nashville, TN)", (180, 200, 220), 6)
tv.blank(6)
tv.add("\U0001f9ea Analyzing [2/5] 203.0.113.45:102 [Siemens S7] (Atlanta, GA)", (0, 200, 255), 15)
tv.add("  \u251c\u2500 Found 1 threat intel result(s)", (180, 200, 220), 8)
tv.add("  \u251c\u2500 Mapped 2 ATT&CK technique(s)", (180, 200, 220), 8)
tv.add("  \u251c\u2500 1 CISA KEV match(es)", (255, 200, 100), 8)
tv.add("  \u251c\u2500 3 nearby geo-event(s)", (180, 200, 220), 8)
tv.add("  \u2502     \u2022 Active Fire Cluster (FRP=187) (40.2km N) [extreme]", (255, 100, 100), 8)
tv.add("  \u2502     \u2022 Volt Typhoon APT Activity (0.0km N) [severe]", (255, 80, 80), 8)
tv.add("  \u2502     \u2022 M4.7 earthquake (160.2km N) [moderate]", (255, 200, 100), 8)
tv.blank(6)
tv.add("\U0001f4cb Generating dossier...", (0, 200, 255), 12)
tv.add("  \u2514\u2500 Priority: P1 - CRITICAL", (255, 60, 60), 20)
tv.blank(6)
tv.add("\U0001f6a8 P1 CRITICAL \u2014 Sending alert!", (255, 60, 60), 24)
tv.add("  Alert status: Alert logged (no webhook configured)", (180, 200, 220), 10)
tv.add("  Saved: dossier_203_0_113_45_102.md, .json", (0, 255, 150), 10)
tv.blank(8)
tv.add("======================================================================", (0, 100, 180), 6)
tv.add("  ANALYSIS COMPLETE", (0, 255, 150), 15)
tv.add("======================================================================", (0, 100, 180), 6)
tv.add("  Assets analyzed: 5", (180, 200, 220), 8)
tv.add("  P1 CRITICAL: 1  |  P2 HIGH: 2  |  P3 MEDIUM: 2", (255, 200, 100), 12)
tv.add("  Dossiers saved to: ./dossiers/", (0, 255, 150), 8)
tv.add("======================================================================", (0, 100, 180), 20)

# ── SLIDE 6: Sample Dossier Preview (12 seconds) ──
img, draw = make_bg()
text_center(draw, "GENERATED DOSSIER", 80, get_font(44, True), (0, 200, 255))
text_center(draw, "203.0.113.45:102 [Siemens S7] (Atlanta, GA) \u2014 P1 CRITICAL", 145, get_font(28), (255, 100, 100))
dossier_lines = [
    ("# SOC Dossier: 203.0.113.45:102 [Siemens S7] (Atlanta, GA)", (0, 220, 255)),
    ("**Priority:** P1 - CRITICAL (score: 72.0/100)", (255, 100, 100)),
    ("", (0,0,0)),
    ("## MITRE ATT&CK Mapping", (0, 200, 255)),
    ("| Technique | Name | Tactic | Confidence |", (120, 140, 170)),
    ("| T0885 | Remote System Discovery | Discovery | 92% |", (180, 200, 220)),
    ("| T0881 | Manipulation of Control | Inhibit Response | 88% |", (180, 200, 220)),
    ("", (0,0,0)),
    ("## CISA Known Exploited Vulnerabilities", (0, 200, 255)),
    ("- **CVE-2024-89012** \u2014 S7-1500 Unauthenticated Memory Access", (255, 200, 100)),
    ("", (0,0,0)),
    ("## Geo Situational Awareness", (0, 200, 255)),
    ("| Active Fire Cluster (FRP=187) | wildfire | extreme | 40.2km N |", (255, 100, 100)),
    ("| Volt Typhoon APT Activity | news | severe | 0.0km N |", (255, 80, 80)),
    ("| M4.7 earthquake Tennessee | earthquake | moderate | 160.2km N |", (255, 200, 100)),
    ("", (0,0,0)),
    ("> \u26a0\ufe0f ACTION REQUIRED \u2014 Critical findings. Immediate attention.", (255, 60, 60)),
]
y = 200
for text, color in dossier_lines:
    if text == "":
        y += 12
        continue
    draw.text((140, y), text, fill=color, font=get_font(22))
    y += 32
add_slide(img, 12)

# ── SLIDE 7: Key Features (8 seconds) ──
img, draw = make_bg()
text_center(draw, "KEY FEATURES", 100, get_font(52, True), (0, 200, 255))
features = [
    "8 Strands Agent tools orchestrating the full intelligence pipeline",
    "Censys ICS/SCADA discovery + SerpApi/Tavily OSINT fusion",
    "MITRE ATT&CK ICS + Enterprise technique mapping with confidence scores",
    "CISA KEV cross-reference with ransomware-use flagging",
    "Live geo-event fusion: GDACS, NASA FIRMS, USGS, NOAA weather",
    "Haversine proximity with compass bearing (cross-border aware)",
    "SOC-ready dossier output: Markdown, PDF, CSV, JSON, STIX 2.1",
    "P1 auto-alerting via Slack/webhook with context-rich messages",
]
for i, f in enumerate(features):
    draw.text((160, 210 + i * 70), f"\u2713  {f}", fill=(180, 220, 180), font=get_font(26))
add_slide(img, 8)

# ── SLIDE 8: Strands SDK Integration (8 seconds) ──
img, draw = make_bg()
text_center(draw, "BUILT WITH STRANDS AGENTS SDK", 100, get_font(48, True), (0, 200, 255))
points = [
    "Strands SDK orchestrates all 7 tools via @tool decorator",
    "Amazon Bedrock (Claude) as the LLM reasoning engine",
    "Agent autonomously decides which tools to call and when",
    "Structured output parsing for reliable data flow",
    "Mock mode for zero-config demo / CI / development",
    "Optionally deployable via Amazon Bedrock AgentCore",
]
for i, p in enumerate(points):
    draw.text((200, 240 + i * 80), f"\u25b6  {p}", fill=(200, 180, 255), font=get_font(28))
add_slide(img, 8)

# ── SLIDE 9: Closing / CTA (8 seconds) ──
img, draw = make_bg()
text_center(draw, "STRANDS GUARDIAN", 200, get_font(72, True), (0, 200, 255))
text_center(draw, "Turning raw ICS exposures into actionable intelligence", 320, get_font(34), (180, 200, 220))
text_center(draw, "\u2014 one Strands agent at a time.", 370, get_font(34), (180, 200, 220))
text_center(draw, "", 440, get_font(24))
text_center(draw, "Open Source  |  Apache 2.0  |  agentsforhumans.devpost.com", 480, get_font(26), (120, 150, 180))
add_slide(img, 8)

total_frames = frame[0]
total_seconds = total_frames / FPS
print(f"Total frames: {total_frames}")
print(f"Estimated duration: {total_seconds:.1f}s ({total_seconds/60:.1f} min)")

# ── Compile with FFmpeg ──
output_path = "/home/z/my-project/strands-guardian/demo/demo_video.mp4"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

print(f"\nCompiling video with FFmpeg...")
print(f"Frames dir: {FRAMES_DIR}")
print(f"Output: {output_path}")

cmd = [
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", os.path.join(FRAMES_DIR, "frame_%05d.png"),
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "23",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    output_path,
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
if result.returncode == 0:
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nVideo saved: {output_path}")
    print(f"Size: {size_mb:.1f} MB")
else:
    print(f"FFmpeg error:")
    print(result.stderr[-2000:])

# Cleanup frames
import shutil
shutil.rmtree(FRAMES_DIR, ignore_errors=True)
print("Cleaned up frame files.")
