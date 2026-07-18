import fitz, sys

pdf = sys.argv[1]
keys = sys.argv[2:]
d = fitz.open(pdf)
for pno, page in enumerate(d):
    dd = page.get_text('dict')
    for bi, b in enumerate(dd['blocks']):
        if b['type'] != 0:
            continue
        for li, l in enumerate(b['lines']):
            txt = ''.join(s['text'] for s in l['spans'])
            if any(k in txt for k in keys):
                x0, y0, x1, y1 = l['bbox']
                fonts = {(s['font'], round(s['size'], 1)) for s in l['spans']}
                print(f'p{pno} b{bi} l{li} bbox=({x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}) {sorted(fonts)}')
                print(f'    TEXT: {txt!r}')
