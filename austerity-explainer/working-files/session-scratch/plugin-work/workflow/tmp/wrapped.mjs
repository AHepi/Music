export default async function run(args, agent, parallel, pipeline, phase, log, budget, workflow) {
const meta = {
  name: 'build-a-place',
  description: "Build a place in Blender in parts (a village, town, harbour, mine, farm, garden, interior, a set or props) from the requester's plain words: plan with researched sizes, ground first, parts built side by side, combined, given real surfaces and wear, audited, drawn with the film owner's renderer rule, checked by fresh helpers, fixed once and checked again",
  whenToUse: "When someone asks for a place, set or props to be built in Blender, whatever the words (they need not mention surfaces, wear or realism: this workflow adds the plugin's own steps). Pass the plugin folder, the kit folder, a work folder and the request exactly as the person wrote it; the notes about this computer, the disk and the money come in args.environment.",
  phases: [
    { title: 'Plan', detail: 'one planner: style note, facts with sources, draft settings, ownership, acceptance list, parts, views, readable features' },
    { title: 'Ground', detail: 'the ground part first, alone, then frozen so every other part is seated on it' },
    { title: 'Build parts', detail: 'one builder per part, side by side up to a cap, each running its own share of the pass and its own checks' },
    { title: 'Combine', detail: 'one integrator: both orders, ownership check, the whole surface-and-wear pass' },
    { title: 'Audit', detail: 'the audit and the preflight stage place on the exact file; up to two repair rounds routed to the owners; no picture before it passes' },
    { title: 'Render', detail: 'the renderer rule (Cycles where lit, EEVEE when not), previews, measures, the style guard' },
    { title: 'Check', detail: 'fresh checkers (look, structure, process, a blind reader), then a skeptic merges and ranks' },
    { title: 'Fix', detail: 'exactly one fix round: one fixer per owner, given only the confirmed findings' },
    { title: 'Re-check', detail: 'a different fresh checker and a second blind reader look at the changed place' },
    { title: 'Report', detail: 'the final gate on the saved file, then a plain-words report' },
  ],
}

// What this does: builds a place in Blender from the requester's plain words and adds the plugin's own steps itself, so the
// request never has to mention surfaces or wear: the surface-and-wear pass (normal maps, displacement, dirt, grime, weathering,
// wetness, moss, weeds, rust, cracks, chips, edge wear, rubbish, damage as shape), the construction check, the audit and the
// preflight stage place, picture measures, fresh checkers who never see the builders' reports, and ONE fix round.
// A concrete example: the request "Build a village in the forest. Needs unkept dirt roads like they've been driven down by horse
// and carriage, an empty stable, a few cottages, some scattered mediaeval props." becomes a plan of five parts (roads_and_ground
// first, then cottages, stable, props, forest_edge), five builders, one integrator, one renderer and four checkers.
//
// The rules the script keeps: nothing is drawn unless the audit passed (or failed only on items the person accepted in writing);
// at most two repair rounds before any picture, routed to the owners the audit names; exactly one fix round after the checkers;
// no paid step (only the renderer may use the person's rented card, and only when the notes allow it); no commit; checkers get no
// builder reports or numbers; the blind reader gets no feature list; a part that comes back empty is reported as missing, never
// dropped quietly; a squint-test miss is reported to the person and never "fixed" by removing character.
// The helpers are told to read their own agent file first, because a plugin agent type is not assumed to be available.
//
// args: {
//   plugin: '/path/to/explainer-film'              (required: the plugin folder, which holds agents/, skills/, bin/, kit/)
//   kit: '/path/to/explainer-film/kit'             (required: the folder that holds place-kit/ and calculators/)
//   folder: '/path/to/work/folder'                 (required: plan, scene, stages, reports, pictures and checks go in it)
//   request: 'Build a village in the forest. ...'  (required: the person's words, exactly as written)
//   place: 'village'                               (optional: the person's name for it)
//   scene: '/path/to/start.blend'                  (optional: a scene to start from; otherwise the ground builder makes an empty one)
//   blender: '/path/to/blender'                    (optional: otherwise the commands look for it themselves)
//   parts: [{ name, owner, brief }]                (optional: otherwise the planner proposes 3 to 8)
//   views: [{ name, camera, size: [w, h] }]        (optional: otherwise the planner proposes at least 3)
//   references: ['/path/to/picture.jpg']           (optional: pictures the person gave; the style guard is made from them)
//   accepted: '/path/to/accepted.json'             (optional: problems the person accepted in writing, with who and date)
//   ledger: '/path/to/spend-ledger.json'           (optional: for the process checker)
//   environment: 'notes about this computer, the disk, where to render, the money rules'   (optional text: the notes win)
//   renderer: 'auto' | 'cycles' | 'eevee'          (default auto: the film owner's rule)
//   rented: true | false | 'auto'                  (default auto: may the renderer use the person's rented card?)
//   finals: false                                  (default: previews only)
//   maxParallelBuilders: 4                         (default 4: more parts wait in a queue, none is skipped)
//   maxRepairRounds: 2                             (default 2, never more)
//   effort: 'medium', checkEffort: 'high', planEffort: same as effort
//   today: 'YYYY-MM-DD'                            (so "latest" figures are judged right; the script never reads the clock)
// }
// Returns { plan, ground, parts, missing_parts, combine, audit, repairs, render, checks, confirmed, fixes, recheck, reading_test,
//           fresh_check, final_gate, stopped, report_markdown }. Every key is always there (null when its phase did not run).
const A = args ?? {}

// ---------------------------------------------------------------------------------------------------------------- the start
const NEEDED = { plugin: 'the plugin folder', kit: 'the folder that holds place-kit and calculators', folder: 'the folder where the plan, stages, reports and pictures go', request: "the person's words, exactly as they wrote them" }
const lacking = Object.keys(NEEDED).filter((key) => !A[key])
if (lacking.length) {
  throw new Error('build-a-place cannot start: ' + lacking.map((key) => `args.${key} (${NEEDED[key]})`).join('; ') + (lacking.length > 1 ? ' are' : ' is') + ' missing.')
}

const EFFORT = A.effort ?? 'medium'
const CHECK_EFFORT = A.checkEffort ?? 'high'
const PLAN_EFFORT = A.planEffort ?? EFFORT
const CAP = Math.max(1, Math.floor(Number(A.maxParallelBuilders) || 4))
const MAX_REPAIRS = Math.max(0, Math.min(2, Math.floor(Number(A.maxRepairRounds ?? 2))))
const READING_LINE = 0.75   // film-settings.json, place_measures reading_test_share_min (judged: 12 of 16 features)
const RENTED = A.rented ?? 'auto'
const RENDERER = A.renderer ?? 'auto'
const FINALS = A.finals === true
const WHERE = RENTED === true ? 'rented' : RENTED === false ? 'local' : 'auto'
const ENGINE = ['cycles', 'eevee'].includes(String(RENDERER).toLowerCase()) ? String(RENDERER).toLowerCase() : 'auto'
const REFERENCES = Array.isArray(A.references) ? A.references : []
const SEVERE = ['must fix', 'should fix']

const F = String(A.folder).replace(/\/+$/, '')
const DIR = { plan: `${F}/plan`, scene: `${F}/scene`, stages: `${F}/stages`, work: `${F}/work`, reports: `${F}/reports`, render: `${F}/render`, pictures: `${F}/pictures`, checks: `${F}/checks` }
const START_FILE = A.scene ?? `${DIR.scene}/start.blend`
const GROUND_FILE = `${DIR.scene}/ground.blend`
const combinedFile = (version) => `${DIR.scene}/round${version}/combined.blend`
const finishedFile = (version) => `${DIR.scene}/round${version}/finished.blend`
const auditFile = (version) => `${DIR.reports}/place-audit-round${version}.json`
const AGENT = { planner: 'place-planner.md', builder: 'place-builder.md', integrator: 'place-integrator.md', renderer: 'place-renderer.md', checker: 'place-checker.md' }
const first = (role) => `First read ${A.plugin}/agents/${AGENT[role]} and follow it.`

// everything the later steps need lives in one object, so an early stop can always write its report
const S = {
  plan: null, ground: null, built: [], missing: [], combine: null, audit: null, auditRounds: [], repairs: [],
  render: null, checks: {}, skeptic: null, confirmed: [], notFixedOnPurpose: [], unverified: [],
  fixes: [], fixOwners: [], fixCombine: null, fixAudit: null, fixRender: null, recheck: null, recheckBlind: null,
  readingTests: [], freshCheck: null, finalGate: null, version: 1, finalFile: null, finalAuditFile: null, finalRender: null, claimOwners: [],
  havePictures: false, stopped: null, notes: [],
}

// ------------------------------------------------------------------------------------------------------------- small helpers
const asText = (value) => (typeof value === 'string' ? value : JSON.stringify(value, null, 1))
const safeWord = (text) => String(text ?? '').trim().toLowerCase().replace(/[^a-z0-9_]+/g, '_').replace(/^_+|_+$/g, '')
const numbered = (list) => ((list ?? []).length ? list.map((item, i) => `${i + 1}. ${item}`).join('\n') : '(none)')
const escapeRegExp = (text) => String(text).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const unique = (list) => [...new Set(list)]
const placeName = () => S.plan?.place ?? A.place ?? 'the place'

// runs work(item) for every item, at most cap at a time; the rest wait in a queue (none is skipped); an item whose work throws gives null
async function runQueued(items, cap, work) {
  const results = new Array(items.length).fill(null)
  if (!items.length) return results
  let next = 0
  const lane = () => async () => {
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
  await parallel(Array.from({ length: Math.min(cap, items.length) }, lane))
  return results
}

// a claim as a bare sentence: no measured result in brackets (a checker must recompute it, not copy it)
const bareClaim = (text) => String(text ?? '').replace(/\s*[(\[][^)\]]*\d[^)\]]*[)\]]/g, '').replace(/\s+/g, ' ').trim()

