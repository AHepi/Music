export const meta = {
  name: 'rewrite-chapter-2-for-newcomers-finish',
  description: 'Judge three newcomer drafts of chapter 2, combine the best, test it on fresh newcomer readers and against the facts and rules, then revise',
  phases: [
    { title: 'Judge', detail: 'three judges, each a different lens' },
    { title: 'Combine', detail: 'the best draft with the best of the others' },
    { title: 'Test', detail: 'fresh newcomers, facts, rules and voice' },
    { title: 'Revise', detail: 'apply what the tests confirm' },
  ],
}

const R = '/home/user/Music/austerity-explainer'
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/script-rewrite'
const T = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/uploads/pinker-toolkit/Steven-Pinker-Teaching-and-Writing-Toolkit'
const LEDGER = `${R}/chapter-2-inflation/18 Research - chapter 2 - what really causes inflation.md`

const CONTEXT = `
A narrated explainer film for a tall phone screen about austerity, from Clara E. Mattei's The Capital Order (2022), narrated
by an AI voice, Malina (warm, steady New Zealand accent, about 140 words a minute). Chapter 2 asks "won't creating new
money just cause inflation?". People got lost in the current version (${R}/chapter-2-inflation/19 Script - chapter 2 - what really causes inflation.md):
it moves too fast and uses terms an ordinary viewer doesn't know. Three new drafts for newcomers are in ${S}/drafts.json
(and readable in ${S}/drafts.md); the helpers' audit, teaching plan, voice brief and fact choice are in ${S}/understanding.md.
The checked research ledger is ${LEDGER}. The project's rules: ${R}/01 Rules - voice, tone and writing style.md and
${R}/06 House rules for the project.md. The user's Pinker teaching and writing toolkit: ${T}.

RULES THAT BIND EVERY WORD: facts only from the ledger, never stronger than its entry, qualifications kept; never "MMT" or
the money view's name ("economists who study how modern money works" if needed); Mattei's interpretations said as hers;
Naomi Klein in spirit only (urgency, direct questions, stakes first, who gains and who pays), never her wording, titles
or coined phrases; Pinker's principles, never his voice; one plain name per thing, no synonyms; every unfamiliar term
explained in plain words at first use or avoided; written for the ear: "..." for pauses, numbers as said, no capitals for
emphasis, no bracketed cues, /məˈteɪi/ for Mattei and /rʊə/ for Ruhr.
Do not edit anything outside your own work folder. Write in plain everyday words.`

const VERDICT = { type: 'object', properties: {
  summary: { type: 'string' },
  scores: { type: 'array', items: { type: 'object', properties: { draft: { type: 'string' }, score: { type: 'number', description: '0 to 10' }, strengths: { type: 'string' }, faults: { type: 'string' } }, required: ['draft', 'score', 'strengths', 'faults'] } },
  best_parts_to_keep: { type: 'string', description: 'specific passages or devices from any draft worth keeping, with page numbers' },
  must_fix: { type: 'string' },
}, required: ['summary', 'scores', 'best_parts_to_keep', 'must_fix'] }

const LENSES = [
  { key: 'newcomers', ask: `Lens: WILL A NEWCOMER FOLLOW IT? Hear each draft once at speaking speed as three first-time viewers
(a 17-year-old student, a 60-year-old retired builder who left school at 16, an adult whose first language isn't English),
who have NOT seen chapter 1. For each: say back the main claim; name the first place they get lost; list any term left
unexplained; count new places, years, numbers and terms per 30 seconds; check each example's lesson is said out loud and
each comparison is mapped. Use the toolkit's reader-comprehension probes. Score each draft 0 to 10 on whether a newcomer
ends up able to explain the idea and apply it to a new case.` },
  { key: 'voice-and-sound', ask: `Lens: VOICE AND SOUND. Read each draft aloud as Malina would. Is it urgent and alive in
the spirit of Naomi Klein (stakes up front, who gains and who pays, concrete scenes and people, sharp questions), without
any of her wording or coined phrases, and without preaching or shouting? Does it trip the tongue anywhere (number strings,
stacked clauses, sound-alike words, stress in the wrong place)? Any stock phrases, generic uplift or empty symmetry (the
toolkit's anti-banality test)? Does it respect the pause, number and no-capitals rules? Score 0 to 10.` },
  { key: 'truth-and-rules', ask: `Lens: TRUTH AND RULES. Check every factual sentence in each draft against its ledger
entry (open the ledger): any claim stronger, more precise or more certain than the ledger allows, a qualification dropped,
a date, place or number changed, a cause asserted where the ledger shows only a correlation, a fact with no ledger id?
Any Mattei interpretation said as plain fact? Any "MMT"? Any synonym swapped for a named thing? Any figure that goes out
of date soon (New Zealand prices 22 October 2026, the Reserve Bank 28 October, unemployment 4 November)? Score 0 to 10;
any factual error is a must-fix.` },
]

phase('Judge')
const judged = await parallel(LENSES.map((l) => () =>
  agent(`${CONTEXT}\n\nYour work folder: ${S}/work-judge-${l.key} (create it).\n\n${l.ask}`,
    { label: `judge:${l.key}`, phase: 'Judge', schema: VERDICT })))
