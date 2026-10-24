export const meta = {
  name: 'why-this-composition-works',
  description: 'Explain, with evidence, why the Nano Banana own-camera picture is well composed and why it is hard to vary; turn it into rules for our 3D shots',
  phases: [
    { title: 'Analyse', detail: 'five critics, each a different lens' },
    { title: 'Check', detail: 'a skeptic tests every claim against the picture and the measurements' },
    { title: 'Rules', detail: 'turn surviving reasons into plain rules for our own 3D shots' },
  ],
}

const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3'
const CONTEXT = `
THE PICTURE: ${S}/compose/results/nano-free-camera.jpg (open it with Read). A tall 9:16 frame for an explainer film about the 1926 British coal lockout, made by the Nano Banana Pro image model from (a) an empty painted pit-village street, ${S}/compose/upload/00-empty-street.jpg, and (b) ten 3D prop pictures, ${S}/compose/results/props-sheet.jpg. The model was told it could choose its own camera and which props to use.
The user (not a designer) says: "this image is good. I'm not sure why, though. Seat next to fire makes sense because fires are used to warm people that likely sat next to the fire at some point. Lamp on seat also makes sense since people use them to see in the dark. I don't understand why the composition balance works, though. It's genuinely hard to vary without taking something away aesthetically and narratively."

MEASUREMENTS already made (automatic; use them, but check them with your own eyes):
- ${S}/why/out/01 thirds grid and converging lines.jpg : white = lines at one third and two thirds of the width and height; yellow = long slanted straight lines found automatically (47); red circle = where those lines meet most densely; blue boxes = notice paper, drum, chair, lantern, pail, street lamp, pithead (boxes drawn by eye).
- ${S}/why/out/02 squint view - big light and dark areas.jpg : heavy blur, five grey levels (what you see when you squint).
- ${S}/why/out/03 warm light only.jpg : orange = clearly warm and bright pixels.
- ${S}/why/out/05 where the visual weight sits.jpg : bright = busy detail or strong light/dark; white cross = centre of weight; white line = middle of the frame.
- ${S}/why/out/04 mirror image.jpg : the picture flipped left to right.
- ${S}/why/out/measurements.json : numbers. Key ones: lines meet at 0.688 across, 0.486 down (0 = left/top, 1 = right/bottom), i.e. at the left edge of the notice board, at about the height of the notice's top lines; centre of weight 0.55 across, 0.51 down; weight left/right 43%/57%; top/middle/bottom thirds 28.5/40/31.5%; warm light is 2.3% of the picture, and 73% of it is in the right third, 23% in the middle third, 4% in the left third; notice paper brightness 0.61 against a picture average of 0.32 (fire 0.63 but only 0.3% of the area; notice paper 3.3%).
OUR OWN CURRENT CLIP for contrast (the user said its props look great but "there's no sense aesthetics with regards to their composition. The camera movement is a little odd too"): ${S}/compose/clip29/frame-4.jpg (street shot), ${S}/compose/clip29/frame-9.jpg (close shot), ${S}/compose/results/clip29-strip.jpg (two frames a second).
Do not spend money or call any generation service. Only look and reason. Be concrete: name positions in the frame. Plain words in the final text (the user is not a designer): if a design term is unavoidable, explain it in one plain sentence.`

const REASONS = {
  type: 'object',
  properties: {
    reasons: { type: 'array', items: { type: 'object', properties: {
      reason: { type: 'string', description: 'one plain sentence' },
      evidence: { type: 'string', description: 'where exactly in the picture or which measurement shows it' },
      picture_job: { type: 'string', description: 'what it does for the look' },
      story_job: { type: 'string', description: 'what it does for the story, or "none"' },
      confidence: { type: 'string', enum: ['high', 'medium', 'low'] } },
      required: ['reason', 'evidence', 'picture_job', 'story_job', 'confidence'] } },
    weak_spots: { type: 'array', items: { type: 'string' }, description: 'what is NOT good in this picture' },
  },
  required: ['reasons', 'weak_spots'],
}

