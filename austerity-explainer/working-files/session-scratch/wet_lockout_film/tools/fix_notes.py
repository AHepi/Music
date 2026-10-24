"""What this does (plain words): applies the fix-round wording changes to the film project's notes, each as an exact old text -> new text swap that
must match exactly once (so nothing is changed by accident). Run once: python3 -I fix_notes.py"""
import sys
ROOT = '/home/user/Music/austerity-explainer/'
STORY = ROOT + 'project-notes/Austerity explainer - project story.md'
KIT_TRAPS = ROOT + 'film-kit/05 Lessons and traps.md'
DEC = ROOT + 'project-notes/Decisions.md'
STA = ROOT + 'project-notes/Status.md'
LES = ROOT + 'project-notes/Lessons.md'
WOR = ROOT + 'project-notes/Workflows.md'
edits = []
def swap(path, old, new): edits.append((path, old, new))

# ---------------------------------------------------------------- 1. the "dot for dot" overclaim
swap(KIT_TRAPS,
"""    that does not ask, and nothing else changes with it (checked dot for dot on eight stills). After a
    new painting, measure how bright the road arrives in the plate view against the painting
    (the wet lockout: 0.935, the dry one with the same look: 0.96).""",
"""    that does not ask, so no other scene's look changes (eight stills drawn with the old and the new stage are dot for dot
    the same; a ninth, the house sample at 20 s, differed in a checker's redraw only by a faint speckle, 7.7 percent of dots by at
    most 7 of 255 with no lighter or darker lean, which adding one space to the old finishing code also causes: project
    `Lessons.md`, lesson 141). After a new painting, measure how bright the road arrives in the plate view against the
    painting (the wet lockout: 0.935, the dry one with the same look: 0.96).""")

swap(DEC,
"so the dry look is one rename away (see `Workflows.md`). Overturn in one line.",
"so the dry look is a swap of the wet pair of paintings for the dry pair (four renames) and one look line away (see `Workflows.md`). Overturn in one line.")
swap(DEC,
"the lockout's look only, the dark frame edge eased from 0.30 to 0.25 with `toe: 1`. No other scene changes (checked dot for dot).",
"the lockout's look only, the dark frame edge eased from 0.30 to 0.25 with `toe: 1`. No other scene's look changes: eight stills are dot for dot the\n"
"  same, and a ninth (house sample, 20 s) differed in a checker's redraw only by a faint speckle (7.7 percent of dots, at most 7 of 255, no lighter or\n"
"  darker lean) of the kind that adding one space to the finishing code also causes (logs 37 and 38, lesson 141).")

swap(STA,
"- **Checked:** other scenes unchanged (eight pictures drawn with the old and the new stage file, 0 dots differ in all eight; the kit's two\n"
"  smoke-test pictures match its example stills);",
"- **Checked:** no other scene's look changes (eight pictures drawn with the old and the new stage file are dot for dot the same; a ninth, the house\n"
"  sample at 20 s, differed in a checker's redraw only by a faint speckle, 7.7 percent of dots by at most 7 of 255 with no lighter or darker lean, which\n"
"  adding one space to the old finishing code also causes: lesson 141; the kit's two\n"
"  smoke-test pictures match its example stills);")

swap(STORY,
"wet street\" and \"27 Wet lockout shot in the film - pictures\". Other scenes come out dot for dot the same.",
"wet street\" and \"27 Wet lockout shot in the film - pictures\". No other scene's look changes (eight comparison pictures are dot for dot the same; a ninth\n"
"  shows only a faint speckle: log 37; the notes were corrected after a check in log 38).")

swap(STORY,
"""      - Other scenes: eight pictures (the dry lockout drawn with the dry painting files, the notice corner twice, chapter 2 twice, chapter 1) drawn with
        the old and the new stage: 0 dots differ in all eight. The kit's own smoke test (two chapter 1 pictures) still matches its example pictures.""",
"""      - Other scenes: nine pictures drawn with the old and the new stage. In the first eight (the dry lockout drawn with the dry painting files, the
        notice corner twice, chapter 2 twice, chapter 1) 0 dots differ. A fresh checker redrew a ninth, the house sample at 20 s, and found 160,257 of
        2,073,600 dots (7.7 percent) different, by at most 7 of 255 (average 0.07), only in rows 1007 to 1648, with no lighter or darker lean: a faint
        speckle no viewer could see. (This entry first said "no other scene changes" for the other scenes; that was too strong, and log 38 says what was
        found.) I drew that picture again: old against new came out dot for dot the same in my drawing, but adding one space to the old stage's finishing
        code (which changes nothing in the maths) gave exactly the checker's 160,257 dots in the same rows, while two spaces, or a change to a comment
        elsewhere in the file, gave none. So the speckle comes from this machine's software drawing and depends on the exact text of the finishing code,
        not from `toe` (which is 0 there and does nothing); I could not show that it is the film grain (with the grain set to 0 the one-space edit still
        changed 5.9 percent of dots by at most 6). The kit's own smoke test (two chapter 1 pictures) still matches its example pictures.""")

swap(WOR,
"""   by default, so no other scene changes (proved on eight stills, dot for dot). Then draw the plate view and measure how
   bright the road arrives against the painting (the wet lockout: 0.935 of painted). Paint the front and the behind
   painting as a wet pair; never mix a wet front with a dry behind painting.""",
"""   by default, so no other scene's look changes (eight stills are dot for dot the same; a ninth, the house sample at 20 s,
   differs in a checker's redraw only by a faint speckle of at most 7 of 255, which adding one space to the finishing code also
   causes: lesson 141). To check other scenes after a stage change, draw each with the old stage and the new stage, and one
   more with the old stage plus one added space as a control, and judge a difference by its size against the control's. Then draw
   the plate view and measure how bright the road arrives against the painting (the wet lockout: 0.935 of painted). Paint the
   front and the behind painting as a wet pair; never mix a wet front with a dry behind painting.""")
