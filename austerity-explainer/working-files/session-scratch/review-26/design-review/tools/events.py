import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
for r in rows:
    for k in r: r[k] = float(r[k])
# dips: luma < 8
print("DIPS / near-black stretches (luma<10):")
inb = False
for r in rows:
    if r['luma'] < 10 and not inb:
        inb = True; s = r['t']
    elif r['luma'] >= 10 and inb:
        inb = False; print(f"  {s:7.2f} - {r['t']:7.2f}")
if inb: print(f"  {s:7.2f} - end")
print("BIG CHANGES (diff > 12):")
for r in rows:
    if r['diff'] > 12: print(f"  t={r['t']:7.2f} diff={r['diff']:.1f} luma={r['luma']:.1f}")
# stillness: stretches where diff < 0.6 for > 1.5s
print("STILL stretches (diff<0.5 for >=2s):")
s = None
for r in rows:
    if r['diff'] < 0.5:
        if s is None: s = r['t']
    else:
        if s is not None and r['t'] - s >= 2.0: print(f"  {s:7.2f} - {r['t']:7.2f} ({r['t']-s:.1f}s)")
        s = None