const ownerNames = () => (S.plan ? S.plan.parts.map((part) => part.owner) : [])
const knownOwner = (name) => {
  const word = safeWord(name)
  return ownerNames().includes(word) ? word : 'integrator'
}
const ownerFromText = (text) => {
  const head = safeWord(String(text ?? '').split(':')[0])
  return ownerNames().includes(head) ? head : 'integrator'
}
const partOf = (owner) => S.plan.parts.find((part) => part.owner === owner)

// ----------------------------------------------------------------------------------------------------------- shared prompt text
const RULES = `RULES FOR EVERYONE
- Spend no money. The only paid thing in this run is drawing pictures on the person's own rented card: only the renderer does it, and only when the notes say it may.
- Never commit or push. Never write a key, an id or a personal detail into any file or answer, and never open the folder where the rented-card account keeps its settings (the client reads the person's settings when it runs).
- Never lower a requirement to make a check pass. The only allowed ways to skip a treatment are an off entry with a true reason in the place settings, and an accepted entry that the person signed (who and the date). You never sign for the person.
- This computer is slow and its disk is small: run only small tests here (small pictures, quick runs); anything bigger waits for the renderer. Keep .blend files few, delete your own scratch files, keep big pictures on the rented card's store and bring back only small previews (under 400 KB).
- Plain everyday words, one word for each thing. Say what a tool measured and what you only judged. Say what you did not test and every failure; never write that something passed when you did not see it pass.
- Return your report as text in your final answer, in the shape asked (it is enforced). Save your evidence as JSON or text files in your own folder as you go: a helper can be refused a report file, and a restart can lose work.`

const environmentText = () => (A.environment ? `\nNOTES ABOUT THIS COMPUTER, THE DISK AND THE MONEY, from the person who started the run (they win over anything else written here):\n${asText(A.environment)}\n` : '')
const blenderText = () => (A.blender
  ? `Blender is at ${A.blender}: give every command that starts Blender the option --blender ${A.blender}.`
  : 'Blender: the commands look for it themselves (the BLENDER setting, then the kit machine settings file, then the PATH). If it cannot be found, stop and say so.')

const runHeader = (who) => `THE RUN
The place: ${placeName()}. Today is ${A.today ?? '(not given)'}.
The request, in the person's own words, exactly: "${A.request}"
The plugin is at ${A.plugin}. The kit (it holds place-kit and calculators) is at ${A.kit}. The run's folder is ${F}.
The place command is ${A.plugin}/bin/explainer-film-place (the preflight is ${A.plugin}/bin/explainer-film-preflight); call them by these full paths when they are not on your PATH.
${blenderText()}
${who === 'checker'
    ? `Your folder for scratch files and your result: ${DIR.checks}/. Pictures are under ${DIR.pictures}/, scene files under ${DIR.scene}/, the plan under ${DIR.plan}/. You work blind to how things were built: do not open the work folder, the stage files or any part report.`
    : `Folders in the run's folder: plan (the plan files), scene (Blender scenes), stages (one stage file for each owner), work (one scratch folder for each owner), reports, render (job files), pictures, checks.`}
${environmentText()}
${RULES}`

const planFilesText = () => {
  const f = S.plan.files
  return `- style note: ${f.style_note}\n- facts table: ${f.facts}\n- place settings: ${f.settings}\n- ownership table: ${f.ownership}\n- acceptance list: ${f.acceptance}`
}
const viewsText = () => numbered(S.plan.views.map((v) => `${v.name}: camera "${v.camera}", ${v.size[0]} x ${v.size[1]}`))

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
  unsure: strs, shared_problems: strs, failures: strs, not_tested: strs, views_to_redraw: strs, seconds: num,
}
const PART_REQUIRED = ['owner', 'stage_file', 'steps_finished', 'objects_added', 'triangles', 'own_audit', 'surface_pass_done', 'wear_preview_done', 'claims', 'unsure', 'shared_problems', 'failures', 'not_tested', 'seconds']
const PART_REPORT = obj(PART_PROPS, PART_REQUIRED)
const GROUND_REPORT = obj({ ...PART_PROPS, start_file: str, ground_file: str, cameras: strs, ground_promise: str }, [...PART_REQUIRED, 'ground_file', 'cameras', 'ground_promise'])

const COMBINE_REPORT = obj({
  order_plain_ok: bool, order_reverse_ok: bool, violations: strs, idempotent: bool,
  combined_file: str, finished_file: str, audit_file: str,
  audit_verdict: { type: 'string', enum: ['pass', 'fail', 'not run'] }, audit_problems: list(AUDIT_PROBLEM),
  repairs_made: strs, missing_parts: strs, failures: strs, not_tested: strs,
}, ['order_plain_ok', 'order_reverse_ok', 'violations', 'idempotent', 'finished_file', 'audit_verdict', 'audit_problems', 'repairs_made', 'failures', 'not_tested'])

const AUDIT_REPORT = obj({
  scene_file: str, audit_file: str, scene_sha256: str, audit_exit_code: num, preflight_exit_code: num,
  verdict: { type: 'string', enum: ['pass', 'fail'] }, quick: bool,
  problems: list(AUDIT_PROBLEM), looks: strs, known: strs, notes: strs,
}, ['scene_file', 'audit_file', 'audit_exit_code', 'preflight_exit_code', 'verdict', 'problems', 'looks', 'known'])

const RENDER_REPORT = obj({
  renderer: str, why: str, where: { type: 'string', enum: ['rented', 'local'] }, device: str, balance_checked: bool, stalled: bool,
  pictures: list(obj({ view: str, path: str, half_path: str, size: list(num), samples: num, seconds: num }, ['view', 'path', 'half_path', 'size', 'samples', 'seconds'])),
  seconds_total: num, estimated_dollars: num, guard_file: str, guard_made_from: str, guard_provisional: bool,
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
${A.place ? `The person calls it: ${A.place}.` : 'Choose a short plain name for it.'}
${A.parts ? `The person asked for these parts, so use them (you may add parts and improve their briefs):\n${asText(A.parts)}` : 'Propose 3 to 8 parts.'}
The ground part is built first, alone, then frozen. Its owner goes in ground_owner. ${A.scene ? `The starting scene is ${A.scene}; the ground builder starts from it.` : `There is no starting scene: the ground builder makes an empty one at ${START_FILE}.`}
${A.views ? `The person wants these views:\n${asText(A.views)}` : 'Propose at least three views.'} The cameras are named "View <name>".
${REFERENCES.length ? `The person gave reference pictures: ${REFERENCES.join(', ')}. Measure them; the style note and the style guard come from them, so the style note is not provisional.` : 'There are no reference pictures: the style note is PROVISIONAL (say so in its first line); the first honest picture will make the style guard.'}
Renderer wished: ${RENDERER}. Rented card allowed: ${RENTED}.
Return the plan in the shape asked.`

