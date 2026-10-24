export const meta = {
  name: 'critique-notice-corner-still',
  description: 'Independent critics check the rebuilt notice corner frame against the liked picture, the composing rules, history and the coming slide; a skeptic merges',
  phases: [
    { title: 'Critique', detail: 'three critics, different lenses' },
    { title: 'Merge', detail: 'skeptic checks claims and ranks fixes' },
  ],
}
const C = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner'
const R = '/home/user/Music/austerity-explainer'
const CONTEXT = `
We are rebuilding, in our own 3D pit village street (Blender), the composition the user liked: ${C}/../compose/results/nano-free-camera.jpg (made by an image model; its notice text is garbled, it is only a guide). Our rebuilt frame, a plain 3D render BEFORE it is repainted in the painted style: ${C}/composed-end.png (1080 x 1920). Side by side with the liked picture's street lines drawn on both: ${C}/compare-composed.jpg. Measurements of our frame: ${C}/measure-composed/ (pictures 01 to 05 and "06 measurements.json"). The rules we compose by: ${R}/film-kit/07 Composing a shot.md (read it).
The user's words on an earlier attempt: "The camera angle is wrong as well. The lines don't converge the same way." We then matched the camera to the liked picture by lining up its winding wheels, chimney, gate, left roofline and kerbs with ours: camera on the right pavement, eye 1.81 m above the pavement under it, level, turned 6.9 degrees left, vertical lens angle 60 degrees. The user then said of the liked picture's lines "You were right here".
What happens next: this frame will be repainted in the series' painted style by an image model (Flux), and a second painting made with the near props (drum, chair, lantern, pail, notice board) painted out. The film then slides the camera 1.5 m straight toward the notice, never turning, ending on this exact frame, and holds it with the titles LOCKED OUT / FROM 1 MAY 1926 top left in the dim sky. The drum's flames, sparks and smoke and the lantern's flicker are drawn live in the film, not in the paintings. Story: Britain, 1 May 1926, the first day of the miners' lockout; no people.
Props near the camera (Blender metres; x across the street, y up it; kerb face x = 2.5, kerb top to 2.68, house fronts x = 4.15; the camera ends at x 2.96, y 17.85): notice board (true size 0.88 x 1.18 m, bottom 0.6 m above the pavement) at (3.40, 22.25); drum (0.59 x 0.86 m) at (2.81, 22.0); kitchen chair (scale 1.05) at (3.34, 21.75); lantern (scale 1.4) on its seat; pail at (3.36, 21.15); gas lamp post (3.87 m) at (3.25, 23.0); handcart with coal sacks on the left kerb at (-2.0, 30.5), more sacks against the left houses. Lights: the fire's light just over the drum's rim; the lamp post's light (dim, 40 W) at its glass; the street's own lamp behind the camera turned down.
Do not spend money or call any generation service. Look at the files; be concrete: name places in the frame (fractions across and down) and, where you can, give the change in metres.`
const SCHEMA = { type: 'object', properties: {
  verdict: { type: 'string', description: 'one paragraph' },
  faults: { type: 'array', items: { type: 'object', properties: {
    fault: { type: 'string' }, where: { type: 'string' }, why_it_matters: { type: 'string' }, fix: { type: 'string', description: 'a concrete change, in metres or settings where possible' },
    severity: { type: 'string', enum: ['must fix before painting', 'fix if cheap', 'leave'] } }, required: ['fault', 'where', 'why_it_matters', 'fix', 'severity'] } },
}, required: ['verdict', 'faults'] }
const LENSES = [
  { key: 'composition', prompt: 'Lens: COMPOSITION against the liked picture and the rules in 07 Composing a shot. Do the street lines now converge the way the liked picture\'s do (the user\'s complaint)? Check the main rule and rules 1 to 12 one by one on our frame (lines meet beside the notice; the brightest parts on the notice; the biggest near props; warm light; touching group; no edges that just touch; nothing big and dark bottom left; titles space top left; right-edge room). Judge the long dark shadow of the drum across the bottom-left road. Say what is still different from the liked picture and whether each difference matters.' },
  { key: 'story', prompt: 'Lens: STORY AND HISTORY. Does every prop make sense on 1 May 1926 in a British pit village street during the lockout, and does its placement make sense (would a person have put it there)? Check the notice board on posts on the pavement, the lamp post right behind it, the chair with a lantern on the seat by a fire in a drum, the pail, the handcart with coal sacks (coal was scarce in the lockout), the colliery chimney, the lit windows. Flag anything anachronistic or implausible, and anything that weakens the story the user liked ("someone sat here by the fire and has just stepped away").' },
  { key: 'slide', prompt: 'Lens: WHAT WILL BREAK when this frame is repainted and the camera slides 1.5 m straight toward the notice (starting further back, ending here). Look for: thin or fiddly shapes the painter will smear (chair slats, lamp post, cart wheels); places where the slide uncovers surfaces hidden from the start position (behind the drum, chair, pail, lamp post, board posts); props the "behind" painting must paint out and what it must continue behind them; anything at the frame edges that might leave the painted area; the shadow wedge bottom left; the pale board frame competing with the notice; the white lamp glass. Say what to change in the 3D scene now (cheap, before the paid repaint) and what to ask the painter.' },
]
phase('Critique')
const critiques = (await parallel(LENSES.map(l => () => agent(`${l.prompt}\n${CONTEXT}`, { label: `critic:${l.key}`, phase: 'Critique', schema: SCHEMA }).then(r => r && ({ lens: l.key, ...r }))))).filter(Boolean)
phase('Merge')
const merged = await agent(`You are a skeptical senior reviewer. Open the pictures yourself and check every fault the critics claim: is it really there, where they say? Reject what the files do not support. Merge duplicates. Then rank the surviving fixes: what must change in the 3D scene before the paid repaint, what to ask the painter, and what to leave. Keep fixes concrete (metres, settings, words for the painter).\n${CONTEXT}\n\nCritics:\n${JSON.stringify(critiques, null, 1)}`, { label: 'skeptic', phase: 'Merge', schema: { type: 'object', properties: {
  convergence_matches: { type: 'boolean' }, convergence_note: { type: 'string' },
  fix_in_3d_now: { type: 'array', items: { type: 'string' } }, ask_the_painter: { type: 'array', items: { type: 'string' } }, leave: { type: 'array', items: { type: 'string' } },
  rejected_claims: { type: 'array', items: { type: 'string' } } }, required: ['convergence_matches', 'convergence_note', 'fix_in_3d_now', 'ask_the_painter', 'leave', 'rejected_claims'] } })
return { critiques, merged }
