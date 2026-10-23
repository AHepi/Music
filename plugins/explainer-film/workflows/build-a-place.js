export const meta = {
  name: 'build-a-place',
  description: "Build a place in Blender in parts (a village, town, harbour, mine, farm, garden, interior, a set or props) from the requester's plain words: plan with researched sizes, ground first, parts built side by side, combined, given real surfaces and wear, audited, drawn with the film owner's renderer rule, checked by fresh helpers, fixed once and checked again",
  whenToUse: "When someone asks for a place, set or props to be built in Blender, whatever the words (they need not mention surfaces, wear or realism: this workflow adds the plugin's own steps). Pass the plugin folder, the kit folder, a work folder and the request exactly as the person wrote it; the notes about this computer, the disk and the money come in args.environment.",
  phases: [
    { title: 'Plan', detail: 'one planner: style note, facts with sources, draft settings, ownership, acceptance list, parts, views, readable features' },
    { title: 'Ground', detail: 'the ground part first, alone, then frozen so every other part is seated on it' },
    { title: 'Build parts', detail: 'one builder per part, side by side up to a cap, each running its own share of the pass and its own checks' },
    { title: 'Combine', detail: 'one integrator: both orders, ownership check, the whole surface-and-wear pass' },
    { title: 'Audit', detail: 'the audit and the preflight stage place on the exact file; up to two repair rounds routed to the owners; no picture before it passes' },
    { title: 'Render', detail: 'the renderer rule (Cycles where lit, EEVEE when not), small quick previews on the rented card inside the allowance, measures, the style guard' },
    { title: 'Check', detail: 'fresh checkers (look, structure, process, a blind reader), then a skeptic merges and ranks' },
    { title: 'Fix', detail: 'exactly one fix round: one fixer per owner, given only the confirmed findings' },
    { title: 'Re-check', detail: 'a different fresh checker and a second blind reader look at the changed place' },
    { title: 'Report', detail: 'full-size pictures drawn once, at the very end, when asked for; the final gate on the saved file; then a plain-words report with the card seconds' },
  ],
}

// What this does: builds a place in Blender from the requester's plain words and adds the plugin's own steps itself, so the
// request never has to mention surfaces or wear: the surface-and-wear pass (normal maps, displacement, dirt, grime, weathering,
// wetness, moss, weeds, rust, cracks, chips, edge wear, rubbish, damage as shape), the construction check, the audit and the
// preflight stage place, picture measures, fresh checkers who never see the builders' reports, and ONE fix round.
// A concrete example: the request "Build one side of a small canal lock: brick walls with stone coping, stone steps, a gravel
// towpath, a timber gate and a few props." becomes a plan of four or five parts (ground_and_water first, then walls_and_steps,
// lock_gate, props), one builder for each, one integrator, one renderer and four checkers. (The lock in the plugin's worked
// examples was built by hand with the same steps.)
//
// The rules the script keeps: nothing is drawn unless the audit passed (or failed only on items the person accepted in writing);
// at most two repair rounds before any picture, routed to the owners the audit names; exactly one fix round after the checkers;
// no paid step except rented-card time, which is LIMITED: every helper has a card-time allowance by its role (builder 10 minutes, fixer 5, integrator 10, renderer 10, checker 3, planner 0), every card job
// is written in one card-time ledger, and the batch rule applies (make every change in one sweep, then look once; try a change as about 10 measurably different versions in ONE batch with
// `explainer-film-place variations`, at most one more batch; small quick pictures until the end; full-size pictures drawn ONCE, at the very end); no commit; checkers get no
// builder reports or numbers; the blind reader gets no feature list; a part that comes back empty is reported as missing, never
// dropped quietly; a squint-test miss is reported to the person and never "fixed" by removing character.
// The helpers are told to read their own agent file first, because a plugin agent type is not assumed to be available.
//
// args: {
//   plugin: '/path/to/explainer-film'              (required: the plugin folder, which holds agents/, skills/, bin/, kit/)
//   kit: '/path/to/explainer-film/kit'             (required: the folder that holds place-kit/ and calculators/)
//   folder: '/path/to/work/folder'                 (required: plan, scene, stages, reports, pictures and checks go in it)
//   request: 'Build one side of a small canal lock ...'  (required: the person's words, exactly as written)
//   place: 'canal lock'                            (optional: the person's name for it)
//   scene: '/path/to/start.blend'                  (optional: a scene to start from; otherwise the ground builder makes an empty one)
//   blender: '/path/to/blender'                    (optional: otherwise the commands look for it themselves)
//   parts: [{ name, owner, brief }]                (optional: otherwise the planner proposes 3 to 8)
//   views: [{ name, camera, size: [w, h] }]        (optional: otherwise the planner proposes at least 3)
//   references: ['/path/to/picture.jpg']           (optional: pictures the person gave; the style guard is made from them)
//   accepted: '/path/to/accepted.json'             (optional: problems the person accepted in writing, with who and date)
//   ledger: '/path/to/spend-ledger.json'           (optional: for the process checker)
//   environment: 'notes about this computer, the disk, where to render, the money rules'   (optional text: the notes win)
//   renderer: 'auto' | 'cycles' | 'eevee'          (default auto: the film owner's rule)
//   rented: true | false | 'auto'                  (default auto: may helpers use the person's rented card? true or auto lets the batch tool and the renderer use it; false keeps every helper off it)
//   finals: false                                  (default: small previews only; true: the renderer draws the full-size finals ONCE, at the very end, after the last fix)
//   cardLedger: '/path/to/card-time-ledger.jsonl'  (default: card-time-ledger.jsonl in the run's folder: every helper writes its card jobs there, under its own name and role)
//   cardClient: 'python3 -I /path/to/client.py'    (optional: a command-line card client with the actions upload, run, job and download; passed to `variations run` as --card-client when the person's settings for the plugin's own client are not set; never put a key or an id in it)
//   cardTeamMinutes: 30                            (optional: the most card minutes the whole run may use; the planner writes it into the ledger; without it the house number holds)
//   maxParallelBuilders: 4                         (default 4: more parts wait in a queue, none is skipped; use 2 on a slow computer)
//   maxRepairRounds: 2                             (default 2, never more)
//   effort: 'medium', checkEffort: 'high', planEffort: same as effort
//   today: 'YYYY-MM-DD'                            (so "latest" figures are judged right; the script never reads the clock)
// }
// Returns { plan, ground, parts, missing_parts, combine, audit, repairs, render, final_render, card_time, checks, confirmed, fixes, recheck, reading_test,
//           fresh_check, final_gate, stopped, report_markdown }. Every key is always there (null when its phase did not run).
const ARGS = args ?? {}

// ---------------------------------------------------------------------------------------------------------------- the start
const NEEDED = { plugin: 'the plugin folder', kit: 'the folder that holds place-kit and calculators', folder: 'the folder where the plan, stages, reports and pictures go', request: "the person's words, exactly as they wrote them" }
const lacking = Object.keys(NEEDED).filter((key) => !ARGS[key])
if (lacking.length) {
  throw new Error('build-a-place cannot start: ' + lacking.map((key) => `args.${key} (${NEEDED[key]})`).join('; ') + (lacking.length > 1 ? ' are' : ' is') + ' missing.')
}

const EFFORT = ARGS.effort ?? 'medium'
const CHECK_EFFORT = ARGS.checkEffort ?? 'high'
const PLAN_EFFORT = ARGS.planEffort ?? EFFORT
const CAP = Math.max(1, Math.floor(Number(ARGS.maxParallelBuilders) || 4))
const MAX_REPAIRS = Math.max(0, Math.min(2, Math.floor(Number(ARGS.maxRepairRounds ?? 2))))
const READING_LINE = 0.75   // film-settings.json, place_measures reading_test_share_min (judged: 12 of 16 features)
const RENTED = ARGS.rented ?? 'auto'
const RENDERER = ARGS.renderer ?? 'auto'
const FINALS = ARGS.finals === true
const CARD_LEDGER = String(ARGS.cardLedger ?? `${String(ARGS.folder).replace(/\/+$/, '')}/card-time-ledger.jsonl`)
const CARD_CLIENT = ARGS.cardClient ? String(ARGS.cardClient) : null
const CARD_TEAM_MINUTES = Number(ARGS.cardTeamMinutes) > 0 ? Number(ARGS.cardTeamMinutes) : null
const CARD_MINUTES = { builder: 10, fixer: 5, integrator: 10, renderer: 10, checker: 3, planner: 0 }   // film-settings.json place_card_time.allowance_minutes (judged); a test keeps them equal
const WHERE = RENTED === true ? 'rented' : RENTED === false ? 'local' : 'auto'
const ENGINE = ['cycles', 'eevee'].includes(String(RENDERER).toLowerCase()) ? String(RENDERER).toLowerCase() : 'auto'
const REFERENCES = Array.isArray(ARGS.references) ? ARGS.references : []
const SEVERE = ['must fix', 'should fix']

const RUN_FOLDER = String(ARGS.folder).replace(/\/+$/, '')
const DIR = { plan: `${RUN_FOLDER}/plan`, scene: `${RUN_FOLDER}/scene`, stages: `${RUN_FOLDER}/stages`, work: `${RUN_FOLDER}/work`, reports: `${RUN_FOLDER}/reports`, render: `${RUN_FOLDER}/render`, pictures: `${RUN_FOLDER}/pictures`, checks: `${RUN_FOLDER}/checks` }
const START_FILE = ARGS.scene ?? `${DIR.scene}/start.blend`
const GROUND_FILE = `${DIR.scene}/ground.blend`
const combinedFile = (version) => `${DIR.scene}/round${version}/combined.blend`
const finishedFile = (version) => `${DIR.scene}/round${version}/finished.blend`
const auditFile = (version) => `${DIR.reports}/place-audit-round${version}.json`
const AGENT = { planner: 'place-planner.md', builder: 'place-builder.md', integrator: 'place-integrator.md', renderer: 'place-renderer.md', checker: 'place-checker.md' }
const first = (role) => `First read ${ARGS.plugin}/agents/${AGENT[role]} and follow it. (In that file and in the skill files it names, \${CLAUDE_PLUGIN_ROOT} means the plugin folder: ${ARGS.plugin}.)`

// everything the later steps need lives in one object, so an early stop can always write its report
const STATE = {
  plan: null, ground: null, built: [], missing: [], combine: null, audit: null, auditRounds: [], repairs: [],
  render: null, checks: {}, skeptic: null, confirmed: [], notFixedOnPurpose: [], unverified: [],
  fixes: [], fixOwners: [], fixCombine: null, fixAudit: null, fixRender: null, recheck: null, recheckBlind: null,
  readingTests: [], freshCheck: null, finalGate: null, version: 1, finalFile: null, finalAuditFile: null, finalRender: null, claimOwners: [],
  havePictures: false, stopped: null, notes: [], cardRows: [], finalsRender: null,
}

