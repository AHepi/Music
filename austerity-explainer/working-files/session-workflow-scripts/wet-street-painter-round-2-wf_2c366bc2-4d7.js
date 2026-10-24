export const meta = {
  name: 'wet-street-painter-round-2',
  description: 'Small rubbish and joint fixes, new full-size wet plate, repaint with a dark plain sky, a wet behind painting, the stage brightness fix in a copy, and a fresh check',
  phases: [
    { title: 'Plate', detail: 'checker fixes to rubbish and joints; full-size wet plate and props-free plate on the rented machine' },
    { title: 'Paint', detail: 'front painting with a dark plain sky; wet behind painting' },
    { title: 'Stage', detail: 'stage copy: wet paintings, brightness fix, plate and moved views' },
    { title: 'Check', detail: 'fresh eyes on everything; one fix round if needed' },
  ],
}

const SC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const PW = SC + '/proc-work'
const SW = PW + '/street_wet'
const RR = SW + '/relief_and_rubbish'
const PT = SW + '/painter_test'
const R2 = SW + '/painter_round_2'
const PICS = PW + '/24 Wet street painting round 2 - pictures'
const LEDGER = PW + '/SPENDING - paid image generation ledger.md'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
const OPTS = { model: 'sonnet', effort: 'xhigh' }

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them. They make a painted explainer film: a 3D street is drawn in Blender (the "plate"), an image model (the "painter", Flux 3 edit on fal) repaints it in the series' style, and the film's three.js "stage" projects that painting back onto the 3D set so the camera can move. Their requests this covers, verbatim: "Can we do one more thing. Add a rubbish mask for gutters and along buildings. And the normal maps between bricks on the ground needs a little work. The light shouldn't be able to wash out the 3d affect so easily. The geometry should still be visible under all conditions." and, on money: "Just do it. $20 budget, ask free. Over that, start asking".
WHERE THINGS ARE:
- The wet street work: ${SW}/ (set_copy = the street copy, read-only for you; tools = wetness layer and 22_render_eevee.py, whose states must start with "today"). Round 2 wetness note: ${SW}/09 Recipe - wetness layer and specular map for the street - how it is made.md (find it with ls if the name differs).
- The finished sett joints (JOINTS layer) and rubbish (RUBBISH layer + pieces) job: ${RR}/ ; recipe note "${RR}/10 Recipe - sett relief and rubbish - how it is made.md"; final plate ${RR}/rubbish/final/final_lockout_plate_wet_setts_and_rubbish.png; the fresh-eyes checker's report: ${RR}/check_round_1/ (its problems list is quoted in your task where it matters).
- The first painter test (one repaint of the earlier wet plate): ${PT}/ — read "notes - wet street painter test.md" (sections 3, 4, 7, 9), briefs/brief_new_wet.txt (the brief exactly as sent), painter_request_and_result.json (settings and how the call was made), alignment/ (the lining-up tool copy and shot check files), stage/ (the stage copy and how stills were drawn), tools/ (its scripts).
- The film project /home/user/Music/austerity-explainer is READ-ONLY: never write there; work on copies.
RENDERING: Blender 5.2.2 at ${BLENDER}, always -b --disable-autoexec. Draw every picture on the rented RunPod machine, which is 50-100 times faster than this shared computer: read ${SC}/runpod/HOW TO RENDER ON THE RENTED MACHINE - cached.md and use ONLY ${SC}/runpod/render_client_cached.py (the older render_client.py and its machine are gone; if a script in relief_and_rubbish calls render_client.py or rent_run.py's old client, use the cached client instead, same actions). Upload what a run needs first (same absolute paths there); the store already has set_copy, tools and maps, but NOT relief_and_rubbish (upload only the parts you need, not the 250 MB folder). Another job (installing and trying Blender skills) may share the same machine; that is fine.
HARD RULES: never print, copy, move or read anything in ~/.runpod; never write into the film project or into ${SW}/set_copy, ${RR} (except where your task says to work on a copy) or ${PT}; do not commit or push; do not stop or end rented machines; keep what you make under 250 MB and delete big scratch files (free disk is about 1.3 GB; stop and report if it falls under 0.9 GB).
MONEY (paid painter calls only): before each call look up the price with the Fal connector's price tool; record every call as a row in ${LEDGER} under "Against the US$20 budget" (time UTC, job, model and settings, price by the price list, request id, running total), keeping the running total; this whole job may spend at most US$3.00 in all; never repeat a call just to get a nicer picture without writing down why. Fal tools are loaded with ToolSearch (e.g. "select:mcp__Fal__get_pricing,mcp__Fal__upload_file,mcp__Fal__submit_job,mcp__Fal__check_job,mcp__Fal__run_model"); on every Fal call pass user_intent with the person's verbatim request above.
REPORTING: plain everyday words in every text field (no jargon; explain an unavoidable technical word in one sentence). Say what you tested, what you did not, and what you are unsure of. Put pictures worth showing (JPG under 400 KB, names that say what they show) in "${PICS}/" and the work in ${R2}/<your step>/.`

const STEP_SCHEMA = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    what_changed: { type: 'string' },
    outputs: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'what'] } },
    measures: { type: 'string' },
    paid_calls: { type: 'array', items: { type: 'object', properties: { request_id: { type: 'string' }, price: { type: 'string' }, why: { type: 'string' } }, required: ['request_id', 'price', 'why'] } },
    failures: { type: 'array', items: { type: 'string' } },
    untested: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'what_changed', 'outputs', 'measures', 'paid_calls', 'failures', 'untested'],
}

phase('Plate')
const plate = await agent(`${COMMON}

YOUR STEP: THE PLATE. Work on a COPY of the joints and rubbish tools: copy ${RR}/setts/tools, ${RR}/setts/maps, ${RR}/rubbish/tools, ${RR}/rubbish/maps into ${R2}/plate/ and change only the copies.
1. Make the fresh-eyes checker's cheap fixes (its words):
   a. "Near-camera coal chips look like faceted gems or dice ... straw reads as stiff laths and matchsticks ... white flat scraps at Amount 2 can read as plastic shards. Fix in rubbish_pieces.py: replace the cinder and clinker shapes with noise-pushed, flatter lumps (height squashed to 0.4-0.7); cap the scale of pieces near the camera at about 0.7; make straw shorter, thinner and curved; add many more tiny dust specks and a few wet-paper clumps in the gutters; make the paper scraps darker and limp when wet."
   b. "In the street's main view the gutter and the wall foot read thin, and the chips are spread evenly over the pavement instead of gathering at the kerb and the foot of the wall ... Fix: weight the piece density (not only the colour layer) by the gutter and wall-foot terms about 2x, raise Patchiness to about 0.7 so heaps gather, and use Amount about 1.4 for street shots."
   c. "In the middle distance of the wet plate the vertical sett joints show as short bright ticks with hooked, S-shaped ends ... Fix: blur the groove-profile picture 1-2 dots along vertical joints in make_joint_pictures.py, or take Far Share from 0.10 to about 0.03 and start the fade at 4 m."
   Check each fix with small before/after pictures (540x960 and 100 % crops) on the rented machine, and re-measure the joints with the job's own measuring script on its 22-picture lighting test set (they must still pass as before: 21 of 22 with puddle and rubbish dots left out; also report the count with every dot counted, as the checker did: 18 of 22 before).
2. Draw, with the fixes, the FULL-SIZE WET LOCKOUT PLATE exactly as the final plate was drawn (1536x2730, EEVEE plate settings, shadow rays 4 / steps 16, 64 samples, wet 0.85 / puddles 0.5, lighting B, JOINTS at strength 1, rubbish at the new defaults): ${R2}/plate/lockout_plate_wet_round2.png.
3. Draw the matching PROPS-FREE wet plate from the same camera and settings, with the near props hidden (the ones a camera move would reveal the ground behind: fire drum and its glow source objects only if hiding them does not change the lighting of the rest... decide and say: the film's behind pictures show the street without the near props), keeping the street, lamps, rubbish on the ground and wetness: ${R2}/plate/lockout_plate_wet_round2_no_props.png. First find out how the film made its own behind painting for this shot (read-only look in the film project: search for 'behind' in its lockout shot files and notes) and match its choice of which props are left out; write down what you found.
4. Save 2-4 pictures for the person in "${PICS}/" (e.g. "24 plate - chips and gutter before and after.jpg", "24 plate - full plate half size.jpg").
In measures, give the joint pass counts and the share of blown-out dots (over 0.97) in the lower third of the plate (it was 2.8 %).`, { ...OPTS, label: 'plate: fixes and full-size plates', phase: 'Plate', schema: STEP_SCHEMA })

phase('Paint')
const front = await agent(`${COMMON}

YOUR STEP: THE FRONT PAINTING. The plate step reported: ${JSON.stringify(plate)}
Repaint the new full-size wet plate (${R2}/plate/lockout_plate_wet_round2.png) ONCE with the same painter, settings and way of sending as the first painter test (see ${PT}/painter_request_and_result.json and notes section 2-3: Flux 3 edit, 2k, pictures sent small to keep the price down, the same style picture), with the brief ${PT}/briefs/brief_new_wet.txt changed as little as possible:
- sky: "the sky is dark grey-blue cloud with soft edges, like image 2's darker skies; no pale, white or bright clouds anywhere; keep the sky as dark as image 1" (the first test added heavy pale-white brush-stroke clouds despite the ban);
- "do not make the lamp reflection streaks on the road stronger or longer than in image 1";
- "keep the thin dark lines between the setts and between the flags everywhere, even where the road shines";
- "keep the small rubbish where image 1 has it (cinders, coal dust, ash, paper scraps, straw, leaves, mud along the gutters and the foot of the walls, round the drum and sacks); add no writing, print or modern litter";
- "the gas lamp glass glows warm amber".
Save the brief as sent (and a side-by-side with the first test's brief) in ${R2}/paint/briefs/. Line the painting up with the copy of the film's lining-up tool (${PT}/alignment/) and save ${R2}/paint/front_painting_lined_up.png.
Then judge it against the plate: sky (share of sky brighter than the plate's sky, the first test had 19 %), joints visible on the road, rubbish kept, wet cues kept (reuse the first test's measuring scripts in ${PT}/tools, run on copies), nothing added or moved.
IF the sky still has pale clouds: do NOT pay for another call; instead put a dark plain sky in for free: take the sky from the plate's own sky or the film's existing lockout painting (read-only copy), cut with Blender's exact sky mask for this camera, with a soft clean edge on the roof lines; save that as ${R2}/paint/front_painting_final.png and say which you used. Otherwise front_painting_final.png is the lined-up painting.
At most ONE paid call in this step (a second only if the first failed outright, e.g. an error or a blank picture; write down why). Save 2-3 pictures for the person (plate | painting | first test's painting, and 100 % crops of road and sky).`, { ...OPTS, label: 'paint: front painting', phase: 'Paint', schema: STEP_SCHEMA })

const behind = await agent(`${COMMON}

YOUR STEP: THE WET BEHIND PAINTING. When the stage's camera moves, it shows a "behind painting" (the street without the near props) where the props used to hide the ground; the film's existing behind painting for this shot is DRY, which showed as dry ghost patches on 56-71 % of the moved road in the first test.
The plate step: ${JSON.stringify(plate)}
The front painting step: ${JSON.stringify(front)}
First read (read-only) how the film made and uses its behind painting for the lockout shot (file names, size, how the stage loads it), so yours drops straight into a COPY of the stage the same way.
Make a WET behind painting in the same hand as the new front painting: repaint the props-free wet plate (${R2}/plate/lockout_plate_wet_round2_no_props.png) with the same painter and settings, the front step's brief adapted (the near props are not there; paint the ground where they stood as wet setts with the same rubbish and puddles), and the front painting (${R2}/paint/front_painting_final.png) as the style picture so both paintings match. Line it up the same way. Save ${R2}/paint/behind_painting_final.png (same sky treatment as the front painting).
At most ONE paid call (a second only if the first failed outright; write down why). Check: where the props stood, the ground is wet road and pavement, not dry and not ghost props; colours and brightness match the front painting where both show the same street (measure the difference on the parts visible in both). Save 1-2 pictures for the person.`, { ...OPTS, label: 'paint: wet behind painting', phase: 'Paint', schema: STEP_SCHEMA })

phase('Stage')
const stage = await agent(`${COMMON}

YOUR STEP: THE STAGE, in a NEW COPY. Make a fresh copy of the stage the way the first test did (see ${PT}/tools/set_up_stage_copy.sh and ${PT}/stage/), into ${R2}/stage/kit_copy/ (big 3D files may be links, only read).
Paintings: front ${R2}/paint/front_painting_final.png, behind ${R2}/paint/behind_painting_final.png.
Steps reported so far: plate ${JSON.stringify(plate)}; front ${JSON.stringify(front)}; behind ${JSON.stringify(behind)}.
1. Draw the film's lockout scene in the copy with the new front and behind paintings: the plate view (first frame), the moved view and one mid-move still, at the same times and camera as the first test (${PT}/tools/render_stage_views.sh, render_stage_midmove.sh). Measure, with the first test's script (${PT}/tools/measure_stage_views.py, run on copies): the share of moved road and pavement pixels that wear a dry-looking behind painting (first test 71 % road / 70 % pavement with the old dry behind painting; aim near 0), and how bright the road arrives compared with the painting (first test: wet road at 0.75 of painted, dry at 0.92).
2. THE BRIGHTNESS FIX: find WHY the stage darkens dark painted values (painting 0.08 -> 0.02, 0.13 -> 0.07, 0.24 -> 0.24, 0.5 -> 0.59; the first test suspected a look setting in the film's scene file, e.g. contrast 1.04, or the renderer's tone mapping or colour space handling). Find the exact setting or code line in the COPY (search the stage code and the lockout scene file). Make the smallest fix in the copy that brings the wet road to at least 0.9 of its painted brightness without changing how the existing dry scenes look (prove that: draw one other existing scene, e.g. the dry lockout with the film's own dry painting, before and after your fix, and measure the difference). Say exactly what the fix would be in the real film project (file, setting, old and new value) — do NOT change the film project.
3. Draw the three views again with the fix. Save the pictures for the person: plate view, moved view, mid-move (before fix | after fix), and a 100 % crop of the near road in the moved view showing whether the joints and rubbish survive.
4. Stills only; no paid calls in this step.`, { ...OPTS, label: 'stage: paintings and brightness fix', phase: 'Stage', schema: STEP_SCHEMA })

phase('Check')
const CHECK_SCHEMA = {
  type: 'object',
  properties: {
    sky_dark_and_plain: { type: 'string', enum: ['yes', 'nearly', 'no'] },
    joints_and_rubbish_survive_painting: { type: 'string', enum: ['yes', 'nearly', 'no'] },
    wet_holds_when_camera_moves: { type: 'string', enum: ['yes', 'nearly', 'no'] },
    stage_brightness_fixed_without_harm: { type: 'string', enum: ['yes', 'nearly', 'no'] },
    usable_as_the_lockout_picture: { type: 'string', enum: ['yes', 'nearly', 'no'] },
    claims_checked: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, holds: { type: 'boolean' }, evidence: { type: 'string' } }, required: ['claim', 'holds', 'evidence'] } },
    problems: { type: 'array', items: { type: 'string', description: 'what, where (picture path), why it matters, the cheapest fix and whether it costs money' } },
    should_fix_now: { type: 'boolean' },
    fixes_for_one_round: { type: 'string' },
    money_total_checked: { type: 'string' },
    overall: { type: 'string' },
    pictures: { type: 'array', items: { type: 'string' } },
  },
  required: ['sky_dark_and_plain', 'joints_and_rubbish_survive_painting', 'wet_holds_when_camera_moves', 'stage_brightness_fixed_without_harm', 'usable_as_the_lockout_picture', 'claims_checked', 'problems', 'should_fix_now', 'fixes_for_one_round', 'money_total_checked', 'overall', 'pictures'],
}
const checkPrompt = (reports) => `${COMMON}

YOU ARE A FRESH-EYES CHECKER. You did none of this work. Open the pictures yourself (full size and 100 % crops; make your own crops), re-run at least three of the measurements yourself from the saved files, and check the ledger's rows against the reports and the Fal connector's request history (mcp__Fal__search_request_history) so the money total is right.
Judge as the person would: does the painted street read wet, with the sett joints and the rubbish still there, a dark plain sky, no dry patches when the camera moves, and a road that is not crushed dark by the stage? Is it usable as the lockout shot's picture? Compare with the first test (${PT}/pictures/) and the earlier dry painting.
List problems with the cheapest fix each, and say if a fix round is worth it now (only for faults a viewer would notice; small paid calls are allowed within the job's US$3.00 cap).
REPORTS: ${JSON.stringify(reports)}`

let check = await agent(checkPrompt({ plate, front, behind, stage }), { ...OPTS, label: 'fresh-eyes check', phase: 'Check', schema: CHECK_SCHEMA })
let fix = null
let recheck = null
if (check && check.should_fix_now) {
  fix = await agent(`${COMMON}

YOUR STEP: ONE FIX ROUND. A fresh-eyes checker found these problems and proposed these fixes: ${JSON.stringify({ problems: check.problems, fixes: check.fixes_for_one_round })}
Earlier steps: plate ${JSON.stringify(plate)}; front ${JSON.stringify(front)}; behind ${JSON.stringify(behind)}; stage ${JSON.stringify(stage)}.
Make the fixes (copies only; at most two paid calls in this round, within the job's US$3.00 cap; prefer free fixes), redraw what they affect (plate, paintings, stage views), re-measure, and save before/after pictures for the person in "${PICS}/" (names starting "24 fix -").`, { ...OPTS, label: 'fix round', phase: 'Check', schema: STEP_SCHEMA })
  recheck = await agent(checkPrompt({ plate, front, behind, stage, fix, first_check: check }), { ...OPTS, label: 'fresh-eyes re-check', phase: 'Check', schema: CHECK_SCHEMA })
}
return { plate, front, behind, stage, check, fix, recheck }
