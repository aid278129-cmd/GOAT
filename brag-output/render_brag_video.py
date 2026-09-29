"""High-performance 1920x1080 motion graphics launch video renderer.
Implements the /brag and /brag-slim specification:
- 20 seconds @ 30 fps (600 frames)
- Audio layer: Happy Beats Business Moves Vol. 12 bed + synchronized SFX hits
- Scene 1: The Hook — Regulatory Gridlock
- Scene 2: Product DNA & Mandatory BIS Applicability
- Scene 3: Deterministic Evidence Gate (0% LLM Hallucination)
- Scene 4: Cryptographic Compliance Passport (SHA-256 Seal)
- Post-process: Extract poster frame at 16.0s (brag.jpg) and bake as frame 0 of brag.mp4
"""

import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH = 1920
HEIGHT = 1080
FPS = 30
DURATION_SEC = 20
TOTAL_FRAMES = FPS * DURATION_SEC

# Output paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_MP4 = os.path.join(BASE_DIR, "brag.mp4")
OUTPUT_POSTER = os.path.join(BASE_DIR, "brag.jpg")
TEMP_VIDEO = os.path.join(BASE_DIR, "temp_video_no_audio.mp4")

MUSIC_PATH = os.path.join(BASE_DIR, "composition", "assets", "music", "happy-beats-business-moves-vol-12-by-ende-dot-app.mp3")
SFX_REVEAL = os.path.join(BASE_DIR, "composition", "assets", "sfx", "impact", "impactSoft_medium_000.ogg")
SFX_SWITCH = os.path.join(BASE_DIR, "composition", "assets", "sfx", "interface", "switch_001.ogg")
SFX_BELL = os.path.join(BASE_DIR, "composition", "assets", "sfx", "impact", "impactBell_heavy_000.ogg")

# Palette
BG_COLOR = (7, 10, 19)
SURFACE_COLOR = (13, 18, 31, 235)
BORDER_COLOR = (30, 41, 59, 255)
CYAN_ACCENT = (56, 189, 248)
CYAN_GLOW = (56, 189, 248, 50)
EMERALD_GREEN = (16, 185, 129)
EMERALD_BG = (16, 185, 129, 35)
TEXT_WHITE = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)
TEXT_DIM = (100, 116, 139)

# Fonts
FONTS_DIR = r"C:\Windows\Fonts"
def get_font(name, size):
    path = os.path.join(FONTS_DIR, name)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

FONT_H1 = get_font("segoeuib.ttf", 74)
FONT_H2 = get_font("segoeuib.ttf", 46)
FONT_H3 = get_font("segoeuib.ttf", 32)
FONT_TITLE = get_font("segoeuib.ttf", 26)
FONT_BODY = get_font("segoeui.ttf", 20)
FONT_BODY_B = get_font("segoeuib.ttf", 20)
FONT_SUB = get_font("segoeui.ttf", 24)
FONT_MONO = get_font("consolab.ttf", 16)
FONT_MONO_SM = get_font("consola.ttf", 14)
FONT_BADGE = get_font("segoeuib.ttf", 15)

def ease_out_cubic(x):
    return 1 - pow(1 - x, 3)

def ease_in_cubic(x):
    return x * x * x

def clamp(val, min_v=0.0, max_v=1.0):
    return max(min_v, min(max_v, val))

# Pre-render base background with subtle radial gradient & cyber grid
def create_base_canvas():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    # Radial glow in upper center
    cx, cy = WIDTH // 2, int(HEIGHT * 0.35)
    for r in range(700, 0, -25):
        alpha = int((1.0 - r / 700.0) * 45)
        color = (15 + alpha, 28 + alpha, 56 + alpha)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    
    # Grid lines
    for x in range(0, WIDTH, 60):
        draw.line([(x, 0), (x, HEIGHT)], fill=(20, 32, 55), width=1)
    for y in range(0, HEIGHT, 60):
        draw.line([(0, y), (WIDTH, y)], fill=(20, 32, 55), width=1)
        
    return img

BASE_CANVAS = create_base_canvas()

