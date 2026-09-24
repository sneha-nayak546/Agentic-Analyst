import pymupdf

doc = pymupdf.open('JGH_Intelligence_Engine_Report.pdf')

print("=== CHECKING TEXT OVERFLOWING TABLE BOUNDS ===")
for page_idx, page in enumerate(doc):
    tables = page.find_tables()
    for t_idx, table in enumerate(tables.tables):
        t_box = table.bbox
        # Get all words on the page
        words = page.get_text('words') # (x0, y0, x1, y1, word, block_no, line_no, word_no)
        # Find words within the table's vertical span
        table_words = [w for w in words if t_box[1] <= (w[1] + w[3])/2 <= t_box[3]]
        
        # Check if any word extends beyond the table right boundary (by more than 2 points)
        overflow_words = [w for w in table_words if w[2] > t_box[2] + 2]
        if overflow_words:
            print(f"Page {page_idx+1:2d} Table {t_idx+1}: Right overflow! Table x1={t_box[2]:.1f}")
            for w in overflow_words[:8]:
                print(f"   Word: '{w[4]}' at x0={w[0]:.1f}, x1={w[2]:.1f}, y0={w[1]:.1f}")

        # table.cells is flat list of (x0, y0, x1, y1) bounding boxes of all cells
        for cell_idx, cell in enumerate(table.cells):
            if isinstance(cell, (tuple, list)) and len(cell) == 4:
                cx0, cy0, cx1, cy1 = cell
                cell_words = [w for w in table_words if cy0 <= (w[1]+w[3])/2 <= cy1 and w[0] >= cx0 - 2]
                cell_overflows = [w for w in cell_words if w[2] > cx1 + 3 and w[0] < cx1]
                if cell_overflows:
                    text_str = " ".join([w[4] for w in cell_overflows])
                    print(f"   Cell {cell_idx} overflow: cx1={cx1:.1f}, word_x1={cell_overflows[-1][2]:.1f}: '{text_str[:40]}'")
