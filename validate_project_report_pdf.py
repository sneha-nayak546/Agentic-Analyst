from pathlib import Path

pdf_path = Path('PROJECT_REPORT.pdf')
print('exists', pdf_path.exists())
if pdf_path.exists():
    print('size', pdf_path.stat().st_size)
    with pdf_path.open('rb') as f:
        header = f.read(4)
    print('header', header)
    assert header == b'%PDF', 'PDF header mismatch'
else:
    raise FileNotFoundError(pdf_path)