// ------------------------------------------------------------------------------------------------------------- small helpers
const asText = (value) => (typeof value === 'string' ? value : JSON.stringify(value, null, 1))
const safeWord = (text) => String(text ?? '').trim().toLowerCase().replace(/[^a-z0-9_]+/g, '_').replace(/^_+|_+$/g, '')
const numbered = (list) => ((list ?? []).length ? list.map((item, index) => `${index + 1}. ${item}`).join('\n') : '(none)')
const escapeRegExp = (text) => String(text).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const unique = (list) => [...new Set(list)]
const placeName = () => STATE.plan?.place ?? ARGS.place ?? 'the place'

// runs work(item) for every item, at most cap at a time; the rest wait in a queue (none is skipped); an item whose work throws gives null
async function runQueued(items, cap, work) {
  const results = new Array(items.length).fill(null)
  if (!items.length) return results
  let next = 0
  const slot = () => async () => {
    while (next < items.length) {
      const index = next++
      try {
        results[index] = await work(items[index], index)
      } catch (problem) {
        log(`One helper stopped with an error and is reported as missing: ${problem && problem.message ? problem.message : problem}`)
        results[index] = null
      }
    }
  }
  await parallel(Array.from({ length: Math.min(cap, items.length) }, slot))
  return results
}

// a claim as a bare sentence: no measured result in brackets (a checker must recompute it, not copy it)
const bareClaim = (text) => String(text ?? '').replace(/\s*[(\[][^)\]]*\d[^)\]]*[)\]]/g, '').replace(/\s+/g, ' ').trim()

const ownerNames = () => (STATE.plan ? STATE.plan.parts.map((part) => part.owner) : [])
const knownOwner = (name) => {
  const word = safeWord(name)
  return ownerNames().includes(word) ? word : 'integrator'
}
const ownerFromText = (text) => {
  const head = safeWord(String(text ?? '').split(':')[0])
  return ownerNames().includes(head) ? head : 'integrator'
}
const partOf = (owner) => STATE.plan.parts.find((part) => part.owner === owner)

// ----------------------------------------------------------------------------------------------------------- shared prompt text
const RULES = `RULES FOR EVERYONE
- Spend no money. The only paid thing in this run is time on the person's own rented card, and it is LIMITED: every helper has an allowance in card minutes by its role, every card job is written in the card-time ledger, and the tools refuse a step that would pass the allowance. The card is used only through the batch tool (explainer-film-place variations) and render, and only when the notes say it may be used. Try things in batches (one sweep of changes, then look once; about 10 measurably different versions in ONE batch; at most one more batch), small quick pictures until the end, full-size pictures once at the very end. Your own section below names your allowance.
- Never commit or push. Never write a key, an id or a personal detail into any file or answer, and never open the folder where the rented-card account keeps its settings (the client reads the person's settings when it runs).
- Never lower a requirement to make a check pass. The only allowed ways to skip a treatment are an off entry with a true reason in the place settings, and an accepted entry that the person signed (who and the date). You never sign for the person.
- This computer is slow and its disk is small: run only small tests here (small pictures, quick runs); anything bigger waits for the renderer. Keep .blend files few, delete your own scratch files, keep big pictures on the rented card's store and bring back only small previews (under 400 KB).
- Plain everyday words, one word for each thing. Say what a tool measured and what you only judged. Say what you did not test and every failure; never write that something passed when you did not see it pass.
- Return your report as text in your final answer, in the shape asked (it is enforced). Save your evidence as JSON or text files in your own folder as you go: a helper can be refused a report file, and a restart can lose work.`

const environmentText = () => (ARGS.environment ? `\nNOTES ABOUT THIS COMPUTER, THE DISK AND THE MONEY, from the person who started the run (they win over anything else written here):\n${asText(ARGS.environment)}\n` : '')
// the part every helper that may use the card gets: who it is in the ledger, its allowance, and the batch rule in a few plain lines
const cardBlock = (name, role) => `YOUR CARD TIME
Your helper name for the card-time ledger is ${name}. Your role is ${role}. The ledger is ${CARD_LEDGER}. Your allowance is ${CARD_MINUTES[role]} minutes of rented-card time (a house number, judged): the tools count it and refuse a step that would pass it. Put --helper ${name} --role ${role} --ledger ${CARD_LEDGER} on every variations, render and rent command you run. \`explainer-film-place card-time show --ledger ${CARD_LEDGER}\` says what you have left.
${RENTED === false ? 'The person said: no rented card in this run. Draw nothing on a card. A batch may be drawn with --where local on a tiny scene, or not at all; say what you could not try.' : `Rented card allowed: ${RENTED}.`}
THE BATCH RULE (read ${ARGS.plugin}/skills/surfaces-wear-and-construction/batched-rounds-and-card-time.md first): make every change you plan in ONE sweep, then look once. Build the scene once and save it. For each change to a thing you are not sure of, write about 10 versions whose settings are far apart and draw them in ONE batch: explainer-film-place variations plan FILE.json (free), then explainer-film-place variations run FILE.json --where ${WHERE}${CARD_CLIENT ? ` --card-client "${CARD_CLIENT}"` : ''} (up to 3 cards at once, 600 x 400, one labelled sheet with measures and the card seconds). Look at the sheet with the Read tool, pick or combine, and draw at most ONE more batch. Small quick pictures until the end; full-size pictures are drawn once, at the very end, by the renderer. Report the card seconds you used (card_seconds) and the batches you drew (batches).`
const builderHelper = (part, mode) => (mode === 'fix' ? { name: `fixer-${part.owner}`, role: 'fixer' } : { name: `builder-${part.owner}`, role: 'builder' })

const blenderText = () => (ARGS.blender
  ? `Blender is at ${ARGS.blender}: give every command that starts Blender the option --blender ${ARGS.blender}.`
  : 'Blender: the commands look for it themselves (the BLENDER setting, then the kit machine settings file, then the PATH). If it cannot be found, stop and say so.')

const runHeader = (who) => `THE RUN
The place: ${STATE.plan?.place ?? ARGS.place ?? '(the planner chooses a name)'}. Today is ${ARGS.today ?? '(not given)'}.
The request, in the person's own words, exactly: "${ARGS.request}"
The plugin is at ${ARGS.plugin}. The kit (it holds place-kit and calculators) is at ${ARGS.kit}. The run's folder is ${RUN_FOLDER}.
The place command is ${ARGS.plugin}/bin/explainer-film-place (the preflight is ${ARGS.plugin}/bin/explainer-film-preflight); call them by these full paths when they are not on your PATH.
${blenderText()}
${who === 'checker'
    ? `Your folder for scratch files and your result: ${DIR.checks}/. Pictures are under ${DIR.pictures}/, scene files under ${DIR.scene}/, the plan under ${DIR.plan}/. You work blind to how things were built: do not open the work folder, the stage files or any part report.`
    : `Folders in the run's folder: plan (the plan files), scene (Blender scenes), stages (one stage file for each owner), work (one scratch folder for each owner), reports, render (job files), pictures, checks.`}
${environmentText()}
${RULES}`

const planFilesText = () => {
  const files = STATE.plan.files
  return `- style note: ${files.style_note}\n- facts table: ${files.facts}\n- place settings: ${files.settings}\n- ownership table: ${files.ownership}\n- acceptance list: ${files.acceptance}`
}
const viewsText = () => numbered(STATE.plan.views.map((view) => `${view.name}: camera "${view.camera}", ${view.size[0]} x ${view.size[1]}`))

// ------------------------------------------------------------------------------------------------------------------- schemas
const str = { type: 'string' }
const num = { type: 'number' }
const bool = { type: 'boolean' }
const strs = { type: 'array', items: str }
const list = (item) => ({ type: 'array', items: item })
const obj = (properties, required) => ({ type: 'object', properties, required: required ?? Object.keys(properties) })
const freeObject = { type: 'object', properties: {}, additionalProperties: true }
const SEVERITY = { type: 'string', enum: ['must fix', 'should fix', 'minor'] }
const VERDICT = { type: 'string', enum: ['yes', 'nearly', 'no', 'not judged'] }
const AUDIT_PROBLEM = obj({ check: str, where: str, owner: str, text: str, fix: str })

const PLAN = obj({
  place: str, place_type: str,
  files: obj({ style_note: str, facts: str, settings: str, ownership: str, acceptance: str }),
  ground_owner: str, scene_file: str, look: str, state: str,
  parts: list(obj({ name: str, owner: str, collection: str, region: list(num), brief: str, steps_in_order: strs, triangle_budget: num }, ['name', 'owner', 'brief'])),
  contracts: strs, frozen: strs,
  views: list(obj({ name: str, camera: str, size: list(num) }, ['name'])),
  readable_features: list(obj({ name: str, keywords: strs })),
  renderer_hint: str, open_questions: strs, notes: str,
}, ['place', 'place_type', 'files', 'ground_owner', 'parts', 'views', 'readable_features'])

const PART_PROPS = {
  owner: str, stage_file: str, work_file: str, steps_finished: str, objects_added: num, triangles: num,
  own_audit: obj({ verdict: str, problems: strs }),
  surface_pass_done: bool, wear_preview_done: bool,
  claims: list(obj({ claim: str, measured_by: str })),
  unsure: strs, shared_problems: strs, failures: strs, not_tested: strs, views_to_redraw: strs, seconds: num, card_seconds: num, batches: num,
}
const PART_REQUIRED = ['owner', 'stage_file', 'steps_finished', 'objects_added', 'triangles', 'own_audit', 'surface_pass_done', 'wear_preview_done', 'claims', 'unsure', 'shared_problems', 'failures', 'not_tested', 'seconds']
const PART_REPORT = obj(PART_PROPS, PART_REQUIRED)
const GROUND_REPORT = obj({ ...PART_PROPS, start_file: str, ground_file: str, cameras: strs, ground_promise: str }, [...PART_REQUIRED, 'ground_file', 'cameras', 'ground_promise'])

const COMBINE_REPORT = obj({
  order_plain_ok: bool, order_reverse_ok: bool, violations: strs, idempotent: bool,
  combined_file: str, finished_file: str, audit_file: str,
  audit_verdict: { type: 'string', enum: ['pass', 'fail', 'not run'] }, audit_problems: list(AUDIT_PROBLEM),
  repairs_made: strs, missing_parts: strs, failures: strs, not_tested: strs, card_seconds: num, batches: num,
}, ['order_plain_ok', 'order_reverse_ok', 'violations', 'idempotent', 'finished_file', 'audit_verdict', 'audit_problems', 'repairs_made', 'failures', 'not_tested'])

const AUDIT_REPORT = obj({
  scene_file: str, audit_file: str, scene_sha256: str, audit_exit_code: num, preflight_exit_code: num,
  verdict: { type: 'string', enum: ['pass', 'fail'] }, quick: bool,
  problems: list(AUDIT_PROBLEM), looks: strs, known: strs, notes: strs,
}, ['scene_file', 'audit_file', 'audit_exit_code', 'preflight_exit_code', 'verdict', 'problems', 'looks', 'known'])

const RENDER_REPORT = obj({
  renderer: str, why: str, where: { type: 'string', enum: ['rented', 'local'] }, device: str, balance_checked: bool, stalled: bool,
  pictures: list(obj({ view: str, path: str, half_path: str, size: list(num), samples: num, seconds: num }, ['view', 'path', 'half_path', 'size', 'samples', 'seconds'])),
  seconds_total: num, estimated_dollars: num, card_seconds: num, guard_file: str, guard_made_from: str, guard_provisional: bool,
  measures: freeObject, notes: strs, failures: strs,
}, ['renderer', 'why', 'where', 'device', 'balance_checked', 'stalled', 'pictures', 'seconds_total', 'estimated_dollars', 'guard_made_from', 'measures', 'notes'])

const CHECK = obj({
  mode: str, was_blind: bool, art_style_kept: VERDICT, lived_in: VERDICT, construction_makes_sense: VERDICT,
  each_element: list(obj({ element: str, verdict: str, why: str })),
  claims_checked: list(obj({ claim: str, holds: bool, evidence: str })),
  problems: list(obj({ what: str, where: str, severity: SEVERITY, cheapest_fix: str, owner: str })),
  should_fix_now: str, not_tested: strs, measures: freeObject, audit_scene_sha1: str,
}, ['mode', 'was_blind', 'art_style_kept', 'lived_in', 'construction_makes_sense', 'each_element', 'claims_checked', 'problems', 'should_fix_now', 'not_tested', 'measures'])

const BLIND = obj({ seen: strs, notes: str }, ['seen'])

const SKEPTIC = obj({
  confirmed: list(obj({ what: str, where: str, severity: SEVERITY, cheapest_fix: str, owner: str, evidence: str, from: str })),
  rejected: list(obj({ what: str, reason: str })),
  not_fixed_on_purpose: list(obj({ what: str, why: str })),
  summary: str,
}, ['confirmed', 'rejected', 'not_fixed_on_purpose', 'summary'])

const FINAL_GATE = obj({
  preflight_exit_code: num, verdict: { type: 'string', enum: ['pass', 'fail'] }, lines: strs, stale: bool, fresh_check_file: str, notes: strs,
}, ['preflight_exit_code', 'verdict', 'lines', 'stale', 'notes'])

// ------------------------------------------------------------------------------------------------------------------ prompts
const planPrompt = () => `${first('planner')}

