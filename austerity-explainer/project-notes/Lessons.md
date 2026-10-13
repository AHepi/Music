# Lessons

What this file is: things that went wrong while building or testing, and how each was fixed.
Only failures in doing the work belong here. Newest at the bottom.

## 2026-10-11

1. **The skill pointed to a folder that did not exist.** Its instructions named
   /mnt/skills/plugins/.../anidoodle, which was missing. The real files are under
   /root/.claude/plugins/synced/.../skills/anidoodle. Fix: searched the machine for the skill's
   tool files and used that folder.
2. **The skill's style-list helper failed inside a new project.** `registry.mjs` needs
   `styles.legacy.json`, which the project setup tool does not copy. Fix: read the style list from
   the skill's own `references/styles/INDEX.md` instead.
3. **A wrong label on a sample sheet.** The lighthouse sample was labelled "two-ink print" but uses
   several ink layers. Fix: relabelled "layered-ink print" and rebuilt the sheet before sending.
4. **Some research websites refused automated reading.** The 1914-1918 Online encyclopedia, Papers
   Past and the 1920 conference records on archive.org could not be opened. Fix: used other sources,
   and left out the facts that only those pages would have confirmed (listed in the research file).

5. **The sound check came out 3 seconds short.** The loudness step (ffmpeg's loudnorm) quietly
   switches audio to 192,000 samples a second, and the padding after it then miscounted. Fix:
   convert back to 48,000 right after the loudness step, and pad to an exact length
   (`apad=whole_dur`). Checked: 23 seconds asked, 23.04 seconds delivered.
6. **The music nearly vanished under the voice.** The first ducking setting pushed the music 31 dB
   under Malina. Fix: tried four settings, measured each, chose the one that puts the music about
   18 dB under the voice.
7. **The first temple engraving read as graph paper.** Shadows on the wall and in the doorway were
   ruled in a square grid of horizontal and vertical lines. Fix: cast shadows in horizontal lines
   only; deep shadow in horizontal lines crossed on a slant. Checked in close-ups at double size.
8. **The doorway then read as chain-link fence.** Three sets of crossing lines left large, regular
   white diamonds. Fix: two sets only, ruled heavier, so only small slivers of paper show.
9. **The columns looked flat and had a spiky fringe at the top.** The lit side had no lines at all,
   and the capital's shadow was drawn with short vertical strokes. Fix: hairlines across the lit
   side swelling into the shadow, and the capital's shadow in horizontal lines fading downward.
10. **A faint ring at the bottom of the page read as a drawn circle.** The old-spill mark was a
    closed ring in the middle of an empty area. Fix: a broken arc, fainter, in the corner.

11. **Levelling the narration pushed its peaks past full scale.** Turning every page to -16 LUFS
    left peaks at +0.2 dB, which would clip in an ordinary audio file. Fix: the narration track is
    kept in floating-point samples (which can go past full scale without damage) and the final mix's
    limiter holds the delivered peaks at -1.6 dB. Checked by measuring the finished mix.
12. **Some marks were tied to the wrong word.** Words that come twice on a page ("shells", "in",
    "a", "its", "it", "and", "prices", "the") were looked up by their first appearance, so a mark
    would have landed on the earlier word. Fix: every lookup now names which appearance it means
    (for example the second "shells"). Caught by checking every lookup against the recording before
    the first test picture.
13. **A cut-out T read as I** ("THREE PARIS"), a narrow cut-out I read as two lines or as a slash.
    Serif fonts give the T a foot like an I; outline and slanted fonts thin an I into strokes. Fix:
    those letters skip those fonts. Checked: every title re-drawn and read at full size; page 5's
    approved picture came out byte-for-byte unchanged.
14. **Layout collisions found in close-ups.** The BORN stamp covered the last letter of MATTEI; the
    birthday candle reached into the header strip; WORK MORE and CONSUME LESS overlapped; the flag on
    the factory was a tiny scribble; the shells and gold bars sat small and off-centre. Fix: moved and
    resized each, gave the flag a solid red cloth, re-centred both engravings, re-checked every page.

15. **The sound came out 5 milliseconds late.** The limiter that keeps peaks under clipping looks
    5 ms ahead, which delays everything by 5 ms. Found by lining up the film's sound against the
    narration track at every page. Fix: switched on the limiter's own delay compensation. Checked:
    0.00 ms at all ten pages. (5 ms cannot be heard, but the fix costs nothing.)
16. **The quality check counted a typing pause as a freeze.** Typing that waits for Malina's next
    word ("GENOA, 1922:" ... "SAME ADVICE") left 0.7 seconds with nothing new on screen, which the
    check flags unless it is declared. Fix: pauses in typing are now declared as rests, worked out
    from the typing itself. No picture changed, so the film did not need rendering again.

17. **The timing tool counted the accent instruction as spoken words.** The new instruction is
    several words long ("[in a warm, steady New Zealand accent]"), and the tool only knew one-word
    cues, so "a", "warm", "New", "Zealand" would have been timed as words Malina says. Fix: everything
    from the opening bracket to the closing one is now the instruction. Checked: the word counts match
    the script again. Still open: after a long instruction, ElevenLabs places the first real word up to
    0.3 seconds late (measured against the recording's actual start); to correct before re-timing pages.

18. **The late first word, fixed.** (Open item from 17.) Measured all ten new pages: ElevenLabs put
    the first word between 0.03 and 0.32 seconds after Malina actually starts (page 2 worst). Fix: the
    timing tool now finds where her voice begins in each recording and moves the first word back to
    it when the gap is more than 0.03 s, printing each change. Checked: nine pages corrected, page 3
    left alone (its first word was already right).
19. **The video samples got history wrong in ways the prompt did not ask for.** All five drew tanks
    from the Second World War (a turret on top), not the boxy First World War kind; all five show a
    tank rolling at the crowd, though the research says troops and tanks came after the clash. The
    linocut sample put a symbol on a placard that can read like a hooked cross; the night sample
    added a red-and-black flag, a real political flag of a particular movement. Fix for the real
    film: describe the tank's shape in the prompt (or give a reference picture), stage scenes from
    the research ledger, ask for blank placards, and check every clip frame by frame before use.

20. **No shadows at all in the first paper test.** Every piece is a flat sheet facing the lamp, and the
    3D library draws shadows from a sheet's back face only (to avoid speckles on solid objects), so a
    sheet lit from the front cast nothing. Found by lighting the scene with the lamp alone (shadows
    would show black: none did) and by a bare test with one card and one wall. Fix: every sheet casts
    from both faces. Checked: shadows show in the lamp-only picture and in the real frames.
21. **The smoothest soft shadows do not work in the hidden browser.** That kind needs a graphics
    feature the software renderer lacks (smooth filtering of half-precision images); it failed
    silently. Fix: the plain kind of shadow with widened, softened edges.
22. **The shadows were too small to see.** Pieces stood only half a unit in front of their page, so
    each shadow hid behind the piece's own paper margin, and dark cobbles hid the rest. Fix: pieces
    stand further out (soldiers 0.7, back crowd 1.25, tank 1.95, front crowd 2.7, miner 1.6), and the
    lamp is a larger share of the light. Then the words' shadows were so far off they read as a second,
    ghostly word; words now stand closer (0.55).
23. **The first page turn looked like a door swinging, and left white strips.** The page swung toward
    the camera around its left edge, and the pieces folded flat with it, showing as pale strips. Fix:
    the page peels from its bottom-right corner over a rolling cylinder of paper, and the pieces fold
    down and are put away before it turns.
24. **The first paper mouth looked like a black bar.** The jaw was cut as a wide rectangle and also
    tipped toward the camera, which made it look bigger and boxy. Fix: a narrower jaw with rounded top
    corners, a smaller drop, no tipping, and a mouth that opens only on the louder syllables (it hung
    open before because the loudness thresholds were too low).
25. **The dust from the tank's landing was invisible.** It burst behind the front crowd. Fix: the dust
    starts higher and in front of the tank, so it rises above the crowd's heads.

## 2026-10-12

26. **Two paintings failed their check.** The row of 1915 shells came out looking like rifle
    cartridges (brass cases, bullet tips), and a re-painted tank came out an odd shape. Fix: the shells
    were painted again as steel artillery shells with copper bands, one row of seven, and cut into seven
    separate pieces; the tank was dropped and page 3 keeps its approved tank. Found on contact sheets of
    every painting before cutting.
27. **The background remover dropped parts of three pictures.** It left out the politician's wooden
    lectern, made Sardinia faint on the map of Italy, and left the coal heap beside the small pithead
    half see-through. Found by laying every cut-out over bright magenta, where missing or faint parts
    show at once. Fix: the lectern is put back from its outline (measured from the painting's colours);
    the map is printed on a small paper card, with the land found by its colour against the plain
    background; the pithead uses a lower threshold for "solid".
28. **Words spoken twice were asked for by their first time, again** (Lesson 12): "war", "get" and
    "prices" each come twice on their page, so the shells, the BACK TO GOLD card and a price tag would
    have come in early. Caught by checking every word lookup against the page's text before filming.
29. **Dust stayed on screen after its page had gone.** When single moments were drawn out of order for
    checking, dust from page 8's gold landing showed up on pages 9 and 10 and on the last blank page.
    Dust and smoke were not put away with their page's pieces. Fix: they now belong to their page and
    are hidden with it. (Filming in order would mostly have hidden this, but a chunk starting mid-way
    could not rely on it.)
30. **Knocked-down pieces near the bottom of the frame showed as pale shapes.** A piece "slapped flat"
    lies toward the camera like a shelf; seen from above, the kitchen table's legs and the flattened pay
    packet showed their plain paper backs as pale blobs. Fix: those pieces fold down and disappear; only
    the squashed pay packet under the iron weight on page 1 (high in the frame, where it reads as
    squashed) stays flat for a moment.
31. **Pieces near the sides were cut off by the frame edge.** A piece standing in front of the page
    looks bigger than its size on the page (it is nearer the camera), so pieces placed to the page's edge
    poked out of the frame. Fix: the factory, price tag, pay packet, basket, school, farm and pithead
    were moved in or made a little smaller; the rule is to keep a piece's edge within the frame at its
    own distance (about 4.1 units from the middle, less for pieces further forward).
32. **A falling word looked washed out, with a ghost behind it.** POWER stood far from the page, so its
    shadow read as a second word (Lesson 22 again), and the dust from its landing burst in front of it.
    Fix: falling words stand at the same distance as other words (0.55) and their dust bursts behind them.
33. **The motion maths divided by zero for a walk with no bounce.** A spring set to no overshoot at all
    (damping 1) gave "not a number", which would have frozen the worker on page 9. Caught when reading
    the code before filming. Fix: the spring has a separate formula for no overshoot.
34. **Filming two halves at once was no faster.** Two hidden browsers side by side took as long for 90
    frames as one browser alone (the machine's two processors are already busy with one). Fix: the
    chapter is filmed one page-sized chunk after another (about 0.85 seconds a frame), which also lets a
    single page be filmed again alone.

35. **Two mistakes in the kit's papers, caught on re-reading.** The paintings ledger filed the shell
    painting as a figure (its number starts with 2, which the sorting rule took for figures), and the
    guide first gave chapter 1 as about 2,500 words (it is about 520 spoken words). Fix: the shells are
    filed as an object and the prompts guide's tables were remade; the word count was corrected
    against the word times.
36. **The folded-paper trees came out almost black.** The lamp clearly lit the paper around them, but
    the trees stayed dark even in plain white. A check with their shadows switched off showed them lit
    properly, so they were shading themselves: the shadow is pushed off each surface along the way
    the surface faces, and the tree surfaces had been built facing inward, so the push went into the
    tree. Fix: no push along the surface for folded props, a slightly larger plain depth margin instead.
37. **The paper crane did not read as a crane from above.** Seen from a high camera, its wings and
    neck flattened into a jumble of spikes (its shadow looked more like a bird than it did). Fix: it is
    turned side-on with the neck rising at the front, the head folded down, the tail rising at the back
    and both wings raised, and the camera came down a little. Checked in close-ups after each change.
38. **The oak's leaves were chopped off in a straight line.** Its sheet of paper was narrower than its
    crown, so leaves past the edge were simply missing. Fix: a wider sheet, with the tree's shape
    measured from its height so widening the sheet doesn't stretch it.
39. **The open pages read as upright walls.** The printed meadow was tiny upright strokes, which from
    the reader's angle look like grain on a wall, and a dark band beside the spine plus a hard crease
    made a box corner. Fix: a rounded fold, a lighter band, and printed things that only read as lying
    flat (a pond drawn as an ellipse, garden rows, round flowers, a stone path).
40. **Faint rings rippled across the pages, and the moon's shadows criss-crossed the lamp's.** The
    rings came from the lamp's shadow being set too tight; the moon's own shadows made the page
    confusing. Fix: a larger shadow margin, and the moon lights without casting shadows.
41. **The first distance picture was too coarse, and the first blur ate the detail.** The paper stage's
    built-in distance drawing squeezed near and far into a few shades, and a strong blur turned the
    oak's leaves and the hills to mush. Fix: a small custom distance drawing spread evenly from near to
    far, and a much gentler blur.
42. **Light leaked out of the cottage's back windows** onto the cypresses, making an odd orange block
    behind the house. Fix: the back wall is solid.
43. **The browser in this machine refused the old "headless" mode.** Fix: the filming tool now looks
    for Playwright's small headless browser first.
44. **A shared 3D helper failed to load inside the browser** because it named its library in a way
    browsers can't follow on their own. Fix: the stage page tells the browser where that library is.
45. **Words said with a trailing "..." didn't match.** "arrives..." wasn't found as "arrives". Fix: all
    trailing dots are dropped when matching words to times.
46. **A word said twice matched the wrong time.** "the machines stand idle" was found instead of the
    later "machines". Fix: ask for the second time it is said (lesson from chapter 1, again).
47. **The first factories page was too close, too bright and cut its labels off.** White boxes filled
    the frame and labels ran off the edge. Fix: the factories stand on a diagonal, the camera starts
    wide, brick and window panes are printed on the card, exposure is lower, and every label keeps
    itself inside the frame.
48. **Moving the camera far inside a painted room tears it.** Thin near things (pillars, cables)
    smear, and the camera sees past the painting's bottom edge as stretched streaks. Fix: small
    moves (1 to 2 units), a softer distance picture, and past the edge the painting is mirrored, which
    passes for more floor.
49. **Models inside a dark painting looked white.** Banknotes came out as white bricks: the soft grey
    "reflection room" that lights shiny things was lighting them far more than the painting's own
    light. Fix: a reflections setting, turned down to 0.3 inside paintings, and banknote edges printed
    as fine green lines.
50. **"43.2,47.5" is not two times.** The filming tool wants still times separated by spaces; with a
    comma it reads one broken number and fails on the second still.
51. **One page's words showed on the next during page turns.** Only when frames were drawn one after
    another; a single test frame looked clean. The browser sometimes reused an old copy of the
    graphics layer when two pages were drawn in one frame. Fix: the graphics layer is copied out pixel
    by pixel for every page, and fully reset before each. Check page turns in ONE run of stills.
52. **Period figures in a present-day street.** 1920s out-of-work men stood in today's New Zealand
    street on page 10. Fix: a hundred-dot panel (3 then 6 empty), echoing page 2's 1915 panel.
53. **The independent critique found what the page builders and I had missed** (seven critics and a
    skeptic): price boards cut off at the right edge on the central page; pale labels on pale walls;
    a key figure still counting while said; a dial sliding as if rates were cut; a broken transition;
    a party-coloured tie; a caricature adding a claim. Fix: all repaired before filming; the lessons
    are now in the plugin's page guide. Lesson: get the critique BEFORE filming starts, not during.
54. **Stopping a filming job with a name pattern can stop your own command.** `pkill -f` with the
    script's name matched the shell running the command and killed it. Fix: stop the job manager and
    each drawing process by its number.
55. **The card house looked unfinished** (your note: "sparse in detail"). It was a box with a roof and two
    lit squares. Fix: a detailed card villa (weatherboards, hipped iron roof with ridge caps, chimney
    with pots, bay window under a gable with fretwork, tall sash windows, a verandah with brackets
    and a railing, a panelled door) on a small lawn with a picket fence, turned to show its depth in
    the street. Two critics (a model maker and a film director) reviewed it first; their best points
    went in. Lesson: a hero prop needs as much detail as the paintings around it.
56. **Filming stopped silently for 90 minutes.** The cloud machine restarted at about 5pm and ended the
    background filming job; the watcher only looked for "finished", so nothing noticed. Fix: run the
    filming script again (finished stretches are kept); the watcher now also stops when the script is
    no longer running.

57. **A camera that never stops reads as restless on a phone.** Most pages crept or drifted for their
    whole length (page 1: one slow push for 20 seconds; pages 3 and 8 never held still). The camera
    rule is now built into the engine: `kit.stillShot` holds still and allows only named moves from
    the viewer's grammar, at most three per shot, and refuses a fourth. A checker measures every shot
    of the film in seconds (`--camera` then `camera_audit.py`).
58. **Measure camera moves against the thing in focus, not the aim point.** In a painted room the
    camera aims at a point 30 units away, so a real one-unit move looked tiny to the first checker.
    Using the focus distance fixed it.
59. **Plain card boxes look poor beside detailed paintings.** The old factory was about 2,000
    triangles with printed brick; the new one, built in Blender by script, is about 22,000 with real
    window openings, sills, copings, gutters, a sawtooth roof with lit glass and a chimney with bands.
    It is still light enough for the software renderer.
60. **Blender's MCP server works headless and earns its place.** It does pass Python to Blender (which
    `pip install bpy` also allows), but its own guidance, its search of Blender's bundled manual and
    Python reference, its scene inspection and its quick thumbnails taught the model-making (lesson
    67). Blender's renderer is far too slow to film with here (35 to 90 seconds a frame), so Blender
    builds the models and the stage films them.
61. **Baking corner shading: keep it local and small.** Blender's default reach (10 units) darkened
    whole walls, and 2048 pixels at 48 samples took 12 minutes on a busy machine. A reach of 0.6,
    1024 pixels and 32 samples took 2 minutes and looks right. A part left out of the bake must not
    share a material with a baked part, or it turns dark brown (the kerb did).
62. **Blender adds ".glb" to any file name that doesn't end in it** ("factory-a.glb.new" became
    "factory-a.glb.new.glb", and the rename after it failed).
63. **Frame with numbers before rendering.** `frame_check.py` says where each thing lands in the tall
    frame for a camera position, in a second. It found price boards off the edge and cut-outs too
    wide for the frame before any still was made.
64. **A tall frame needs things stacked in depth, not side by side.** Three cut-outs in a row were 2.4
    units wide and fell off both edges; staggered front to back, they fit large. Soft barrels, crates
    and a cart in the near corners fill the bottom third.
65. **Corner checks miss a flat card's middle.** The clearance check now samples points across every
    face, and the overlap check ignores hidden parts (both found by the reviewer).
66. **Words over a busy set need a soft dark band** (chimneys, papers on a desk), as the street
    already had.
67. **The Blender MCP's own guidance caught real faults.** Its rules and its bundled manual showed
    that my bevels shaded as hard facets (harden normals was off) and the cut brick walls had razor
    corners; following them, and joining parts by material (232 parts to 19), made each works about
    34,000 triangles and visibly finer. Its sandbox refuses `read_factory_settings` (use
    `read_homefile(use_empty=True, use_factory_startup=True)`), Blender's default renderer crashes
    without a graphics card (switch to Cycles before any render), and Blender needs `--online-mode`
    for the add-on's local connection.
68. **A detail can read as something else on a phone.** New stone blocks beside round gutter ends
    looked like little cameras on the wall; dark glass lenses made reading glasses look like
    sunglasses; a figured wood pattern looked like a contour map. A before-and-after judge in the
    real film frame caught all three.


69. **Background jobs in a cloud session stop after 2 hours.** The chapter's filming (about 5 hours,
    because the detailed model pages draw at 12 to 15 seconds a picture against 2.7 for the others)
    was stopped mid-way, losing two pieces in progress (finished pieces were kept). Fix: film in
    stretches that each fit (`FILM_FROM` / `FILM_TO` on the filming script).
70. **Detailed models cost drawing time, mostly in their surfaces, not their shapes.** A profiling
    tool (`profile_frame.mjs`) showed the realistic materials of the works and town were most of
    page 3's 12 seconds a picture; matte materials halve it but looked flatter and darker, so the
    realistic look was kept and the time accepted.
71. **Save long work often: the cloud machine can restart without warning.** It restarted at 02:53
    and lost both chunks in progress (about 30 minutes of page 3). The filming tool now keeps every
    60 frames as it finishes them, so a restart or the 2-hour stop costs at most one piece per worker
    (about 13 minutes on the slowest page), and running it again carries on.
72. **Check whether a repository is public before pushing everything.** This one is, so the
    soundtrack stayed out, and every new file was searched for passwords, keys and personal details
    first. When Claude Code's safety check blocks a save, take out what it most likely objects to
    (session records, job numbers, machine paths) and ask, rather than forcing it through.
73. **Prove a repository is complete by rebuilding from a fresh copy.** Drawing the same moments from
    a clean clone and from the working kit, and comparing them pixel for pixel, showed nothing was
    missing; reading the notes against the files found 16 stale paths that a file count would miss.
74. **Projection makes 3D models belong in a painting.** SAM 3D's own surfaces looked like toys
    beside the brushwork; letting each model wear the painting, shone onto it from where it was
    painted, brought back the headlights' glow, the windscreen's interior and the brushwork. Only the
    sides the painting never showed need the model's own surface.
75. **Check what a model file carries before lighting it.** SAM 3D's files have no surface directions
    (normals), so they drew as black blocks until those were worked out on loading.
76. **"Clear of the painted surface" is not "standing on the ground".** Sliding a model back until it
    touches the painted room stopped on smeared background and left the wheels half a unit up. Fit the
    ground from the forecourt around the object's base, and flatten the depth there.
77. **A painted room tears at near, upright things.** Even a short camera move bends canopy posts and
    building edges; solid foreground objects make the tearing behind them more noticeable, not less.
78. **A stand-in is only as good as what's behind it.** Boxes that wear the painting keep posts and a
    canopy straight on a push, but the background they hide must be properly repainted: a quick free
    smear is covered on a straight push and shows on any sideways step (log 24).
79. **Keep the painted light by giving no lamp to anything that shows the painting.** When the
    stand-ins took some lamp and the background didn't, their edges showed as a brightness jump.
    Showing the painting exactly on both, and putting shadows on a see-through ground, matched them.
80. **An AI painting's perspective doesn't add up.** A true rectangle fitted to the canopy missed its
    painted edges by about 45 pixels; fit shapes to their painted corners instead. Faces seen almost
    edge-on from the painting's view must still wear the painting, or they draw dark.

81. **Rooms lit by their own glow are cheap and can change on a word.** Each room of the house shows
    its walls and cut-outs by their own light, scaled by a light level, instead of a dozen real lamps:
    about 1.8 seconds a frame here when filming two at a time, and lights go out on a beat (log 27).
82. **In a dark room, the cut-outs must go dark too.** Moonlight kept their white paper edges glowing
    as outlines; scale their colour as well as their glow by the room's light.
83. **Check the pictures against the history, not only the words.** Gold dropping into an empty vault
    said "Britain gained gold"; a shrinking kitchen pay packet said "every family's pay fell". The fix
    was a padlock on gold already there, and the miners' packet. Give the facts checker the pictures.
84. **A street needs its own light to read as outside.** People standing just in front of lit rooms
    look as if they are inside them; a lit pavement and a lamp pool separate the street.
85. **Two surfaces in the same plane flicker when the camera moves.** A room's ceiling sat exactly on
    the slab above it and swapped colour in one frame at the start of a move; keep built surfaces a hair
    apart (log 27).
86. **Check the film in motion, not only stills.** Pieces popping in for one frame, things passing
    through floors and flat pale cards only showed in the moving film; a frame-to-frame difference
    measure finds them quickly.
87. **A cut-out snaps off half way through a fade unless told otherwise.** Cut-outs are drawn only
    where they are at least half solid, so lowering their opacity made the strike crowd vanish in one
    frame at 50%. While a piece fades, lower that threshold (setFading in house-sample/page-1.js).

## Traps

- Check for shadows with the lamp alone: a scene can look fine while casting no shadows at all.
- A video model adds things nobody asked for (symbols, flags, the wrong era's machines): check
  every generated clip frame by frame before it goes in the film.
- Before trusting a skill's stated folder, check it exists.
- A word spoken twice on a page must be asked for by which time it is spoken.
- Check every title letter by letter at full size: a cut-out font can turn one letter into another.
- Measure, don't assume, that sound and pictures line up; filters can add delay.
- A fact that only a blocked page could confirm stays out of the film.
- Lay every cut-out over a loud colour (magenta) before using it: missing and faint parts show at once.
- Anything a page shows (pieces, dust, smoke) must be put away with that page, or it can linger.
- A paper piece's edge must stay inside the frame at the piece's own distance from the camera.
- Folded paper props are built with faces pointing either way: never push shadows along the face
  for them, or they shade themselves dark.
- A cut-out's sheet must be bigger than everything drawn on it, or the overflow is cut off in a
  straight line.
- From an angle, upright strokes printed on a flat page read as a wall; print shapes that only read
  as lying flat.
- Inside a painted room, keep camera moves small and turn reflections down (lessons 48, 49).
- Draw page turns in one run of stills: some faults only show when frames follow each other (lesson 51).
- Run the independent critique before filming (lesson 53).
