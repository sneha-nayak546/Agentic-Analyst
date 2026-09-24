import pymupdf
import json

doc = pymupdf.open('JGH_Intelligence_Engine_Report.pdf')

figures_pages = [6, 7, 11, 14, 19, 20]

for pno in figures_pages:
    page = doc[pno - 1]
    print(f"\n==================== FIGURE ON PAGE {pno} ====================")
    # Find all text blocks that look like figure caption or labels
    for b in page.get_text('blocks'):
        txt = b[4].strip().replace('\n', ' ')
        if b[1] > 50 and b[3] < 800 and ('Figure' in txt or b[3] < 360):
            print(f"Text ({b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, {b[3]:.1f}): {txt[:80]}")
    
    # List unique drawing shapes
    drawings = [d for d in page.get_drawings() if d['rect'].y0 > 50 and d['rect'].y1 < 360]
    print(f"Total drawings in figure area: {len(drawings)}")
    rects = [d['rect'] for d in drawings if d.get('fill') is not None]
    print(f"Filled shapes count: {len(rects)}")
    for r in rects[:15]:
        print(f"   Filled rect: ({r.x0:.1f}, {r.y0:.1f}, {r.x1:.1f}, {r.y1:.1f}) w={r.width:.1f}, h={r.height:.1f}")
