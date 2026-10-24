export const meta = {
  name: 'verify-shot-checker',
  description: 'Independent helpers try to break the new shot checker: code and maths, findings against the pictures, and plain-language wording',
  phases: [{ title: 'Verify', detail: 'three lenses in parallel' }],
}
const K = '/home/user/work/paper-pop-up-film-kit'
const C = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner'
const FILES = `
The tool (two parts):
- ${K}/paper-film/blender/shot_facts.py : runs inside Blender after a scene is dressed; draws every named group of props in a flat colour (ids.png, and each group alone in solo/NAME.png) and writes facts.json (camera, where the street's lines meet on screen, per-group distance, size, grounding).
- ${K}/paper-film/tools/check_shot.py : reads those plus an optional finished picture and writes report.md and marked.jpg: the composing rules (${'/home/user/Music/austerity-explainer/film-kit/07 Composing a shot.md'}), near-touches between props, the reference picture comparison and a camera match.
- Check file: ${K}/examples/notice-corner/shot-check.json
Outputs to examine (all already made; do not run Blender, it is busy drawing):
- The real composed frame: facts ${C}/facts-end/ (facts.json, ids.png, solo/), picture ${C}/composed-end.png, report ${C}/check-end/report.md and marked.jpg.
- Deliberately broken tests in ${C}/tests/: a-old-camera (the camera 0.42 m too high, 0.29 m too far right, turned 1 degree too little: the fault the user saw), b-pail-on-eaves (the pail lifted 5 m onto the roof edge), c-chair-touching (chair moved 0.17 m toward the board), d-pail-half-out (pail moved 0.75 m right, into the wall), e-camera-tilted (tilted up 3 degrees). Each has a facts folder and a NAME-report folder with report.md and marked.jpg.
- The reference picture: ${C}/../compose/results/nano-free-camera.jpg
You may run: python3 ${K}/paper-film/tools/check_shot.py --check ${K}/examples/notice-corner/shot-check.json --facts FOLDER [--picture PNG] --out SOME_NEW_FOLDER_IN ${C}/verify (make it). Do not change the tool's files; report only. Do not spend money.`
const SCHEMA = { type: 'object', properties: {
  verdict: { type: 'string' },
  problems: { type: 'array', items: { type: 'object', properties: {
    where: { type: 'string', description: 'file and function, or report item' }, problem: { type: 'string' }, evidence: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['wrong answer', 'misleading', 'minor'] } }, required: ['where', 'problem', 'evidence', 'fix', 'severity'] } },
}, required: ['verdict', 'problems'] }
phase('Verify')
const results = await parallel([
  () => agent(`You are a careful reviewer of measuring code. Read both files fully. Hunt for wrong answers: sign errors (left/right, up/down, nearer/further, the camera turn and its effect on where the lines meet), wrong unit conversions (pixels to metres at a distance; the camera-match projection; the vertical field of view versus the 9:16 frame), mask logic (visible versus alone, specks, overlaps hidden by a third thing, distance transforms), group matching by name (could a mesh land in the wrong group?), grounding rays, the main-rule spots, and anything that would crash on another shot (no picture, no reference, a group not visible, a group partly behind the camera). For each suspected bug, prove it: work a concrete number through by hand or run the checker on the existing facts folders. Report only real problems with evidence.${FILES}`, { label: 'verify:code', phase: 'Verify', schema: SCHEMA }),
  () => agent(`You check the checker's findings against the pictures. For the real composed frame and each broken test, open report.md, marked.jpg, ids.png (flat colours: each named prop its own colour, grey = the rest of the set, black = sky) and the picture, and judge every reported problem: is it real and correctly described (where, how big, which thing is in front, which way the fix goes)? Then look for real faults the checker missed (against the rules file), for example the long dark shadow across the bottom-left road in composed-end.png, a prop cut by the frame edge, or something that looks wrong but is not reported. Also check the broken tests caught what they should: a (camera too high, too far right, turned too little), b (pail on the roof edge), e (tilt); and explain what c and d actually did.${FILES}`, { label: 'verify:findings', phase: 'Verify', schema: SCHEMA }),
  () => agent(`You read the reports as the user would: a non-programmer who tests ideas by having an assistant write the code, and wants everyday language, no jargon or abbreviations, one word per thing (never a synonym), concrete numbers, and one clear thing to do first. Read every report.md in the outputs and the top comment of both tool files. Flag wording that is unclear, misleading, inconsistent (two names for one thing, e.g. "story props" and "story group", "subject" and "notice"), or a fix that a person could not act on (for example "raise it on screen"). Suggest exact replacement wording.${FILES}`, { label: 'verify:wording', phase: 'Verify', schema: SCHEMA }),
])
return results.filter(Boolean)
