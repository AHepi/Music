export const meta = {
  name: 'motion-check-notice-corner',
  description: 'Two helpers check the filmed notice-corner clip frame by frame and as a viewer; a skeptic verifies',
  phases: [
    { title: 'Watch', detail: 'a motion checker and a viewer' },
    { title: 'Verify', detail: 'a skeptic checks every finding' },
  ],
}
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3'
const K = '/home/user/work/paper-pop-up-film-kit'
const CONTEXT = `
You are checking a finished 13-second film clip for phones (1080 x 1920, 30 frames a second, music only):
${S}/32 Test - notice corner slide.mp4
It shows a pit village street at dusk on 1 May 1926, the first day of the British miners' lockout. The camera slides
1.5 m toward a notice on a timber board ("PITS WILL BE CLOSED ... NEW TERMS") over 0.3 to 8.5 s, without turning, then
holds; titles: BRITAIN 1926 (1 to 5 s), LOCKED OUT / FROM 1 MAY 1926 (8.5 to 12 s); fade in over the first second and
out over the last. How it is made: the street was built in 3D in Blender, drawn once from where the slide starts (the
plate), repainted by an image model, and the painting is shone back onto the same 3D shapes from that spot. Round the near
props (the drum, chair, lantern, pail, board, corner gas lamp) a second painting with those props painted out takes over
once the camera moves, so the road and walls they hid show. The notice paper, the board and its posts and the colliery
sign keep their own sharp 3D surfaces, lit by the film page's own lights (including a warm light under the notice).
Live on top: the drum's flames, sparks and smoke, the lantern's flicker, two thin chimney smokes, soft shadows under the
near props faded in as the camera moves. The page: ${K}/paper-film/scenes/notice-corner.js.
A frame-to-frame scan found no jumps (largest change 3.67 on a 0-255 scale, in the fade-out).
Extract frames yourself with ffmpeg (for example every frame from 0 to 2 s, every 5th frame after) into your own work
folder, and look at them at full size and zoomed in. Do not edit anything outside your work folder; spend no money.
Write in plain everyday words, with places as fractions of the frame (0 across = left edge, 0 down = top) and times in
seconds. Report only what you actually saw or measured; say what you could not check.`
const FINDINGS = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      title: { type: 'string' }, when: { type: 'string' }, where: { type: 'string' }, what: { type: 'string' },
      fix: { type: 'string' }, severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } },
      required: ['title', 'when', 'where', 'what', 'fix', 'severity'] } },
    not_checked: { type: 'string' },
  },
  required: ['summary', 'findings', 'not_checked'],
}
const WATCHERS = [
  { key: 'motion', angle: `Your angle: faults that only show in motion. Look for: anything appearing, vanishing or blinking (the switch to the
props-removed painting round the near props in the first second; contact shadows fading in); painted outlines or
ghost copies of props left on the road or walls as the camera moves; edges of the sharp notice board not matching the
painted surroundings; the painting smearing or stretching at the frame's edges or anywhere the camera uncovers
something; the flames, sparks and smoke looking wrong (a stiff sheet, a neat row, floating off the drum); the camera
turning (where the street's lines meet should stay put on screen while near things grow); flicker; the notice's small
print shimmering. Compare frames 0.3 s apart through the slide.` },
  { key: 'viewer', angle: `Your angle: a viewer on a phone. Watch it as a whole, then frame by frame at the start, middle and end. Does the
eye go to the notice? Is the story clear (the pits closed, someone kept watch by the fire and stepped away)? Can the
titles and the notice's big words be read at phone size, and are they ever on top of something busy? Is the music's
start and end smooth (listen by measuring the sound's loudness over time with ffmpeg, e.g. the ebur128 filter)?
Does anything look out of place for 1926, distracting, or unfinished? Is the pace right for 13 seconds?` },
]
phase('Watch')
const results = await parallel(WATCHERS.map((w) => () =>
  agent(`${CONTEXT}\n\nYour work folder: ${S}/corner/motion-check/work-${w.key} (create it).\n\n${w.angle}\n\nReturn your findings, worst first.`,
    { label: `watch:${w.key}`, phase: 'Watch', schema: FINDINGS })))
const got = results.map((r, i) => r ? { watcher: WATCHERS[i].key, ...r } : null).filter(Boolean)
phase('Verify')
const VERDICT = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: 'plain words: can this clip be sent to the user as it is; what, if anything, must be fixed first' },
    confirmed: { type: 'array', items: { type: 'object', properties: {
      title: { type: 'string' }, from: { type: 'string' }, evidence: { type: 'string' }, fix: { type: 'string' },
      severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['title', 'from', 'evidence', 'fix', 'severity'] } },
    rejected: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, why: { type: 'string' } }, required: ['title', 'why'] } },
    not_checked: { type: 'string' },
  },
  required: ['summary', 'confirmed', 'rejected', 'not_checked'],
}
const verdict = await agent(`${CONTEXT}\n\nYour work folder: ${S}/corner/motion-check/work-skeptic (create it).\n\nYou are the skeptic. Two helpers watched the clip;
their findings are below. Check EVERY finding yourself in the frames (extract the exact frames they name). Reject what
does not hold up. Rank what is confirmed: must-fix before sending the clip, should-fix, minor. A must-fix is something a
viewer would notice on a phone.\n\nFindings:\n${JSON.stringify(got, null, 1)}`, { label: 'skeptic', phase: 'Verify', schema: VERDICT })
return { watchers: got, verdict }
