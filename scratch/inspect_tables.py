import pymupdf

doc = pymupdf.open('JGH_Intelligence_Engine_Report.pdf')

for page_idx, page in enumerate(doc):
    tables = page.find_tables()
    for t_idx, table in enumerate(tables.tables):
        bbox = table.bbox
        # Table bounding box: (x0, y0, x1, y1)
        # Check if table bbox exceeds margins (left margin ~50, right margin ~545)
        is_wide = bbox[0] < 45 or bbox[2] > 550
        cols = table.col_count if hasattr(table, 'col_count') else len(table.cols)
        print(f"P{page_idx+1:2d} T{t_idx+1}: bbox=({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}), cols={cols}, rows={table.row_count} {'*** TABLE WIDER THAN MARGINS ***' if is_wide else ''}")
        
        # Check cell contents and text positions within cells
        for r_idx, row in enumerate(table.extract()):
            for c_idx, cell in enumerate(row):
                if cell and len(str(cell)) > 30:
                    pass
