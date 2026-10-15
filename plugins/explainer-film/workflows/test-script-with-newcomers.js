export const meta = {
  name: 'test-script-with-newcomers',
  description: 'Test a narration script on imagined first-time viewers, a fact checker, a rules-and-voice reader and a skeptic, then make only the confirmed fixes and re-check every changed sentence',
  whenToUse: 'After a script is written and before it is recorded, especially when viewers got lost in an earlier version. Pass the script, the research ledger, a work folder and today\'s date; optionally the rules file, the older version and a viewer-only version.',
  phases: [
    { title: 'Viewer copy', detail: 'what a viewer hears and sees, nothing else (skipped if given)' },
    { title: 'Test', detail: 'imagined newcomers, facts, rules and voice, a skeptic' },
    { title: 'Fix', detail: 'confirmed fixes only' },
    { title: 'Verify', detail: 'every changed sentence checked again, then a last fix if needed' },
  ],
}

// What this does: the newcomer test used on chapter 2 of the austerity explainer (log 33), where
// viewers got lost because the recorded chapter moved too fast and used words most people don't know.
// Four fresh helpers test the script, a fixer makes only the fixes it confirms against the ledger, and
// a re-checker reads every changed sentence again. The imagined viewers are a first filter only: the
// script should still be read to one or two real newcomers before recording.
//
// args: {
//   script: '/path/to/NN Script - chapter.md'      (required: pages with narration, research ids, pictures)
//   ledger: '/path/to/NN Research - chapter.md'     (required: the checked research ledger)
//   work: '/path/to/scratch/folder'                 (required: helpers write only inside it)
//   today: '15 October 2026'                        (required: so "latest" figures are judged right)
//   rules: '/path/to/rules file.md'                 (optional: voice, tone and writing rules)
//   viewer: '/path/to/viewer copy.md'               (optional: narration and on-screen words only)
//   older: '/path/to/the version people got lost in.md' (optional: for the skeptic's comparison)
//   audience: 'a general New Zealand audience'      (optional)
//   wordsPerMinute: 160                             (optional: the narrator's measured speed)
//   voice: 'urgent and direct, in the spirit of ...' (optional: the voice the script aims for)
// }
const A = args ?? {}
for (const key of ['script', 'ledger', 'work', 'today']) {
  if (!A[key]) throw new Error(`test-script-with-newcomers needs args.${key}`)
}
const W = A.work
const SPEED = A.wordsPerMinute ?? 160
const AUDIENCE = A.audience ?? 'a general audience'

const CONTEXT = `
A narrated explainer film for a phone screen, for ${AUDIENCE}. Today is ${A.today}. The script to check: ${A.script}.
The checked research ledger: ${A.ledger}.${A.rules ? ` The project's voice and writing rules: ${A.rules}.` : ''}
${A.voice ? `The voice it aims for: ${A.voice}.` : ''}
RULES THAT BIND EVERY WORD: facts only from the ledger, never stronger than its entry, qualifications kept; opinions said as
someone's ("she argues"); one plain name for each thing, and never one word for two things; every unfamiliar word explained
in plain words the first time, or left out; written for the ear: "..." for pauses, numbers written as said, no capitals for
emphasis, no bracketed cues except the one accent line. Do not edit anything outside your own work folder. Write in plain
everyday words.`

const FINDINGS = { type: 'object', properties: {
  summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', properties: {
    page: { type: 'number' }, quote: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['page', 'quote', 'problem', 'fix', 'severity'] } },
  not_checked: { type: 'string' },
}, required: ['summary', 'findings', 'not_checked'] }

phase('Viewer copy')
let viewer = A.viewer
if (!viewer) {
  viewer = `${W}/viewer-copy.md`
  await agent(`${CONTEXT}\n\nYour work folder: ${W} (create it).\n\nWrite ${viewer}: for each page of the script, only what a viewer
hears (the narration, word for word) and sees (the words and pictures on screen, from the page's picture notes). Leave out
research ids, notes, fix histories and anything else a viewer would never meet. Change no words. Return the file's path.`,
    { label: 'viewer copy', phase: 'Viewer copy' })
}