const groundBlock = () => `YOU ARE THE GROUND PART and you go first, alone. Nothing else is built until you are done.
Starting scene: ${A.scene ? `${A.scene} (copy it, never change the original)` : `none: make an empty scene and save it as ${START_FILE}`}.
Make the graded ground, the lane shapes, the verge and the puddle hollows; make the view cameras named in the views list; apply your stage file to the starting scene and save the result as ${GROUND_FILE}. That file is then FROZEN: every other part is seated on it.
No buildings and no props are yours. Say in ground_promise what the ground promises the others (for example "inside 1.2 m of each lane centre line the ground is as it is").`

const buildBlock = () => `Work on your own COPY of ${GROUND_FILE} (the frozen ground: never change it, never save over it). Seat everything on it.`

const fixBlock = (findings, why) => `THIS IS A FIX ROUND (${why}). Only these confirmed findings about your part are yours; fix them and nothing else:
${numbered(findings.map((f) => `${f.what ?? f.text} (where: ${f.where ?? 'not said'}; cheapest fix: ${f.cheapest_fix ?? f.fix ?? 'not said'}; severity: ${f.severity ?? 'must fix'})`))}
Change only your own stage file ${DIR.stages}/stage_<owner>.py, run it again with your checks, and name in views_to_redraw the views that changed (by view name). Do not make the part less characterful to chase a number: a squint-test miss is reported to the person, never fixed.`

const builderPrompt = (part, mode, findings, why) => `${first('builder')}

${runHeader('builder')}

YOUR MODE: ${mode}. YOUR PART: ${part.name}. Owner: ${part.owner}. Collection: "Place: ${part.owner}".
Region (x0, y0, x1, y1 in metres): ${JSON.stringify(part.region ?? [])}. Triangle budget for this part: ${part.triangle_budget ?? 'the budget the audit holds (house numbers)'}.
The plan files:
${planFilesText()}
Views (the ground part makes the cameras):
${viewsText()}
Frozen (nobody but the ground part changes these): ${asText(S.plan.frozen.length ? S.plan.frozen : ['cameras', 'lights', 'the world', 'render settings', 'the ground height'])}
Contracts between owners: ${asText(S.plan.contracts.length ? S.plan.contracts : ['none written'])}
The other owners (their objects are not yours to touch): ${ownerNames().filter((o) => o !== part.owner).join(', ') || 'none'}.

${mode === 'ground' ? groundBlock() : mode === 'fix' ? fixBlock(findings, why) : buildBlock()}

YOUR BRIEF:
${part.brief}

YOUR STEPS, in priority order (a finished step 1 plus step 2 is already a valid delivery):
${numbered(part.steps_in_order)}

Your stage file: ${DIR.stages}/stage_${part.owner}.py. Your own folder for scratch files and evidence: ${DIR.work}/${part.owner}/.
Give every object its owner and its role as it is made. Claims in your report are bare sentences with no measured number in them; the tool that measured each goes in measured_by.`

const stagePaths = () => S.built.filter((b) => b.report).map((b) => b.report.stage_file || `${DIR.stages}/stage_${b.part.owner}.py`)
const stageList = () => stagePaths().map((path, i) => `- ${S.built.filter((b) => b.report)[i].part.owner}: ${path}`).join('\n') || '(none)'

const combinePrompt = (version, repairs, groundChanged) => `${first('integrator')}

${runHeader('integrator')}

YOUR MODE: combine (version ${version}).
The frozen ground: ${GROUND_FILE}.${groundChanged ? ` THE GROUND STAGE WAS CHANGED: rebuild ${GROUND_FILE} first (apply ${DIR.stages}/stage_${S.plan.ground_owner}.py to ${START_FILE} and save), then apply every other stage again.` : ''}
The stage files to combine:
${stageList()}
Parts that did NOT report (do not combine them; list them as missing in your answer): ${S.missing.length ? S.missing.join(', ') : 'none'}.
The plan files:
${planFilesText()}
Run these, in this order (each one starts Blender):
1. explainer-film-place combine --scene ${GROUND_FILE} --stages ${stagePaths().join(' ')} --order plain --owners ${S.plan.files.ownership} --save-as ${combinedFile(version)} --out ${DIR.reports}/combine-plain-round${version}.json
2. explainer-film-place combine --scene ${GROUND_FILE} --stages ${stagePaths().join(' ')} --order reverse --owners ${S.plan.files.ownership} --out ${DIR.reports}/combine-reverse-round${version}.json
3. explainer-film-place finish --scene ${combinedFile(version)} --settings ${S.plan.files.settings} --save-as ${finishedFile(version)}
Never use a quick run for the finished scene. Step 3 writes place-audit.json beside the finished scene and prints the audit; the official audit of this round is made later by another helper. Delete the combined scene of any older round when you are sure it is not needed.
Look: ${S.plan.look ?? 'from the settings'}; state: ${S.plan.state ?? 'from the settings'} (change them only when a repair below says so).
${repairs.length ? `REPAIRS ASKED OF YOU (settings, role tags and dials only: geometry is never yours and goes back to its owner):\n${numbered(repairs.map((r) => `${r.text} (where: ${r.where}; fix: ${r.fix})`))}\n` : ''}Return your report in the shape asked.`

const auditPrompt = (version) => `${first('integrator')}

${runHeader('integrator')}

YOUR MODE: audit. Prove this file and change nothing: ${finishedFile(version)}. Never save it again and never run the whole pass again.
Settings: ${S.plan.files.settings}. Facts table: ${S.plan.files.facts}. Ownership table: ${S.plan.files.ownership}.
Run these, in this order:
1. explainer-film-place audit --scene ${finishedFile(version)} --settings ${S.plan.files.settings} --facts ${S.plan.files.facts} --out ${auditFile(version)}
2. explainer-film-preflight place --place-audit ${auditFile(version)} --blend ${finishedFile(version)} --place-settings ${S.plan.files.settings} --reports ${DIR.reports}/preflight-round${version}${A.accepted ? ` --accepted ${A.accepted}` : ''}
The preflight reports go into ${DIR.reports}/preflight-round${version}/, so nothing lands beside the plugin. ${A.accepted ? 'The accepted file is the person\'s: you never write an accepted entry.' : 'There is no accepted file.'}
Every FAIL goes into problems with the owner of the object it names ('integrator' for settings, role tags and dials). Return your report in the shape asked.`

