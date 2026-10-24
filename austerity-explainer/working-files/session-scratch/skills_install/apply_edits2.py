import json, os, sys
ST = sys.argv[1]
EX = "scenario-blender-expert"
edits = [
 (EX, "SKILL.md",
  "Never install anything (no `npx`, `pip`, add-ons or extensions), never sign in to or call an outside service, and do not load add-ons.",
  "Never install or download anything (no `npx`, `pip`, add-ons or extensions), never sign in to or call an outside service, and load no add-on other than Blender's own bundled ones (Rigify, Node Wrangler), only when a task needs them.",
  "wording fix so the local rule does not contradict the previs/Rigify and Node Wrangler advice (bundled add-ons only, no download)"),
 (EX, "references/blender-5.2-deltas.md",
  "Get Extensions (online) or legacy zip;",
  "Get Extensions (online) or legacy zip (never do either here: nothing is downloaded or installed);",
  "remaining pointer to online extensions"),
]
log = json.load(open("edit_log.json"))
bad = 0
for skill, rel, old, new, why in edits:
    p = os.path.join(ST, skill, rel)
    t = open(p, encoding="utf-8", newline="").read()
    n = t.count(old)
    if n != 1:
        print("FAIL", n, rel, old[:60]); bad += 1; continue
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
    log.append({"file": f"{skill}/{rel}", "old": old, "new": new, "why": why, "count_before": n, "status": "applied (second pass)"})
    print("ok", rel)
json.dump(log, open("edit_log.json", "w"), indent=1)
print("failures", bad)
