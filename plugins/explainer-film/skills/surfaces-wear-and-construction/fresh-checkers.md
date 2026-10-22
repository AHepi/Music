# Fresh checkers (how to be checked honestly)

What this is: how a place is checked by helpers who did not build it, what they get, what they must say, and what
their answers look like. Builders are good at their own claims and bad at their own blind spots, so the check is done
by someone else.

**Example first (the Japanese garden, 22 October).** Three claims by builders did not survive a fresh checker:
- A builder claimed moss and mould covered 9.8 percent of the bridge planks. A fresh checker counted olive-green
  pixels in a 100 percent crop: 0.6 percent on one run of planks and 3.8 percent on the other. The planks looked clean
  and pale; the builder's number came from a flat top-down view with another formula.
- A report said "nothing vanished". The saved file had dropped 58 unused materials and one node group (they belonged
  to stages that had replaced them, so it was harmless, but the sentence was wrong).
- The integrator said a plank normal map failed its direction test (+0.061, the limit is +0.25). The checker found the
  test plane had the wrong shape for a long thin map; with the right plane the number was +0.55 (and +0.99 from the
  other side). The map was fine; the test was wrong.
Also found only by a fresh look: 48 leftover preview cameras in the scene file, pale clean planks, one knot stamped on
most planks, and moss cushions like rows of bean bags.

## The rules

1. The checker did not build the thing. It gets: the request, the style note, the acceptance list, the scene file and the
   pictures. It does NOT get the builders' reports or their numbers.
2. It gets the builders' CLAIMS as bare sentences ("every plank rests on at least two supports") and recomputes each
   with its own code, and where possible with a different formula.
3. It says plainly whether it was blind to the feature list.
4. It lists problems, each with the cheapest fix and the owner who should make it.
5. It says what it did not test.
6. It may not edit anything.

A second kind of checker looks at the process: money against the ledger, seconds against the reports, privacy (search every
file written for keys, ids, the name of the provider's settings folder and personal details), disk space, and leftovers (preview cameras, unused data
dropped on save).

After the fixes, a DIFFERENT fresh checker compares each old finding with the new pictures and looks for new faults,
because fixes make new faults (the garden's fix round made the squint score worse). One fix round, then stop.

## The result shape (the same for every checker)

```
{ "mode": "look" | "structure" | "process" | "blind_reader" | "recheck",
  "was_blind": true | false,
  "art_style_kept": "yes" | "nearly" | "no",
  "lived_in": "yes" | "nearly" | "no",
  "construction_makes_sense": "yes" | "nearly" | "no",
  "each_element": [ { "element": "...", "verdict": "...", "why": "..." } ],
  "claims_checked": [ { "claim": "...", "holds": true | false, "evidence": "..." } ],
  "problems": [ { "what": "...", "where": "...", "severity": "must fix" | "should fix" | "minor",
                  "cheapest_fix": "...", "owner": "..." } ],
  "should_fix_now": "...",
  "not_tested": [ "..." ],
  "measures": { } }
```

A blind reader (who has only the pictures, at half size) returns `{ "seen": [ "text", ... ] }`; the script counts how many
of the planned features appear in what it saw (the reading test). `explainer-film-place`'s judge,
`calculators/place_audit_check.py fresh FRESH_CHECK.json`, fails when a claim has `holds` false (unless the finding is
accepted) and gives a LOOK when `was_blind` or `not_tested` is missing. The preflight takes it as `--fresh-check`.

## The scripts a checker should write for itself

A scene fingerprint (objects, materials, node groups, light links); supports found by rays straight down; normal-map
wiring (Tangent, Non-Color, the Normal Map node's UV layer, where its output goes) and direction under a low light;
UV hygiene (a layer on every user, mirrored share); an ownership diff against the ownership file; 100 percent crops of
every changed place, with before and after strips side by side. Write each result to a file as you go.

## The honest limits

- The reading test was never run with a truly blind reviewer before. Its 12-of-16 line is a judgement.
- A checker can over-trust the builders' own test files. Let it write its own tests.
- A container restart can lose a checker's work (it did, once, in the garden): save results to files as you go, and
  say so in the result when something was lost.
- A checker's verdict on the look is an opinion with reasons. The person decides what to accept.
