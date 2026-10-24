export const meta = {
  name: 'plugin-add-missing-lessons',
  description: 'Add the 40 missing lessons from the earlier sets to the plugin (text, the stage toe fix, checks), verify each one is there, and re-run one blind newcomer',
  phases: [
    { title: 'Plan', detail: 'split the 40 lessons into two non-overlapping sets of files' },
    { title: 'Write', detail: 'two writers at once: kit code and stage; skills, docs, agents, hook and workflows' },
    { title: 'Verify', detail: 'a fresh checker per lesson and the tests; one blind newcomer and a judge' },
    { title: 'Fix', detail: 'apply what the checks found' },
  ],
}

const SC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const P = '/home/user/Music/plugins/explainer-film'
const A = '/home/user/Music/austerity-explainer'
const WORK = SC + '/plugin-work'
const AUDIT = WORK + '/lessons_audit_result.json'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
const OPUS = { model: 'opus', effort: 'xhigh' }   // the person: Opus 5.5 for the plugin work
const SONNET = { model: 'sonnet', effort: 'xhigh' } // the blind newcomer stands in for the smaller model the plugin is for

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them. The project's Claude Code plugin "explainer-film" (${P}, version 1.4.0, uncommitted work is fine) must carry everything the project has learned, so that any model (often a smaller one such as Sonnet) given only the plugin and a plain request does things right without being told. A read-only audit just checked about 370 lessons from the earlier sets (the austerity film's project notes in ${A}/project-notes: Lessons.md, Decisions.md, Workflows.md, the project story; the film kit ${A}/film-kit; the coal mine /home/user/Music/mine-scene; the Japanese courtyard /home/user/Music/japanese-courtyard (read only); the texture and garden work /home/user/Music/procedural-textures). About 210 are carried, about 90 partly, about 70 missing; it ranked 40 that matter (11 high, 26 medium, 3 low) and wrote, for each, the exact text to add and where. The full audit is ${AUDIT} (JSON: "merged.missing_that_matter" is the list of 40; "reads" holds every lesson with its source and evidence; read the sources themselves when the audit's wording is not enough).
HARD RULES: write only inside ${P} and your own scratch folder ${WORK}/lessons/<your step>/; never commit or push; never print, copy, move or read anything in ~/.runpod, and never put keys, endpoint ids, machine ids or volume ids into the plugin; never put the person's name, email or any personal detail anywhere or into a request to an outside website; never copy the person's own Astra Blender add-on (${SC}/astra-upload*, ${SC}/astra-work); never write in /home/user/Music/japanese-courtyard or in ${A} (read only). The plugin must stay generic (any place); a guard test (kit/calculators/tests/test_place_generic.py) keeps out the words of one particular coming test request; do not add place examples beyond the ones already there (the canal lock, the Japanese garden, the coal mine, the austerity film's pit-village street and Works).
BLENDER: ${BLENDER} headless (-b --disable-autoexec; xvfb-run -a for anything drawn; this computer is slow: tiny tests only). No rented card time is needed for this job; if a check truly needs one, use only the plugin's own rented-card tools within the card-time allowance and report the seconds.
WRITING: plain everyday words for smaller models and the person; one word for each thing (the plugin already says "variation", "card", "helper", "the person"); a concrete example before a general rule; say measured or judged; code with full plain-word names and a plain note at the top of each file. Where a lesson can be enforced by a check (a preflight line, an audit line, a lint, a test), prefer the check plus one short line of text over a long paragraph. Keep all plugin tests passing (python3 ${P}/kit/calculators/tests/run_all.py, with and without BLENDER set). Report in plain words what you did, tested and did not, and every failure.`

const STEP = { type: 'object', properties: {
  summary: { type: 'string' }, lessons_done: { type: 'array', items: { type: 'object', properties: { lesson: { type: 'string' }, status: { type: 'string', enum: ['added', 'added with a check', 'partly', 'not done'] }, where: { type: 'string' }, why_not: { type: 'string' } }, required: ['lesson', 'status', 'where', 'why_not'] } },
  files_changed: { type: 'array', items: { type: 'string' } }, tests_run: { type: 'string' }, failures: { type: 'array', items: { type: 'string' } }, untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'lessons_done', 'files_changed', 'tests_run', 'failures', 'untested'] }

phase('Plan')
const SPLIT = { type: 'object', properties: {
  code_and_stage: { type: 'string', description: 'the lessons (by their text) and the exact files the code writer owns' },
  text_and_routing: { type: 'string', description: 'the lessons and the exact files the text writer owns' },
  shared_files_rule: { type: 'string', description: 'how any file both need is handled (one owner only, the other leaves a note)' },
  skipped: { type: 'array', items: { type: 'string' } },
}, required: ['code_and_stage', 'text_and_routing', 'shared_files_rule', 'skipped'] }
const split = await agent(`${COMMON}
YOUR STEP: PLAN. Read the audit's 40 lessons (and the partly-carried high and medium ones in "reads" that the 40 do not already cover). Split the work between two writers who will work at the same time without touching the same file: (1) "code and stage": the kit code, the stage (for example porting the dark-and-wet "toe" look setting from ${A}/paper-film/stage/cinema-stage.js into ${P}/kit/paper-film/stage/cinema-stage.js and the lockout test scene's settings, with kit-sync-notes), calculators, preflight and audit lines, lints and tests that enforce lessons; (2) "text and routing": skills and their reference files, house rules, the tips guide, kit/docs, agents, the hook's reminder text and trigger words, and the workflows' prompts (for example a history and period critic and the 'what critics must still judge' list in critique-film.js, pictures for the fact checker, the three places where the plugin contradicts itself). Give every file exactly one owner. List anything you would skip and why (for example lessons only about the anidoodle drawing tool).`, { ...OPUS, label: 'plan the split', phase: 'Plan', schema: SPLIT })

phase('Write')
const writers = await parallel([
  () => agent(`${COMMON}
YOUR STEP: WRITE, owner "code and stage". Your lessons and files: ${split.code_and_stage}
Rule for shared files: ${split.shared_files_rule}
The other writer works at the same time on: ${split.text_and_routing}`, { ...OPUS, label: 'write: code and stage', phase: 'Write', schema: STEP }),
  () => agent(`${COMMON}
YOUR STEP: WRITE, owner "text and routing". Your lessons and files: ${split.text_and_routing}
Rule for shared files: ${split.shared_files_rule}
The other writer works at the same time on: ${split.code_and_stage}`, { ...OPUS, label: 'write: text and routing', phase: 'Write', schema: STEP }),
])

phase('Verify')
const VERDICT = { type: 'object', properties: {
  passed: { type: 'boolean' }, per_lesson: { type: 'array', items: { type: 'object', properties: { lesson: { type: 'string' }, present: { type: 'string', enum: ['yes', 'partly', 'no'] }, evidence: { type: 'string' } }, required: ['lesson', 'present', 'evidence'] } },
  findings: { type: 'array', items: { type: 'object', properties: { problem: { type: 'string' }, where: { type: 'string' }, fix: { type: 'string' }, severity: { type: 'string', enum: ['blocking', 'should fix', 'minor'] } }, required: ['problem', 'where', 'fix', 'severity'] } },
  summary: { type: 'string' },
}, required: ['passed', 'per_lesson', 'findings', 'summary'] }
const NEWCOMER = { type: 'object', properties: { plan: { type: 'string' }, plugin_parts_used: { type: 'array', items: { type: 'string' } } }, required: ['plan', 'plugin_parts_used'] }
const [checked, newcomer] = await parallel([
  () => agent(`${COMMON}
YOUR STEP: VERIFY (fresh; you wrote none of it). For each of the audit's 40 lessons, find it in the plugin now and say yes, partly or no, quoting the file and line (and the check that enforces it, if any). Run every plugin test with and without BLENDER; run the guard test; check that the stage change works (a tiny local check is enough) and that skills, kit, preflight, hook and workflows agree on names and commands. Look for anything the writers broke or made contradictory.
WRITERS' REPORTS: ${JSON.stringify(writers)}`, { ...OPUS, label: 'verify: every lesson and the tests', phase: 'Verify', schema: VERDICT }),
  () => agent(`You have a Claude Code plugin for making films installed at ${P} (read its README first, then whatever it tells you to read). A person asks you, in these words: "Build an old mountain monastery courtyard in Blender for a film." Do not build anything. Write the step-by-step plan you would follow, as concretely as you can (what you would make, in what order, with which plugin parts and kit commands, how you would test changes, how you would light it and frame it, how you would check the result, how you would work with the person), and list the plugin parts you would use. Read only the plugin folder; do not read any other folder.`, { ...SONNET, label: 'newcomer', phase: 'Verify', schema: NEWCOMER }),
])
const judged = await agent(`${COMMON}
YOUR STEP: JUDGE THE BLIND NEWCOMER. A fresh smaller model was given only the plugin and a plain request with no word about surfaces, wear, testing, light, framing or how to work with the person. Say for its plan whether it applies, without being asked: normal maps, displacement, dirt, grime where things touch and where water runs, weeds, moss, weathering, damage including missing pieces, wetness or rubbish where they belong, construction that makes sense, real-world scale, the world round the place (backdrop from every view, the ground's edge hidden, low-sun shadows), the style rule, the measures, the audit and preflight, fresh checkers, batched testing (one full sweep, about 10 measured variations per change on the cards, one look, small pictures until the end, a card-time allowance), the renderer rule, the tall phone frame and camera rules if it is for a film, one small test for the person's reaction before the whole thing, and the helper and privacy rules. For each miss, quote the plugin text that caused it and give the smallest change.
PLAN: ${JSON.stringify(newcomer)}`, { ...OPUS, label: 'judge the newcomer', phase: 'Verify', schema: VERDICT })

phase('Fix')
const fix = await agent(`${COMMON}
YOUR STEP: FIX. Apply every blocking and should-fix finding below (and cheap minor ones), in the plugin only; rerun all tests. Report each finding as fixed or not, with why.
VERIFY: ${JSON.stringify(checked)}
NEWCOMER JUDGE: ${JSON.stringify(judged)}
WRITERS: ${JSON.stringify(writers)}`, { ...OPUS, label: 'fix', phase: 'Fix', schema: STEP })

return { split, writers, checked, newcomer, judged, fix }