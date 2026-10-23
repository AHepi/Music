"""What this is: batched variation rounds. Instead of one small change, then a check, then another small change, a helper writes about 10 measurably different versions of one change,
and this package draws them all small and quick in up to 3 rented-card jobs at the same time, measures every picture, and shows ONE labelled contact sheet.
keys.py (the settings a variation may change, and how far apart two are), spec.py (read, check before drawing, split, estimate, make and refine), apply.py and worker.py (inside Blender),
cards.py (the two ways to talk to a rented card), compare.py (measures and the check after drawing), sheet.py (the contact sheet), runner.py (the whole batch), verb.py (the command line).
Nothing here imports Blender except apply.py and worker.py, so planning, measuring and the sheet work anywhere.
"""
