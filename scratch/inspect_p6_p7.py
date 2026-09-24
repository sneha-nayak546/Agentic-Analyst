import pymupdf

doc = pymupdf.open('JGH_Intelligence_Engine_Report.pdf')

for pno in [6, 7, 11]:
    page = doc[pno - 1]
    print(f"=== PAGE {pno} SHAPES ===")
    drawings = page.get_drawings()
    for d in drawings:
        r = d['rect']
        if d.get('fill') is not None and 100 < r.y0 < 350:
            print(f"Fill {d.get('fill')}: rect=({r.x0:.1f}, {r.y0:.1f}, {r.x1:.1f}, {r.y1:.1f})")
    
    # Also print text blocks in that region
    for b in page.get_text('blocks'):
        if 100 < b[1] < 350:
            txt = b[4].replace('\n', ' ')
            print(f"Text: ({b[0]:.1f}, {b[1]:.1f}) to ({b[2]:.1f}, {b[3]:.1f}): '{txt}'")
