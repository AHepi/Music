export const meta = {
  name: 'plugin-generic-and-batching',
  description: 'Remove everything in the plugin written for one particular request, add batched variation rounds and a card-time allowance, then re-run the blind newcomer test cleanly',
  phases: [
    { title: 'Make generic', detail: 'remove the one-request example and data; real examples instead' },
    { title: 'Batching', detail: 'one full sweep, about 10 measured variations per change spread over the cards, one look; card-time allowance' },
    { title: 'Verify', detail: 'tests, a real batch on the cards, a scan for leftovers, two blind newcomers and a judge' },
    { title: 'Fix', detail: 'apply what the checks found' },
  ],
}

const SC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const P = '/home/user/Music/plugins/explainer-film'
const PT = '/home/user/Music/procedural-textures'
const WORK = SC + '/plugin-work'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
const CLIENT = SC + '/runpod/render_client_serverless.py'
const GUIDE = SC + '/runpod/HOW TO RENDER - pay per second.md'
const OPTS = { model: 'opus', effort: 'xhigh' }  // the person, 23 October: use Opus 5.5 for the plugin work
const OPTS_SONNET = { model: 'sonnet', effort: 'xhigh' }  // the finished first step ran on Sonnet (kept so its result stays cached); the newcomers stand in for the smaller models the plugin is for
const PRIOR = WORK + '/workflow_result_A.json'
const BATCH_WORDS = "And batch them with workers. Do one full sweep of changes, then look. Instead of one small change, then check. Maybe even batch according to variations. So maybe 10 variations that are measurably different for each asset change. That way, they can test multiple different types of changes at once."

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them. The Claude Code plugin "explainer-film" (${P}) was just given version 1.4.0: a new skill surfaces-wear-and-construction, the place kit (kit/place-kit, command bin/explainer-film-place), a preflight stage "place", agents place-*, a hook, and the workflow workflows/build-a-place.js. The goal: any model (often a smaller one such as Sonnet) asked with a plain request to build a place, a set or props in Blender applies the full surface, wear and construction treatment by itself, because the plugin carries it. The full report of how 1.4.0 was made, its tests and the faults found and fixed is ${PRIOR} (large JSON; read the parts you need).
HARD RULES: write only inside ${P} and your own scratch folder ${WORK}/<your step>/; never commit or push; never print, copy, move or read anything in ~/.runpod, and never put keys, endpoint ids, machine ids or volume ids into the plugin; never put the person's name, email or any personal detail anywhere or into a request to an outside website; never copy the person's own Astra Blender add-on (${SC}/astra-upload*, ${SC}/astra-work); never write in /home/user/Music/japanese-courtyard. Disk: about 2.5 GB free and shared; big files stay on the rented store.
BLENDER: ${BLENDER} headless (-b --disable-autoexec; xvfb-run -a for anything drawn here; this computer is slow: tiny tests only). Anything bigger renders on the rented cards: read ${GUIDE}; use only ${CLIENT} (if jobs wait more than 5 minutes while workers show idle, stop and report it; never purge the queue or change the endpoint).
WRITING: plain everyday words for smaller models and the person; one word for each thing; a concrete example before a general rule; code with full plain-word names and a plain note at the top of each file. Keep all plugin tests passing (python3 ${P}/kit/calculators/tests/run_all.py, with and without BLENDER set). Report in plain words: what you did, what you tested, what you did not, every failure.`

const STEP = { type: 'object', properties: {
  summary: { type: 'string' }, files_changed: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'what'] } },
  tests_run: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } }, runpod_seconds: { type: 'string' },
  failures: { type: 'array', items: { type: 'string' } }, untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'files_changed', 'tests_run', 'pictures', 'runpod_seconds', 'failures', 'untested'] }

phase('Make generic')
const generic = await agent(`${COMMON}
YOUR STEP: MAKE THE PLUGIN GENERIC AGAIN. While 1.4.0 was being written, every helper could see one particular request the person had made: "Build a village in the forest. Needs unkept dirt roads like they've been driven down by horse and carriage, an empty stable, a few cottages, some scattered mediaeval props." That request is the person's coming TEST of the plugin: a fresh model will be given only those words and the plugin. So the plugin must not contain that request, a plan for it, or anything that exists only because of it; otherwise the test proves nothing. Today it does: the request is quoted word for word in skills/surfaces-wear-and-construction/SKILL.md; there is a whole worked plan for it (a-forest-village-example.md, the-required-steps.md uses it as its example, data/examples/forest-village-place-settings.json and forest-village-ownership.json, "Starter numbers for a mediaeval forest village" in construction-and-scale.md, cottage and stable construction notes, a horse-and-cart lane worked example in wear-recipes.md, "empty stable" readings, a cottage camera in rendering-on-rented-cards.md, the village place type leaning to forest, thatch and dirt lanes, entries such as a horse stall in real_world_facts.json, workflow and test fixtures modelled on that village, the README and tips guide where they echo it). Find ALL of it (search the whole plugin for: forest, village (but the pit-village street of the austerity film is old and legitimate), cottage, stable, horse, carriage, cart, hoof, thatch, wattle, manger, dung, straw, lane, rut, mediaeval, medieval, and any passage that reads like a plan for that request).
RULES FOR WHAT TO DO: (1) Remove the quoted request, the worked plan, the example files and the one-request numbers. (2) Keep capabilities that serve many kinds of places (for example unpaved ground with wheel ruts serves mine yards, farms and building sites; a forest-floor ground role serves gardens and parks; generic place-type presets for village, town, harbour, mine, farm, garden, interior and generic may stay, but each must be neutral: a village preset must not lean to forest, timber, thatch or dirt lanes more than to stone, brick or tile). Remove data entries whose only reason was that request (say which you removed and why, and which borderline ones you kept and why). (3) Replace the worked example with places this project really built and measured: the Japanese garden (${PT}/garden, "${PT}/garden/30 Plan - Japanese garden - all the advice.md" and garden/character, story logs 30-31 in "${PT}/Procedural textures - project story.md") and the small canal lock built with the plugin itself in the smoke test (${WORK}/verify/ and the smoke report in ${PRIOR}); use their real numbers and say measured or judged. (4) Rewrite test fixtures and the workflow's examples around a neutral place (the canal lock or the garden), keep every test meaningful and passing. (5) Do not weaken the routing: the surface-and-wear pass and the construction check stay REQUIRED steps for any place.
Report every file changed, every removal, and the final search results showing no leftover.`, { ...OPTS_SONNET, label: 'make generic', phase: 'Make generic', schema: STEP })

phase('Batching')
const batching = await agent(`${COMMON}
NOTE FROM THE MAIN SESSION: two earlier attempts at this step (on a smaller model) were cut off, first by a container restart, then because the person switched the plugin work to a stronger model. Their partly finished changes are saved in git: compare the last commit with commit 6fab3bf, which is from before this step began (git -C /home/user/Music diff 6fab3bf HEAD -- plugins/explainer-film). Check that work critically, then finish it or redo what is wrong. Do not commit.
YOUR STEP: BATCHED ROUNDS AND A CARD-TIME ALLOWANCE. In the last real job (the Japanese garden), helpers spent US$10.89 of rented-card time, while the finished pictures cost about 5 cents: they rebuilt the whole scene for every small test, drew tests at full size and quality, ran about 25 versions of one tree one after another, and nothing limited their card time. The person then said, verbatim: "${BATCH_WORDS}" Earlier they agreed to: a card-time allowance per helper, small and quick test pictures, the scene built once and saved, and full-size pictures drawn once at the end. The person's words are also in "${WORK}/00 Person's rules for card time and batching (22 October).md".
BUILD THIS INTO THE PLUGIN (generic, any place):
1. A kit tool (a new verb of explainer-film-place, for example "variations") that takes a saved scene, a list of about 10 variations of one or more changes (each a named set of dial or settings values, or a small script hook), and the cameras to look through; checks BEFORE drawing that the variations are measurably different (settings far enough apart; drop near-duplicates and say so); splits them across up to 3 rented-card jobs sent at the same time (each job opens the scene once and, for each of its variations, re-opens or resets the scene, applies the variation, draws small quick pictures, about 600 x 400 with EEVEE or low-sample Cycles by the renderer rule, and measures them); then checks AFTER drawing that the pictures differ measurably (flag pairs that came out nearly the same); and makes ONE labelled contact sheet with each variation's name, its settings and its measures (value range, detail energy, colour and saturation shift, squint score against a baseline) plus the card seconds used. It must also run locally on a tiny scene for tests.
2. A card-time ledger and allowance: every rented-card job is logged with its billed seconds; each helper gets an allowance (a house number in film-settings.json, for example 10 minutes of card time for a builder and 5 for a fixer, judged), and the tool refuses or warns past it.
3. The rule, written into the skills (surfaces-wear-and-construction, build-and-paint-a-place, make-3d-models, the tips guide) and the workflow build-a-place.js and its agents: make every change you plan in one full sweep, then look once; for each change to a thing, draw about 10 measurably different versions in one batch spread over the cards, look at the sheet, pick or combine, at most one more batch; build the scene once and save it; small quick pictures until the end; full-size pictures drawn once at the very end; stay inside the allowance and report card seconds.
4. Tests that run here (with a tiny scene and a fake card) and keep all old tests passing. Then prove it once for real: on the rented cards, run one batch of 10 measurably different variations of one wear change on the small canal-lock scene from the smoke test (find it in ${WORK}/verify/ and the smoke report in ${PRIOR}; if its .blend is not reachable, build a tiny stand-in with the plugin), across up to 3 jobs at once, and report the card seconds, the wake-up times, and the sheet (JPG under 400 KB in ${WORK}/batching/).
Work on top of the "make generic" step's changes (it finished before you started): ${JSON.stringify(generic)}`, { ...OPTS, label: 'batching and card allowance', phase: 'Batching', schema: STEP })

