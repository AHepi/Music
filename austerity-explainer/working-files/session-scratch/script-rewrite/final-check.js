export const meta = {
  name: 'rewrite-chapter-2-for-newcomers-final-check',
  description: 'Test the revised newcomer script of chapter 2 again with fresh testers (newcomers, facts, rules and voice), then make only the confirmed fixes',
  phases: [
    { title: 'Test', detail: 'fresh newcomers, facts, rules and voice' },
    { title: 'Fix', detail: 'confirmed fixes only' },
    { title: 'Verify', detail: 'every changed line checked again' },
  ],
}

const R = '/home/user/Music/austerity-explainer'
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/script-rewrite'
const T = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/uploads/pinker-toolkit/Steven-Pinker-Teaching-and-Writing-Toolkit'
const LEDGER = `${R}/chapter-2-inflation/18 Research - chapter 2 - what really causes inflation.md`
const SCRIPT_FILE = args.script
const VIEWER_FILE = args.viewer

const CONTEXT = `
A narrated explainer film for a tall phone screen about austerity, from Clara E. Mattei's The Capital Order (2022), narrated
by an AI voice, Malina (warm, steady New Zealand accent, about 140 words a minute). This is a newcomer version of chapter 2,
"what really causes inflation", written because people got lost in the first version. The script to check:
${SCRIPT_FILE}. The checked research ledger: ${LEDGER}. The project's rules: ${R}/01 Rules - voice, tone and writing style.md.
The Pinker teaching and writing toolkit the script follows: ${T}.
RULES THAT BIND EVERY WORD: facts only from the ledger, never stronger than its entry, qualifications kept; never "MMT" or
the money view's name ("economists who study how modern money works" if needed); Mattei's interpretations said as hers;
Naomi Klein in spirit only (urgency, direct questions, stakes first, who gains and who pays), never her wording, titles
or coined phrases; one plain name per thing; every unfamiliar term explained at first use or avoided; written for the
ear: "..." for pauses, numbers as said, no capitals for emphasis, no bracketed cues, /məˈteɪi/ for Mattei.
Do not edit anything outside your own work folder. Write in plain everyday words.`

const FINDINGS = { type: 'object', properties: {
  summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', properties: {
    page: { type: 'number' }, quote: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['page', 'quote', 'problem', 'fix', 'severity'] } },
  not_checked: { type: 'string' },
}, required: ['summary', 'findings', 'not_checked'] }

const TESTS = [
  { key: 'newcomers', ask: `You have never seen any version of this chapter or any earlier draft. Read ONLY ${VIEWER_FILE}
(what a viewer hears and sees, page by page); do not open the script file, its notes or any earlier draft.
Hear it once at speaking speed as four first-time viewers who have not seen chapter 1: a 15-year-old; a 70-year-old who
left school at 15; an adult whose first language isn't English; and a busy parent half-watching on a phone. For each,
answer the toolkit's comprehension probes: the main claim in their own words; what each term means; where they first
hesitated; how each example supports the point; and two new cases they could now reason about ("the government pays idle
builders to build homes" and "the government pays for new hospitals while every builder is already busy"). Also check:
can each of them say what "Spent on what?" and "who pays?" mean by the end? Report every point of confusion.` },
  { key: 'facts', ask: `Check every factual sentence against the ledger entry its page cites (open the ledger; read each
entry's claim, plain version, confidence, notes, the 12 October second fact check and the Traps). A finding for any claim
stronger, more precise or more certain than its entry; a dropped qualification; a changed date, place, number or unit; a
cause stated where the entry supports less; a general rule stated about "new money" where the entry speaks of spending; a
fact with no id or a wrong id; a Mattei interpretation not marked as hers; and any figure that goes out of date soon (New
Zealand prices 22 October 2026, the Reserve Bank 28 October, unemployment 4 November). Every factual error is a must-fix.
Give special care to the lines no second checker has read yet: page 2 "It also tries to stop prices going up too fast";
page 11 "partly from that, and partly from world prices, like oil" and "The biggest push came from homes... building new
ones, and rents" (is Stats NZ's "driven mainly by" about the whole 7.3% or only one group?); page 14 "Our Reserve Bank, and
others like it, see putting people out of work as unfortunate... but not the goal" (does the ledger support this for our
Reserve Bank?) and Mattei "argues that putting people out of work is the main goal" (against C2-H18's own words).` },
  { key: 'rules-and-voice', ask: `Check the rules and the voice: no "MMT"; /məˈteɪi/ for Mattei; no capitals for emphasis; no
bracketed cues; numbers written as said; "..." for pauses; one name per thing (list every synonym swap, and every word
used in two senses, such as "cost" or "pays"); every term explained at first use; no wording, title or coined phrase of
Naomi Klein's, or a near copy (including any "shock"); no stock phrases; nothing that trips the tongue. Does it still have
urgency and stakes, in the spirit of Naomi Klein, or has the revision made it flat? Count spoken words and estimate the
length at 140 words a minute plus about 0.6 seconds for each "...".` },
  { key: 'the-people-who-got-lost', ask: `The people who watched the recorded chapter 2 got lost because it moved too fast and used
terms an average person doesn't know. Read the recorded script (${R}/chapter-2-inflation/19 Script - chapter 2 - what really
causes inflation.md) and then this new one. Be a skeptic: does the new one actually fix both complaints, page by page? Where
is it still fast or dense (count new names, numbers, places and terms per page)? Where is a term still unexplained or
explained too late? Where has it gone too far the other way: padded, repetitive, patronising, or so long a phone viewer
would drop off (it is about 965 words, roughly 7 to 8 minutes)? Name specific lines that could go without losing the
teaching, and any place the urgency in the spirit of Naomi Klein has gone flat. Mark as must-fix only what would still lose
a newcomer.` },
]

