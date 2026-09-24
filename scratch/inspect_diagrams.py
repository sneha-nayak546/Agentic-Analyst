import pymupdf

doc = pymupdf.open('JGH_Intelligence_Engine_Report.pdf')

print("=== PAGE-BY-PAGE DRAWINGS & DIAGRAMS ===")
for pno in range(len(doc)):
    page = doc[pno]
    drawings = page.get_drawings()
    # Filter out header/footer lines: y < 45 or y > 810
    diagram_shapes = [d for d in drawings if d['rect'].y0 >= 45 and d['rect'].y1 <= 810]
    # Check if there are rects/lines indicating a diagram (excluding simple table borders)
    # Tables also have rects/lines, but diagrams usually have colored rects, circles, or paths
    colored_shapes = [d for d in diagram_shapes if d.get('fill') is not None]
    if colored_shapes:
        min_x = min(d['rect'].x0 for d in colored_shapes)
        max_x = max(d['rect'].x1 for d in colored_shapes)
        min_y = min(d['rect'].y0 for d in colored_shapes)
        max_y = max(d['rect'].y1 for d in colored_shapes)
        print(f"Page {pno+1:2d}: {len(colored_shapes)} colored shapes, bbox=({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f}) | width={max_x-min_x:.1f}")