swap(WOR,
"`paper-film/out/`, which is not kept). No other scene needs filming again, because the stage change leaves them dot for dot the same.",
"`paper-film/out/`, which is not kept). No other scene needs filming again, because the stage change leaves their look the same (step 8 above;\n"
"   at most a faint speckle can differ).")

# ---------------------------------------------------------------- 3. filming time agrees with the log
swap(WOR,
"""3. Film the lockout again (`bash paper-film/tools/film-chapter-parallel.sh lockout-test 2 240` from inside `film-kit/`; the wet clip took
   56 minutes with nothing else running much, more than an hour when other drawing jobs shared the machine; the output goes to""",
"""3. Film the lockout again (`bash paper-film/tools/film-chapter-parallel.sh lockout-test 2 240` from inside `film-kit/`; the wet clip took
   56 minutes in all (its two halves, filmed side by side, took 47 and 56) and the dry clip before it 71 minutes (62 and 71), while other
   drawing jobs were running on the machine, so plan for an hour or more; the output goes to""")
swap(STORY,
"""    - **What went wrong:** nothing in the film. The only failures were those two disk-space test cases. (Filming took 62 and 71 minutes for the two halves
      of the dry clip and 47 and 56 for the wet, because other drawing jobs were running at the same time.)""",
"""    - **What went wrong:** nothing in the film. The only failures were those two disk-space test cases (and, found later by a checker, notes that said
      more than was tested: log 38). (Filming took 62 and 71 minutes for the two halves of the dry clip and 47 and 56 for the wet; the halves ran side by
      side, so the whole clips took 71 and 56 minutes. Other drawing jobs were running on the machine at the time, so these are not the fastest times; the dry
      clip, filmed first, took longer than the wet one for the same work.)""")

# ---------------------------------------------------------------- 4. "one rename"
swap(WOR,
"To go back to the dry street (one rename and one look line, nothing else):",
"To go back to the dry street (swap the wet pair of paintings for the dry pair, which is four renames, and change one look line; nothing else):")
swap(STA,
"""If you want the dry street back it is one rename and one look line (`Workflows.md`, "The lockout shot:
  wet street or dry street").""",
"""If you want the dry street back, swap the wet pair of paintings for the dry pair (four renames) and change one look line
  (`Workflows.md`, "The lockout shot: wet street or dry street").""")
swap(STORY,
"tell me if you want the dry street back (one rename; `Workflows.md`).",
"tell me if you want the dry street back (swap the wet pair of paintings for the dry pair and change one look line; `Workflows.md`).")

# ---------------------------------------------------------------- 5. lesson 140 stated as fact
swap(LES,
"""    machine had about 1.3 GB. Nothing in the film, the stage or the paintings was wrong (the same checks pass with disk to spare).
    Before reading a failed planning check as a fault in a change, look at the free disk first (log 37).""",
"""    machine had about 1.3 GB. Nothing in the film, the stage or the paintings was wrong: on a scratch copy of the plugin in which the free-disk
    reading was set to 50 GB (the plugin itself untouched), all 66 checks of that test file passed (log 38; it also passed in log 35).
    Before reading a failed planning check as a fault in a change, look at the free disk first (log 37).""")
swap(STORY,
"""      - The kit's other checks: the plugin's tests (728 of 730 pass; the two that fail are the preflight's "filming is ready" cases, which need 4 GB of free
        disk while this machine had 1.3: lesson 140),""",
"""      - The kit's other checks: the plugin's tests (728 of 730 pass; the two that fail are the preflight's "filming is ready" cases, which need 4 GB of free
        disk while this machine had 1.3: lesson 140; in log 38 they passed on a scratch copy told there was room),""")

# ---------------------------------------------------------------- 6. phone playback: what was looked at
swap(STA,
"""- **Not checked:** watching at full speed or on a phone; sound""",
"""- **Not checked:** watching at full speed, and playing on a phone (the file is in the usual phone format, H.264, 1080 x 1920, 30 a second, with its index
  at the front, checked with the file inspector in log 38, but it was not played on one; in the plain dark sky I saw no contour steps at normal or 3 times
  contrast, and faint steps at 10 times, as in any 8-bit video; not fixed, because it cannot be seen and fixing it means filming again); sound""")
swap(STORY,
"""    - **Not checked, or unsure:** how it plays at full speed or on a phone; sound;""",
"""    - **Not checked, or unsure:** how it plays at full speed or on a phone (log 38 checked the file's format and the dark sky for contour steps, not a phone); sound;""")

# ---------------------------------------------------------------- headers and lesson list
swap(STA,
"**As of 2026-10-21 for the lockout shot (log 37); everything else as of 2026-10-15, afternoon.**",
"**As of 2026-10-21 for the lockout shot (logs 37 and 38); everything else as of 2026-10-15, afternoon.**")
swap(LES,
"## 2026-10-21 (the wet lockout shot in the film, log 37)",
"## 2026-10-21 (the wet lockout shot in the film, logs 37 and 38)")

for path, old, new in edits:
    text = open(path, encoding='utf-8').read()
    n = text.count(old)
    if n != 1:
        print('NOT EXACTLY ONCE (%d):' % n, path.split('/')[-1], '|', old[:70].replace('\n', ' '))
        sys.exit(1)
for path, old, new in edits:
    text = open(path, encoding='utf-8').read()
    open(path, 'w', encoding='utf-8').write(text.replace(old, new))
print('applied', len(edits), 'edits')