const renderPrompt = (tag, views, previous, file) => `${first('renderer')}

${runHeader('renderer')}

YOUR JOB: draw the pictures of ${file}. Round: ${tag}.
The renderer rule: ${RENDERER} (auto means the film owner's rule: Cycles where lamps, lit windows, lanterns or fires are on, EEVEE when they are off). Rented card allowed: ${RENTED} (auto: use it when the client says workers can start, otherwise only tiny local pictures, and say so).
Views to draw:
${numbered(views.map((v) => `${v.name}: camera "${v.camera}", ${v.size[0]} x ${v.size[1]}`))}
Finals: ${FINALS ? 'yes, also draw the final-size pictures' : 'no, previews only'}.
Write the job file to ${DIR.render}/job-${tag}.json (its scene is ${file}), the pictures into ${DIR.pictures}/${tag}/ and the half-size copies into ${DIR.pictures}/half/${tag}/. Name each half-size copy by its number only (view-1.jpg, view-2.jpg and so on, in the order of the views), so that its file name tells a reader nothing.
Draw with: explainer-film-place render --scene ${file} --job ${DIR.render}/job-${tag}.json --where ${WHERE} --engine ${ENGINE}${FINALS ? ' --finals' : ''}
${previous ? `This is a later round. Use the existing style guard ${S.render.guard_file ?? `${DIR.pictures}/style-guard.json`} and do not make a new one. The previous round's pictures (for the squint test): ${previous.join(', ')}.` : `Make the style guard from ${REFERENCES.length ? `the reference pictures: ${REFERENCES.join(', ')}` : 'your first honest picture (say it is PROVISIONAL)'} and write it to ${DIR.pictures}/style-guard.json.`}
Return your report in the shape asked.`

const claimsText = () => {
  const rows = []
  S.claimOwners = []
  const add = (owner, claim) => { rows.push(`[${owner}] ${bareClaim(claim)}`); S.claimOwners.push({ owner, key: plainKey(claim) }) }
  for (const b of S.built) if (b.report) for (const c of b.report.claims) add(b.part.owner, c.claim)
  if (S.ground) for (const c of S.ground.claims) add(S.plan.ground_owner, c.claim)
  return numbered(rows)
}

const picturePaths = (render, half) => (render?.pictures ?? []).map((p) => (half ? p.half_path : p.path))

// who owns a claim a checker sent back: its [owner] tag when it kept one, else the claim it matches, else the integrator
const plainKey = (text) => bareClaim(text).replace(/^\[[^\]]*\]\s*/, '').toLowerCase()
function claimOwner(text) {
  const tag = /^\s*\[([^\]]+)\]/.exec(String(text ?? ''))
  if (tag && ownerNames().includes(safeWord(tag[1]))) return safeWord(tag[1])
  const key = plainKey(text)
  const match = S.claimOwners.find((c) => c.key && (key.includes(c.key) || c.key.includes(key)))
  return match ? match.owner : 'integrator'
}

const checkContext = (render) => `THE PLACE TO CHECK
The request, in the person's own words, exactly: "${A.request}"
Style note: ${S.plan.files.style_note}
Acceptance list: ${S.plan.files.acceptance}
Facts table: ${S.plan.files.facts}
Place settings: ${S.plan.files.settings}
The finished scene file: ${S.finalFile}
The pictures (look at them with the Read tool):
${numbered(picturePaths(render, false))}
The style guard (for measures): ${S.render?.guard_file ?? '(none was made)'}${S.render?.guard_provisional ? ' (PROVISIONAL: it was made from the first honest picture)' : ''}
Put the SHA-1 of the scene file you checked (sha1sum) in audit_scene_sha1.`

const checkerPrompt = (mode, extra, render) => `${first('checker')}

${runHeader('checker')}

YOUR MODE: ${mode}.
${checkContext(render ?? S.render)}
Write your scratch files and your result into ${DIR.checks}/${mode}/.
${extra}
Return your result in the shape asked.`

const lookExtra = () => `The planned features, to judge one by one in each_element (you were NOT blind to this list: say was_blind false):
${numbered(S.plan.readable_features.map((f) => `${f.name} (viewers would say: ${(f.keywords ?? []).join(', ')})`))}
The builders' claims, as bare sentences to recompute where a picture can show them (do not look for their numbers):
${claimsText()}`

const structureExtra = () => `The builders' claims, as bare sentences to recompute with your own scripts on the scene file (use another formula than the obvious one where you can; list the ones you could not test in not_tested):
${claimsText()}`

const processExtra = () => `The money and disk rules, and anything else about how the work may be done, are in the notes above. ${A.ledger ? `The spend ledger is ${A.ledger}.` : 'There is no spend ledger.'}
What the renderer says it did (check it against the logs next to the pictures, do not trust it): ${S.render ? JSON.stringify({ renderer: S.render.renderer, where: S.render.where, device: S.render.device, balance_checked: S.render.balance_checked, stalled: S.render.stalled, seconds_total: S.render.seconds_total, estimated_dollars: S.render.estimated_dollars, pictures: S.render.pictures.map((p) => ({ view: p.view, seconds: p.seconds })) }) : 'no pictures were drawn'}
The audited file is ${S.finalFile}; its audit is ${S.finalAuditFile}. Check privacy over every file written in the run's folders, leftovers in the scene (preview cameras, unused data), the disk used, and whether the audit is stale.`

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
${checkContext(S.render)}
Fresh checkers looked at this place; their findings and every claim that did not hold are below. For EACH one, check it yourself (open the picture, run a script on the scene). Keep only what is real and what a viewer or a builder would care about. Merge duplicates. Rank honestly: must fix only for something wrong, broken or misleading that a viewer would notice; should fix for a clear improvement worth a small change; minor for the rest. Keep the cheapest concrete fix and its owner (a part owner: ${ownerNames().join(', ')}; or integrator for settings, role tags and dials). A squint-test miss, or any finding whose only cure is to remove character from the place, goes in not_fixed_on_purpose, never in confirmed: the person decides.
Findings:
${JSON.stringify(findings, null, 1)}
Return your answer in the shape asked.`

const recheckExtra = (oldRender) => `You are a DIFFERENT checker from the first round and you did not make the fixes. The confirmed findings of the first round, which the fix round tried to fix:
${numbered(S.confirmed.map((f) => `${f.what} (where: ${f.where}; owner: ${f.owner})`))}
The first round's pictures, for comparison: ${picturePaths(oldRender, false).join(', ')}.
For each finding say, as a claim, whether it is fixed (holds true or false, with the evidence from the new picture or the scene). Then look for NEW faults the fixes caused.`

const gatePrompt = (fresh) => `${first('integrator')}

${runHeader('integrator')}

YOUR MODE: gate (the last step). The final scene is ${S.finalFile}; its audit is ${S.finalAuditFile}. The pictures are in ${DIR.pictures}/ (${picturePaths(S.finalRender, false).join(', ') || 'none'}). The style guard is ${S.render?.guard_file ?? '(none)'}. Settings: ${S.plan.files.settings}. Preflight reports go into ${DIR.reports}/preflight-final/ (use --reports with that folder).
${A.accepted ? `The person's accepted file is ${A.accepted} (pass it with --accepted).` : ''}
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
  for (const wanted of Array.isArray(A.parts) ? A.parts : []) {
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
  const given = Array.isArray(A.views) && A.views.length ? A.views : (raw.views ?? [])
  const views = (given.length ? given : [{ name: 'wide' }, { name: 'lane_close' }, { name: 'detail_close' }]).map((v, i) => {
    const name = safeWord(v.name) || `view_${i + 1}`
    return { name, camera: v.camera || `View ${name}`, size: Array.isArray(v.size) && v.size.length === 2 ? v.size : [1200, 800] }
  })
  const f = raw.files ?? {}
  const files = {
    style_note: f.style_note || `${DIR.plan}/style-note.md`, facts: f.facts || `${DIR.plan}/real-world-facts.json`,
    settings: f.settings || `${DIR.plan}/place-settings.json`, ownership: f.ownership || `${DIR.plan}/ownership.json`,
    acceptance: f.acceptance || `${DIR.plan}/acceptance.json`,
  }
  const features = (raw.readable_features ?? []).filter((x) => x && x.name).map((x) => ({
    name: x.name, keywords: (x.keywords?.length ? x.keywords : String(x.name).split(/\s+/)).map((k) => String(k).toLowerCase()),
  }))
  return {
    place: raw.place || A.place || 'the place', place_type: raw.place_type || 'generic', files, ground_owner: groundOwner,
    look: raw.look, state: raw.state, parts, contracts: raw.contracts ?? [], frozen: raw.frozen ?? [], views,
    readable_features: features, renderer_hint: raw.renderer_hint ?? '', open_questions: raw.open_questions ?? [], notes: raw.notes ?? '',
  }
}