phase('Verify')
const VERDICT = { type: 'object', properties: {
  passed: { type: 'boolean' }, findings: { type: 'array', items: { type: 'object', properties: { problem: { type: 'string' }, where: { type: 'string' }, fix: { type: 'string' }, severity: { type: 'string', enum: ['blocking', 'should fix', 'minor'] } }, required: ['problem', 'where', 'fix', 'severity'] } },
  evidence: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' },
}, required: ['passed', 'findings', 'evidence', 'pictures', 'summary'] }
const NEWCOMER = { type: 'object', properties: { plan: { type: 'string' }, plugin_parts_used: { type: 'array', items: { type: 'string' } } }, required: ['plan', 'plugin_parts_used'] }

const verifyAll = () => agent(`${COMMON}
YOUR STEP: VERIFY (fresh; you changed none of it). (1) Run every plugin test with and without BLENDER. (2) Scan the whole plugin for anything left from one particular request (a village in the forest with dirt roads driven by horse and carriage, an empty stable, a few cottages and mediaeval props): its words quoted, a plan for it, example files or data that exist only for it; also scan for keys, ids, personal details and machine paths. (3) Read the new batching tool and rule as a newcomer and run the tool once locally on a tiny scene. (4) Check the skills, kit, preflight, hook and workflow still agree on names and commands. Report findings with the fix.
REPORTS: make generic: ${JSON.stringify(generic)}; batching: ${JSON.stringify(batching)}`, { ...OPTS, label: 'verify: tests, scan, batching', phase: 'Verify', schema: VERDICT })
const newcomer = (place, n) => agent(`You have a Claude Code plugin for making films installed at ${P} (read its README first, then whatever it tells you to read). A person asks you, in these words: "Build ${place} in Blender for a film." Do not build anything. Write the step-by-step plan you would follow, as concretely as you can (what you would make, in what order, with which plugin parts and kit commands, how you would test changes and how you would check the result), and list the plugin parts you would use. Read only the plugin folder; do not read any other folder.`, { ...OPTS_SONNET, label: `newcomer ${n}`, phase: 'Verify', schema: NEWCOMER })

