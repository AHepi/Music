"""What this does (plain words): second part of the fix-round note changes: the exact sky wording, lessons 141 and 142, the Status fix-round bullet and
the story's log 38. Each swap must match exactly once. Run once: python3 -I fix_notes_2.py"""
import sys
ROOT = '/home/user/Music/austerity-explainer/project-notes/'
STORY = ROOT + 'Austerity explainer - project story.md'
STA = ROOT + 'Status.md'
LES = ROOT + 'Lessons.md'
edits = []
def swap(path, old, new): edits.append((path, old, new))

swap(STA,
"in the plain dark sky I saw no contour steps at normal or 3 times\n  contrast, and faint steps at 10 times, as in any 8-bit video;",
"in the plain dark sky I saw no contour steps at normal contrast, one faint\n  horizontal line in one frame at 3 times contrast, and faint steps at 10 times, as in any 8-bit video;")

# ---- lessons 141 and 142
swap(LES,
"""    Before reading a failed planning check as a fault in a change, look at the free disk first (log 37).
""",
"""    Before reading a failed planning check as a fault in a change, look at the free disk first (log 37).

141. **"Dot for dot" proved less than the notes said: this machine's drawing can speckle when only the text of the finishing code changes.** Eight
    comparison pictures drawn with the old and the new stage came out dot for dot the same, and the notes said no other scene changes, proved. A
    checker redrew a ninth (the house sample at 20 s) and found 160,257 of 2,073,600 dots (7.7 percent) different, by at most 7 of 255 (average
    0.07), only in rows 1007 to 1648, with no lighter or darker lean, and named the film grain. Drawn again (log 38): old against new came out
    identical in my drawing, but the old stage with one space added in the finishing code gave exactly those 160,257 dots, while two spaces, or a
    changed comment elsewhere in the file, gave none; and with the grain set to 0 the one-space edit still changed 5.9 percent of dots by at most
    6, so the grain is not shown to be the cause. The drawing here is sensitive to the exact text of the finishing code, whatever the change means.
    Fix: the notes now say what was measured. Next time draw a control (the old stage plus one space) beside the old and the new, judge a
    difference by its size against the control's, and say how many pictures were compared (log 38).
142. **Dollar signs were eaten when a record file was written through the shell.** `lockout-paintings.json` came out with `US/bin/bash.048` where
    `US$0.048` was meant (the shell read `$0` as its own name); a checker found it. Fix: `US$0.` put back and the file loaded again to check it is
    still valid. Write any text with prices through the file-writing tool or a quoted here-document, then search the file for `bin/bash` (log 38).
""")
swap(LES,
"- Before blaming a change for a failed planning check (the preflight's \"filming\" cases), check the free disk (lesson 140).\n",
"- Before blaming a change for a failed planning check (the preflight's \"filming\" cases), check the free disk (lesson 140).\n"
"- A \"dot for dot\" proof needs a control and a count of the pictures compared: this machine's drawing speckles when only the finishing code's text\n"
"  changes (lesson 141). After writing text with prices through the shell, search it for `bin/bash` (lesson 142).\n")

# ---- Status: the fix round
swap(STA,
"\n## Later (not started): the full set, an immersive camera, light that reacts to characters (decision 43)\n",
"""- **Fix round after a check (log 38):** notes only, nothing in the film changed and nothing was filmed again. The statements that said no other scene
  changes "dot for dot" now say what was measured (a faint speckle in a ninth picture; lesson 141); the prices in `lockout-paintings.json` got their dollar
  signs back (lesson 142); the filming times agree; the way back to dry is described as four renames and one look line; lesson 140 now says what was tried.
  Not fixed: the faint contour steps in the dark sky (invisible at normal contrast; filming again takes over an hour for nothing a viewer sees) and
  the plugin's and chapter 2's copies of the stage (outside this job).

## Later (not started): the full set, an immersive camera, light that reacts to characters (decision 43)
""")