// ----------------------------------------------------------------------------------- audit gate and problem routing
const combineClean = (combine) => !!combine && combine.order_plain_ok !== false && combine.order_reverse_ok !== false && combine.idempotent !== false && (combine.violations ?? []).length === 0
const gateOk = (combine, audit) => !!audit && audit.verdict === 'pass' && combineClean(combine)

function collectProblems(combine, audit) {
  const found = []
  for (const text of combine?.violations ?? []) found.push({ check: 'ownership', where: 'combine', owner: ownerFromText(text), text, fix: 'each owner changes only its own objects' })
  if (combine && combine.order_plain_ok === false) found.push({ check: 'combine', where: 'plain order', owner: 'integrator', text: 'the stages could not be combined in plain order', fix: 'read the combine report; the stage that fails goes back to its owner' })
  if (combine && combine.order_reverse_ok === false) found.push({ check: 'combine', where: 'reverse order', owner: 'integrator', text: 'the reverse order gives a different or broken scene: a stage depends on the order', fix: 'the stage that depends on another stage goes back to its owner' })
  if (combine && combine.idempotent === false) found.push({ check: 'combine', where: 'run twice', owner: 'integrator', text: 'running the stages twice does not give the same scene: a stage is not idempotent', fix: 'the stage must first remove what it made earlier' })
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
  const rows = S.plan.readable_features.map((feature) => {
    const hit = (feature.keywords ?? []).find((word) => word && new RegExp('\\b' + escapeRegExp(word)).test(text))
    return { feature: feature.name, found: !!hit, by: hit ?? null }
  })
  const found = rows.filter((r) => r.found).length
  const planned = rows.length
  return {
    round, planned, found, share: planned ? Math.round((found / planned) * 1000) / 1000 : 0, line: READING_LINE,
    passed: planned > 0 && found / planned >= READING_LINE, missed: rows.filter((r) => !r.found).map((r) => r.feature), rows,
    was_blind: blind, how: 'keyword match on a blind reader\'s own words (judged, crude)',
  }
}

// a blind reader is only blind when the prompt shares no word with the feature list
function leakedWords(prompt) {
  const text = prompt.toLowerCase()
  return unique(S.plan.readable_features.flatMap((f) => (f.keywords ?? []).concat(String(f.name).toLowerCase().split(/\s+/))).filter((w) => w && w.length > 2 && new RegExp('\\b' + escapeRegExp(w) + '\\b').test(text)))
}

// ------------------------------------------------------------------------------------------------- the fresh-check object
const WORSE = { yes: 0, 'not judged': 0, nearly: 1, no: 2 }
function worstVerdict(results, key) {
  let worst = 'not judged'
  let rank = -1
  for (const r of results) {
    const v = r[key] ?? 'not judged'
    if (v !== 'not judged' && WORSE[v] >= rank) { worst = v; rank = WORSE[v] }
  }
  return worst
}

function composeFresh() {
  if (S.recheck) return S.recheck
  const results = ['look', 'structure'].map((k) => S.checks[k]).filter(Boolean)
  if (!results.length) return null
  return {
    mode: 'look and structure', was_blind: results.every((r) => r.was_blind === true),
    art_style_kept: worstVerdict(results, 'art_style_kept'), lived_in: worstVerdict(results, 'lived_in'), construction_makes_sense: worstVerdict(results, 'construction_makes_sense'),
    each_element: results.flatMap((r) => r.each_element), claims_checked: results.flatMap((r) => r.claims_checked),
    problems: S.confirmed.map((f) => ({ what: f.what, where: f.where, severity: f.severity, cheapest_fix: f.cheapest_fix, owner: f.owner })),
    should_fix_now: results.map((r) => r.should_fix_now).filter(Boolean).join(' '), not_tested: unique(results.flatMap((r) => r.not_tested)), measures: {},
    audit_scene_sha1: (results.find((r) => r.audit_scene_sha1) ?? {}).audit_scene_sha1,
  }
}