def draw_top_nav(draw):
    # Logo Pill
    draw.rounded_rectangle([80, 36, 460, 78], radius=21, fill=(13, 18, 31, 230), outline=(56, 189, 248, 120), width=1)
    draw.ellipse([102, 50, 116, 64], fill=CYAN_ACCENT)
    draw.text((130, 46), "ZYNTRIX COMPLIANCE COMPILER", fill=TEXT_WHITE, font=FONT_TITLE)
    
    # Badge
    draw.rounded_rectangle([WIDTH - 380, 36, WIDTH - 80, 78], radius=21, fill=(56, 189, 248, 25), outline=(56, 189, 248, 100), width=1)
    draw.text((WIDTH - 355, 48), "SIH 2026 OFFICIAL SOLUTION", fill=CYAN_ACCENT, font=FONT_BADGE)

def render_frame(t):
    """Render a single frame at time t (in seconds)."""
    frame = BASE_CANVAS.copy()
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    draw_top_nav(draw)
    
    # -------------------------------------------------------------
    # SCENE 1: HOOK (0.0s - 4.0s)
    # -------------------------------------------------------------
    if t < 4.2:
        s1_alpha = 1.0
        if t < 0.6:
            s1_alpha = ease_out_cubic(t / 0.6)
        elif t > 3.6:
            s1_alpha = 1.0 - ease_in_cubic((t - 3.6) / 0.4)
            
        y_shift = int((1.0 - ease_out_cubic(clamp(t / 0.7))) * 35)
        
        # Kicker
        kicker_col = (*CYAN_ACCENT, int(255 * s1_alpha))
        draw.text((WIDTH//2, 330 + y_shift), "01 // REGULATORY GRIDLOCK SOLVED", fill=kicker_col, font=FONT_MONO, anchor="mm")
        
        # Big Headline
        h1_col = (*TEXT_WHITE, int(255 * s1_alpha))
        draw.text((WIDTH//2, 420 + y_shift), "20,000+ INDIAN STANDARDS.", fill=h1_col, font=FONT_H1, anchor="mm")
        
        # Cyan highlight line
        h2_col = (*CYAN_ACCENT, int(255 * s1_alpha))
        draw.text((WIDTH//2, 510 + y_shift), "Zero LLM Hallucinations in Regulatory Verdicts.", fill=h2_col, font=FONT_H1, anchor="mm")
        
        # Subtext
        sub_col = (*TEXT_MUTED, int(230 * s1_alpha))
        draw.text((WIDTH//2, 605 + y_shift), "Stop manually searching gazette PDFs. Zyntrix deterministically compiles product DNA", fill=sub_col, font=FONT_SUB, anchor="mm")
        draw.text((WIDTH//2, 642 + y_shift), "into certified BIS compliance pathways with cryptographic evidence assurance.", fill=sub_col, font=FONT_SUB, anchor="mm")

    # -------------------------------------------------------------
    # SCENE 2: PRODUCT DNA INGESTION (4.0s - 9.0s)
    # -------------------------------------------------------------
    elif t < 9.0:
        s2_t = t - 4.0
        s2_alpha = 1.0
        if s2_t < 0.5:
            s2_alpha = ease_out_cubic(s2_t / 0.5)
        elif s2_t > 4.6:
            s2_alpha = 1.0 - ease_in_cubic((s2_t - 4.6) / 0.4)
            
        card_w, card_h = 1360, 600
        cx, cy = (WIDTH - card_w) // 2, (HEIGHT - card_h) // 2 + 30
        
        # Main Card background
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=24, fill=(13, 18, 31, int(245 * s2_alpha)), outline=(56, 189, 248, int(130 * s2_alpha)), width=2)
        
        # Card Header
        draw.text((cx + 50, cy + 45), "STEP 1 • MULTIMODAL TECHNICAL INGESTION", fill=(*CYAN_ACCENT, int(255 * s2_alpha)), font=FONT_MONO)
        draw.text((cx + 50, cy + 80), "ThermoSteel TS-1000V-IND (1000 mL)", fill=(*TEXT_WHITE, int(255 * s2_alpha)), font=FONT_H3)
        
        # Top-right parsed badge
        bx, by = cx + card_w - 290, cy + 65
        draw.rounded_rectangle([bx, by, bx + 240, by + 44], radius=22, fill=(16, 185, 129, int(45 * s2_alpha)), outline=(16, 185, 129, int(160 * s2_alpha)), width=1)
        draw.text((bx + 20, by + 12), "✓ SPECIFICATION PARSED", fill=(*EMERALD_GREEN, int(255 * s2_alpha)), font=FONT_BADGE)
        
        draw.line([(cx + 50, cy + 145), (cx + card_w - 50, cy + 145)], fill=(255, 255, 255, int(25 * s2_alpha)), width=1)
        
        # 4 DNA parameter boxes
        boxes = [
            ("FOOD-CONTACT METALLURGY", "Austenitic SS 304 (04Cr18Ni10)", "IS 6911 Conformance Verified"),
            ("POLYMER STOPPER & SEAL", "Virgin Polypropylene & Platinum Silicone", "IS 9845 Food-Grade Migration (BPA-Free)"),
            ("GOVERNING INDIAN STANDARD", "IS 17526:2021 (Domestic Vacuum Flasks)", "Mandatory Scheme-I (ISI Mark)"),
            ("STATUTORY REGULATION", "DPIIT Domestic Water Bottles Order, 2023", "Compulsory Gazette QCO Enforced"),
        ]
        
        grid_w = (card_w - 140) // 2
        grid_h = 175
        for i, (lbl, val, tag) in enumerate(boxes):
            gx = cx + 50 + (i % 2) * (grid_w + 40)
            gy = cy + 175 + (i // 2) * (grid_h + 25)
            
            draw.rounded_rectangle([gx, gy, gx + grid_w, gy + grid_h], radius=16, fill=(15, 23, 42, int(220 * s2_alpha)), outline=(255, 255, 255, int(25 * s2_alpha)), width=1)
            draw.text((gx + 24, gy + 22), lbl, fill=(*TEXT_MUTED, int(255 * s2_alpha)), font=FONT_MONO_SM)
            draw.text((gx + 24, gy + 56), val, fill=(*TEXT_WHITE, int(255 * s2_alpha)), font=FONT_TITLE)
            
            # Badge inside box
            draw.rounded_rectangle([gx + 24, gy + 110, gx + grid_w - 24, gy + 148], radius=8, fill=(16, 185, 129, int(30 * s2_alpha)), outline=(16, 185, 129, int(90 * s2_alpha)), width=1)
            draw.text((gx + 38, gy + 120), f"✓ {tag}", fill=(*EMERALD_GREEN, int(255 * s2_alpha)), font=FONT_BADGE)

    # -------------------------------------------------------------
    # SCENE 3: EVIDENCE GATE & CLAUSE EVALUATION (9.0s - 14.5s)
    # -------------------------------------------------------------
    elif t < 14.5:
        s3_t = t - 9.0
        s3_alpha = 1.0
        if s3_t < 0.5:
            s3_alpha = ease_out_cubic(s3_t / 0.5)
        elif s3_t > 5.1:
            s3_alpha = 1.0 - ease_in_cubic((s3_t - 5.1) / 0.4)
            
        card_w, card_h = 1420, 620
        cx, cy = (WIDTH - card_w) // 2, (HEIGHT - card_h) // 2 + 30
        
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=24, fill=(13, 18, 31, int(245 * s3_alpha)), outline=(56, 189, 248, int(130 * s3_alpha)), width=2)
        
        # Header
        draw.text((cx + 50, cy + 40), "STEP 4 • DETERMINISTIC EVIDENCE GATE", fill=(*CYAN_ACCENT, int(255 * s3_alpha)), font=FONT_MONO)
        draw.text((cx + 50, cy + 72), "Empirical Clause Verification Matrix (IS 17526:2021)", fill=(*TEXT_WHITE, int(255 * s3_alpha)), font=FONT_H3)
        
        bx, by = cx + card_w - 380, cy + 60
        draw.rounded_rectangle([bx, by, bx + 330, by + 42], radius=21, fill=(16, 185, 129, int(45 * s3_alpha)), outline=(16, 185, 129, int(160 * s3_alpha)), width=1)
        draw.text((bx + 20, by + 11), "ALL 4 STATUTORY CLAUSES SATISFIED", fill=(*EMERALD_GREEN, int(255 * s3_alpha)), font=FONT_BADGE)
        
        clauses = [
            ("Clause 4.2.1", "Stainless Steel Chemical Metallurgy (Cr 18.2%, Ni 8.1%)", "SAIL Mill Test Certificate #MTC-304", "SATISFIED"),
            ("Clause 5.2", "Inversion Leakage Test (180° Inverted for 10 Minutes)", "NABL Accredited Report #NTH/044", "SATISFIED"),
            ("Clause 5.4", "Thermal Heat Retention (Initial 95°C -> 65.5°C after 6h >= 60.0°C)", "NABL Accredited Report #NTH/044", "SATISFIED"),
            ("Clause 7.1", "Statutory Product Markings & Reserved ISI License CM/L Space", "Packaging Artwork Declaration", "SATISFIED"),
        ]
        
        row_y = cy + 140
        row_h = 76
        for i, (c_code, c_desc, c_ev, c_res) in enumerate(clauses):
            ry = row_y + i * (row_h + 14)
            draw.rounded_rectangle([cx + 50, ry, cx + card_w - 50, ry + row_h], radius=14, fill=(15, 23, 42, int(200 * s3_alpha)), outline=(255, 255, 255, int(20 * s3_alpha)), width=1)
            
            draw.text((cx + 75, ry + 26), c_code, fill=(*CYAN_ACCENT, int(255 * s3_alpha)), font=FONT_TITLE)
            draw.text((cx + 250, ry + 27), c_desc, fill=(*TEXT_WHITE, int(255 * s3_alpha)), font=FONT_BODY)
            draw.text((cx + card_w - 460, ry + 28), c_ev, fill=(*TEXT_MUTED, int(255 * s3_alpha)), font=FONT_MONO_SM)
            
            # Pill tag
            px, py = cx + card_w - 170, ry + 20
            draw.rounded_rectangle([px, py, px + 95, py + 36], radius=18, fill=(16, 185, 129, int(35 * s3_alpha)), outline=(16, 185, 129, int(150 * s3_alpha)), width=1)
            draw.text((px + 12, py + 9), c_res, fill=(*EMERALD_GREEN, int(255 * s3_alpha)), font=FONT_BADGE)
            
        # Banner at bottom
        banner_y = cy + card_h - 75
        draw.rounded_rectangle([cx + 50, banner_y, cx + card_w - 50, banner_y + 48], radius=12, fill=(56, 189, 248, int(25 * s3_alpha)), outline=(56, 189, 248, int(100 * s3_alpha)), width=1)
        draw.text((WIDTH // 2, banner_y + 24), "⚡ 0% LLM AUTHORITY ON COMPLIANCE • DETERMINISTIC REGULATORY CERTAINTY", fill=(*TEXT_WHITE, int(255 * s3_alpha)), font=FONT_BADGE, anchor="mm")

    # -------------------------------------------------------------
    # SCENE 4: PASSPORT HERO & OUTRO (14.5s - 20.0s)
    # -------------------------------------------------------------
    else:
        s4_t = t - 14.5
        s4_alpha = 1.0
        if s4_t < 0.7:
            s4_alpha = ease_out_cubic(s4_t / 0.7)
            
        card_w, card_h = 1180, 560
        cx, cy = (WIDTH - card_w) // 2, (HEIGHT - card_h) // 2 + 35
        
        # Outer glow
        draw.rounded_rectangle([cx - 4, cy - 4, cx + card_w + 4, cy + card_h + 4], radius=30, fill=None, outline=(56, 189, 248, int(60 * s4_alpha)), width=3)
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=28, fill=(14, 23, 42, int(250 * s4_alpha)), outline=(56, 189, 248, int(180 * s4_alpha)), width=2)
        
        # Passport top badge
        bx, by = WIDTH // 2 - 140, cy + 45
        draw.rounded_rectangle([bx, by, bx + 280, by + 40], radius=20, fill=(16, 185, 129, int(45 * s4_alpha)), outline=(16, 185, 129, int(160 * s4_alpha)), width=1)
        draw.text((WIDTH // 2, by + 20), "● CRYPTOGRAPHICALLY ISSUED", fill=(*EMERALD_GREEN, int(255 * s4_alpha)), font=FONT_BADGE, anchor="mm")
        
        # Title
        draw.text((WIDTH // 2, cy + 135), "DIGITAL COMPLIANCE PASSPORT", fill=(*TEXT_WHITE, int(255 * s4_alpha)), font=FONT_H1, anchor="mm")
        draw.text((WIDTH // 2, cy + 195), "ThermoSteel 1000ml • Fully Certified for BIS Scheme-I (ISI Mark) Licensing", fill=(*TEXT_MUTED, int(255 * s4_alpha)), font=FONT_SUB, anchor="mm")
        
        # Standard mark badge
        draw.rounded_rectangle([WIDTH//2 - 250, cy + 240, WIDTH//2 + 250, cy + 295], radius=14, fill=(15, 23, 42, int(230 * s4_alpha)), outline=(56, 189, 248, int(110 * s4_alpha)), width=1)
        draw.text((WIDTH // 2, cy + 267), "SCHEME-I (ISI MARK) • IS 17526:2021 • LICENCE PRE-VERIFIED", fill=(*CYAN_ACCENT, int(255 * s4_alpha)), font=FONT_MONO, anchor="mm")
        
        # Hash Box
        hx, hy = WIDTH // 2 - 420, cy + 330
        draw.rounded_rectangle([hx, hy, hx + 840, hy + 50], radius=10, fill=(0, 0, 0, int(160 * s4_alpha)), outline=(56, 189, 248, int(90 * s4_alpha)), width=1)
        draw.text((WIDTH // 2, hy + 25), "SHA-256: e8b4f179d6c384a0b271d473489cf8b139265f24ad919421ea34cf640f2f3e82", fill=(*CYAN_ACCENT, int(255 * s4_alpha)), font=FONT_MONO_SM, anchor="mm")
        
        # Brand outro at bottom of card
        draw.text((WIDTH // 2, cy + 450), "ZYNTRIX • INTELLIGENT STANDARDS FOR MODERN INDUSTRY", fill=(*TEXT_WHITE, int(255 * s4_alpha)), font=FONT_TITLE, anchor="mm")
        draw.text((WIDTH // 2, cy + 488), "Accurate • Source-Backed • Zero Hallucination", fill=(*TEXT_MUTED, int(200 * s4_alpha)), font=FONT_BODY, anchor="mm")
        
    frame.paste(overlay, (0, 0), overlay)
    return frame


def render_video():
    print(f"Starting frame generation: {TOTAL_FRAMES} frames ({DURATION_SEC}s @ {FPS}fps)...")
    
    # Start ffmpeg process piping raw RGB frames
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        TEMP_VIDEO
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    
    for f in range(TOTAL_FRAMES):
        t = f / float(FPS)
        frame = render_frame(t)
        raw_bytes = frame.tobytes()
        proc.stdin.write(raw_bytes)
        if f % 60 == 0:
            print(f"  Rendered {f}/{TOTAL_FRAMES} frames ({int(t)}s / {DURATION_SEC}s)...")
            
    proc.stdin.close()
    proc.wait()
    print("Video frame encoding complete.")
    
    # Extract settled poster frame (at 16.0s = frame 480)
    print("Extracting poster frame (brag.jpg) at 16.0s...")
    poster_frame = render_frame(16.0)
    poster_frame.save(OUTPUT_POSTER, quality=95)
    print(f"Saved poster: {OUTPUT_POSTER}")
    
    # Multiplex audio: Music bed + SFX hits
    print("Multiplexing audio tracks (Music bed + SFX)...")
    filter_complex = (
        f"[1:a]volume=0.50,afade=t=out:st=18.5:d=1.5[m];"
        f"[2:a]adelay=4000|4000,volume=0.70[s1];"
        f"[3:a]adelay=9000|9000,volume=0.75[s2];"
        f"[4:a]adelay=14500|14500,volume=0.85[s3];"
        f"[m][s1][s2][s3]amix=inputs=4:duration=first:dropout_transition=2[a]"
    )
    
    final_cmd = [
        "ffmpeg", "-y",
        "-i", TEMP_VIDEO,
        "-i", MUSIC_PATH,
        "-i", SFX_REVEAL,
        "-i", SFX_SWITCH,
        "-i", SFX_BELL,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(DURATION_SEC),
        "-movflags", "+faststart",
        OUTPUT_MP4
    ]
    
    subprocess.run(final_cmd, check=True)
    
    # Bake poster into Frame 0 per brag rules
    print("Baking poster into Frame 0 of brag.mp4...")
    baked_temp = os.path.join(BASE_DIR, "brag_baked.mp4")
    bake_cmd = [
        "ffmpeg", "-y",
        "-i", OUTPUT_MP4,
        "-i", OUTPUT_POSTER,
        "-filter_complex", "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v]",
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        baked_temp
    ]
    subprocess.run(bake_cmd, check=True)
    
    if os.path.exists(OUTPUT_MP4):
        os.remove(OUTPUT_MP4)
    os.rename(baked_temp, OUTPUT_MP4)
    
    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)
        
    print(f"SUCCESS: Rendered complete launch video to {OUTPUT_MP4}")

if __name__ == "__main__":
    render_video()
