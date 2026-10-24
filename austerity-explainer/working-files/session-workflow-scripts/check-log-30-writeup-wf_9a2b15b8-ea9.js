export const meta = {
  name: 'check-log-30-writeup',
  description: 'Independent checkers verify the log 30 write-up and composing rules against the evidence and the user\'s language rules',
  phases: [{ title: 'Check', detail: 'facts and language, in parallel' }],
}
const R = '/home/user/Music/austerity-explainer'
const W = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921'
const FILES = `
Write-up to check:
- ${R}/project-notes/Austerity explainer - project story.md : log entry 30 (search for "30. **Letting fal"), the first bullet of "Where things stand", the new word list rows (Composition, Where the lines meet, Brightest parts, Nano Banana Pro, Seedance, Draft), the "Spent so far" line and "Next step".
- ${R}/film-kit/07 Composing a shot.md : twelve rules for composing a shot.
- ${R}/project-notes/Lessons.md lessons 98 to 104; ${R}/project-notes/Decisions.md items 35 and 36; ${R}/project-notes/Status.md section "Arranging test and why it works".
Evidence:
- ${W}/tasks/wcpie5an4.output : JSON, first critique (rankings, lessons, a skeptic's verdict with claims_checked).
- ${W}/tasks/wg6x6l6tf.output : JSON, second critique (why the picture works: kept and rejected reasons, rules, rebuild plan).
- ${R}/experiments/30 Why it works - measurements/measurements.json and its "clip 29 at 4 seconds" folder; the pictures in ${R}/experiments/ whose names start with "30".
Do not change any file; report only. Do not spend money or call generation services.`
const SCHEMA = { type: 'object', properties: { problems: { type: 'array', items: { type: 'object', properties: {
  file: { type: 'string' }, quote: { type: 'string', description: 'the exact words at fault' }, problem: { type: 'string' }, fix: { type: 'string', description: 'exact replacement words' }, severity: { type: 'string', enum: ['wrong', 'misleading', 'minor'] } },
  required: ['file', 'quote', 'problem', 'fix', 'severity'] } } }, required: ['problems'] }
phase('Check')
const [facts, language] = await parallel([
  () => agent(`You are a fact checker. Check every number and factual claim in the write-up against the evidence: percentages, scores, costs (Nano Banana Pro US$0.15 per picture x2; Flux 3 edit US$0.024 per megapixel, output 1536x2736 = 4.2 MP plus 14.7 MP of input pictures if inputs count; Seedance 2.5 US$0.0214 per 1000 tokens, tokens = width x height x 24 fps x 10 s / 1024 at 480x854), positions, which model did what, what the critics actually concluded, and what was rejected. Flag claims stated more strongly than the evidence allows, claims the evidence contradicts, and important evidence-backed points that are missing or misrepresented. Open the pictures to confirm visual claims.\n${FILES}`, { label: 'check:facts', phase: 'Check', schema: SCHEMA }),
  () => agent(`You check writing against the user's rules. The user is not a programmer and wants: everyday language; no jargon, abbreviations or codes (an unavoidable technical word explained in one plain sentence first); one word per thing, never a synonym swapped in (e.g. if the text says "the notice" it should not also call it "the poster"; "the camera" not also "the lens" for the same thing; "props" consistently); no capitals for emphasis; never the word "MMT"; no portraits of real people; Mattei's interpretations marked as hers; files named with a two-digit number and plain words, never "final" or "v2". Check the write-up files for breaches, including in the new rules file and lessons. Also flag sentences a non-designer would not understand.\n${FILES}`, { label: 'check:language', phase: 'Check', schema: SCHEMA }),
])
return { facts, language }
