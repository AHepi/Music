# What this does: counts listener load per page in the newcomer narration, using the same four kinds as
# the first-round audit of the recorded chapter 2 (P place change, Y year or date, N number, T term,
# reference or new idea a newcomer must take in). Terms are split into "explained on the spot" (Te)
# and "still unexplained or explained late" (Tu), because the recorded audit counted both as load.
# Items are tagged by hand from narration-revised.txt. Speed: words at 150 and 164 words a minute
# (164 is what Malina actually ran on the recorded chapter 2), plus 0.6 s per "...".
# Run: python3 -I load_per_page.py /path/to/narration-revised.txt
import re, sys

ITEMS = {
    1: [("Te", "inflation (defined)"), ("Tu", "creates new money (who, how: page 2)"),
        ("Te", "the usual cure (glossed: loans cost more)")],
    2: [("P", "New Zealand"), ("Te", "the Reserve Bank (by what it does)"),
        ("Te", "it tries to stop prices going up too fast"),
        ("Te", "economists who study how modern money works"),
        ("Tu", "a government can't run out of its own money (claim, not unpacked; government vs Reserve Bank)"),
        ("Te", "workers, materials and machines as the limit")],
    3: [("Te", "two factories = a whole country"), ("Te", "the quiet factory"),
        ("Te", "new money spent on what the factory makes")],
    4: [("Te", "flat out / the flat-out factory")],
    5: [("Te", "spare"), ("Te", "most economists agree"), ("Te", "the rule: spare / none spare, once spent, mostly")],
    6: [("P", "Britain"), ("Y", "First World War"), ("Tu", "in uniform (idiom)"), ("N", "one in a hundred"),
        ("Te", "German submarines sank ships"), ("Te", "paid partly with new money"),
        ("Y", "end of the war"), ("N", "roughly doubled"), ("Te", "close to the flat-out factory")],
    7: [("Y", "1915"), ("P", "Glasgow"), ("Tu", "homes already short (idiom)"),
        ("Te", "builders and materials gone to the war"),
        ("Tu", "for homes, like the flat-out factory (picture re-mapped from a country to one kind of thing; no money in the scene)"),
        ("N", "up to a quarter"), ("Y", "November"), ("N", "twenty thousand"),
        ("Te", "refusing to pay the extra"), ("Te", "Britain's Parliament"),
        ("Te", "rents on small homes back to before the war")],
    8: [("P", "Japan (and a jump of a century)"), ("Y", "2013"), ("Te", "Japan's version of our Reserve Bank"),
        ("N", "double the money it had created"), ("N", "two years"), ("Tu", "the warning (callback to 0:15)")],
    9: [("N", "eight years"), ("N", "half a percent a year"), ("Te", "on average"),
        ("Tu", "sat in the banks (which banks, why)"), ("Te", "never reached the factory"),
        ("Te", "whether it's spent... and on what"), ("Te", "spare ... to make what it buys")],
    10: [("P", "here, New Zealand"), ("Y", "2020"), ("Te", "Reserve Bank created new money"),
         ("Tu", "help with wages (vague)"), ("Y", "end of 2021"), ("N", "three in a hundred"),
         ("N", "more than thirty years")],
    11: [("Te", "close to the flat-out factory"), ("Tu", "world prices, like oil (explained on page 15)"),
         ("Tu", "biggest push ... building new ones (heard as the activity, not its price)")],
    12: [("Te", "interest rate / interest (defined right after use)"), ("Te", "loans cost more, less to spend"),
         ("Te", "prices go up more slowly, not down"), ("Te", "the flat-out factory slows")],
    13: [("Y", "late 2021"), ("Y", "2023"), ("Y", "middle of 2026"), ("N", "nearly six in a hundred"),
         ("Te", "not the only reason")],
    14: [("Te", "our Reserve Bank and others like it"), ("Te", "Clara E. Mattei, the book this series follows"),
         ("Te", "the main goal (her view)"), ("Te", "power to ask for more pay")],
    15: [("Y", "June 2026"), ("N", "four point one percent"), ("N", "two point nine percent"),
         ("Tu", "if ... hadn't changed ... would have (counterfactual with decimals)"),
         ("Te", "fuel costs more -> almost everything made or moved"), ("Te", "in both factories")],
    16: [],
}

def split_pages(text):
    pages, title, lines = [], None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if title is not None:
                pages.append((title, " ".join(lines).strip()))
            title, lines = line[3:].strip(), []
        else:
            lines.append(line)
    if title is not None:
        pages.append((title, " ".join(lines).strip()))
    return pages

def words(text):
    out = []
    for w in re.findall(r"[A-Za-zɐ-ʯˈ'/-]+", text.replace("...", " ")):
        out.extend([p for p in w.split("-") if p])
    return out

pages = split_pages(open(sys.argv[1], encoding="utf-8").read())
print("page  words  s@150  s@164  P Y N Te Tu  all  per10s@150  per10s@164  longest-sentence")
tot = {"P": 0, "Y": 0, "N": 0, "Te": 0, "Tu": 0}
tw = ts150 = ts164 = 0
for i, (title, body) in enumerate(pages, 1):
    n = len(words(body)); pauses = body.count("...")
    s150 = n / 150 * 60 + pauses * 0.6
    s164 = n / 164 * 60 + pauses * 0.6
    kinds = [k for k, _ in ITEMS[i]]
    c = {k: kinds.count(k) for k in tot}
    for k in tot: tot[k] += c[k]
    allc = sum(c.values())
    sentences = [s for s in re.split(r"(?<=[.?])\s+", body) if s]
    longest = max(len(words(s)) for s in sentences)
    tw += n; ts150 += s150; ts164 += s164
    print(f"{i:4d}  {n:5d}  {s150:5.1f}  {s164:5.1f}  {c['P']} {c['Y']} {c['N']} {c['Te']:2d} {c['Tu']:2d}  {allc:3d}  {allc/s150*10:6.1f}      {allc/s164*10:6.1f}      {longest}")
allt = sum(tot.values())
print(f"TOTAL words {tw}; speech+pauses {ts150:.0f} s at 150, {ts164:.0f} s at 164")
print(f"items: P {tot['P']} Y {tot['Y']} N {tot['N']} Te {tot['Te']} Tu {tot['Tu']} = {allt}; "
      f"{allt/ts150*10:.1f} per 10 s at 150, {allt/ts164*10:.1f} at 164")
print(f"places+years+numbers: {tot['P']+tot['Y']+tot['N']} (recorded: 14+15+23 = 52)")
print("recorded chapter 2 for comparison: 689 words, 252 s, 100 items, 4.0 per 10 s")
