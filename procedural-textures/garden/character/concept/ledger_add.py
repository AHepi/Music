#!/usr/bin/env python3
# usage: ledger_add.py "time" "step" "model+settings" best worst "price text" "request id"
# Appends one row under the "Japanese garden character" heading of the spending ledger and keeps the running total.
import sys, json, os
S = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work"
L = S + "/SPENDING - paid image generation ledger.md"
ST = S + "/garden/character/concept/ledger_state.json"
t, step, model, best, worst, price, rid = sys.argv[1:8]
best = float(best)
worst = float(worst)
st = json.load(open(ST)) if os.path.exists(ST) else {"best": 0.0, "worst": 0.0, "n": 0}
st["best"] = round(st["best"] + best, 4)
st["worst"] = round(st["worst"] + worst, 4)
st["n"] += 1
json.dump(st, open(ST, "w"))
row = "| %s | %s | %s | %s | %s | US$%.2f worst case / US$%.2f best case (of US$15.00; this step's cap US$8.00) |\n" % (
    t, step, model, price, rid, st["worst"], st["best"])
open(L, "a").write(row)
print(row.strip())
print(st)