${runHeader('planner')}

YOUR JOB: plan this place. Write the plan files into ${DIR.plan}/ with exactly these names: style-note.md, real-world-facts.json, place-settings.json, ownership.json, acceptance.json. Never touch a Blender scene.
${ARGS.place ? `The person calls it: ${ARGS.place}.` : 'Choose a short plain name for it.'}
${ARGS.parts ? `The person asked for these parts, so use them (you may add parts and improve their briefs):\n${asText(ARGS.parts)}` : 'Propose 3 to 8 parts.'}
The ground part is built first, alone, then frozen. Its owner goes in ground_owner, and in ownership.json under frozen.set_by (the ground part is the one that makes the cameras, the lights and the world, so without that field its own camera is a violation). ${ARGS.scene ? `The starting scene is ${ARGS.scene}; the ground builder starts from it.` : `There is no starting scene: the ground builder makes an empty one at ${START_FILE}.`}
${ARGS.views ? `The person wants these views:\n${asText(ARGS.views)}` : 'Propose at least three views.'} The cameras are named "View <name>".
${REFERENCES.length ? `The person gave reference pictures: ${REFERENCES.join(', ')}. Measure them; the style note and the style guard come from them, so the style note is not provisional.` : 'There are no reference pictures: the style note is PROVISIONAL (say so in its first line); the first honest picture will make the style guard.'}
Renderer wished: ${RENDERER}. Rented card allowed: ${RENTED}.
CARD TIME: you have none (planner allowance ${CARD_MINUTES.planner} minutes). The run's card-time ledger is ${CARD_LEDGER}; each helper has an allowance by its role (builder ${CARD_MINUTES.builder} minutes, fixer ${CARD_MINUTES.fixer}, integrator ${CARD_MINUTES.integrator}, renderer ${CARD_MINUTES.renderer}, checker ${CARD_MINUTES.checker}). ${CARD_TEAM_MINUTES ? `The person set a total for the whole run of ${CARD_TEAM_MINUTES} card minutes: write it down with explainer-film-place card-time start --team-minutes ${CARD_TEAM_MINUTES} --ledger ${CARD_LEDGER} (it costs nothing) and say so in the last line of the style note.` : 'The person set no total for the whole run: the house number holds.'} Tell each part's brief to make every change in one sweep, build the scene once, and try an unsure change as about 10 far-apart versions in ONE batch (explainer-film-place variations), at most one more batch.
Return the plan in the shape asked.`

const groundBlock = () => `YOU ARE THE GROUND PART and you go first, alone. Nothing else is built until you are done.
Starting scene: ${ARGS.scene ? `${ARGS.scene} (copy it, never change the original)` : `none: make an empty scene and save it as ${START_FILE}`}.
Make the ground (a plain rectangle gets a graded grid; any other shape is split in place and keeps its outline), the road shapes, the verge and the puddle hollows; make the view cameras named in the views list and the sun (ownership.json lets you, through frozen.set_by); apply your stage file to the starting scene and save the result as ${GROUND_FILE}. The quick way, which also checks your stage file against the ownership table:
explainer-film-place combine --scene ${START_FILE} --stages ${DIR.stages}/stage_${STATE.plan.ground_owner}.py --order plain --owners ${STATE.plan.files.ownership} --save-as ${GROUND_FILE}
That file is then FROZEN: every other part is seated on it.
No buildings and no props are yours. Say in ground_promise what the ground promises the others (for example "inside 1.2 m of each road centre line the ground is as it is").`

const buildBlock = (part) => `Work on your own COPY of ${GROUND_FILE}, saved as ${DIR.work}/${part.owner}/scene.blend, with your stage file applied to it (the frozen ground: never change the original, never save over it). Seat everything on it.`

const fixBlock = (findings, why) => `THIS IS A FIX ROUND (${why}). Only these confirmed findings about your part are yours; fix them and nothing else:
${numbered(findings.map((finding) => `${finding.what ?? finding.text} (where: ${finding.where ?? 'not said'}; cheapest fix: ${finding.cheapest_fix ?? finding.fix ?? 'not said'}; severity: ${finding.severity ?? 'must fix'})`))}
Change only your own stage file ${DIR.stages}/stage_<owner>.py, run it again with your checks, and name in views_to_redraw the views that changed (by view name). Do not make the part less characterful to chase a number: a squint-test miss is reported to the person, never fixed.`

// the steps the plugin adds to every part, whatever the brief says (the request never has to mention surfaces, wear or construction)
const requiredStepsText = (part, base) => `THE STEPS THE PLUGIN ADDS (required for your part whatever the brief says; the person never has to ask for them):
1. Build from the ground up at the real sizes of the facts table: every part carried, nothing floating, every object with its owner and its role.
2. Run the surface-and-wear pass on your part (real normal maps, displacement, roughness and colour variation, dirt, grime, weathering, wetness, moss, weeds, rust, cracks, chips, edge wear, rubbish, damage as shape) and read every line it prints:
explainer-film-place finish-part --scene ${DIR.work}/${part.owner}/scene.blend --settings ${STATE.plan.files.settings} --owner ${part.owner} --quick --save-as ${DIR.work}/${part.owner}/part.blend
3. Run the construction check on it and read every FAIL line:
explainer-film-place construction --scene ${DIR.work}/${part.owner}/part.blend --settings ${STATE.plan.files.settings} --owner ${part.owner} --out ${DIR.work}/${part.owner}/construction.json
4. Prove your stage file is safe next to the others (it must give the same scene when run twice and must change nothing that is not yours):
explainer-film-place combine --scene ${base} --stages ${DIR.stages}/stage_${part.owner}.py --order plain --owners ${STATE.plan.files.ownership} --out ${DIR.work}/${part.owner}/combine.json
A step you did not run is reported as not run, never as done.`

const builderPrompt = (part, mode, findings, why) => `${first('builder')}

${runHeader('builder')}

YOUR MODE: ${mode}. YOUR PART: ${part.name}. Owner: ${part.owner}. Collection: "Place: ${part.owner}".
Region (x0, y0, x1, y1 in metres): ${JSON.stringify(part.region ?? [])}. Triangle budget for this part: ${part.triangle_budget ?? 'the budget the audit holds (house numbers)'}.
The plan files:
${planFilesText()}
Views (the ground part makes the cameras):
${viewsText()}
Frozen (nobody but the ground part changes these):
${numbered(STATE.plan.frozen.length ? STATE.plan.frozen : ['cameras', 'lights', 'the world', 'render settings', 'the ground height'])}
Contracts between owners:
${numbered(STATE.plan.contracts.length ? STATE.plan.contracts : ['none written'])}
The other owners (their objects are not yours to touch): ${ownerNames().filter((name) => name !== part.owner).join(', ') || 'none'}.

${mode === 'ground' ? groundBlock() : mode === 'fix' ? fixBlock(findings, why) : buildBlock(part)}

YOUR BRIEF:
${part.brief}

${requiredStepsText(part, mode === 'ground' ? START_FILE : GROUND_FILE)}

${cardBlock(builderHelper(part, mode).name, builderHelper(part, mode).role)}

YOUR STEPS, in priority order (a finished step 1 plus step 2 is already a valid delivery):
${numbered(part.steps_in_order)}

Your stage file: ${DIR.stages}/stage_${part.owner}.py. Your own folder for scratch files and evidence: ${DIR.work}/${part.owner}/.
Give every object its owner and its role as it is made. Claims in your report are bare sentences with no measured number in them; the tool that measured each goes in measured_by.`

const stagePaths = () => STATE.built.filter((entry) => entry.report).map((entry) => entry.report.stage_file || `${DIR.stages}/stage_${entry.part.owner}.py`)
const stageList = () => stagePaths().map((path, index) => `- ${STATE.built.filter((entry) => entry.report)[index].part.owner}: ${path}`).join('\n') || '(none)'

const combinePrompt = (version, repairs, groundChanged) => `${first('integrator')}

${runHeader('integrator')}

