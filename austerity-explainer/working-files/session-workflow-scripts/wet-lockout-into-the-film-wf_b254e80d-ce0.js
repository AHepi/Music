export const meta = {
  name: 'wet-lockout-into-the-film',
  description: 'Put the round 2 wet paintings and the stage darkening fix into the real film (old dry versions kept), film the lockout clip, check it frame by frame, update the film project notes',
  phases: [
    { title: 'Apply and film', detail: 'swap paintings, apply the two stage changes, run the kit checks, film the clip' },
    { title: 'Check', detail: 'fresh eyes: every frame, other scenes unchanged, notes updated' },
    { title: 'Fix', detail: 'one fix round and a re-check if needed' },
  ],
}

const SC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const PW = SC + '/proc-work'
const R2 = PW + '/street_wet/painter_round_2'
const FILM = '/home/user/Music/austerity-explainer'
const KIT = FILM + '/film-kit'
const OUT = SC + '/wet_lockout_film'
const PICS = PW + '/27 Wet lockout shot in the film - pictures'
const OPTS = { model: 'sonnet', effort: 'xhigh' }

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them, and they make a painted explainer film (the austerity explainer, in ${FILM}). A second painter round made a WET version of the film's lockout shot (pit village street at dusk after rain): a front painting and a wet behind painting (the street without the near props, shown where the moving camera sees past them), plus a fix for the film's stage, which made dark painted values too dark (a new "toe" switch, off unless a scene asks for it, and the lockout scene's dark frame edge eased from 0.30 to 0.25). All of that was tested only in a COPY of the stage. Read its report first: ${R2}/ (paint/front_painting_final.png, paint/behind_painting_final.png, stage/the_fix/*.diff and the patched files in stage/the_fix/patched/, stage/ stills and numbers, check_round_2/ the checker's report; pictures in ${PW}/24 Wet street painting round 2 - pictures/).
THE PERSON'S WORDS, verbatim: first, about the look: "No keep it. The reference doesn't have to be followed exactly. This already looks incredible." Then, asked whether the lockout shot in the actual film should become the wet street: "Oh yes please. But I want to use the full set when we get around to it. Because I want to now do something more immersive with the camera moving through the street. The lighting reacting to characters moving around on set will add more detail and narrative context for some sequences."
So: the lockout shot in the real film becomes the wet street now. The "full set, immersive camera, lighting reacting to characters" is a LATER plan: record it in the film project's notes; do not start it.
THE FILM PROJECT'S OWN RULES apply to every change in it: read ${FILM}/06 House rules for the project.md, ${KIT}/00 START HERE.md, ${KIT}/01 How to make a film with this kit.md, ${KIT}/05 Lessons and traps.md, and the project's Decisions.md, Status.md, Lessons.md, Workflows.md and project story (find them; probably in ${FILM}/project-notes/). Every change updates them: Decisions.md quotes the person's exact words (spelling included) and marks the helper's own calls; Status.md says where things stand; Lessons.md only gets build or test failures; Workflows.md gets any changed procedure; the film project's story gets a new numbered log entry (next number in its own log; add, never rewrite); every document keeps its Traps section.
SAFETY: change ONLY what this job needs in ${FILM}: the lockout paintings, the two stage files the fix touches, any kit documentation of the new switch, and the notes above. KEEP the old dry paintings as alternates next to the new ones (e.g. lockout-painted-dry.jpg, lockout-behind-dry.jpg) so the dry look is one rename away; the git history also keeps them. Never touch other scenes' assets. Do not commit or push (the main session does). Never print, copy, move or read anything in ~/.runpod. No paid calls. Disk is tight (about 2 GB free, shared with other jobs): put working files in ${OUT}/ (limit 400 MB, delete frame dumps once the clip and contact sheets are made).
REPORTING: plain everyday words; say what was tested, what was not, what you are unsure of. Pictures for the person in "${PICS}/" (JPG under 400 KB, names start "27 ").`

const STEP = { type: 'object', properties: {
  summary: { type: 'string' }, film_changes: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, change: { type: 'string' } }, required: ['file', 'change'] } },
  clip: { type: 'string', description: 'path of the finished lockout clip (mp4) and how it was made, length, size' },
  checks: { type: 'array', items: { type: 'object', properties: { what: { type: 'string' }, result: { type: 'string' }, passed: { type: 'boolean' } }, required: ['what', 'result', 'passed'] } },
  pictures: { type: 'array', items: { type: 'string' } }, failures: { type: 'array', items: { type: 'string' } }, untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'film_changes', 'clip', 'checks', 'pictures', 'failures', 'untested'] }

phase('Apply and film')
const apply = await agent(`${COMMON}

