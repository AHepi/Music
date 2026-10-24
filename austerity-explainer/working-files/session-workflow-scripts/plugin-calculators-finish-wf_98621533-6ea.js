export const meta = {
  name: 'plugin-calculators-finish',
  description: 'Finish the plugin calculators: preflight runner, self-contained tests, LLM tips guide and skills, version bump; then an adversarial tester and a fresh-model dry run, and a fixer',
  phases: [
    { title: 'Integrate and document', detail: 'preflight and tests; tips guide and skills' },
    { title: 'Verify', detail: 'adversarial tester; fresh-model dry run' },
    { title: 'Fix', detail: 'confirmed problems only' },
  ],
}

const R = '/home/user/Music/austerity-explainer'
const K = `${R}/film-kit`
const PL = '/home/user/Music/plugins/explainer-film'
const C = `${PL}/kit/calculators`
const SP = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const D = `${SP}/plugin-calculators/inventory-and-design.json`
const B = `${SP}/plugin-calculators/build-result.json`

const BASE = `
THE USER'S REQUEST (not a programmer): "All the runs and adjustments you've made, can you make them into automatic calculations the plugin
makes automatically so they don't have to be exhaustively searched for every time a new video is made. Along with tips and tricks for LLMs
to follow."
WHERE THINGS STAND: the plugin ${PL} now has calculators in ${C} (frame_geometry, settings + ${PL}/kit/film-settings.json, place_facts,
plan_shot, view_audit, paint_request, after_painting, plan_states, plan_page_timing, plan_budget, plan_effects, plan_lights), Blender
tools (kit/paper-film/blender/make_check_file.py, model_lint.py), page tools (kit/paper-film/tools/page_events.mjs, check_page_layout.mjs,
camera_audit.py extended), narration tools (kit/narration-tools/lint_script.py, sound_gates.py), and tests in ${C}/tests (run_all.py). The
design, inventory (423 items with llm_tip fields) and skeptic are in ${D}; the builders' reports (what each built, its API, what is not done)
are in ${B}. READ BOTH FIRST.
RULES: the plugin must stand alone for someone who has only the plugin: no file may name this machine's session folders (/tmp/claude-0...,
/root/.claude...); tests that need large real pictures from this project look for them through an environment setting or the repository
path austerity-explainer/film-kit next to the plugin and SKIP with a plain message when absent (never fail); small fixtures live in
${C}/tests/fixtures. Plain note at the top of every file; full plain-word names; the existing style. No money; no paid service. Do not change
the film kit (${K}) or anything under ${R}: another team is working there. Do not commit (the lead commits). Report in plain everyday words.`

const REPORT = { type: 'object', properties: {
  summary: { type: 'string' }, files: { type: 'array', items: { type: 'string' } },
  tests: { type: 'string' }, not_done_or_unsure: { type: 'string' },
}, required: ['summary', 'files', 'tests', 'not_done_or_unsure'] }

const STAGES = `The preflight's stages and command (fixed, so the docs can name them): ${PL}/bin/explainer-film-preflight STAGE [options], where
STAGE is one of: script (before recording), record (after recording), shots (before building or drawing a place's views), plates (before
paying for paintings), paint (after each painting arrives), pages (while building pages), film (before filming), finish (after finishing).`

const INTEGRATE = `YOUR TASK: integrate. ${STAGES}
1. Build ${C}/preflight.py and the wrapper ${PL}/bin/explainer-film-preflight (design "Preflight runner"; skeptic: read each check file's
   "accepted" list and show accepted items as known, block only on new failures; hash the inputs; one report (JSON + plain words) with
   pass/warn/fail, cost and time; block paid and long steps on failures; require a critique newer than every page file before filming).
   Each stage calls the calculators that apply; a stage whose inputs are missing says exactly which file to make and which tool makes it.
2. Make every test self-contained by the RULES above (fix the tests that name session folders; replace session paths in fixtures and their
   sources notes with plain descriptions; copy any small fixture still needed). Run ${C}/tests/run_all.py until everything passes or
   skips with a reason; make run_all print how many checks passed, failed and skipped, and its time.
3. Add "kind_of_shot", "figures" and "accepted" to the plugin's example check files where the builders' reports say so (W1, W2, W3, the
   notice corner, the people test), so the examples show the new fields.
4. Update ${C}/README.md: every calculator, what it computes, its command, its inputs and outputs, what it replaces (which hand searches),
   and the preflight stage that runs it. Prove the preflight on the project's chapter 2 data: run each stage you can (script on the newcomer
   narration script, shots on the Works and checkout place facts fixtures, pages on pages 3 to 5, plates on the people test) and paste the
   plain reports' first lines into your report.`