// ------------------------------------------------------------------------------------------------------------ the report
function reportMarkdown() {
  const p = S.plan
  const out = []
  const add = (...lines) => out.push(...lines)
  const yesNo = (value) => (value === true ? 'yes' : value === false ? 'no' : 'not said')
  add(`# ${placeName()}: what was built and what was checked`, '', `The request, as it was given: "${A.request}"`, '')
  if (S.stopped) add(`**The run stopped early: ${S.stopped}**`, '')
  add('## What I did')
  if (p) {
    add(`- Planned ${p.parts.length} part(s): ${p.parts.map((x) => `${x.name} (owner ${x.owner})`).join('; ')}. The ground part, ${p.ground_owner}, was built first and frozen.`)
    add(`- Look chosen: ${p.look ?? 'from the settings'}; state: ${p.state ?? 'from the settings'}. ${REFERENCES.length ? 'The style rule was measured from the reference pictures.' : 'There were no reference pictures, so the style note and the style guard are PROVISIONAL.'}`)
    if (p.open_questions.length) add(`- The planner could not settle these (facts from memory stay marked guess until a source confirms them): ${p.open_questions.join('; ')}.`)
  }
  if (S.ground) add(`- Ground: built (${S.ground.ground_file}); it promises: ${S.ground.ground_promise}. Steps finished: ${S.ground.steps_finished}.`)
  if (S.built.length) {
    const reported = S.built.filter((b) => b.report)
    add(`- Parts that reported: ${reported.map((b) => `${b.part.owner} (steps finished: ${b.report.steps_finished}; own pass done: ${yesNo(b.report.surface_pass_done)}; own wear preview looked at: ${yesNo(b.report.wear_preview_done)})`).join('; ') || 'none'}.`)
  }
  if (S.missing.length) add(`- **MISSING parts (no report came back, so they were NOT combined): ${S.missing.join(', ')}.**`)
  if (S.combine) {
    add(`- Combined in plain order: ${yesNo(S.combine.order_plain_ok)}; in reverse order: ${yesNo(S.combine.order_reverse_ok)}; running the stages twice gives the same scene: ${yesNo(S.combine.idempotent)}. Ownership violations: ${S.combine.violations.length ? S.combine.violations.join('; ') : 'none'}.`)
    if (S.combine.repairs_made.length) add(`- Repairs the integrator made (settings, role tags and dials only): ${S.combine.repairs_made.join('; ')}.`)
  }
  add('', '## The audit (measured by tools on the exact saved file)')
  if (S.audit) {
    add(`- Verdict: **${S.audit.verdict.toUpperCase()}** after ${S.repairs.length} repair round(s) before any picture (at most ${MAX_REPAIRS}). Scene file: ${S.audit.scene_file}${S.audit.scene_sha256 ? ` (SHA-256 ${S.audit.scene_sha256})` : ''}. Made from a quick run: ${yesNo(S.audit.quick)}.`)
    for (const x of S.audit.problems) add(`- FAIL ${x.check} [${x.where}] (owner ${x.owner}): ${x.text}. Fix: ${x.fix}`)
    for (const x of S.audit.looks) add(`- LOOK ${x}`)
    for (const x of S.audit.known) add(`- KNOWN (switched off on purpose or accepted by the person) ${x}`)
    for (const r of S.repairs) add(`- Repair round ${r.round}: owners asked: ${r.owners.join(', ') || 'only settings'}; problems routed: ${r.problems}; reports back: ${r.reported}.`)
  } else add('- No audit was run.')
  add('', '## Pictures')
  const r = S.render
  if (r) {
    add(`- Renderer: ${r.renderer} (${r.why}). Drawn ${r.where === 'rented' ? 'on the rented card' : 'on this computer'}; device: ${r.device}. Balance checked: ${yesNo(r.balance_checked)}. Stalled: ${yesNo(r.stalled)}.`)
    add(`- ${r.pictures.length} picture(s), ${r.seconds_total} seconds in all (measured by the logs next to the pictures). The cost is an ESTIMATE: about US$${r.estimated_dollars} from seconds and the hourly price; a real bill was once about 2.5 times the work seconds and was never explained.`)
    add(`- Style guard: ${r.guard_made_from}${r.guard_provisional ? ' (PROVISIONAL: it locks in whatever the first picture was)' : ''}. Picture measures: ${JSON.stringify(r.measures)}.`)
    for (const x of r.notes) add(`- Renderer note: ${x}`)
    for (const x of r.failures ?? []) add(`- Renderer failure: ${x}`)
  } else add('- No pictures were drawn.')
  add('', '## What the fresh checkers found (judged, with the numbers they recomputed)')
  for (const key of ['look', 'structure', 'process']) {
    const c = S.checks[key]
    if (!c) { add(`- ${key} checker: no result came back or it did not run.`); continue }
    add(`- ${key} checker (blind to the feature list: ${yesNo(c.was_blind)}): art style kept: ${c.art_style_kept}; lived in: ${c.lived_in}; construction makes sense: ${c.construction_makes_sense}. ${c.claims_checked.filter((x) => x.holds === false).length} of ${c.claims_checked.length} claim(s) did NOT hold. ${c.problems.length} problem(s) listed.`)
    for (const x of c.claims_checked.filter((y) => y.holds === false)) add(`  - A builder's claim that did not hold: "${bareClaim(x.claim)}" (evidence: ${x.evidence})`)
  }
  if (S.readingTests.length) {
    for (const t of S.readingTests) add(`- Reading test, round ${t.round}: a blind reader (blind: ${yesNo(t.was_blind)}) named ${t.found} of ${t.planned} planned features (${Math.round(t.share * 100)} percent; the line is ${Math.round(t.line * 100)} percent): ${t.passed ? 'PASSED' : 'MISSED'}. Not named: ${t.missed.join(', ') || 'none'}. This is a keyword match on free words: judged and crude.`)
  }
  if (S.skeptic) add(`- Skeptic: ${S.confirmed.length} finding(s) confirmed, ${S.skeptic.rejected.length} rejected. ${S.skeptic.summary}`)
  for (const x of S.confirmed) add(`  - ${x.severity.toUpperCase()}: ${x.what} (where: ${x.where}; owner: ${x.owner}). Cheapest fix: ${x.cheapest_fix}`)
  for (const x of S.unverified) add(`  - NOT CONFIRMED (no skeptic could check it, so nothing was done about it): ${x.what} (${x.severity})`)
  for (const x of S.notFixedOnPurpose) add(`- NOT FIXED ON PURPOSE (the person decides): ${x.what}. ${x.why}`)
  add('', '## The fix round (exactly one)')
  if (S.fixes.length || S.fixOwners.length) {
    add(`- Owners asked to fix confirmed findings: ${S.fixOwners.join(', ') || 'only settings (the integrator)'}. Reports back: ${S.fixes.length}.`)
    for (const f of S.fixes) add(`  - ${f.owner}: steps finished: ${f.steps_finished}; failures: ${f.failures.join('; ') || 'none'}; not tested: ${f.not_tested.join('; ') || 'nothing said'}.`)
    if (S.fixAudit) add(`- Audit after the fixes: **${S.fixAudit.verdict.toUpperCase()}** (${S.fixAudit.problems.length} problem(s)).`)
    if (S.recheck) add(`- Re-check by a different fresh checker: art style kept: ${S.recheck.art_style_kept}; lived in: ${S.recheck.lived_in}; construction: ${S.recheck.construction_makes_sense}; ${S.recheck.claims_checked.filter((x) => x.holds === false).length} finding(s)/claim(s) still not holding; ${S.recheck.problems.length} problem(s) left or new.`)
    for (const x of S.recheck?.problems ?? []) add(`  - ${x.severity.toUpperCase()}: ${x.what} (where: ${x.where}; owner: ${x.owner})`)
  } else add('- Nothing was fixed (nothing was confirmed that needed it, or pictures were missing).')
  if (S.finalGate) {
    add('', '## The final gate (the preflight stage place on the final saved file)')
    add(`- Verdict: **${S.finalGate.verdict.toUpperCase()}** (exit ${S.finalGate.preflight_exit_code}); the audit is stale: ${yesNo(S.finalGate.stale)}.`)
    for (const x of S.finalGate.lines) add(`  - ${x}`)
  }
  add('', '## Measured and judged')
  add('- MEASURED by tools: every audit line, the construction and normal-map checks, the picture measures, the seconds of each picture, the combine check.')
  add('- JUDGED: how the place looks (checkers and the reading test), the sizes from memory (marked weak or guess in the facts table), the style guard when it came from the first picture, the cost estimate.')
  add('- Fresh checkers are helpers of the same kind as the builders and can share blind spots; the person\'s own eyes decide the look.')
  add('', '## What was not tested')
  const notTested = unique([
    ...(S.built.flatMap((b) => b.report?.not_tested ?? [])), ...(S.ground?.not_tested ?? []), ...(S.combine?.not_tested ?? []),
    ...Object.values(S.checks).flatMap((c) => c?.not_tested ?? []), ...(S.recheck?.not_tested ?? []),
  ])
  add(...(notTested.length ? notTested.map((x) => `- ${x}`) : ['- Nothing was reported as untested (check that this is believable).']))
  add('- Not tested by this workflow at all: the place seen by the person, a blind reader who was never given any hint (the reading test was only ever run this way here), and the lighter plan masks and the Cycles runs of the kit on a village-size scene unless a log above says otherwise.')
  add('', '## Every failure and everything that came back empty')
  const failures = unique([
    ...(S.missing.map((m) => `part ${m}: no report came back`)),
    ...(S.ground?.failures ?? []), ...S.built.flatMap((b) => b.report?.failures ?? []), ...(S.combine?.failures ?? []),
    ...(S.render?.failures ?? []), ...(S.notes ?? []),
  ])
  add(...(failures.length ? failures.map((x) => `- ${x}`) : ['- None were reported.']))
  add('', '## For you to decide')
  const decide = []
  if (S.render?.guard_provisional) decide.push('The style guard came from the first picture. If the first picture was bland, so is the guard: judge the pictures yourself or give a reference picture.')
  if (S.notFixedOnPurpose.length) decide.push('Findings that were not fixed on purpose (a squint-test miss, or a cure that would remove character) are listed above.')
  if (S.readingTests.some((t) => !t.passed)) decide.push('The reading test missed its line: some planned features do not read at half size.')
  if (S.audit && S.audit.verdict === 'fail') decide.push('The audit still fails; nothing was drawn. Read the FAIL lines above. Only you can accept a problem, in writing, with your name and the date.')
  if (S.audit?.known?.length) decide.push('Some treatments were switched off on purpose (KNOWN above): check the reasons are true.')
  add(...(decide.length ? decide.map((x) => `- ${x}`) : ['- Nothing is waiting for you except looking at the pictures.']))
  return out.join('\n')
}