const TESTS = [
  { key: 'newcomers', ask: `You have never seen any version of this film. Read ONLY ${viewer} (what a viewer hears and sees);
do not open the script file, its notes or any earlier draft. Hear it once at speaking speed as four first-time viewers: a
15-year-old; a 70-year-old who left school at 15; an adult whose first language isn't English; and a busy parent
half-watching on a phone. For each, answer these questions about understanding: the main claim in their own words; what each
term means; where they first hesitated; how each example supports the point; two new cases they could now reason about
(make them up from the script's own main idea); and whether they can use the closing lines. Report every point of confusion.` },
  { key: 'facts', ask: `Check every factual sentence against the ledger entry its page cites (open the ledger; read each entry's
claim, plain version, confidence, notes and the Traps). A finding for any claim stronger, more precise or more certain than its
entry; a dropped qualification; a changed date, place, number or unit; a cause stated where the entry supports less; a
general rule stated more broadly than its evidence; a fact with no id or a wrong id; an opinion not marked as someone's; and
any figure that goes out of date soon after ${A.today}. Every factual error is a must-fix.` },
  { key: 'rules-and-voice', ask: `Check the rules and the voice: numbers written as said; "..." for pauses; no capitals for
emphasis; no bracketed cues; one name for each thing (list every synonym swap, and every word used in two senses); every term
explained at first use; never two new numbers in one sentence except a "from... to" pair; no aside between a subject and its
verb; no stock phrases; nothing that trips the tongue. Does the voice still have life and stakes, or has it gone flat? Count
spoken words and estimate the length at ${SPEED} words a minute plus about 0.6 seconds for each "...".` },
  { key: 'skeptic', ask: `${A.older ? `Viewers got lost in an older version (${A.older}). Read it, then this one.` : 'Read the script.'}
Be a skeptic: is it actually easy for a newcomer to follow, page by page? Where is it still fast or dense (count new names,
numbers, places and terms per page)? Where is a term still unexplained or explained too late? Where has it gone too far the
other way: padded, repetitive, patronising, or so long a phone viewer would drop off? Name lines that could go without losing
the teaching. Mark as must-fix only what would still lose a newcomer.` },
]

phase('Test')
const tested = await parallel(TESTS.map((t) => () =>
  agent(`${CONTEXT}\n\nYour work folder: ${W}/test-${t.key} (create it).\n\n${t.ask}`,
    { label: `test:${t.key}`, phase: 'Test', schema: FINDINGS })))
const findings = TESTS.map((t, i) => `### ${t.key}\n${JSON.stringify(tested[i], null, 1)}`).join('\n\n')

const SCRIPT = { type: 'object', properties: {
  title: { type: 'string' }, estimated_seconds: { type: 'number' }, spoken_words: { type: 'number' },
  pages: { type: 'array', items: { type: 'object', properties: {
    page: { type: 'number' }, name: { type: 'string' }, text: { type: 'string' },
    research_ids: { type: 'array', items: { type: 'string' } }, pictures: { type: 'string' } },
    required: ['page', 'name', 'text', 'research_ids', 'pictures'] } },
  fixes_made: { type: 'string', description: 'each finding: fixed (how), or rejected (why)' },
}, required: ['title', 'estimated_seconds', 'spoken_words', 'pages', 'fixes_made'] }

phase('Fix')
const fixed = await agent(`${CONTEXT}\n\nYour work folder: ${W}/fix (create it).\n\nWHAT FOUR FRESH TESTERS FOUND:\n${findings}\n\nYOUR TASK: read the
script file. Be skeptical of each finding: check it against the ledger and the script yourself, since a tester can be wrong.
Fix every confirmed must-fix and should-fix, and minor ones where the fix is cheap and safe; change nothing else. Keep the
page notes (research ids, pictures, on-screen words) in step with the words. Return the full script (every page) and, in
fixes_made, every finding with what you did and why. Write it to ${W}/fix/script.md too, in the same layout as the original.`,
  { label: 'fix', phase: 'Fix', schema: SCRIPT })

const VERIFY = { type: 'object', properties: {
  summary: { type: 'string' }, changed_sentences_checked: { type: 'number' }, findings: FINDINGS.properties.findings,
}, required: ['summary', 'changed_sentences_checked', 'findings'] }

phase('Verify')
const verified = await agent(`${CONTEXT}\n\nYour work folder: ${W}/verify (create it).\n\nA fixer has just changed the script. Before:
${A.script}. After: ${W}/fix/script.md. The fixer's notes:\n${fixed ? fixed.fixes_made : '(none: the fixer failed)'}\n\nYOUR TASK: compare the
narration page by page and list every changed sentence. Check each one afresh, as a skeptic: against its ledger entry, against
every rule above, and by ear. Also check that nothing was changed by accident, and that the page notes still match the words.
A finding only for a real problem; every factual error is a must-fix.`, { label: 'verify', phase: 'Verify', schema: VERIFY })

let last = null
if (verified && verified.findings.some((f) => f.severity !== 'minor')) {
  last = await agent(`${CONTEXT}\n\nYour work folder: ${W}/last-fix (create it).\n\nThe script: ${W}/fix/script.md. A re-checker found:
${JSON.stringify(verified.findings, null, 1)}\n\nCheck each against the ledger and the script yourself; fix the confirmed must-fix
and should-fix ones only, changing nothing else. Return the full script and, in fixes_made, every finding with what you did
and why. Write it to ${W}/last-fix/script.md too.`, { label: 'last fix', phase: 'Verify', schema: SCRIPT })
} else {
  log('the re-check found nothing above minor: no last fix')
}
return { viewer, tested: TESTS.map((t, i) => ({ key: t.key, ...(tested[i] || {}) })), fixed, verified, last,
  final_script: last ? `${W}/last-fix/script.md` : `${W}/fix/script.md` }
