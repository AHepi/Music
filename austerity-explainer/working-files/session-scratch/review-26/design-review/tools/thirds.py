import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
for r in rows:
    for k in r: r[k] = float(r[k])
pages = [(1,0.0,20.0),(2,20.0,42.6),(3,42.6,74.3),(4,74.3,94.8),(5,94.8,128.1),(6,128.1,155.6),(7,155.6,179.9),(8,179.9,207.9),(9,207.9,237.9),(10,237.9,270.4)]
print("page  top_luma top_edge | mid_luma mid_edge | bot_luma bot_edge | top20 edge | bot20 edge")
for p,a,b in pages:
    sel = [r for r in rows if a <= r['t'] < b and r['luma'] > 15]
    n = len(sel)
    f = lambda k: sum(r[k] for r in sel)/n
    print(f"{p:4d}  {f('top_luma'):7.1f} {f('top_edge'):7.3f} | {f('mid_luma'):7.1f} {f('mid_edge'):7.3f} | {f('bot_luma'):7.1f} {f('bot_edge'):7.3f} | {f('top20_edge'):7.3f} | {f('bot20_edge'):7.3f}")