const [verified, newcomers] = await parallel([
  verifyAll,
  () => parallel([() => newcomer('a small fishing harbour with a fish market', 1), () => newcomer('an old railway station with a goods yard', 2)]),
])
const judged = await agent(`${COMMON}
YOUR STEP: JUDGE THE BLIND NEWCOMERS. Two fresh models were given only the plugin and a plain request with no word about surfaces, wear or how to test. For each plan say whether it applies, without being asked: normal maps, displacement, dirt, grime (where things touch and where water runs), weeds, moss, weathering, damage (chips, cracks, missing pieces), wetness or rubbish where they belong, construction that makes sense, real-world scale, the style rule, the measures, the audit and preflight, fresh checkers; and whether it tests changes the batched way (one full sweep, about 10 measured variations per change spread over the cards, one look, small pictures until the end, a card-time allowance). For each miss, quote the plugin text that caused it and give the smallest change that would make a model pick it.
PLANS: ${JSON.stringify(newcomers)}`, { ...OPTS, label: 'verify: judge the newcomers', phase: 'Verify', schema: VERDICT })

phase('Fix')
const fix = await agent(`${COMMON}
YOUR STEP: FIX. Apply every blocking and should-fix finding below (and cheap minor ones), in the plugin only; rerun all tests. Report each finding as fixed or not, with why.
VERIFY: ${JSON.stringify(verified)}
NEWCOMER JUDGE: ${JSON.stringify(judged)}
EARLIER STEPS: make generic: ${JSON.stringify(generic)}; batching: ${JSON.stringify(batching)}`, { ...OPTS, label: 'fix', phase: 'Fix', schema: STEP })

return { generic, batching, verified, newcomers, judged, fix }