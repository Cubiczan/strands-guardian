#!/usr/bin/env python3
"""Fast demo video: generate minimal slide PNGs, compile with FFmpeg."""
import os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
F_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

fb = lambda s: ImageFont.truetype(F_BOLD, s)
fr = lambda s: ImageFont.truetype(F_REG, s)

def bg(c=(12,16,36)):
    img = Image.new("RGB", (W,H), c)
    d = ImageDraw.Draw(img)
    for x in range(0,W,80): d.line([(x,0),(x,H)],fill=(255,255,255,6))
    for y in range(0,H,80): d.line([(0,y),(W,y)],fill=(255,255,255,6))
    for y in range(3): d.line([(0,y),(W,y)],fill=(0,180,255))
    return img, d

def ctr(d,t,y,f,c=(200,210,230)):
    bb=d.textbbox((0,0),t,font=f); tw=bb[2]-bb[0]
    d.text(((W-tw)//2,y),t,fill=c,font=f)

D = tempfile.mkdtemp(prefix="sgf_")
slides = []

# 1) Title 6s
img,d = bg()
ctr(d,"STRANDS GUARDIAN",250,fb(80),(0,200,255))
ctr(d,"Autonomous ICS/SCADA Threat Intelligence Agent",370,fr(36))
ctr(d,"Built with Strands Agents SDK + Amazon Bedrock",435,fr(28),(120,150,180))
bb=d.textbbox((0,0),"AGENTS FOR HUMANS HACKATHON 2026",font=fb(26)); bw=bb[2]-bb[0]
bx=(W-bw)//2-15; d.rounded_rectangle([bx,510,bx+bw+30,555],radius=10,fill=(0,180,255))
ctr(d,"AGENTS FOR HUMANS HACKATHON 2026",515,fb(26),(255,255,255))
slides.append((img,6))

# 2) Problem 8s
img,d = bg()
ctr(d,"THE PROBLEM",100,fb(52),(255,100,100))
for i,t in enumerate([
    "SOC analysts spend 2-3 hours daily correlating ICS threats",
    "Jumping between 6+ tools: Censys, Google, ATT&CK, NOAA...",
    "Exposed SCADA devices get a raw IP and port. No context.",
    "A wildfire 40 miles away turns an exposure into a 5-alarm incident",
    "    and nobody connects the dots in time.","",
    "Every minute of delay = an exploitable window for adversaries.",
]):
    c=(220,180,180) if i<5 else (255,200,100) if i==6 else (200,200,200)
    d.text((140,220+i*70),t,fill=c,font=fr(32))
slides.append((img,8))

# 3) Who + Why 6s
img,d = bg()
ctr(d,"WHO IT'S FOR",80,fb(52),(0,200,255))
for i,t in enumerate([
    "SOC analysts at electric utilities and grid operators",
    "CISOs and security teams at critical infrastructure",
    "Infrastructure defenders at DHS CISA, FBI, and partners",
]):
    d.text((200,200+i*70),f"\u25cf  {t}",fill=(180,200,220),font=fr(32))
ctr(d,"Why it matters: Defenders need automation, not more dashboards.",580,fr(28),(255,200,100))
slides.append((img,6))

# 4) Architecture 10s
arch = Image.open("/home/z/my-project/strands-guardian/assets/architecture.png")
if arch.size!=(W,H): arch=arch.resize((W,H),Image.LANCZOS)
slides.append((arch,10))

# 5) Terminal demo - build as single image with all lines
img,d = bg((8,12,24))
d.rounded_rectangle([60,40,W-60,H-40],radius=12,fill=(15,20,35),outline=(0,80,140))
d.ellipse([80,52,96,68],fill=(255,80,80))
d.ellipse([104,52,120,68],fill=(255,200,50))
d.ellipse([128,52,144,68],fill=(80,255,80))
d.text((160,53),"strands-guardian \u2014 bash",fill=(100,120,150),font=fr(18))

term_lines = [
    ("$ strands-guardian \"Monitor grid assets in the Southeast US\" --mock", (0,255,150)),
    ("", None),
    ("strands-agents SDK not installed. Running in standalone/demo mode.", (255,200,100)),
    ("\U0001f916 Strands Guardian running in MOCK mode", (0,200,255)),
    ("\U0001f4ac Prompt: Monitor grid assets in the Southeast US", (180,190,210)),
    ("", None),
    ("======================================================================", (0,100,180)),
    ("  STRANDS GUARDIAN \u2014 Autonomous ICS Threat Intelligence Agent", (0,200,255)),
    ("======================================================================", (0,100,180)),
    ("  Scope: US | Radius: 200.0km | Mode: MOCK", (180,190,210)),
    ("", None),
    ("\U0001f50d Step 1: Discovering ICS/SCADA assets...", (0,200,255)),
    ("  Found 5 exposed ICS asset(s)", (0,255,150)),
    ("  \u2022 198.51.100.12:502 [Modbus TCP] (Houston, TX)", (180,200,220)),
    ("  \u2022 203.0.113.45:102 [Siemens S7] (Atlanta, GA)", (180,200,220)),
    ("  \u2022 192.0.2.88:20000 [DNP3] (Chattanooga, TN)", (180,200,220)),
    ("  \u2022 198.51.100.201:44818 [EtherNet/IP] (Charlotte, NC)", (180,200,220)),
    ("  \u2022 203.0.113.77:47808 [BACnet] (Nashville, TN)", (180,200,220)),
    ("", None),
    ("\U0001f9ea Analyzing [2/5] 203.0.113.45:102 [Siemens S7] (Atlanta, GA)", (0,200,255)),
    ("  \u251c\u2500 Found 1 threat intel result(s)", (180,200,220)),
    ("  \u251c\u2500 Mapped 2 ATT&CK technique(s)", (180,200,220)),
    ("  \u251c\u2500 1 CISA KEV match(es)", (255,200,100)),
    ("  \u251c\u2500 3 nearby geo-event(s)", (180,200,220)),
    ("  \u2502     \u2022 Active Fire Cluster (FRP=187) (40.2km N) [extreme]", (255,100,100)),
    ("  \u2502     \u2022 Volt Typhoon APT Activity (0.0km N) [severe]", (255,80,80)),
    ("  \u2502     \u2022 M4.7 earthquake (160.2km N) [moderate]", (255,200,100)),
    ("", None),
    ("\U0001f4cb Generating dossier...", (0,200,255)),
    ("  \u2514\u2500 Priority: P1 - CRITICAL", (255,60,60)),
    ("", None),
    ("\U0001f6a8 P1 CRITICAL \u2014 Sending alert!", (255,60,60)),
    ("  Alert status: Alert logged (no webhook configured)", (180,200,220)),
    ("  Saved: dossier_203_0_113_45_102.md, .json", (0,255,150)),
    ("", None),
    ("======================================================================", (0,100,180)),
    ("  ANALYSIS COMPLETE", (0,255,150)),
    ("======================================================================", (0,100,180)),
    ("  Assets analyzed: 5", (180,200,220)),
    ("  P1 CRITICAL: 1  |  P2 HIGH: 2  |  P3 MEDIUM: 2", (255,200,100)),
    ("  Dossiers saved to: ./dossiers/", (0,255,150)),
    ("======================================================================", (0,100,180)),
]
y = 80
for txt, col in term_lines:
    if not txt:
        y += 10
        continue
    d.text((90, y), txt, fill=col, font=fr(22))
    y += 26
slides.append((img, 50))

# 6) Dossier preview 10s
img,d = bg()
ctr(d,"GENERATED DOSSIER — P1 CRITICAL",70,fb(38),(255,100,100))
ctr(d,"203.0.113.45:102 [Siemens S7] (Atlanta, GA)",125,fr(26),(180,200,220))
dlines = [
    ("## MITRE ATT&CK Mapping", (0,200,255)),
    ("| T0885 | Remote System Discovery | Discovery | 92% |", (180,200,220)),
    ("| T0881 | Manipulation of Control | Inhibit Response | 88% |", (180,200,220)),
    ("", None),
    ("## CISA Known Exploited Vulnerabilities", (0,200,255)),
    ("- CVE-2024-89012: S7-1500 Unauthenticated Memory Access", (255,200,100)),
    ("", None),
    ("## Geo Situational Awareness", (0,200,255)),
    ("| Active Fire Cluster (FRP=187) | wildfire | extreme | 40.2km N |", (255,100,100)),
    ("| Volt Typhoon APT Activity | news | severe | 0.0km N |", (255,80,80)),
    ("| M4.7 earthquake Tennessee | earthquake | moderate | 160.2km N |", (255,200,100)),
    ("", None),
    ("> ACTION REQUIRED — Critical findings. Immediate attention.", (255,60,60)),
]
y=190
for txt,col in dlines:
    if not txt: y+=10; continue
    d.text((140,y),txt,fill=col,font=fr(24)); y+=34
slides.append((img,10))

# 7) Key features 8s
img,d = bg()
ctr(d,"KEY FEATURES",100,fb(52),(0,200,255))
for i,t in enumerate([
    "8 Strands Agent tools orchestrating the full intelligence pipeline",
    "Censys ICS/SCADA discovery + SerpApi/Tavily OSINT fusion",
    "MITRE ATT&CK ICS + Enterprise technique mapping with confidence",
    "CISA KEV cross-reference with ransomware-use flagging",
    "Live geo-event fusion: GDACS, NASA FIRMS, USGS, NOAA",
    "Haversine proximity with compass bearing (cross-border aware)",
    "SOC-ready dossier: Markdown, PDF, CSV, JSON, STIX 2.1",
    "P1 auto-alerting via Slack/webhook with context-rich messages",
]):
    d.text((160,210+i*65),f"\u2713  {t}",fill=(180,220,180),font=fr(24))
slides.append((img,8))

# 8) Strands SDK 8s
img,d = bg()
ctr(d,"BUILT WITH STRANDS AGENTS SDK",100,fb(48),(0,200,255))
for i,t in enumerate([
    "Strands SDK orchestrates all 7 tools via @tool decorator",
    "Amazon Bedrock (Claude) as the LLM reasoning engine",
    "Agent autonomously decides which tools to call and when",
    "Structured output parsing for reliable data flow",
    "Mock mode for zero-config demo / CI / development",
    "Optionally deployable via Amazon Bedrock AgentCore",
]):
    d.text((200,240+i*80),f"\u25b6  {t}",fill=(200,180,255),font=fr(28))
slides.append((img,8))

# 9) Closing 6s
img,d = bg()
ctr(d,"STRANDS GUARDIAN",200,fb(72),(0,200,255))
ctr(d,"Turning raw ICS exposures into actionable intelligence",320,fr(34))
ctr(d,"\u2014 one Strands agent at a time.",370,fr(34))
ctr(d,"Open Source  |  Apache 2.0  |  github.com/icohangar-ops/strands-guardian",480,fr(24),(120,150,180))
slides.append((img,6))

# Write slide images
for i,(img,dur) in enumerate(slides):
    p = os.path.join(D, f"slide_{i:02d}.png")
    img.save(p)
    print(f"Slide {i}: {dur}s -> {p}")

total_dur = sum(d for _,d in slides)
print(f"\nTotal duration: {total_dur}s ({total_dur/60:.1f} min)")

# FFmpeg concat file
concat = os.path.join(D, "concat.txt")
with open(concat, "w") as f:
    for i,(img,dur) in enumerate(slides):
        sp = os.path.join(D, f"slide_{i:02d}.png")
        f.write(f"file '{sp}'\n")
        f.write(f"duration {dur}\n")
    # Repeat last frame (ffmpeg concat demuxer quirk)
    f.write(f"file '{os.path.join(D, f'slide_{len(slides)-1:02d}.png')}')\n")

out = "/home/z/my-project/strands-guardian/demo/demo_video.mp4"
os.makedirs(os.path.dirname(out), exist_ok=True)

cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", concat,
    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    "-vf", "fps=24",
    out,
]
print(f"\nRunning FFmpeg...")
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
if r.returncode == 0:
    sz = os.path.getsize(out)/(1024*1024)
    print(f"Video saved: {out} ({sz:.1f} MB)")
else:
    print(f"FFmpeg error: {r.stderr[-1500:]}")

import shutil
shutil.rmtree(D, ignore_errors=True)
print("Cleaned up.")