function done(stopped) {
  if (stopped) S.stopped = stopped
  const reading = S.readingTests.length ? S.readingTests[S.readingTests.length - 1] : null
  return {
    plan: S.plan, ground: S.ground, parts: [...(S.ground ? [S.ground] : []), ...S.built.filter((b) => b.report).map((b) => b.report)], missing_parts: S.missing,
    combine: S.combine, audit: S.audit, repairs: S.repairs, render: S.render,
    checks: { look: S.checks.look ?? null, structure: S.checks.structure ?? null, process: S.checks.process ?? null, blind_reader: S.checks.blind ?? null, skeptic: S.skeptic },
    confirmed: S.confirmed, fixes: S.fixes,
    recheck: S.recheck ? { check: S.recheck, blind_reader: S.recheckBlind, audit_after_fix: S.fixAudit, render_after_fix: S.fixRender } : null,
    reading_test: reading, fresh_check: S.freshCheck, final_gate: S.finalGate, stopped: S.stopped, report_markdown: reportMarkdown(),
  }
}

// ======================================================================================================== the run
// ---- Plan
phase('Plan')
const rawPlan = await agent(planPrompt(), { label: 'plan', phase: 'Plan', schema: PLAN, effort: PLAN_EFFORT })
if (!rawPlan || !(rawPlan.parts ?? []).length) {
  return done('the planner came back with no plan (or a plan with no parts), so nothing was built')
}
S.plan = normalisePlan(rawPlan)
if (S.plan.parts.length < 3 || S.plan.parts.length > 8) log(`The plan has ${S.plan.parts.length} part(s); 3 to 8 is usual. Going on with it.`)
if (!S.plan.readable_features.length) S.notes.push('The planner named no readable features, so the reading test could not be made.')
log(`Plan: ${S.plan.parts.map((x) => x.owner).join(', ')}; the ground part is ${S.plan.ground_owner}; ${S.plan.readable_features.length} readable feature(s); ${S.plan.views.length} view(s).`)

// ---- Ground (serial: everything else is seated on it)
phase('Ground')
const groundPart = partOf(S.plan.ground_owner)
S.ground = await agent(builderPrompt(groundPart, 'ground'), { label: `ground:${groundPart.owner}`, phase: 'Ground', schema: GROUND_REPORT, effort: EFFORT })
if (!S.ground || !S.ground.ground_file) {
  return done('the ground part came back with no ground file, so nothing can be seated on it')
}
log(`Ground frozen: ${S.ground.ground_file}`)

// ---- Build parts (side by side, at most CAP at a time; the rest wait in a queue)
phase('Build parts')
const others = S.plan.parts.filter((part) => part.owner !== S.plan.ground_owner)
if (others.length > CAP) log(`${others.length} parts and room for ${CAP} builders at once: the rest wait in a queue, none is skipped.`)
const reports = await runQueued(others, CAP, (part) => agent(builderPrompt(part, 'build'), { label: `build:${part.owner}`, phase: 'Build parts', schema: PART_REPORT, effort: EFFORT }))
S.built = others.map((part, i) => ({ part, report: reports[i] }))
S.missing = S.built.filter((b) => !b.report).map((b) => b.part.owner)
if (S.missing.length) log(`No report from: ${S.missing.join(', ')}. They are reported as missing and not combined.`)
if (others.length && S.built.every((b) => !b.report)) {
  return done('no builder came back with a report, so there is nothing to combine with the ground')
}

// ---- Combine
phase('Combine')
S.version = 1
S.combine = await agent(combinePrompt(S.version, [], false), { label: 'combine', phase: 'Combine', schema: COMBINE_REPORT, effort: EFFORT })
if (!S.combine) {
  return done('the integrator came back with nothing, so there is no combined scene to audit')
}
log(`Combined: plain ${S.combine.order_plain_ok}, reverse ${S.combine.order_reverse_ok}, idempotent ${S.combine.idempotent}, ${S.combine.violations.length} violation(s).`)

// ---- Audit: nothing is drawn until it passes; at most MAX_REPAIRS repair rounds, routed to the owners the audit names
phase('Audit')
S.audit = await runAudit(S.version, 'audit')
S.auditRounds.push(S.audit)
let repairRound = 0
while (!gateOk(S.combine, S.audit) && repairRound < MAX_REPAIRS) {
  repairRound++
  const problems = collectProblems(S.combine, S.audit)
  const byOwner = groupByOwner(problems)
  const owners = [...byOwner.keys()].filter((o) => o !== 'integrator' && partOf(o))
  const settingsRepairs = byOwner.get('integrator') ?? []
  log(`Audit round ${repairRound}: ${problems.length} problem(s); asking ${owners.join(', ') || 'only the integrator (settings)'} to repair them.`)
  const fixed = await runQueued(owners, CAP, (owner) => agent(builderPrompt(partOf(owner), 'fix', byOwner.get(owner), `repair before any picture, round ${repairRound}`), { label: `repair${repairRound}:${owner}`, phase: 'Audit', schema: PART_REPORT, effort: EFFORT }))
  const stillMissing = owners.filter((o, i) => !fixed[i])
  if (stillMissing.length) S.notes.push(`Repair round ${repairRound}: no report from ${stillMissing.join(', ')}.`)
  fixed.forEach((report, i) => {
    if (!report) return
    if (owners[i] === S.plan.ground_owner) S.ground = { ...S.ground, ...report }
    const entry = S.built.find((b) => b.part.owner === owners[i])
    if (entry) entry.report = { ...entry.report, ...report }
  })
  S.repairs.push({ round: repairRound, owners, problems: problems.length, reported: fixed.filter(Boolean).length, summary: problems.slice(0, 5).map((x) => `${x.check}: ${x.text}`) })
  S.version += 1
  S.combine = await agent(combinePrompt(S.version, settingsRepairs, owners.includes(S.plan.ground_owner)), { label: `recombine${repairRound}`, phase: 'Audit', schema: COMBINE_REPORT, effort: EFFORT })
  if (!S.combine) {
    return done(`the integrator came back with nothing in repair round ${repairRound}, so there is no scene to audit`)
  }
  S.audit = await runAudit(S.version, `audit${repairRound}`)
  S.auditRounds.push(S.audit)
}
if (!gateOk(S.combine, S.audit)) {
  return done(`the audit still fails after ${repairRound} repair round(s), so no picture was drawn (nothing is drawn unless the audit passes or fails only on items the person accepted in writing)`)
}
S.finalFile = S.combine.finished_file || finishedFile(S.version)
S.finalAuditFile = S.audit.audit_file || auditFile(S.version)
log(`Audit passed on ${S.finalFile} after ${repairRound} repair round(s).`)

// ---- Render (the renderer rule decides the engine; only previews unless finals were asked for)
phase('Render')
S.render = await agent(renderPrompt('round1', S.plan.views, null, S.finalFile), { label: 'render', phase: 'Render', schema: RENDER_REPORT, effort: EFFORT })
if (!S.render) {
  S.notes.push('The renderer came back with nothing: no picture was drawn.')
} else if (S.render.stalled) {
  S.notes.push('The renderer stopped: jobs waited more than five minutes while workers showed idle. The queue was not purged and the endpoint was not changed. The person should look at the rented card account before another run.')
} else if (!S.render.pictures.length) {
  S.notes.push('The renderer drew no pictures.')
} else {
  S.havePictures = true
  S.finalRender = S.render
}
if (!S.havePictures) log('No pictures: only the structure and process checkers run, and there is no fix round (a fix needs pictures to be checked).')

// ---- Check (fresh checkers; none of them sees a builder report or number)
phase('Check')
const jobs = [{ key: 'structure', run: () => agent(checkerPrompt('structure', structureExtra()), { label: 'check:structure', phase: 'Check', schema: CHECK, effort: CHECK_EFFORT }) },
  { key: 'process', run: () => agent(checkerPrompt('process', processExtra()), { label: 'check:process', phase: 'Check', schema: CHECK, effort: CHECK_EFFORT }) }]
