import pymupdf
import sys
from pathlib import Path

doc = pymupdf.open('JGH_Intelligence_Engine_Report.pdf')
PAGE_W = 595.28
PAGE_H = 841.89

print("=== DIAGRAM / DRAWING EDGE ANALYSIS ===")
for i, page in enumerate(doc):
    drawings = page.get_drawings()
    # Header bar is at y < 50, footer bar is at y > 800
    body_drawings = [d for d in drawings if d['rect'].y0 > 50 and d['rect'].y1 < 800]
    for d in body_drawings:
        r = d['rect']
        # If any drawing rect is < 35 pt from left or > PAGE_W - 35 on right
        if r.x0 < 35 or r.x1 > PAGE_W - 35:
            print(f"Page {i+1:2d}: Drawing near edge: x0={r.x0:.1f}, x1={r.x1:.1f}, y0={r.y0:.1f}, y1={r.y1:.1f} (width={r.width:.1f})")

print("\n=== TEXT OUTSIDE MARGINS (< 40 or > 555) ===")
for i, page in enumerate(doc):
    blocks = page.get_text('blocks')
    for b in blocks:
        # b: (x0, y0, x1, y1, text, block_no, block_type)
        if b[1] > 50 and b[3] < 800:
            if b[0] < 40 or b[2] > 555.28:
                first_line = b[4].split('\n')[0][:60]
                print(f"Page {i+1:2d}: Text out: x0={b[0]:.1f}, x1={b[2]:.1f} | {first_line}")
