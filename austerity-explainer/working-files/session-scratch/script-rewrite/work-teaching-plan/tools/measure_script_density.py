# What this does: reads the recorded chapter 2 script and, for each page, counts spoken words,
# spoken numbers (written as words or digits) and sentences, and works out seconds per page from
# the page's recorded start and end times. Read-only; prints a table.
import re, sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
pages = re.split(r"^## ", text, flags=re.M)[1:]
number_words = r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|twenty|thirty|forty|fifty|hundred|hundreds|thousand|million|billion|billions|trillion|half|quarter|double|doubled|quadruples|percent|\d[\d,\.]*)\b"
total_words = total_numbers = 0
for page in pages:
    lines = page.strip().split("\n")
    title = lines[0]
    m = re.search(r"\((\d+):(\d+)–(\d+):(\d+)\)", title)
    seconds = (int(m.group(3))*60+int(m.group(4))) - (int(m.group(1))*60+int(m.group(2))) if m else 0
    spoken = " ".join(l for l in lines[1:] if l.strip() and not l.startswith("Research:"))
    spoken = re.sub(r"/[^/]+/", "X", spoken)
    words = len(re.findall(r"[A-Za-z0-9'’]+", spoken))
    numbers = len(re.findall(number_words, spoken, flags=re.I))
    sentences = len(re.findall(r"[.?!](\s|$)", spoken))
    total_words += words; total_numbers += numbers
    print(f"{title[:48]:48} words={words:3d} seconds={seconds:3d} number-words={numbers:2d} sentences={sentences:2d}")
print(f"TOTAL words={total_words} number-words={total_numbers}")
