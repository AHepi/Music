export const meta = {
  name: 'recheck-sam3d-snapshot',
  description: 'Fresh check that the SAM 3D test fixes worked and the snapshot captions are honest',
  phases: [{ title: 'Recheck' }],
}
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/sam3d'
const K = '/home/user/work/paper-pop-up-film-kit'
const SCHEMA = { type: 'object', properties: {
  fixed: { type: 'array', items: { type: 'string' } },
  still_wrong: { type: 'array', items: { type: 'object', properties: { problem: { type: 'string' }, severity: { type: 'string', enum: ['major', 'minor'] }, where: { type: 'string' } }, required: ['problem', 'severity'] } },
  captions_honest: { type: 'boolean' }, caption_note: { type: 'string' }, verdict: { type: 'string' } },
  required: ['fixed', 'still_wrong', 'captions_honest', 'verdict'] }
phase('Recheck')
const r = await agent(`A test put 3D models (from SAM 3D on fal) into a painting used in a narrated film: painting 409, a 1973 petrol station at night. An earlier critique found: the teal car misplaced, floating and pink-trimmed; one colour tint over each whole model turned chrome and headlights pale cyan and killed the headlight glow; a dark windscreen with no interior; models floating; a circular colour check; the painted background tearing when the camera moves; and captions that oversold the result. Fixes made since: the teal car is now left painted (not 3D); each model now wears the painting's own pixels projected from where it was painted, wherever that surface was visible in the painting, and only hidden sides use SAM's surface, tinted by comparing the two; the ground under each object is fitted from the forecourt around its base and the models stand on it (lowest points 0.01 to 0.03 units above); the colour/brightness handling now matches the stage's; the camera move was shortened.
Check with your own eyes and measurements (Read tool for pictures; Python with Pillow and numpy to crop and measure). Read-only: change nothing.
Pictures (1080x1920): original painting view ${S}/render-a/original/still-190.00.jpg; with 3D models, same view ${S}/render-m/painting/still-190.00.jpg; short push-in ${S}/render-m/small-push/still-190.00.jpg; the snapshot sheet "${S}/22 Snapshot - SAM 3D petrol station.jpg" with its captions. Object masks at 1536x2736: ${K}/assets/reliefs/sam-3d-test/mask-1.png (red car), mask-3/4/5.png (pumps).
Say which earlier problems are fixed, what is still wrong (with where, in pixels), and whether each caption is honest. Be strict and brief.`, { label: 'fix check', phase: 'Recheck', schema: SCHEMA, effort: 'medium' })
return r