phase('Test')
const tested = await parallel(TESTS.map((t) => () =>
  agent(`${CONTEXT}\n\nYour work folder: ${S}/work-final-${t.key} (create it).\n\n${t.ask}`,
    { label: `final:${t.key}`, phase: 'Test', schema: FINDINGS })))
const findings = TESTS.map((t, i) => `### ${t.key}\n${JSON.stringify(tested[i], null, 1)}`).join('\n\n')

const SCRIPT = { type: 'object', properties: {
  title: { type: 'string' }, how_it_teaches: { type: 'string' }, estimated_seconds: { type: 'number' }, spoken_words: { type: 'number' },
  pages: { type: 'array', items: { type: 'object', properties: {
    page: { type: 'number' }, name: { type: 'string' }, seconds: { type: 'number' }, text: { type: 'string' },
    research_ids: { type: 'array', items: { type: 'string' } }, terms_explained: { type: 'array', items: { type: 'string' } },
    pictures: { type: 'string' } }, required: ['page', 'name', 'seconds', 'text', 'research_ids', 'terms_explained', 'pictures'] } },
  fixes_made: { type: 'string', description: 'each finding: fixed (how), or rejected (why)' },
}, required: ['title', 'how_it_teaches', 'estimated_seconds', 'spoken_words', 'pages', 'fixes_made'] }

phase('Fix')
const fixed = await agent(`${CONTEXT}\n\nYour work folder: ${S}/work-final-fix (create it).\n\nWHAT THREE FRESH TESTERS FOUND:\n${findings}\n\nYOUR TASK: read the script file. Be skeptical of each finding: check it against the ledger and the script
yourself, since a tester can be wrong. Fix every confirmed must-fix and should-fix, and minor ones where the fix is cheap
and safe; change nothing else, and keep the chapter's length and voice. Return the full final script (every page, even the
unchanged ones) and, in fixes_made, every finding with what you did and why. Write it to ${S}/work-final-fix/final.md too.`,
  { label: 'final:fix', phase: 'Fix', schema: SCRIPT })
const VERIFY = { type: 'object', properties: {
  summary: { type: 'string' },
  changed_lines_checked: { type: 'number' },
  findings: FINDINGS.properties.findings,
}, required: ['summary', 'changed_lines_checked', 'findings'] }

phase('Verify')
const verified = await agent(`${CONTEXT}\n\nYour work folder: ${S}/work-final-verify (create it).\n\nA fixer has just changed the
script. The script before: ${SCRIPT_FILE}. The script after: ${S}/work-final-fix/final.md. The fixer's notes:\n${fixed ? fixed.fixes_made : '(none: the fixer failed)'}\n\nYOUR TASK:
compare the narration page by page and list every changed sentence. Check each changed sentence afresh, as a skeptic: against
its ledger entry (open the ledger), against every rule above, and by ear (does it trip the tongue, is anything newly
unexplained, does it break the one-name rule or repeat the rule in different words?). Also check that nothing the fixer
didn't mean to change was changed, and that the page notes (research ids, pictures, on-screen words) still match the words.
A finding only for a real problem; every factual error is a must-fix.`, { label: 'final:verify', phase: 'Verify', schema: VERIFY })

let last = null
if (verified && verified.findings.some((f) => f.severity === 'must-fix' || f.severity === 'should-fix')) {
  last = await agent(`${CONTEXT}\n\nYour work folder: ${S}/work-final-last (create it).\n\nThe script: ${S}/work-final-fix/final.md.
A verifier checked the latest changes and found:\n${JSON.stringify(verified.findings, null, 1)}\n\nCheck each against the ledger
and the script yourself; fix the confirmed must-fix and should-fix ones only, changing nothing else. Return the full script
and, in fixes_made, every finding with what you did and why. Write it to ${S}/work-final-last/final.md too.`,
    { label: 'final:last-fix', phase: 'Verify', schema: SCRIPT })
}
return { tested: TESTS.map((t, i) => ({ key: t.key, ...(tested[i] || {}) })), fixed, verified, last }