YOUR JOB: APPLY AND FILM.
1. Before changing anything, film the CURRENT (dry) lockout clip exactly as the kit films it (the lockout example in ${KIT}/examples/lockout-test and the kit's filming instructions), or, if the kit already has a finished dry clip, use that; keep it in ${OUT}/before/ as the comparison.
2. Put in the paintings: make the front and behind paintings in the same format, size, colour handling and file names the scene loads now (read lockout-test.js and the current files ${KIT}/assets/models/pit-village/lockout-painted.jpg and lockout-behind.jpg; match their pixel size and JPEG quality unless the round 2 report says otherwise), after renaming the current ones to the -dry alternates.
3. Apply the two stage changes from ${R2}/stage/the_fix/ (the .diff files; compare with the patched copies) to the real files. Confirm the result matches the copy that was tested.
4. Run the kit's own checks (its preflight runner and tests, whatever ${KIT} documents) and prove other scenes are unchanged: draw the same eight comparison stills the round 2 stage step drew (the film's own dry lockout is gone now, so use the -dry alternates for that one, and the notice corner, chapter 2 and chapter 1 scenes) with the old and new stage files and compare dot for dot.
5. Film the wet lockout clip the way the kit films it (same length, size and frame rate as the before clip; with the kit's own fire, flames and smoke; with sound only if the kit's lockout example has it). Save it as ${OUT}/27 Lockout shot - wet street.mp4 and copy it to "${PICS}/".
6. Look at EVERY frame yourself (contact sheets of all frames at small size, and full-size frames every 0.5 s plus the first 1.5 s frame by frame where the camera starts to move and the behind painting first shows): look for dry patches, ghosts or seams where front and behind paintings meet, painted prop shadows left outside the 3D props, flicker, the joints and rubbish, the sky and roof lines (the checker saw a possible 2-dot misfit at the roofs). Measure the road's brightness against the painting as the stage step did.
7. Sheets for the person: "27 Before and after - dry and wet lockout, same moments.jpg" (6 moments side by side), "27 Every half second - wet lockout.jpg".
8. Update the film project's notes as its house rules require (Decisions.md with both of the person's quotes above, Status.md, Lessons.md for any failure, Workflows.md if the way to switch dry/wet or the toe switch needs explaining, the kit doc that lists scene settings, and a new numbered entry in the film project's story).`, { ...OPTS, label: 'apply and film the wet lockout', phase: 'Apply and film', schema: STEP })

phase('Check')
const CHECK = { type: 'object', properties: {
  clip_ready_to_show: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  other_scenes_unchanged: { type: 'boolean' }, notes_follow_house_rules: { type: 'boolean' },
  film_diff_only_intended: { type: 'boolean' },
  problems: { type: 'array', items: { type: 'string', description: 'what, which frame or file, why a viewer or the person would notice, the cheapest fix' } },
  claims_checked: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, holds: { type: 'boolean' }, evidence: { type: 'string' } }, required: ['claim', 'holds', 'evidence'] } },
  should_fix_now: { type: 'boolean' }, fixes: { type: 'string' }, overall: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } },
}, required: ['clip_ready_to_show', 'other_scenes_unchanged', 'notes_follow_house_rules', 'film_diff_only_intended', 'problems', 'claims_checked', 'should_fix_now', 'fixes', 'overall', 'pictures'] }
const checkPrompt = (reports) => `${COMMON}

YOU ARE A FRESH-EYES CHECKER (you did none of this). (1) Watch the wet clip frame by frame yourself (extract frames with ffmpeg into ${OUT}/check/, then delete them), especially the first seconds of the camera move, and compare with the before clip at the same moments; save your telling crops in "${PICS}/" named "27 Checker - ...". (2) Run git -C /home/user/Music diff --stat and git status for ${FILM}: every changed or new file must be one this job needed; read the stage code diff line by line; confirm the toe switch is off for every other scene. (3) Re-draw two of the other-scene comparison stills yourself and compare dot for dot. (4) Check the notes follow the house rules (the person's words quoted exactly, Status, Lessons, Workflows, story entry, Traps sections). Say whether the clip is ready to show the person, and list problems with the cheapest fix.
REPORTS: ${JSON.stringify(reports)}`
let check = await agent(checkPrompt({ apply }), { ...OPTS, label: 'fresh-eyes check', phase: 'Check', schema: CHECK })

let fix = null, recheck = null
if (check && check.should_fix_now) {
  phase('Fix')
  fix = await agent(`${COMMON}

YOUR JOB: ONE FIX ROUND. The checker found: ${JSON.stringify({ problems: check.problems, fixes: check.fixes })}
Earlier report: ${JSON.stringify(apply)}
Fix what a viewer or the person would notice (free fixes only), re-film the clip if anything that shows changed, redo the sheets, keep the notes up to date (Lessons.md for the failures), and say what you did not fix and why.`, { ...OPTS, label: 'fix round', phase: 'Fix', schema: STEP })
  recheck = await agent(checkPrompt({ apply, first_check: check, fix }), { ...OPTS, label: 're-check', phase: 'Fix', schema: CHECK })
}
return { apply, check, fix, recheck }
