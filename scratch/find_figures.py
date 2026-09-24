import pymupdf

doc = pymupdf.open('JGH_Intelligence_Engine_Report.pdf')

for pno, page in enumerate(doc):
    for b in page.get_text('blocks'):
        txt = b[4].strip()
        if "Figure" in txt:
            print(f"Page {pno+1:2d}: {txt}")