const verdicts = LENSES.map((l, i) => `### ${l.key}\n${JSON.stringify(judged[i], null, 1)}`).join('\n\n')

const SCRIPT = { type: 'object', properties: {
  title: { type: 'string' },
  how_it_teaches: { type: 'string', description: 'the takeaway sentence, the model, the cases, the recaps, and what was cut or deferred' },
  estimated_seconds: { type: 'number' },
  spoken_words: { type: 'number' },
  pages: { type: 'array', items: { type: 'object', properties: {
    page: { type: 'number' }, name: { type: 'string' }, seconds: { type: 'number' }, text: { type: 'string' },
    research_ids: { type: 'array', items: { type: 'string' } }, terms_explained: { type: 'array', items: { type: 'string' } },
    pictures: { type: 'string' } }, required: ['page', 'name', 'seconds', 'text', 'research_ids', 'terms_explained', 'pictures'] } },
  changes_from_old: { type: 'string' },
}, required: ['title', 'how_it_teaches', 'estimated_seconds', 'spoken_words', 'pages', 'changes_from_old'] }

phase('Combine')
const combined = await agent(`${CONTEXT}\n\nYour work folder: ${S}/work-combine (create it).\n\nThree judges scored the drafts:\n${verdicts}\n\nYOUR TASK: write the
final newcomer script. Start from the best-scoring draft overall (weigh newcomer understanding first, then truth, then
voice), graft in the specific best parts the judges named from the others, and fix every must-fix. Keep it about 5 to 6
and a half minutes (roughly 650 to 850 spoken words), pages of 20 to 40 seconds with one idea each, every fact tied to its
ledger id, every term explained at first use. Read it aloud in your head as Malina and fix anything that trips. Write it
to ${S}/work-combine/combined.md as well.`, { label: 'combine', phase: 'Combine', schema: SCRIPT })

const FINDINGS = { type: 'object', properties: {
  summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', properties: {
    page: { type: 'number' }, quote: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['page', 'quote', 'problem', 'fix', 'severity'] } },
  not_checked: { type: 'string' },
}, required: ['summary', 'findings', 'not_checked'] }

const TESTS = [
  { key: 'fresh-newcomers', ask: `You have never seen any earlier version of this chapter. Hear this script once, at speaking
speed, as three first-time viewers (a 17-year-old student, a 60-year-old retired builder who left school at 16, an adult
whose first language isn't English) who have not seen chapter 1. For each, answer the toolkit's comprehension probes: the
main claim in their own words; what each term means; where they first hesitated or would have needed to hear it again;
how each example supports the point; and one new case they could now reason about (for example: "the government pays
for new hospitals while builders are already flat out; what happens to prices?"). Report every point of confusion as a
finding. Do not open the old script or the drafts.` },
  { key: 'facts', ask: `Check every factual sentence against the ledger entry its page cites (open the ledger and read the
entry, its plain version, its confidence and its notes). A finding for: any claim stronger, more precise or more certain
than the entry; a dropped qualification; a changed date, place, number or unit; a cause stated where the entry supports
less; a fact with no ledger id; a wrong id; a Mattei interpretation not marked as hers; and any figure that goes out of date
soon. Every factual error is a must-fix.` },
  { key: 'rules-and-voice', ask: `Check the rules and the voice: no "MMT"; Mattei and Ruhr written /məˈteɪi/ and /rʊə/; no
capitals for emphasis; no bracketed cues; numbers written as said; "..." used for pauses; one name per thing (list any
synonym swap); every term explained at first use; no wording, title or coined phrase of Naomi Klein's (or a near copy);
no Pinker mannerisms; no stock phrases or generic uplift; nothing that would trip Malina's tongue. Count spoken words and
estimate the length at 140 words a minute plus about 0.6 seconds for each "...".` },
]

phase('Test')
const tested = await parallel(TESTS.map((t) => () =>
  agent(`${CONTEXT}\n\nYour work folder: ${S}/work-test-${t.key} (create it).\n\nTHE SCRIPT TO TEST (also in ${S}/work-combine/combined.md):\n${JSON.stringify(combined, null, 1)}\n\n${t.ask}`,
    { label: `test:${t.key}`, phase: 'Test', schema: FINDINGS })))
const findings = TESTS.map((t, i) => `### ${t.key}\n${JSON.stringify(tested[i], null, 1)}`).join('\n\n')

phase('Revise')
const final = await agent(`${CONTEXT}\n\nYour work folder: ${S}/work-revise (create it).\n\nTHE SCRIPT:\n${JSON.stringify(combined, null, 1)}\n\nWHAT THREE FRESH TESTERS FOUND:\n${findings}\n\nYOUR TASK: be skeptical of each finding (check it against the ledger and
the script yourself; a tester can be wrong). Fix every confirmed must-fix and should-fix, and minor ones where the fix is
cheap and safe. Change nothing else. Return the final script, and in changes_from_old list both what changed from the old
chapter 2 and, separately, which test findings you fixed, which you rejected and why. Write it to ${S}/work-revise/final.md as well.`,
  { label: 'revise', phase: 'Revise', schema: SCRIPT })

return { judged: LENSES.map((l, i) => ({ key: l.key, ...(judged[i] || {}) })), combined, tested: TESTS.map((t, i) => ({ key: t.key, ...(tested[i] || {}) })), final }