YOUR MODE: combine (version ${version}).
The frozen ground: ${GROUND_FILE}.${groundChanged ? ` THE GROUND STAGE WAS CHANGED: rebuild ${GROUND_FILE} first (apply ${DIR.stages}/stage_${STATE.plan.ground_owner}.py to ${START_FILE} and save), then apply every other stage again.` : ''}
The stage files to combine:
${stageList()}
Parts that did NOT report (do not combine them; list them as missing in your answer): ${STATE.missing.length ? STATE.missing.join(', ') : 'none'}.
The plan files:
${planFilesText()}
Run these, in this order (each one starts Blender):
1. explainer-film-place combine --scene ${GROUND_FILE} --stages ${stagePaths().join(' ')} --order plain --owners ${STATE.plan.files.ownership} --save-as ${combinedFile(version)} --out ${DIR.reports}/combine-plain-round${version}.json
2. explainer-film-place combine --scene ${GROUND_FILE} --stages ${stagePaths().join(' ')} --order reverse --owners ${STATE.plan.files.ownership} --out ${DIR.reports}/combine-reverse-round${version}.json
3. explainer-film-place finish --scene ${combinedFile(version)} --settings ${STATE.plan.files.settings} --facts ${STATE.plan.files.facts} --save-as ${finishedFile(version)}
Never use a quick run for the finished scene. Step 3 writes place-audit.json beside the finished scene and prints the audit; the official audit of this round is made later by another helper. Delete the combined scene of any older round when you are sure it is not needed.
Look: ${STATE.plan.look ?? 'from the settings'}; state: ${STATE.plan.state ?? 'from the settings'} (change them only when a repair below says so).
${repairs.length ? `REPAIRS ASKED OF YOU (settings, role tags and dials only: geometry is never yours and goes back to its owner):\n${numbered(repairs.map((repair) => `${repair.text} (where: ${repair.where}; fix: ${repair.fix})`))}\n` : ''}${cardBlock('integrator', 'integrator')}
Return your report in the shape asked.`

const auditPrompt = (version) => `${first('integrator')}

${runHeader('integrator')}

YOUR MODE: audit. Prove this file and change nothing: ${finishedFile(version)}. Never save it again and never run the whole pass again.
Settings: ${STATE.plan.files.settings}. Facts table: ${STATE.plan.files.facts}. Ownership table: ${STATE.plan.files.ownership}.
Run these, in this order:
1. explainer-film-place audit --scene ${finishedFile(version)} --settings ${STATE.plan.files.settings} --facts ${STATE.plan.files.facts} --out ${auditFile(version)}
2. explainer-film-preflight place --place-audit ${auditFile(version)} --blend ${finishedFile(version)} --place-settings ${STATE.plan.files.settings} --reports ${DIR.reports}/preflight-round${version}${ARGS.accepted ? ` --accepted ${ARGS.accepted}` : ''}
The preflight reports go into ${DIR.reports}/preflight-round${version}/, so nothing lands beside the plugin. ${ARGS.accepted ? 'The accepted file is the person\'s: you never write an accepted entry.' : 'There is no accepted file.'}
Every FAIL goes into problems with the owner of the object it names ('integrator' for settings, role tags and dials). Return your report in the shape asked.`

const renderPrompt = (tag, views, previous, file, finalOnly = false) => `${first('renderer')}

${runHeader('renderer')}

YOUR JOB: draw the pictures of ${file}. Round: ${tag}.
The renderer rule: ${RENDERER} (auto means the film owner's rule: Cycles where lamps, lit windows, lanterns or fires are on, EEVEE when they are off). Rented card allowed: ${RENTED} (auto: use it when the client says workers can start, otherwise only tiny local pictures, and say so).
Views to draw:
${numbered(views.map((view) => `${view.name}: camera "${view.camera}", ${view.size[0]} x ${view.size[1]}`))}
${finalOnly
    ? 'THIS IS THE ONE FULL-SIZE DRAWING OF THE RUN, at the very end: draw ONLY the final-size pictures (no previews, so write each view as "kinds": ["final"] in the job file), at the sizes above, from this file, which is the last audited file. Nothing is tried here: the small quick pictures of the earlier rounds were for that.'
    : `Finals: no. These are the small quick pictures (previews) that the checkers look at. The full-size pictures are drawn ONCE, at the very end, and only when the person asked for them (${FINALS ? 'they did' : 'they did not'}); never draw one to test something.`}
${cardBlock('renderer', 'renderer')}
Write the job file to ${DIR.render}/job-${tag}.json (its scene is ${file}), the pictures into ${DIR.pictures}/${tag}/ and the half-size copies into ${DIR.pictures}/half/${tag}/. Name each half-size copy by its number only (view-1.jpg, view-2.jpg and so on, in the order of the views), so that its file name tells a reader nothing.
Draw with: explainer-film-place render --scene ${file} --job ${DIR.render}/job-${tag}.json --where ${WHERE} --engine ${ENGINE}${finalOnly ? ' --finals' : ''} --helper renderer --role renderer --ledger ${CARD_LEDGER}
${previous ? `This is a later round. Use the existing style guard ${STATE.render.guard_file ?? `${DIR.pictures}/style-guard.json`} and do not make a new one. The previous round's pictures (for the squint test): ${previous.join(', ')}.` : `Make the style guard from ${REFERENCES.length ? `the reference pictures: ${REFERENCES.join(', ')}` : 'your first honest picture (say it is PROVISIONAL)'} and write it to ${DIR.pictures}/style-guard.json.`}
Return your report in the shape asked.`

const claimsText = () => {
  const rows = []
  STATE.claimOwners = []
  const add = (owner, claim) => { rows.push(`[${owner}] ${bareClaim(claim)}`); STATE.claimOwners.push({ owner, key: plainKey(claim) }) }
  for (const entry of STATE.built) if (entry.report) for (const claim of entry.report.claims) add(entry.part.owner, claim.claim)
  if (STATE.ground) for (const claim of STATE.ground.claims) add(STATE.plan.ground_owner, claim.claim)
  return numbered(rows)
}

const picturePaths = (render, half) => (render?.pictures ?? []).map((picture) => (half ? picture.half_path : picture.path))

// who owns a claim a checker sent back: its [owner] tag when it kept one, else the claim it matches, else the integrator
const plainKey = (text) => bareClaim(text).replace(/^\[[^\]]*\]\s*/, '').toLowerCase()
function claimOwner(text) {
  const tag = /^\s*\[([^\]]+)\]/.exec(String(text ?? ''))
  if (tag && ownerNames().includes(safeWord(tag[1]))) return safeWord(tag[1])
  const key = plainKey(text)
  const match = STATE.claimOwners.find((known) => known.key && (key.includes(known.key) || known.key.includes(key)))
  return match ? match.owner : 'integrator'
}

const checkContext = (render) => `THE PLACE TO CHECK
The request, in the person's own words, exactly: "${ARGS.request}"
Style note: ${STATE.plan.files.style_note}
Acceptance list: ${STATE.plan.files.acceptance}
Facts table: ${STATE.plan.files.facts}
Place settings: ${STATE.plan.files.settings}
The finished scene file: ${STATE.finalFile}
The pictures (look at them with the Read tool):
${numbered(picturePaths(render, false))}
The style guard (for measures): ${STATE.render?.guard_file ?? '(none was made)'}${STATE.render?.guard_provisional ? ' (PROVISIONAL: it was made from the first honest picture)' : ''}
Put the SHA-1 of the scene file you checked (sha1sum) in audit_scene_sha1.`

const checkerPrompt = (mode, extra, render) => `${first('checker')}

${runHeader('checker')}

YOUR MODE: ${mode}.
${checkContext(render ?? STATE.render)}
Write your scratch files and your result into ${DIR.checks}/${mode}/.
${extra}
Return your result in the shape asked.`

const lookExtra = () => `The planned features, to judge one by one in each_element (you were NOT blind to this list: say was_blind false):
${numbered(STATE.plan.readable_features.map((feature) => `${feature.name} (viewers would say: ${(feature.keywords ?? []).join(', ')})`))}
The builders' claims, as bare sentences to recompute where a picture can show them (do not look for their numbers):
${claimsText()}`

const structureExtra = () => `The builders' claims, as bare sentences to recompute with your own scripts on the scene file (use another formula than the obvious one where you can; list the ones you could not test in not_tested):
${claimsText()}`

const processExtra = () => `The money and disk rules, and anything else about how the work may be done, are in the notes above. ${ARGS.ledger ? `The spend ledger is ${ARGS.ledger}.` : 'There is no spend ledger.'}
THE CARD-TIME LEDGER is ${CARD_LEDGER} (read it with explainer-film-place card-time show --ledger ${CARD_LEDGER}). Allowances in minutes by role: ${Object.entries(CARD_MINUTES).map(([role, minutes]) => `${role} ${minutes}`).join(', ')}${CARD_TEAM_MINUTES ? `; the whole run: ${CARD_TEAM_MINUTES}` : ''}. Say whether every helper stayed inside its allowance, whether the card seconds that helpers REPORTED match the ledger, whether any change was tried in more than two batches, whether tests were drawn at full size, and whether full-size pictures were drawn more than once or before the end. What the helpers reported: ${asText(cardTimeSummary().reported)}.
What the renderer says it did (check it against the logs next to the pictures, do not trust it): ${STATE.render ? JSON.stringify({ renderer: STATE.render.renderer, where: STATE.render.where, device: STATE.render.device, balance_checked: STATE.render.balance_checked, stalled: STATE.render.stalled, seconds_total: STATE.render.seconds_total, estimated_dollars: STATE.render.estimated_dollars, pictures: STATE.render.pictures.map((picture) => ({ view: picture.view, seconds: picture.seconds })) }) : 'no pictures were drawn'}
The audited file is ${STATE.finalFile}; its audit is ${STATE.finalAuditFile}. Check privacy over every file written in the run's folders, leftovers in the scene (preview cameras, unused data), the disk used, and whether the audit is stale.`

// the blind reader does NOT read the checker agent file (its examples would give the game away): this prompt holds its whole job
const blindPrompt = (render, round) => `You are a reader of pictures. Round ${round}.
Look at these pictures with the Read tool. They are half-size pictures of one drawn scene:
${numbered(picturePaths(render, true))}
Do not open any other file and do not look in any other folder: you are told nothing else, on purpose.
List everything you can name in them, as short plain phrases, one thing for each phrase: what it is, what it is made of, what state it is in. Do not guess what anyone asked for.
Return your list as the shape asked.`

const skepticPrompt = (findings) => `${first('checker')}

${runHeader('checker')}

YOUR MODE: skeptic.
${checkContext(STATE.render)}
Fresh checkers looked at this place; their findings and every claim that did not hold are below. For EACH one, check it yourself (open the picture, run a script on the scene). Keep only what is real and what a viewer or a builder would care about. Merge duplicates. Rank honestly: must fix only for something wrong, broken or misleading that a viewer would notice; should fix for a clear improvement worth a small change; minor for the rest. Keep the cheapest concrete fix and its owner (a part owner: ${ownerNames().join(', ')}; or integrator for settings, role tags and dials). A squint-test miss, or any finding whose only cure is to remove character from the place, goes in not_fixed_on_purpose, never in confirmed: the person decides.
Findings:
${JSON.stringify(findings, null, 1)}
Return your answer in the shape asked.`

const recheckExtra = (oldRender) => `You are a DIFFERENT checker from the first round and you did not make the fixes. The confirmed findings of the first round, which the fix round tried to fix:
${numbered(STATE.confirmed.map((finding) => `${finding.what} (where: ${finding.where}; owner: ${finding.owner})`))}
The first round's pictures, for comparison: ${picturePaths(oldRender, false).join(', ')}.
For each finding say, as a claim, whether it is fixed (holds true or false, with the evidence from the new picture or the scene). Then look for NEW faults the fixes caused.`

const gatePrompt = (fresh) => `${first('integrator')}

${runHeader('integrator')}

YOUR MODE: gate (the last step). The final scene is ${STATE.finalFile}; its audit is ${STATE.finalAuditFile}. The pictures are in ${DIR.pictures}/ (${picturePaths(STATE.finalRender, false).join(', ') || 'none'}). The style guard is ${STATE.render?.guard_file ?? '(none)'}. Settings: ${STATE.plan.files.settings}. Preflight reports go into ${DIR.reports}/preflight-final/ (use --reports with that folder).
${ARGS.accepted ? `The person's accepted file is ${ARGS.accepted} (pass it with --accepted).` : ''}
The fresh checkers' final result, as JSON, to save as ${DIR.reports}/fresh-check.json before you run the preflight:
${JSON.stringify(fresh, null, 1)}
Return your answer in the shape asked.`

// ------------------------------------------------------------------------------------------------------ plan normalising
function normalisePlan(raw) {
  const seen = new Set()
  const parts = []
  for (const given of raw.parts ?? []) {
    let owner = safeWord(given.owner || given.name) || `part_${parts.length + 1}`
    while (seen.has(owner)) owner = `${owner}_2`
    seen.add(owner)
    parts.push({ name: given.name || owner, owner, collection: `Place: ${owner}`, region: given.region ?? [], brief: given.brief ?? '', steps_in_order: given.steps_in_order ?? [], triangle_budget: given.triangle_budget })
  }
  for (const wanted of Array.isArray(ARGS.parts) ? ARGS.parts : []) {
    const owner = safeWord(wanted.owner || wanted.name)
    if (owner && !seen.has(owner)) {
      log(`The planner left out the part the person asked for (${owner}): added with the brief as given.`)
      seen.add(owner)
      parts.push({ name: wanted.name || owner, owner, collection: `Place: ${owner}`, region: [], brief: wanted.brief ?? '', steps_in_order: [], triangle_budget: undefined })
    }
  }
  let groundOwner = safeWord(raw.ground_owner)
  if (!seen.has(groundOwner)) {
    log(`The plan names no usable ground part (${raw.ground_owner}): the first part, ${parts[0]?.owner}, is built first as the ground.`)
    groundOwner = parts[0]?.owner
  }
  const givenViews = Array.isArray(ARGS.views) && ARGS.views.length ? ARGS.views : (raw.views ?? [])
  const views = (givenViews.length ? givenViews : [{ name: 'wide' }, { name: 'road_close' }, { name: 'detail_close' }]).map((view, index) => {
    const name = safeWord(view.name) || `view_${index + 1}`
    return { name, camera: view.camera || `View ${name}`, size: Array.isArray(view.size) && view.size.length === 2 ? view.size : [1200, 800] }
  })
  const named = raw.files ?? {}
  const files = {
    style_note: named.style_note || `${DIR.plan}/style-note.md`, facts: named.facts || `${DIR.plan}/real-world-facts.json`,
    settings: named.settings || `${DIR.plan}/place-settings.json`, ownership: named.ownership || `${DIR.plan}/ownership.json`,
    acceptance: named.acceptance || `${DIR.plan}/acceptance.json`,
  }
  const features = (raw.readable_features ?? []).filter((feature) => feature && feature.name).map((feature) => ({
    name: feature.name, keywords: (feature.keywords?.length ? feature.keywords : String(feature.name).split(/\s+/)).map((word) => String(word).toLowerCase()),
  }))
  return {
    place: raw.place || ARGS.place || 'the place', place_type: raw.place_type || 'generic', files, ground_owner: groundOwner,
    look: raw.look, state: raw.state, parts, contracts: raw.contracts ?? [], frozen: raw.frozen ?? [], views,
    readable_features: features, renderer_hint: raw.renderer_hint ?? '', open_questions: raw.open_questions ?? [], notes: raw.notes ?? '',
  }
}

// ----------------------------------------------------------------------------------- audit gate and problem routing
const combineClean = (combine) => !!combine && combine.order_plain_ok !== false && combine.order_reverse_ok !== false && combine.idempotent !== false && (combine.violations ?? []).length === 0
// the verdict of the audit helper counts only when the preflight's own exit code agrees (a helper's words are a claim, an exit code is a fact)
const gateOk = (combine, audit) => !!audit && audit.verdict === 'pass' && audit.preflight_exit_code === 0 && combineClean(combine)

function collectProblems(combine, audit) {
  const found = []
  for (const text of combine?.violations ?? []) found.push({ check: 'ownership', where: 'combine', owner: ownerFromText(text), text, fix: 'each owner changes only its own objects' })
  if (combine && combine.order_plain_ok === false) found.push({ check: 'combine', where: 'plain order', owner: 'integrator', text: 'the stages could not be combined in plain order', fix: 'read the combine report; the stage that fails goes back to its owner' })
  if (combine && combine.order_reverse_ok === false) found.push({ check: 'combine', where: 'reverse order', owner: 'integrator', text: 'the reverse order gives a different or broken scene: a stage depends on the order', fix: 'the stage that depends on another stage goes back to its owner' })
  if (combine && combine.idempotent === false) found.push({ check: 'combine', where: 'run twice', owner: 'integrator', text: 'running the stages twice does not give the same scene: a stage is not idempotent', fix: 'the stage must first remove what it made earlier' })
  if (audit && audit.verdict === 'pass' && audit.preflight_exit_code !== 0) found.push({ check: 'audit', where: 'the audit helper', owner: 'integrator', text: `the helper said the audit passed, but the preflight's exit code was ${audit.preflight_exit_code}`, fix: 'run the preflight stage place again and read its lines' })
  for (const problem of audit?.problems ?? []) found.push({ ...problem, owner: knownOwner(problem.owner) })
  for (const problem of combine?.audit_problems ?? []) if (!audit) found.push({ ...problem, owner: knownOwner(problem.owner) })
  return found
}