const DOCS = `YOUR TASK: the guide and the skills. ${STAGES}
1. Write ${PL}/kit/docs/"LLM tips and tricks.md": the tips guide for a model making the next film (design "tips_guide_outline"; the
   inventory's llm_tip fields; the skeptic's corrections; "judgement_only"). Plain words, short numbered tips grouped by stage, each tip
   naming the calculator or preflight stage that checks it, or "judgement: ask a critic" when nothing can. Start with "How to work" (run the
   preflight first, compute before you render, one change then measure, quote numbers, never trust a single still, and so on). Include the
   numbers to know with their units and kinds (measured, judged, invented), the people test's lessons (lessons 135 to 139 in
   ${R}/project-notes/Lessons.md), money (prices change: check before each paid batch), and the traps that cost the most rounds (single file
   seen end-on; story high over bare floor; smoke blown away from the camera; the painter leaving shadows; a cut where only people change).
2. Update the skills so they call the calculators at the right moments instead of describing hand searches: make-explainer-film (route to
   the preflight stages and the tips guide), make-3d-models or a new skill build-and-paint-a-place (the built-and-painted look: place facts,
   plan_shot, view_audit, make_check_file, model_lint, plan_lights, paint_request, after_painting, plan_states, plan_effects), build-cinema-page
   (plan_page_timing, page_events, check_page_layout, camera_audit --built-set), record-narration (lint_script before and after, sound_gates),
   film-and-finish (plan_budget, the film and finish stages, sound gates), paint-and-cut (paint_request and after_painting for paintings),
   check-and-critique (what the critics must still judge). Keep each skill's description accurate for triggering.
3. Update ${PL}/README.md and bump the version to 1.3.0 in ${PL}/.claude-plugin/plugin.json and the marketplace file at the repository root
   (/home/user/Music/.claude-plugin/marketplace.json if it exists), with a plain changelog entry.
Read the calculators' --help to get every command right; if a command does not exist yet (the integrator is writing preflight.py in parallel),
use the fixed stage names above.`

phase('Integrate and document')
const [integrated, docs] = await parallel([
  () => agent(`${BASE}\n\n${INTEGRATE}`, { label: 'finish:integrate', phase: 'Integrate and document', schema: REPORT }),
  () => agent(`${BASE}\n\n${DOCS}`, { label: 'finish:docs', phase: 'Integrate and document', schema: REPORT }),
])

const ISSUES = { type: 'object', properties: {
  summary: { type: 'string' },
  issues: { type: 'array', items: { type: 'object', properties: {
    where: { type: 'string' }, problem: { type: 'string' }, evidence: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['where', 'problem', 'evidence', 'fix', 'severity'] } },
}, required: ['summary', 'issues'] }

phase('Verify')
const [tester, dryRun] = await parallel([
  () => agent(`${BASE}\n\nThe integrator's report:\n${JSON.stringify(integrated, null, 1)}\nThe docs report:\n${JSON.stringify(docs, null, 1)}\n\nYOUR TASK: you are an adversarial tester. Work in ${SP}/plugin-calculators/tester (create it); change no plugin file.
Run ${C}/tests/run_all.py. Then try to break things: run every calculator's command and every preflight stage with real inputs, with
missing inputs and with wrong inputs; check every claimed number against its recorded source yourself (open the source); look for tests that
claim to prove something they only repeat; look for any file naming session folders, any file over 5 MB, any password or key; check that the
skills' and guide's commands exist and run as written; check the guide's numbers agree with film-settings.json. Report every real problem
with evidence and a concrete fix.`, { label: 'verify:adversarial-tester', phase: 'Verify', schema: ISSUES }),
  () => agent(`${BASE}\n\nYOUR TASK: you are a fresh model who has never seen this project. Work in ${SP}/plugin-calculators/dry-run (create it); change
no plugin file and do NOT read the project notes, the design file or the builders' reports: use ONLY the plugin (${PL}: its README, skills,
docs including "LLM tips and tricks.md", and the calculators' --help). Your job: plan one new view of a new place as the plugin teaches,
without rendering anything. The place: "a family-run corner shop's counter in Japan, 2013, at night: the counter with a basket of
groceries, the till, a small lit sign, a window to the street; the camera where a customer stands; no people". Write its place facts by
hand from this description (invent sensible sizes in metres), then run the shot planner, the view audit, the effects planner (no smoke, so
say what it does), the light planner, the painter's request builder (prompt only, no paid call) and the budget planner. Report as an
outsider: what worked; every place the docs were unclear, wrong or missing; every command that failed and why; what you would have had to
search by hand anyway.`, { label: 'verify:fresh-model-dry-run', phase: 'Verify', schema: ISSUES }),
])

phase('Fix')
const fixer = await agent(`${BASE}\n\nThe adversarial tester's issues:\n${JSON.stringify(tester, null, 1)}\n\nThe fresh model's dry run issues:\n${JSON.stringify(dryRun, null, 1)}\n\nYOUR TASK: fix every must-fix and should-fix issue that you can confirm yourself (reproduce it first; if you cannot, say so and leave it). Minor ones where cheap. Re-run ${C}/tests/run_all.py and the commands you touched. Report per issue: fixed (how), not reproduced, or left (why).`,
  { label: 'fix:confirmed-issues', phase: 'Fix', schema: REPORT })

return { integrated, docs, tester, dryRun, fixer }