if (S.havePictures) {
  jobs.unshift({ key: 'look', run: () => agent(checkerPrompt('look', lookExtra()), { label: 'check:look', phase: 'Check', schema: CHECK, effort: CHECK_EFFORT }) })
  jobs.push({ key: 'blind', run: () => agent(blindPrompt(S.render, 1), { label: 'blind:1', phase: 'Check', schema: BLIND, effort: CHECK_EFFORT }) })
}
const checkResults = await parallel(jobs.map((job) => job.run))
jobs.forEach((job, i) => { if (checkResults[i]) S.checks[job.key] = checkResults[i]; else S.notes.push(`The ${job.key} checker came back with nothing.`) })

if (S.checks.blind && S.plan.readable_features.length) {
  const leaks = leakedWords(blindPrompt(S.render, 1))
  if (leaks.length) log(`The blind reader's prompt shares words with the feature list (${leaks.join(', ')}): it is reported as not blind.`)
  S.readingTests.push(readingTest(1, S.checks.blind.seen, leaks.length === 0))
  const t = S.readingTests[0]
  log(`Reading test: ${t.found} of ${t.planned} planned features named (${t.passed ? 'passed' : 'missed'}).`)
}

const findings = []
for (const key of ['look', 'structure', 'process']) {
  const c = S.checks[key]
  if (!c) continue
  for (const problem of c.problems) findings.push({ from: `${key} checker`, ...problem, owner: knownOwner(problem.owner) })
  for (const claim of c.claims_checked) if (claim.holds === false) findings.push({ from: `${key} checker: a builder's claim did not hold`, what: `claim: ${bareClaim(claim.claim)}`, where: 'the claim', severity: 'must fix', cheapest_fix: 'correct the scene or the claim', owner: claimOwner(claim.claim), evidence: claim.evidence })
}
if (findings.length) {
  S.skeptic = await agent(skepticPrompt(findings), { label: 'skeptic', phase: 'Check', schema: SKEPTIC, effort: CHECK_EFFORT })
  if (S.skeptic) {
    S.confirmed = S.skeptic.confirmed.map((f) => ({ ...f, owner: knownOwner(f.owner) }))
    S.notFixedOnPurpose = S.skeptic.not_fixed_on_purpose
  } else {
    S.unverified = findings
    S.notes.push(`The skeptic came back with nothing: ${findings.length} finding(s) stay unverified and none was acted on.`)
  }
}
log(`${findings.length} finding(s) from the checkers; ${S.confirmed.length} confirmed.`)

// ---- Fix (exactly one round, only confirmed findings that need it, only when pictures can check the result)
phase('Fix')
const toFix = S.confirmed.filter((f) => SEVERE.includes(f.severity))
let fixDone = false
let fixFile = null
if (!toFix.length) {
  log('Nothing confirmed needs fixing: no fix round.')
} else if (!S.havePictures) {
  log('Findings need fixing, but there are no pictures to check a fix with: no fix round. The findings are in the report.')
} else {
  const byOwner = groupByOwner(toFix)
  const owners = [...byOwner.keys()].filter((o) => o !== 'integrator' && partOf(o))
  const settingsRepairs = (byOwner.get('integrator') ?? []).map((f) => ({ text: f.what, where: f.where, fix: f.cheapest_fix }))
  S.fixOwners = owners
  log(`Fix round (the only one): ${owners.length} owner(s) (${owners.join(', ') || 'settings only'}), ${toFix.length} finding(s).`)
  const fixed = await runQueued(owners, CAP, (owner) => agent(builderPrompt(partOf(owner), 'fix', byOwner.get(owner), 'the one fix round after the checkers'), { label: `fix:${owner}`, phase: 'Fix', schema: PART_REPORT, effort: EFFORT }))
  S.fixes = fixed.filter(Boolean)
  owners.forEach((o, i) => { if (!fixed[i]) S.notes.push(`Fix round: no report from ${o}.`) })
  S.version += 1
  S.fixCombine = await agent(combinePrompt(S.version, settingsRepairs, owners.includes(S.plan.ground_owner)), { label: 'combine:fix', phase: 'Fix', schema: COMBINE_REPORT, effort: EFFORT })
  if (S.fixCombine) {
    S.fixAudit = await runAudit(S.version, 'audit:fix')
    if (gateOk(S.fixCombine, S.fixAudit)) {
      fixDone = true
    } else {
      S.notes.push('After the fix round the audit does not pass, so nothing was drawn again and the first audited file stays the final one. The stage files have changed since that file was made.')
    }
  } else {
    S.notes.push('After the fix round the integrator came back with nothing: nothing was combined or drawn again.')
  }
  if (fixDone) {
    const named = unique(S.fixes.flatMap((f) => f.views_to_redraw ?? []).map(safeWord))
    const wanted = S.plan.views.filter((v) => named.includes(v.name))
    const redraw = wanted.length ? wanted : S.plan.views
    if (!wanted.length) log('The fixers did not name the views that changed: all views are drawn again.')
    const previous = picturePaths(S.render, false)
    fixFile = S.fixCombine.finished_file || finishedFile(S.version)
    S.fixRender = await agent(renderPrompt('round2', redraw, previous, fixFile), { label: 'render:fix', phase: 'Fix', schema: RENDER_REPORT, effort: EFFORT })
    if (!S.fixRender || S.fixRender.stalled || !S.fixRender.pictures.length) {
      S.notes.push(`The pictures after the fix round could not be drawn (nothing came back, or the card stalled). The fixed scene ${fixFile} passed its audit but nobody has looked at it, so the first audited scene stays the final one.`)
      fixDone = false
    }
  }
}

// ---- Re-check (a different fresh checker and a second blind reader look at the changed place)
phase('Re-check')
if (fixDone) {
  // the new picture set: the redrawn views, and the earlier pictures of the views that were not drawn again
  const redrawnViews = S.fixRender.pictures.map((p) => p.view)
  const mixed = { ...S.fixRender, pictures: [...S.render.pictures.filter((p) => !redrawnViews.includes(p.view)), ...S.fixRender.pictures], guard_file: S.render.guard_file, guard_provisional: S.render.guard_provisional }
  S.finalFile = fixFile
  S.finalAuditFile = S.fixAudit.audit_file || auditFile(S.version)
  S.finalRender = mixed
  const results = await parallel([
    () => agent(checkerPrompt('recheck', recheckExtra(S.render), mixed), { label: 'recheck', phase: 'Re-check', schema: CHECK, effort: CHECK_EFFORT }),
    () => agent(blindPrompt(mixed, 2), { label: 'blind:2', phase: 'Re-check', schema: BLIND, effort: CHECK_EFFORT }),
  ])
  S.recheck = results[0]
  S.recheckBlind = results[1]
  if (!S.recheck) S.notes.push('The re-check came back with nothing.')
  if (S.recheckBlind && S.plan.readable_features.length) {
    const leaks = leakedWords(blindPrompt(mixed, 2))
    S.readingTests.push(readingTest(2, S.recheckBlind.seen, leaks.length === 0))
    const t = S.readingTests[S.readingTests.length - 1]
    log(`Reading test after the fix: ${t.found} of ${t.planned} (${t.passed ? 'passed' : 'missed'}).`)
  } else if (!S.recheckBlind) S.notes.push('The second blind reader came back with nothing.')
} else {
  log('No re-check: there was no fix round with new pictures.')
}

// ---- Report (the final gate on the saved file, then the plain-words report)
phase('Report')
S.freshCheck = composeFresh()
if (S.freshCheck && S.finalFile) {
  S.finalGate = await agent(gatePrompt(S.freshCheck), { label: 'gate', phase: 'Report', schema: FINAL_GATE, effort: EFFORT })
  if (!S.finalGate) S.notes.push('The final gate came back with nothing: the preflight stage place was not run on the final file.')
} else {
  S.notes.push('No fresh checker result, so the final gate was not run with one.')
}
return done(null)
}