const groupByOwner = (problems) => {
  const groups = new Map()
  for (const problem of problems) {
    const owner = problem.owner || 'integrator'
    if (!groups.has(owner)) groups.set(owner, [])
    groups.get(owner).push(problem)
  }
  return groups
}

async function runAudit(version, label) {
  const result = await agent(auditPrompt(version), { label, phase: 'Audit', schema: AUDIT_REPORT, effort: EFFORT })
  if (result) return result
  return { scene_file: finishedFile(version), audit_file: auditFile(version), audit_exit_code: 2, preflight_exit_code: 2, verdict: 'fail', quick: false,
    problems: [{ check: 'audit', where: 'the audit did not run', owner: 'integrator', text: 'the helper that proves the file returned nothing', fix: 'run the audit again' }], looks: [], known: [], notes: ['no answer came back'] }
}

// --------------------------------------------------------------------------------------------------------- reading test
function readingTest(round, seen, blind) {
  const text = (seen ?? []).join('\n').toLowerCase()
  const rows = STATE.plan.readable_features.map((feature) => {
    const hit = (feature.keywords ?? []).find((word) => word && new RegExp('\\b' + escapeRegExp(word)).test(text))
    return { feature: feature.name, found: !!hit, by: hit ?? null }
  })
  const found = rows.filter((row) => row.found).length
  const planned = rows.length
  return {
    round, planned, found, share: planned ? Math.round((found / planned) * 1000) / 1000 : 0, line: READING_LINE,
    passed: planned > 0 && found / planned >= READING_LINE, missed: rows.filter((row) => !row.found).map((row) => row.feature), rows,
    was_blind: blind, how: 'keyword match on a blind reader\'s own words (judged, crude)',
  }
}

// a blind reader is only blind when its prompt shares no word with the feature list (the plain words viewers would say, and the words of the names)
const STOP_WORDS = ['the', 'and', 'with', 'for', 'from', 'that', 'this', 'above', 'between', 'into', 'its', 'are', 'was', 'not', 'any']
function leakedWords(prompt) {
  const text = prompt.toLowerCase()
  const words = STATE.plan.readable_features.flatMap((feature) => (feature.keywords ?? []).concat(String(feature.name).toLowerCase().split(/[^a-z]+/)))
  return unique(words.filter((word) => word && word.length > 2 && !STOP_WORDS.includes(word) && new RegExp('\\b' + escapeRegExp(word) + '\\b').test(text)))
}

// ------------------------------------------------------------------------------------------------- the fresh-check object
const WORSE = { yes: 0, 'not judged': 0, nearly: 1, no: 2 }
function worstVerdict(results, key) {
  let worst = 'not judged'
  let rank = -1
  for (const result of results) {
    const verdict = result[key] ?? 'not judged'
    if (verdict !== 'not judged' && WORSE[verdict] >= rank) { worst = verdict; rank = WORSE[verdict] }
  }
  return worst
}

function composeFresh() {
  if (STATE.recheck) return STATE.recheck
  const results = ['look', 'structure'].map((key) => STATE.checks[key]).filter(Boolean)
  if (!results.length) return null
  return {
    mode: 'look and structure', was_blind: results.every((result) => result.was_blind === true),
    art_style_kept: worstVerdict(results, 'art_style_kept'), lived_in: worstVerdict(results, 'lived_in'), construction_makes_sense: worstVerdict(results, 'construction_makes_sense'),
    each_element: results.flatMap((result) => result.each_element), claims_checked: results.flatMap((result) => result.claims_checked),
    problems: STATE.confirmed.map((finding) => ({ what: finding.what, where: finding.where, severity: finding.severity, cheapest_fix: finding.cheapest_fix, owner: finding.owner })),
    should_fix_now: results.map((result) => result.should_fix_now).filter(Boolean).join(' '), not_tested: unique(results.flatMap((result) => result.not_tested)), measures: {},
    audit_scene_sha1: (results.find((result) => result.audit_scene_sha1) ?? {}).audit_scene_sha1,
  }
}

// ------------------------------------------------------------------------------------------------------ card time as the helpers reported it
// every helper reports the card seconds it used (read from the ledger, which the tools write); the process checker compares them with the ledger itself
function noteCard(name, role, report) {
  if (!report || (report.card_seconds === undefined && report.batches === undefined)) return
  STATE.cardRows.push({ name, role, card_seconds: Number(report.card_seconds ?? 0), batches: Number(report.batches ?? 0) })
}

function cardTimeSummary() {
  const byName = new Map()
  for (const row of STATE.cardRows) {
    const known = byName.get(row.name) ?? { name: row.name, role: row.role, card_seconds: 0, batches: 0 }
    // a helper that reports twice (a ledger total each time) is counted once, at its largest total; batches add up
    known.card_seconds = Math.max(known.card_seconds, row.card_seconds)
    known.batches += row.batches
    byName.set(row.name, known)
  }
  const reported = [...byName.values()]
  return {
    ledger: CARD_LEDGER, team_minutes: CARD_TEAM_MINUTES, allowance_minutes: CARD_MINUTES, reported,
    reported_card_seconds: Math.round(reported.reduce((sum, row) => sum + row.card_seconds, 0) * 10) / 10,
    over_allowance: reported.filter((row) => row.card_seconds > (CARD_MINUTES[row.role] ?? 0) * 60).map((row) => row.name),
  }
}

