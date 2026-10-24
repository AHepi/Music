export const meta = {
  name: 'composition-critique',
  description: 'Independent critics judge fal composition and camera results against the current 3D clip, then a skeptic checks the verdict',
  phases: [
    { title: 'Critique', detail: 'three critics, each a different lens' },
    { title: 'Verdict', detail: 'combine and adversarially check' },
  ],
}

const D = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/compose'
const FILES = `
Files (open each with the Read tool; they are images unless noted):
- ${D}/upload/00-empty-street.jpg : the empty painted street that every model was given as the background
- ${D}/results/props-sheet.jpg : the ten 3D props every model was given (handcart, coal sacks, rusty oil-drum brazier, notice on board, two dustbins, barrel, coal tub on rails, wooden pail, white kitchen chair, hurricane lantern)
- ${D}/results/clip29-strip.jpg : CURRENT CLIP made in our own 3D pipeline, two frames a second, 12 s (top row then bottom row, left to right). The user said of it: "It looks ok. The props look great. But there's no sense aesthetics with regards to their composition. The camera movement is a little odd too."
- ${D}/clip29/frame-4.jpg and ${D}/clip29/frame-9.jpg : full-size frames of the current clip (street shot, close shot)
- ${D}/results/nano-same-view.jpg : Nano Banana Pro, asked to place props in the same camera view
- ${D}/results/nano-free-camera.jpg : Nano Banana Pro, allowed to choose its own camera
- ${D}/results/flux-same-view.jpg : Flux 3 edit, same camera view
- ${D}/results/seedance-strip.jpg : Seedance 2.5 reference-to-video, 10 s draft at 480p, two frames a second (top row then bottom row). It is one continuous move, no cut.
- ${D}/results/seedance-three.jpg : Seedance first, middle and last frame side by side
- ${D}/results/seedance-middle.jpg : Seedance 4.2 s to 5.4 s at 8 frames a second (proves there is no cut)
Context: a tall 9:16 explainer film about the 1926 British coal lockout, in a painted, inked, illustrated style. The shot's job: show a pit village street at dusk on the day the lock-out notice goes up; end on the notice. No people. Do not spend money or call any generation service; only look at the files.`

const CRITIC = {
  type: 'object',
  properties: {
    ranking: { type: 'array', items: { type: 'object', properties: {
      name: { type: 'string' }, score_out_of_10: { type: 'number' }, strengths: { type: 'array', items: { type: 'string' } }, weaknesses: { type: 'array', items: { type: 'string' } } },
      required: ['name', 'score_out_of_10', 'strengths', 'weaknesses'] } },
    key_lessons: { type: 'array', items: { type: 'string' }, description: 'Concrete, specific lessons we can apply to our own 3D layout or camera' },
    recommendation: { type: 'string' },
  },
  required: ['ranking', 'key_lessons', 'recommendation'],
}

const LENSES = [
  { key: 'composition', prompt: `You are an art director for illustrated films. Judge COMPOSITION and AESTHETICS only: arrangement of props, foreground/middle/background depth, focal point, leading lines, balance, negative space, whether props look placed by a person with a reason (story clutter) or scattered like a catalogue, scale consistency, whether props match the painted style or look pasted. Rank these five: current clip, Nano same view, Nano own camera, Flux same view, Seedance (judge its best frames). Be blunt and specific with positions in the frame.` },
  { key: 'camera', prompt: `You are a cinematographer. Judge CAMERA MOVEMENT only: compare the current clip's move (strip) with Seedance's move. Describe each move precisely (start framing, path, speed changes, end framing, height, lens feel), what feels motivated vs odd, and why the user found the current move "a little odd". Also say what camera position and lens the two Nano Banana pictures imply, and whether either would be a better start or end frame. Give the current clip and Seedance a score; for the still pictures score them as possible key frames.` },
  { key: 'pipeline', prompt: `You are a technical director deciding how to USE these results. Judge fidelity and usability: does each keep the street from the background picture unchanged; does each keep the props' real look (compare against the props sheet: e.g. the brazier is a rusty oil drum, the chair is white, the notice board has a dark plank board and a roof strip); is the notice text readable and correct (it should be about pits closed and new terms, 1926; flag invented or garbled dates); period accuracy for a 1926 Welsh/English pit village; flaws (floating rails, fire outside the drum, props in the middle of the road). Then judge two routes: (A) use the best picture as a LAYOUT GUIDE and re-place our 3D props and camera in Blender to match, keeping our own pipeline; (B) use Seedance output directly as the shot, including upgrading the 480p draft to 1080p. Weigh control, consistency across many shots, text legibility, style match, cost and repeatability. Score each result for usability.` },
]

phase('Critique')
const critiques = await parallel(LENSES.map(l => () =>
  agent(`${l.prompt}\n${FILES}`, { label: `critic:${l.key}`, phase: 'Critique', schema: CRITIC })
    .then(r => r && ({ lens: l.key, ...r }))))
const got = critiques.filter(Boolean)
log(`${got.length} of ${LENSES.length} critics returned`)

phase('Verdict')
const VERDICT = {
  type: 'object',
  properties: {
    best_composition: { type: 'string' },
    best_camera: { type: 'string' },
    route: { type: 'string', description: 'A (layout guide for our 3D) or B (use Seedance directly) or a mix, with the reason' },
    specific_layout_plan: { type: 'array', items: { type: 'string' }, description: 'Prop by prop: where it goes in the street and why, for the winning layout' },
    specific_camera_plan: { type: 'string' },
    risks: { type: 'array', items: { type: 'string' } },
    claims_checked: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, holds: { type: 'boolean' }, note: { type: 'string' } }, required: ['claim', 'holds', 'note'] } },
  },
  required: ['best_composition', 'best_camera', 'route', 'specific_layout_plan', 'specific_camera_plan', 'risks', 'claims_checked'],
}
const verdict = await agent(`You are a skeptical senior reviewer. Three critics judged the same images. Open the images yourself and CHECK their factual claims (what is where in each picture, readable text, cuts, flaws). Reject any claim the images do not support. Then give one combined verdict: which result has the best composition, which camera move is best, which route to take (A: use as a layout guide for our own 3D props and camera; B: use Seedance output directly; or a mix), a prop-by-prop layout plan for the winner, a camera plan, and the risks.\n${FILES}\n\nCritics' reports (JSON):\n${JSON.stringify(got, null, 1)}`, { label: 'skeptic-verdict', phase: 'Verdict', schema: VERDICT })
return { critiques: got, verdict }
