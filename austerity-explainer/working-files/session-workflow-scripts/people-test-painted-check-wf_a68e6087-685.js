export const meta = {
  name: 'people-test-painted-check',
  description: 'Fresh helpers check the painted people test: looks, painter faults, the figures, and whether the cut reads as people leaving',
  phases: [{ title: 'Check', detail: 'four independent fresh helpers' }],
}
const P = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint'
const K = '/home/user/Music/austerity-explainer/film-kit'
const F = `${K}/assets/models/inflation-chapter-2-newcomers/people-test`
const BASE = `
CONTEXT: an explainer film for a phone screen (1080 x 1920). Places are built in 3D in Blender, drawn once (the "plate"), repainted
by an image model (Flux) in the series' painted style, and the painting is shone back onto the 3D set in a film stage. This is the
"people test": can painted workers seen from behind work in this look? Files:
- the plate: ${F}/people-test-plate.jpg; the helper plate without people: ${F}/people-test-helper-plate.jpg
- the painting: ${F}/people-test-painting.png; the same painting with the people painted out: ${F}/people-test-painting-behind.jpg;
  the "men gone" state picture: ${F}/people-test-painting-state.png and its mask ${F}/people-test-painting-state-mask.png
- how they were made (prompts): ${F}/people-test-paintings.json
- the films (4 s, 30 frames a second): ${P}/people-test-painted.mp4 (painted men; at 2.0 s a time cut to the state picture) and
  ${P}/people-test-silhouettes.mp4 (dark figures standing over the painting without people); a weights still ${P}/weights/still-1.00.jpg
  (orange wears the painting, blue the set's own surface)
- the standard the user loved: ${K}/../experiments/"32 Notice corner - plate and painting.jpg" and "32 Notice corner - film frames at 1, 4.5 and 9.5 seconds.jpg"
Use ffmpeg to take frames (for example every frame from 1.8 to 2.2 s) and Python (PIL, numpy, opencv) to measure. Look at pictures at
full size and at phone size (about 360 pixels wide). Spend no money; change no file in the repository; work in your own scratch folder
${P}/check-NAME (create it). Report in plain everyday words, with measurements where you can, and a clear verdict.`

const VERDICT = { type: 'object', properties: {
  verdict: { type: 'string', enum: ['works', 'works with fixes', 'does not work'] },
  summary: { type: 'string' },
  problems: { type: 'array', items: { type: 'object', properties: {
    what: { type: 'string' }, where: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['what', 'where', 'fix', 'severity'] } },
}, required: ['verdict', 'summary', 'problems'] }

const CHECKS = [
  { name: 'looks', task: `You are a film designer who has not seen this before. Judge the painting and the painted film against the notice corner
standard: does it read as one hand-painted picture in the series' style, is the light and composition good, does anything read as a 3D
render, a toy or a model? Compare the painting with the plate: what did the painter improve, what did it lose?` },
  { name: 'painter-faults', task: `You are a careful checker of what an image model changed. Compare the painting with the plate shape by shape:
count everything that moved, was added, was lost or was garbled (lettering, lamps, windows, the gates, chimney, winding wheels, thin
parts like lamp posts and downpipes, the gutter, the steps), and anything the prompt forbade (flames, smoke, glows, puddles, new
shadows, new people). Then compare the people-out painting with the main painting: did it remove every person and their shadow, and
change nothing else? Measure where it differs. Check the state picture at the cut: any seam at the mask's edge, any ghost or shadow left,
anything that jumps besides the people.` },
  { name: 'figures', task: `You check the figures only. Count the figures in the painting against the plate (5 near men and 6 small walkers
40 to 60 m away). For each: same place, size and pose? any face, eyes, skin or detail added? does any look like a photograph, a shop
dummy, a statue or a toy? does the man meant to face the camera show a face? Then compare the two ways of showing people: painted
(people-test-painted.mp4) and dark silhouettes over the painting (people-test-silhouettes.mp4). Which reads better at phone size, and why?` },
  { name: 'first-viewer', task: `You are a first-time viewer. Do NOT read people-test-paintings.json or any notes first, and do not look at the
masks. Watch ${P}/people-test-painted.mp4 (take frames every 0.1 s and look at them in order at phone size), then say in plain words what
happens in it. Does the moment at 2 seconds read as time passing (the men have gone somewhere), or as a glitch or a mistake? Would you
notice anything odd? Then watch ${P}/people-test-silhouettes.mp4 the same way and say how the people look there.` },
]

phase('Check')
const results = await parallel(CHECKS.map((c) => () => agent(`${BASE.replace('check-NAME', 'check-' + c.name)}\n\nYOUR TASK: ${c.task}`,
  { label: `check:${c.name}`, phase: 'Check', schema: VERDICT })))
return Object.fromEntries(CHECKS.map((c, i) => [c.name, results[i]]))