# ---- story log 38
swap(STORY,
"""    - **Cost:** nothing (the two wet paintings were paid for in the wet street test: about US$0.20 to US$0.28 each).

## Next step
""",
"""    - **Cost:** nothing (the two wet paintings were paid for in the wet street test: about US$0.20 to US$0.28 each).

38. **The wet lockout notes corrected after a check** (21 October 2026, the same day as log 37; decision 43 unchanged). A fresh checker went over log 37's
    work and found notes that said more than was tested, a record file with damaged prices, and two sentences that disagreed. Nothing in the film
    changed and nothing was filmed again; the clip and the pictures sent with log 37 stand.
    - **Changed in the notes:** "no other scene changes / proved dot for dot" now says what was measured (decision 43, Status, Workflows step 8, the kit's
      traps, and the "Other scenes" line of log 37, in place, because log 37 had not been committed yet); the filming time in Workflows now agrees with
      log 37 (56 minutes for the wet clip and 71 for the dry, both while other drawing jobs shared the machine); the way back to dry is now said as "swap
      the wet pair of paintings for the dry pair (four renames) and change one look line", where Status, the next step and decision 43 had said "one rename";
      lesson 140 now says what was tried.
    - **Changed in a file:** the two price lines of `film-kit/assets/models/pit-village/lockout-paintings.json` had lost their dollar signs
      (`US/bin/bash.048`); they read `US$0.048` and so on again, and the file still loads.
    - **What was tried and found:** (1) I drew the house sample at 20 s again with the old stage, the new stage and variants of the old one. Old against
      new: identical in my drawing. Old plus one space in the finishing code against old: 160,257 dots (7.7 percent) different, at most 7 of 255, rows
      1007 to 1648, exactly the checker's numbers. Old plus two spaces, or a changed comment elsewhere in the file: identical to old. With the grain set to 0
      the one-space edit still changed 5.9 percent of dots by at most 6, so I could not confirm the checker's "it is the grain"; the speckle belongs to
      this machine's software drawing and its response to the text of the finishing code (lesson 141). (2) The two disk-space test cases: on a scratch copy
      of the plugin with the free-disk reading set to 50 GB, all 66 checks of that file passed; the plugin itself was not touched (lesson 140). (3) The
      clip's file: H.264 High, 1080 x 1920, 30 a second, 360 frames, 48 MB (32 megabits a second), index at the front, standard 4:2:0 colour, colour matrix
      tagged; at normal contrast the dark plain sky shows no contour steps in the three frames I looked at (1.5, 7.0 and 11.5 s); at 3 times contrast there is one
      faint horizontal line in the first; at 10 times faint steps (as in any 8-bit video).
    - **Not fixed, and why:** the faint contour steps (invisible at normal contrast, and a fix means filming for over an hour again); a phone was not
      used to play the clip; the plugin's and chapter 2's copies of the stage still lack `toe` (outside this job).
    - **What went wrong:** lessons 141 (a "dot for dot" proof with no control) and 142 (dollar signs eaten by the shell).
    - **Cost:** nothing.

## Next step
""")
swap(STORY,
"- The lockout shot is the wet street since log 37. Its wet and dry paintings swap as a pair, with the look line (`toe`, `vignette`); see `Workflows.md`.",
"- The lockout shot is the wet street since log 37. Its wet and dry paintings swap as a pair, with the look line (`toe`, `vignette`); see `Workflows.md`.\n"
"- Do not write \"dot for dot\" for a stage change without a control and a count of the pictures compared (log 38, lesson 141).")

for path, old, new in edits:
    n = open(path, encoding='utf-8').read().count(old)
    if n != 1:
        print('NOT EXACTLY ONCE (%d):' % n, path.split('/')[-1], '|', old[:80].replace('\n', ' ')); sys.exit(1)
for path, old, new in edits:
    t = open(path, encoding='utf-8').read(); open(path, 'w', encoding='utf-8').write(t.replace(old, new))
print('applied', len(edits), 'edits')