// ------------------------------------------------------------------------------------------------------------ the report
function reportMarkdown() {
  const plan = STATE.plan
  const report = []
  const say = (...lines) => report.push(...lines)
  const yesNo = (value) => (value === true ? 'yes' : value === false ? 'no' : 'not said')
  const failedClaims = (check) => check.claims_checked.filter((claim) => claim.holds === false)
  say(`# ${placeName()}: what was built and what was checked`, '', `The request, as it was given: "${ARGS.request}"`, '')
  if (STATE.stopped) say(`**The run stopped early: ${STATE.stopped}**`, '')
  say('## What I did')
  if (plan) {
    say(`- Planned ${plan.parts.length} part(s): ${plan.parts.map((part) => `${part.name} (owner ${part.owner})`).join('; ')}. The ground part, ${plan.ground_owner}, was built first and frozen.`)
    say(`- Look chosen: ${plan.look ?? 'from the settings'}; state: ${plan.state ?? 'from the settings'}. ${REFERENCES.length ? 'The style rule was measured from the reference pictures.' : 'There were no reference pictures, so the style note and the style guard are PROVISIONAL.'}`)
    if (plan.open_questions.length) say(`- The planner could not settle these (facts from memory stay marked guess until a source confirms them): ${plan.open_questions.join('; ')}.`)
  }
  if (STATE.ground) say(`- Ground: built (${STATE.ground.ground_file}); it promises: ${STATE.ground.ground_promise}. Steps finished: ${STATE.ground.steps_finished}.`)
  if (STATE.built.length) {
    const reported = STATE.built.filter((entry) => entry.report)
    say(`- Parts that reported: ${reported.map((entry) => `${entry.part.owner} (steps finished: ${entry.report.steps_finished}; own pass done: ${yesNo(entry.report.surface_pass_done)}; own wear preview looked at: ${yesNo(entry.report.wear_preview_done)})`).join('; ') || 'none'}.`)
  }
  if (STATE.missing.length) say(`- **MISSING parts (no report came back, so they were NOT combined): ${STATE.missing.join(', ')}.**`)
  if (STATE.combine) {
    say(`- Combined in plain order: ${yesNo(STATE.combine.order_plain_ok)}; in reverse order: ${yesNo(STATE.combine.order_reverse_ok)}; running the stages twice gives the same scene: ${yesNo(STATE.combine.idempotent)}. Ownership violations: ${STATE.combine.violations.length ? STATE.combine.violations.join('; ') : 'none'}.`)
    if (STATE.combine.repairs_made.length) say(`- Repairs the integrator made (settings, role tags and dials only): ${STATE.combine.repairs_made.join('; ')}.`)
  }
  say('', '## The audit (measured by tools on the exact saved file)')
  if (STATE.audit) {
    say(`- Verdict: **${STATE.audit.verdict.toUpperCase()}** after ${STATE.repairs.length} repair round(s) before any picture (at most ${MAX_REPAIRS}). Scene file: ${STATE.audit.scene_file}${STATE.audit.scene_sha256 ? ` (SHA-256 ${STATE.audit.scene_sha256})` : ''}. Made from a quick run: ${yesNo(STATE.audit.quick)}.`)
    for (const problem of STATE.audit.problems) say(`- FAIL ${problem.check} [${problem.where}] (owner ${problem.owner}): ${problem.text}. Fix: ${problem.fix}`)
    for (const line of STATE.audit.looks) say(`- LOOK ${line}`)
    for (const line of STATE.audit.known) say(`- KNOWN (switched off on purpose or accepted by the person) ${line}`)
    for (const repair of STATE.repairs) say(`- Repair round ${repair.round}: owners asked: ${repair.owners.join(', ') || 'only settings'}; problems routed: ${repair.problems}; reports back: ${repair.reported}.`)
  } else say('- No audit was run.')
  say('', '## Pictures')
  const render = STATE.render
  if (render) {
    say(`- Renderer: ${render.renderer} (${render.why}). Drawn ${render.where === 'rented' ? 'on the rented card' : 'on this computer'}; device: ${render.device}. Balance checked: ${yesNo(render.balance_checked)}. Stalled: ${yesNo(render.stalled)}.`)
    say(`- ${render.pictures.length} picture(s), ${render.seconds_total} seconds in all (measured by the logs next to the pictures). The cost is an ESTIMATE: about US$${render.estimated_dollars} from seconds and the hourly price; a real bill was once about 2.5 times the work seconds and was never explained.`)
    say(`- Style guard: ${render.guard_made_from}${render.guard_provisional ? ' (PROVISIONAL: it locks in whatever the first picture was)' : ''}. Picture measures: ${JSON.stringify(render.measures)}.`)
    for (const note of render.notes) say(`- Renderer note: ${note}`)
    if (STATE.fixRender) say(`- After the fix round ${STATE.fixRender.pictures.length} picture(s) were drawn again (${STATE.fixRender.seconds_total} seconds; an estimate of about US$${STATE.fixRender.estimated_dollars}). The renderer's own words: ${STATE.fixRender.why}.`)
    for (const failure of render.failures ?? []) say(`- Renderer failure: ${failure}`)
  } else say('- No pictures were drawn.')
  say('', '## Card time (the rented cards)')
  const card = cardTimeSummary()
  if (card.reported.length) {
    for (const row of card.reported) say(`- ${row.name} (${row.role}): ${row.card_seconds} card seconds of ${(CARD_MINUTES[row.role] ?? 0) * 60} allowed; ${row.batches} batch(es).${card.over_allowance.includes(row.name) ? ' **OVER ITS ALLOWANCE.**' : ''}`)
    say(`- In all the helpers reported ${card.reported_card_seconds} card seconds${CARD_TEAM_MINUTES ? ` (the person's total for the run: ${CARD_TEAM_MINUTES} minutes)` : ''}. Card seconds are work + wake-up + the idle tail, read from the card-time ledger (${card.ledger}); a price made from them is an ESTIMATE, never a bill. The process checker compared these figures with the ledger: see its findings above.`)
  } else say(`- No helper reported any card seconds (the ledger is ${card.ledger}). Either the card was not used, or a helper did not say so: read the ledger with explainer-film-place card-time show.`)
  if (STATE.finalsRender) say(`- Full-size pictures, drawn once at the very end: ${STATE.finalsRender.pictures.length} picture(s), ${STATE.finalsRender.seconds_total} seconds (an estimate of about US$${STATE.finalsRender.estimated_dollars}).`)
  else if (FINALS) say('- Full-size pictures were asked for but not drawn (see the failures).')
  say('', '## What the fresh checkers found (judged, with the numbers they recomputed)')
  for (const key of ['look', 'structure', 'process']) {
    const check = STATE.checks[key]
    if (!check) { say(`- ${key} checker: no result came back or it did not run.`); continue }
    say(`- ${key} checker (blind to the feature list: ${yesNo(check.was_blind)}): art style kept: ${check.art_style_kept}; lived in: ${check.lived_in}; construction makes sense: ${check.construction_makes_sense}. ${failedClaims(check).length} of ${check.claims_checked.length} claim(s) did NOT hold. ${check.problems.length} problem(s) listed.`)
    for (const claim of failedClaims(check)) say(`  - A builder's claim that did not hold: "${bareClaim(claim.claim)}" (evidence: ${claim.evidence})`)
  }
  for (const test of STATE.readingTests) {
    say(`- Reading test, round ${test.round}: a blind reader (blind: ${yesNo(test.was_blind)}) named ${test.found} of ${test.planned} planned features (${Math.round(test.share * 100)} percent; the line is ${Math.round(test.line * 100)} percent): ${test.passed ? 'PASSED' : 'MISSED'}. Not named: ${test.missed.join(', ') || 'none'}. This is a keyword match on free words: judged and crude.`)
  }
  if (STATE.skeptic) say(`- Skeptic: ${STATE.confirmed.length} finding(s) confirmed, ${STATE.skeptic.rejected.length} rejected. ${STATE.skeptic.summary}`)
  for (const finding of STATE.confirmed) say(`  - ${finding.severity.toUpperCase()}: ${finding.what} (where: ${finding.where}; owner: ${finding.owner}). Cheapest fix: ${finding.cheapest_fix}`)
  for (const finding of STATE.unverified) say(`  - NOT CONFIRMED (no skeptic could check it, so nothing was done about it): ${finding.what} (${finding.severity})`)
  for (const item of STATE.notFixedOnPurpose) say(`- NOT FIXED ON PURPOSE (the person decides): ${item.what}. ${item.why}`)
  say('', '## The fix round (exactly one)')
  if (STATE.fixes.length || STATE.fixOwners.length) {
    say(`- Owners asked to fix confirmed findings: ${STATE.fixOwners.join(', ') || 'only settings (the integrator)'}. Reports back: ${STATE.fixes.length}.`)
    for (const fix of STATE.fixes) say(`  - ${fix.owner}: steps finished: ${fix.steps_finished}; failures: ${fix.failures.join('; ') || 'none'}; not tested: ${fix.not_tested.join('; ') || 'nothing said'}.`)
    if (STATE.fixAudit) say(`- Audit after the fixes: **${STATE.fixAudit.verdict.toUpperCase()}** (${STATE.fixAudit.problems.length} problem(s)).`)
    if (STATE.recheck) say(`- Re-check by a different fresh checker: art style kept: ${STATE.recheck.art_style_kept}; lived in: ${STATE.recheck.lived_in}; construction: ${STATE.recheck.construction_makes_sense}; ${failedClaims(STATE.recheck).length} finding(s) or claim(s) still not holding; ${STATE.recheck.problems.length} problem(s) left or new.`)
    for (const problem of STATE.recheck?.problems ?? []) say(`  - ${problem.severity.toUpperCase()}: ${problem.what} (where: ${problem.where}; owner: ${problem.owner})`)
  } else say('- Nothing was fixed (nothing was confirmed that needed it, or pictures were missing).')
  if (STATE.finalGate) {
    say('', '## The final gate (the preflight stage place on the final saved file)')
    say(`- Verdict: **${STATE.finalGate.verdict.toUpperCase()}** (exit ${STATE.finalGate.preflight_exit_code}); the audit is stale: ${yesNo(STATE.finalGate.stale)}.`)
    for (const line of STATE.finalGate.lines) say(`  - ${line}`)
  }
  say('', '## Measured and judged')
  say('- MEASURED by tools: every audit line, the construction and normal-map checks, the picture measures, the seconds of each picture, the combine check.')
  say('- JUDGED: how the place looks (checkers and the reading test), the sizes from memory (marked weak or guess in the facts table), the style guard when it came from the first picture, the cost estimate.')
  say('- Fresh checkers are helpers of the same kind as the builders and can share blind spots; the person\'s own eyes decide the look.')
  say('', '## What was not tested')
  const notTested = unique([
    ...STATE.built.flatMap((entry) => entry.report?.not_tested ?? []), ...(STATE.ground?.not_tested ?? []), ...(STATE.combine?.not_tested ?? []),
    ...Object.values(STATE.checks).flatMap((check) => check?.not_tested ?? []), ...(STATE.recheck?.not_tested ?? []),
  ])
  say(...(notTested.length ? notTested.map((line) => `- ${line}`) : ['- Nothing was reported as untested (check that this is believable).']))
  say('- Not tested by this workflow at all: the place seen by the person, a blind reader who was never given any hint (the reading test was only ever run this way here), and the lighter plan masks and the Cycles runs of the kit on a scene much bigger than the small test places unless a log above says otherwise.')
  say('', '## Every failure and everything that came back empty')
  const failures = unique([
    ...STATE.missing.map((owner) => `part ${owner}: no report came back`),
    ...(STATE.ground?.failures ?? []), ...STATE.built.flatMap((entry) => entry.report?.failures ?? []), ...(STATE.combine?.failures ?? []),
    ...(STATE.render?.failures ?? []), ...STATE.fixes.flatMap((fix) => fix.failures ?? []), ...(STATE.fixRender?.failures ?? []), ...STATE.notes,
  ])
  say(...(failures.length ? failures.map((line) => `- ${line}`) : ['- None were reported.']))
  say('', '## For you to decide')
  const decide = []
  if (STATE.render?.guard_provisional) decide.push('The style guard came from the first picture. If the first picture was bland, so is the guard: judge the pictures yourself or give a reference picture.')
  if (STATE.notFixedOnPurpose.length) decide.push('Findings that were not fixed on purpose (a squint-test miss, or a cure that would remove character) are listed above.')
  if (STATE.readingTests.some((test) => !test.passed)) decide.push('The reading test missed its line: some planned features do not read at half size.')
  if (STATE.audit && STATE.audit.verdict === 'fail') decide.push('The audit still fails; nothing was drawn. Read the FAIL lines above. Only you can accept a problem, in writing, with your name and the date.')
  if (STATE.audit?.known?.length) decide.push('Some treatments were switched off on purpose (KNOWN above): check the reasons are true.')
  say(...(decide.length ? decide.map((line) => `- ${line}`) : ['- Nothing is waiting for you except looking at the pictures.']))
  return report.join('\n')
}

function done(stopped) {
  if (stopped) STATE.stopped = stopped
  const reading = STATE.readingTests.length ? STATE.readingTests[STATE.readingTests.length - 1] : null
  return {
    plan: STATE.plan, ground: STATE.ground, parts: [...(STATE.ground ? [STATE.ground] : []), ...STATE.built.filter((entry) => entry.report).map((entry) => entry.report)], missing_parts: STATE.missing,
    combine: STATE.combine, audit: STATE.audit, repairs: STATE.repairs, render: STATE.render, final_render: STATE.finalsRender, card_time: cardTimeSummary(),
    checks: { look: STATE.checks.look ?? null, structure: STATE.checks.structure ?? null, process: STATE.checks.process ?? null, blind_reader: STATE.checks.blind ?? null, skeptic: STATE.skeptic },
    confirmed: STATE.confirmed, fixes: STATE.fixes,
    recheck: STATE.recheck ? { check: STATE.recheck, blind_reader: STATE.recheckBlind, audit_after_fix: STATE.fixAudit, render_after_fix: STATE.fixRender } : null,
    reading_test: reading, fresh_check: STATE.freshCheck, final_gate: STATE.finalGate, stopped: STATE.stopped, report_markdown: reportMarkdown(),
  }
}

// ======================================================================================================== the run
// ---- Plan
phase('Plan')
const rawPlan = await agent(planPrompt(), { label: 'plan', phase: 'Plan', schema: PLAN, effort: PLAN_EFFORT })
if (!rawPlan || !(rawPlan.parts ?? []).length) {
  return done('the planner came back with no plan (or a plan with no parts), so nothing was built')
}
STATE.plan = normalisePlan(rawPlan)
if (STATE.plan.parts.length < 3 || STATE.plan.parts.length > 8) log(`The plan has ${STATE.plan.parts.length} part(s); 3 to 8 is usual. Going on with it.`)
if (!STATE.plan.readable_features.length) STATE.notes.push('The planner named no readable features, so the reading test could not be made.')
log(`Plan: ${STATE.plan.parts.map((part) => part.owner).join(', ')}; the ground part is ${STATE.plan.ground_owner}; ${STATE.plan.readable_features.length} readable feature(s); ${STATE.plan.views.length} view(s).`)

// ---- Ground (serial: everything else is seated on it)
phase('Ground')
const groundPart = partOf(STATE.plan.ground_owner)
STATE.ground = await agent(builderPrompt(groundPart, 'ground'), { label: `ground:${groundPart.owner}`, phase: 'Ground', schema: GROUND_REPORT, effort: EFFORT })
if (!STATE.ground || !STATE.ground.ground_file) {
  return done('the ground part came back with no ground file, so nothing can be seated on it')
}
noteCard(`builder-${groundPart.owner}`, 'builder', STATE.ground)
log(`Ground frozen: ${STATE.ground.ground_file}`)

// ---- Build parts (side by side, at most CAP at a time; the rest wait in a queue)
phase('Build parts')
const others = STATE.plan.parts.filter((part) => part.owner !== STATE.plan.ground_owner)
if (others.length > CAP) log(`${others.length} parts and room for ${CAP} builders at once: the rest wait in a queue, none is skipped.`)
const reports = await runQueued(others, CAP, (part) => agent(builderPrompt(part, 'build'), { label: `build:${part.owner}`, phase: 'Build parts', schema: PART_REPORT, effort: EFFORT }))
STATE.built = others.map((part, index) => ({ part, report: reports[index] }))
others.forEach((part, index) => noteCard(`builder-${part.owner}`, 'builder', reports[index]))
STATE.missing = STATE.built.filter((entry) => !entry.report).map((entry) => entry.part.owner)
if (STATE.missing.length) log(`No report from: ${STATE.missing.join(', ')}. They are reported as missing and not combined.`)
if (others.length && STATE.built.every((entry) => !entry.report)) {
  return done('no builder came back with a report, so there is nothing to combine with the ground')
}

// ---- Combine
phase('Combine')
STATE.version = 1
STATE.combine = await agent(combinePrompt(STATE.version, [], false), { label: 'combine', phase: 'Combine', schema: COMBINE_REPORT, effort: EFFORT })
if (!STATE.combine) {
  return done('the integrator came back with nothing, so there is no combined scene to audit')
}
noteCard('integrator', 'integrator', STATE.combine)
log(`Combined: plain ${STATE.combine.order_plain_ok}, reverse ${STATE.combine.order_reverse_ok}, idempotent ${STATE.combine.idempotent}, ${STATE.combine.violations.length} violation(s).`)

// ---- Audit: nothing is drawn until it passes; at most MAX_REPAIRS repair rounds, routed to the owners the audit names
phase('Audit')
STATE.audit = await runAudit(STATE.version, 'audit')
STATE.auditRounds.push(STATE.audit)
let repairRound = 0
while (!gateOk(STATE.combine, STATE.audit) && repairRound < MAX_REPAIRS) {
  repairRound++
  const problems = collectProblems(STATE.combine, STATE.audit)
  const byOwner = groupByOwner(problems)
  const asked = [...byOwner.keys()].filter((owner) => owner !== 'integrator' && partOf(owner))
  const owners = asked.filter((owner) => !STATE.missing.includes(owner))
  if (asked.length > owners.length) STATE.notes.push(`Repair round ${repairRound}: ${asked.filter((owner) => STATE.missing.includes(owner)).join(', ')} never reported, so its problems could not be sent to a builder.`)
  const settingsRepairs = byOwner.get('integrator') ?? []
  log(`Audit round ${repairRound}: ${problems.length} problem(s); asking ${owners.join(', ') || 'only the integrator (settings)'} to repair them.`)
  const fixed = await runQueued(owners, CAP, (owner) => agent(builderPrompt(partOf(owner), 'fix', byOwner.get(owner), `repair before any picture, round ${repairRound}`), { label: `repair${repairRound}:${owner}`, phase: 'Audit', schema: PART_REPORT, effort: EFFORT }))
  const stillMissing = owners.filter((owner, index) => !fixed[index])
  if (stillMissing.length) STATE.notes.push(`Repair round ${repairRound}: no report from ${stillMissing.join(', ')}.`)
  fixed.forEach((report, index) => {
    if (!report) return
    noteCard(`fixer-${owners[index]}`, 'fixer', report)
    if (owners[index] === STATE.plan.ground_owner) STATE.ground = { ...STATE.ground, ...report }
    const built = STATE.built.find((entry) => entry.part.owner === owners[index])
    if (built) built.report = { ...built.report, ...report }
  })
  STATE.repairs.push({ round: repairRound, owners, problems: problems.length, reported: fixed.filter(Boolean).length, summary: problems.slice(0, 5).map((problem) => `${problem.check}: ${problem.text}`) })
  STATE.version += 1
  STATE.combine = await agent(combinePrompt(STATE.version, settingsRepairs, owners.includes(STATE.plan.ground_owner)), { label: `recombine${repairRound}`, phase: 'Audit', schema: COMBINE_REPORT, effort: EFFORT })
  if (!STATE.combine) {
    return done(`the integrator came back with nothing in repair round ${repairRound}, so there is no scene to audit`)
  }
  noteCard('integrator', 'integrator', STATE.combine)
  STATE.audit = await runAudit(STATE.version, `audit${repairRound}`)
  STATE.auditRounds.push(STATE.audit)
}
if (!gateOk(STATE.combine, STATE.audit)) {
  return done(`the audit still fails after ${repairRound} repair round(s), so no picture was drawn (nothing is drawn unless the audit passes or fails only on items the person accepted in writing)`)
}
STATE.finalFile = STATE.combine.finished_file || finishedFile(STATE.version)
STATE.finalAuditFile = STATE.audit.audit_file || auditFile(STATE.version)
log(`Audit passed on ${STATE.finalFile} after ${repairRound} repair round(s).`)

// ---- Render (the renderer rule decides the engine; only previews unless finals were asked for)
phase('Render')
STATE.render = await agent(renderPrompt('round1', STATE.plan.views, null, STATE.finalFile), { label: 'render', phase: 'Render', schema: RENDER_REPORT, effort: EFFORT })
noteCard('renderer', 'renderer', STATE.render)
if (!STATE.render) {
  STATE.notes.push('The renderer came back with nothing: no picture was drawn.')
} else if (STATE.render.stalled) {
  STATE.notes.push('The renderer stopped: jobs waited more than five minutes while workers showed idle. The queue was not purged and the endpoint was not changed. The person should look at the rented card account before another run.')
} else if (!STATE.render.pictures.length) {
  STATE.notes.push('The renderer drew no pictures.')
} else {
  STATE.havePictures = true
  STATE.finalRender = STATE.render
}
if (!STATE.havePictures) log('No pictures: only the structure and process checkers run, and there is no fix round (a fix needs pictures to be checked).')

// ---- Check (fresh checkers; none of them sees a builder report or number)
phase('Check')
const jobs = [{ key: 'structure', run: () => agent(checkerPrompt('structure', structureExtra()), { label: 'check:structure', phase: 'Check', schema: CHECK, effort: CHECK_EFFORT }) },
  { key: 'process', run: () => agent(checkerPrompt('process', processExtra()), { label: 'check:process', phase: 'Check', schema: CHECK, effort: CHECK_EFFORT }) }]
if (STATE.havePictures) {
  jobs.unshift({ key: 'look', run: () => agent(checkerPrompt('look', lookExtra()), { label: 'check:look', phase: 'Check', schema: CHECK, effort: CHECK_EFFORT }) })
  jobs.push({ key: 'blind', run: () => agent(blindPrompt(STATE.render, 1), { label: 'blind:1', phase: 'Check', schema: BLIND, effort: CHECK_EFFORT }) })
}
const checkResults = await parallel(jobs.map((job) => job.run))
jobs.forEach((job, index) => { if (checkResults[index]) STATE.checks[job.key] = checkResults[index]; else STATE.notes.push(`The ${job.key} checker came back with nothing.`) })

if (STATE.checks.blind && STATE.plan.readable_features.length) {
  const leaks = leakedWords(blindPrompt(STATE.render, 1))
  if (leaks.length) log(`The blind reader's prompt shares words with the feature list (${leaks.join(', ')}): it is reported as not blind.`)
  STATE.readingTests.push(readingTest(1, STATE.checks.blind.seen, leaks.length === 0))
  const test = STATE.readingTests[0]
  log(`Reading test: ${test.found} of ${test.planned} planned features named (${test.passed ? 'passed' : 'missed'}).`)
}

const findings = []
for (const key of ['look', 'structure', 'process']) {
  const check = STATE.checks[key]
  if (!check) continue
  for (const problem of check.problems) findings.push({ from: `${key} checker`, ...problem, owner: knownOwner(problem.owner) })
  for (const claim of check.claims_checked) if (claim.holds === false) findings.push({ from: `${key} checker: a builder's claim did not hold`, what: `claim: ${bareClaim(claim.claim)}`, where: 'the claim', severity: 'must fix', cheapest_fix: 'correct the scene or the claim', owner: claimOwner(claim.claim), evidence: claim.evidence })
}
if (findings.length) {
  STATE.skeptic = await agent(skepticPrompt(findings), { label: 'skeptic', phase: 'Check', schema: SKEPTIC, effort: CHECK_EFFORT })
  if (STATE.skeptic) {
    // a squint-test miss whose cure is to take character away is never fixed here, even when a skeptic confirmed it: the person decides
    const takesCharacterAway = (finding) => /squint/i.test(finding.what) && /\b(remove|delete|cut|reduce|fewer|less|simplif|flatten|blur|tone down)/i.test(finding.cheapest_fix)
    const confirmed = STATE.skeptic.confirmed.map((finding) => ({ ...finding, owner: knownOwner(finding.owner) }))
    STATE.confirmed = confirmed.filter((finding) => !takesCharacterAway(finding))
    STATE.notFixedOnPurpose = [...STATE.skeptic.not_fixed_on_purpose, ...confirmed.filter(takesCharacterAway).map((finding) => ({ what: finding.what, why: 'a squint-test miss is reported to the person and never fixed by removing character; the cheapest fix offered was: ' + finding.cheapest_fix }))]
  } else {
    STATE.unverified = findings
    STATE.notes.push(`The skeptic came back with nothing: ${findings.length} finding(s) stay unverified and none was acted on.`)
  }
}
log(`${findings.length} finding(s) from the checkers; ${STATE.confirmed.length} confirmed.`)

// ---- Fix (exactly one round, only confirmed findings that need it, only when pictures can check the result)
phase('Fix')
const toFix = STATE.confirmed.filter((finding) => SEVERE.includes(finding.severity))
let fixDone = false
let fixFile = null
if (!toFix.length) {
  log('Nothing confirmed needs fixing: no fix round.')
} else if (!STATE.havePictures) {
  log('Findings need fixing, but there are no pictures to check a fix with: no fix round. The findings are in the report.')
} else {
  const byOwner = groupByOwner(toFix)
  const owners = [...byOwner.keys()].filter((owner) => owner !== 'integrator' && partOf(owner))
  const settingsRepairs = (byOwner.get('integrator') ?? []).map((finding) => ({ text: finding.what, where: finding.where, fix: finding.cheapest_fix }))
  STATE.fixOwners = owners
  log(`Fix round (the only one): ${owners.length} owner(s) (${owners.join(', ') || 'settings only'}), ${toFix.length} finding(s).`)
  const fixed = await runQueued(owners, CAP, (owner) => agent(builderPrompt(partOf(owner), 'fix', byOwner.get(owner), 'the one fix round after the checkers'), { label: `fix:${owner}`, phase: 'Fix', schema: PART_REPORT, effort: EFFORT }))
  STATE.fixes = fixed.filter(Boolean)
  fixed.forEach((report, index) => noteCard(`fixer-${owners[index]}`, 'fixer', report))
  owners.forEach((owner, index) => { if (!fixed[index]) STATE.notes.push(`Fix round: no report from ${owner}.`) })
  STATE.version += 1
  STATE.fixCombine = await agent(combinePrompt(STATE.version, settingsRepairs, owners.includes(STATE.plan.ground_owner)), { label: 'combine:fix', phase: 'Fix', schema: COMBINE_REPORT, effort: EFFORT })
  if (STATE.fixCombine) {
    noteCard('integrator', 'integrator', STATE.fixCombine)
    STATE.fixAudit = await runAudit(STATE.version, 'audit:fix')
    if (gateOk(STATE.fixCombine, STATE.fixAudit)) {
      fixDone = true
    } else {
      STATE.notes.push('After the fix round the audit does not pass, so nothing was drawn again and the first audited file stays the final one. The stage files have changed since that file was made.')
    }
  } else {
    STATE.notes.push('After the fix round the integrator came back with nothing: nothing was combined or drawn again.')
  }
  if (fixDone) {
    const named = unique(STATE.fixes.flatMap((fix) => fix.views_to_redraw ?? []).map(safeWord))
    const wanted = STATE.plan.views.filter((view) => named.includes(view.name))
    const redraw = wanted.length ? wanted : STATE.plan.views
    if (!wanted.length) log('The fixers did not name the views that changed: all views are drawn again.')
    const previous = picturePaths(STATE.render, false)
    fixFile = STATE.fixCombine.finished_file || finishedFile(STATE.version)
    STATE.fixRender = await agent(renderPrompt('round2', redraw, previous, fixFile), { label: 'render:fix', phase: 'Fix', schema: RENDER_REPORT, effort: EFFORT })
    noteCard('renderer', 'renderer', STATE.fixRender)
    if (!STATE.fixRender || STATE.fixRender.stalled || !STATE.fixRender.pictures.length) {
      STATE.notes.push(`The pictures after the fix round could not be drawn (nothing came back, or the card stalled). The fixed scene ${fixFile} passed its audit but nobody has looked at it, so the first audited scene stays the final one.`)
      fixDone = false
    }
  }
}

// ---- Re-check (a different fresh checker and a second blind reader look at the changed place)
phase('Re-check')
if (fixDone) {
  // the new picture set: the redrawn views, and the earlier pictures of the views that were not drawn again
  const redrawnViews = STATE.fixRender.pictures.map((picture) => picture.view)
  const mixed = { ...STATE.fixRender, pictures: [...STATE.render.pictures.filter((picture) => !redrawnViews.includes(picture.view)), ...STATE.fixRender.pictures], guard_file: STATE.render.guard_file, guard_provisional: STATE.render.guard_provisional }
  STATE.finalFile = fixFile
  STATE.finalAuditFile = STATE.fixAudit.audit_file || auditFile(STATE.version)
  STATE.finalRender = mixed
  const results = await parallel([
    () => agent(checkerPrompt('recheck', recheckExtra(STATE.render), mixed), { label: 'recheck', phase: 'Re-check', schema: CHECK, effort: CHECK_EFFORT }),
    () => agent(blindPrompt(mixed, 2), { label: 'blind:2', phase: 'Re-check', schema: BLIND, effort: CHECK_EFFORT }),
  ])
  STATE.recheck = results[0]
  STATE.recheckBlind = results[1]
  if (!STATE.recheck) STATE.notes.push('The re-check came back with nothing.')
  if (STATE.recheckBlind && STATE.plan.readable_features.length) {
    const leaks = leakedWords(blindPrompt(mixed, 2))
    STATE.readingTests.push(readingTest(2, STATE.recheckBlind.seen, leaks.length === 0))
    const test = STATE.readingTests[STATE.readingTests.length - 1]
    log(`Reading test after the fix: ${test.found} of ${test.planned} (${test.passed ? 'passed' : 'missed'}).`)
  } else if (!STATE.recheckBlind) STATE.notes.push('The second blind reader came back with nothing.')
} else {
  log('No re-check: there was no fix round with new pictures.')
}

// ---- Report (the final gate on the saved file, then the plain-words report)
phase('Report')
// the full-size pictures: drawn ONCE, at the very end, from the last audited file, and only when the person asked for them
if (FINALS && STATE.havePictures && STATE.finalFile) {
  STATE.finalsRender = await agent(renderPrompt('final', STATE.plan.views, picturePaths(STATE.finalRender, false), STATE.finalFile, true), { label: 'render:final', phase: 'Report', schema: RENDER_REPORT, effort: EFFORT })
  noteCard('renderer', 'renderer', STATE.finalsRender)
  if (!STATE.finalsRender || STATE.finalsRender.stalled || !STATE.finalsRender.pictures.length) {
    STATE.notes.push('The full-size pictures could not be drawn (nothing came back, or the card stalled). The small pictures the checkers looked at stay the only pictures.')
    STATE.finalsRender = null
  }
} else if (FINALS) {
  STATE.notes.push('Full-size pictures were asked for, but there were no pictures to build on (the audit failed or nothing was drawn), so none were drawn.')
}
STATE.freshCheck = composeFresh()
if (STATE.freshCheck && STATE.finalFile) {
  STATE.finalGate = await agent(gatePrompt(STATE.freshCheck), { label: 'gate', phase: 'Report', schema: FINAL_GATE, effort: EFFORT })
  if (!STATE.finalGate) STATE.notes.push('The final gate came back with nothing: the preflight stage place was not run on the final file.')
} else {
  STATE.notes.push('No fresh checker result, so the final gate was not run with one.')
}
return done(null)
