"""What this does: prints the word times file in a compact form for planning when things appear.

Use: python3 -I print_word_times.py WORD_TIMES.json
"""

import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    word_times = json.load(handle)

for page in word_times["pages"]:
    cue_list = ", ".join(f"{cue['text']}@{cue['start']:.2f}-{cue['end']:.2f}" for cue in page["cues"])
    print(f"== page {page['page']} ({page['name']}) cues: {cue_list}")
    entries = [f"{word['start']:.2f}-{word['end']:.2f} {word['text']}" for word in page["words"]]
    for index in range(0, len(entries), 6):
        print("   " + " | ".join(entries[index:index + 6]))