const LENSES = [
  { key: 'lines', prompt: `Lens: LINES, SHAPES AND PLACEMENT. Where do the street's lines lead the eye? Where is the camera's eye height (where the lines meet sets the horizon) and what sits on it? Which things sit on the one-third lines? What shapes do the main objects make together (check any triangle or diagonal you claim really exists)? Where do things overlap and what does overlapping do? What frames the picture at its edges (lamp post, houses)? How do near, middle and far layers step back?` },
  { key: 'light', prompt: `Lens: LIGHT AND COLOUR. Using the squint, warm-light and weight views and your own eyes: where does the eye go first, second, third, and why (brightness, warmth, size, sharpness)? How do the three warm lights (street lamp, fire, lantern) relate to each other and to the notice? How does the cool blue rest of the picture help? Is the picture balanced left to right and top to bottom, and how is the heavy right side balanced by the left?` },
  { key: 'story', prompt: `Lens: STORY AND SET DRESSING. Build on the user's two observations (seat by the fire, lantern on the seat). For every object in the picture, why would a real person in May 1926 have left it exactly there? What do the objects together say happened (who was here, what they were doing, what has stopped)? How does the pithead in the distance relate to the notice in the foreground? What does the absence of people do? Flag anything that does not make story sense.` },
  { key: 'vary', prompt: `Lens: WHY IT IS HARD TO VARY. For each main element (notice board, drum with fire, chair, lantern, pail, street lamp, empty left half of the road, cart and sacks, coal tub, barrel, pithead and chimney, the camera's position and height), say what would be lost if it were removed, and what would be lost if it moved to a different place (name one realistic alternative place each). Then state the general principle that explains why this picture resists change. Also list the few changes that WOULD be safe or would improve it.` },
  { key: 'contrast', prompt: `Lens: WHAT OUR CLIP DOES DIFFERENTLY. Compare the picture with our current clip frames. For each difference in camera position, height, lens, where the lines lead, where the props stand, how props group or stand alone, where the light is, and what the eye lands on, say which one most explains the user's "no sense of aesthetics". Be specific to what you see in our frames.` },
]

phase('Analyse')
const analyses = await parallel(LENSES.map(l => () =>
  agent(`${l.prompt}\n${CONTEXT}`, { label: `analyse:${l.key}`, phase: 'Analyse', schema: REASONS }).then(r => r && ({ lens: l.key, ...r }))))
const got = analyses.filter(Boolean)
log(`${got.length} of ${LENSES.length} analyses returned`)

phase('Check')
const CHECKED = {
  type: 'object',
  properties: {
    kept: { type: 'array', items: { type: 'object', properties: {
      reason: { type: 'string' }, evidence: { type: 'string' }, picture_job: { type: 'string' }, story_job: { type: 'string' }, strength: { type: 'string', enum: ['main', 'supporting'] } },
      required: ['reason', 'evidence', 'picture_job', 'story_job', 'strength'] } },
    rejected: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, why_rejected: { type: 'string' } }, required: ['claim', 'why_rejected'] } },
    why_hard_to_vary: { type: 'string', description: 'the one general principle, in two or three plain sentences' },
    weak_spots: { type: 'array', items: { type: 'string' } },
  },
  required: ['kept', 'rejected', 'why_hard_to_vary', 'weak_spots'],
}
const checked = await agent(`You are a skeptical picture editor. Five critics gave reasons why this picture works. Open the picture and the measurement views yourself and test EVERY claim: is the thing really where they say, does the line really lead there, does the triangle really exist, is the brightness claim matched by the measurements? Reject anything unsupported, vague, or that would be true of almost any picture. Merge duplicates. Keep at most 9 reasons, marked main or supporting, ordered by how much they explain. Then give the one principle for why it is hard to vary, and the real weak spots.\n${CONTEXT}\n\nCritics' reports:\n${JSON.stringify(got, null, 1)}`, { label: 'skeptic', phase: 'Check', schema: CHECKED })

phase('Rules')
const RULES = {
  type: 'object',
  properties: {
    rules: { type: 'array', items: { type: 'object', properties: {
      rule: { type: 'string', description: 'an instruction a builder can follow when placing 3D props and the camera, in plain words' },
      how_to_check: { type: 'string', description: 'a concrete check on a test frame, ideally measurable' },
      from_reason: { type: 'string' } }, required: ['rule', 'how_to_check', 'from_reason'] } },
    rebuild_plan: { type: 'array', items: { type: 'string' }, description: 'steps to rebuild this exact picture in our Blender street with our real 3D props and camera, including camera height and where the street lines must meet' },
    camera_move_idea: { type: 'string', description: 'one short camera move that keeps these qualities through the whole move and ends on the notice' },
  },
  required: ['rules', 'rebuild_plan', 'camera_move_idea'],
}
const rules = await agent(`Turn these checked reasons into rules for building future shots in our own 3D pipeline (a Blender street with real 3D props, rendered and then repainted, with a camera that moves). Each rule must be something a builder can follow and check on a test frame. Also write a plan to rebuild this exact picture in our 3D street, and one camera move idea that keeps the qualities while moving.\n${CONTEXT}\n\nChecked reasons:\n${JSON.stringify(checked, null, 1)}`, { label: 'rules', phase: 'Rules', schema: RULES })
return { analyses: got, checked, rules }
