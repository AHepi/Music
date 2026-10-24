export const meta = {
  name: 'station-test-critic',
  description: 'Independently judge the 3D petrol station test stills and captions',
  phases: [{ title: 'Critique', detail: 'two independent critics, medium effort' }],
}
const DIR = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/station'
const CONTEXT = `Context: a short animated film is made from AI paintings shown as "painted rooms" (each painting wrapped onto a depth surface, so a camera can move a little). Moving the camera in on a painted room bends anything near and upright (posts, canopy edges) because it is one stretched surface. This test (plan 23, first test) rebuilt the petrol station in painting 409 as simple 3D boxes that wear the painting projected from where it was painted: the two canopy posts, the kiosk, the canopy deck and the pump island. The red car and three pumps are 3D models from an earlier test (SAM 3D). The forecourt ground and the road are STILL the painted room in this test (not 3D yet); the queued cars, houses, sky are background. The painted room behind uses a version of the painting with the station painted out. Lighting rule: the painting's own painted light is kept exactly (no stage lamp on the painted room or the boxes); a see-through ground shows only shadows of the car and pumps.

Pass marks for this test:
A. From the painting's own viewpoint the 3D version must look like the painting (measured: mean pixel difference 4.08 of 255, 6.4% of pixels off by more than 12; per part: front post 1.7, rear post 4.8, kiosk 6.7, canopy 2.8, pump island 16.8).
B. On a 1.25x push toward the pump island, the posts and canopy edge must stay straight and the posts must slide cleanly in front of the kiosk, where the plain painted room bends them.

Files (all JPG, open them with the Read tool, it shows images):
- ${DIR}/r3/original/still-190.00.jpg : plain painted room, painting viewpoint (= the painting as the film shows it now)
- ${DIR}/r4/painting/still-190.00.jpg : 3D station, painting viewpoint
- ${DIR}/r5/original-push/still-190.00.jpg : plain painted room, 1.25x push
- ${DIR}/r5/push/still-190.00.jpg : 3D station, same 1.25x push
- ${DIR}/r4/push-side/still-190.00.jpg : 3D station, same push plus a small step sideways
- ${DIR}/r3/diff.jpg : difference picture between the first two (brighter = more different)
- ${DIR}/23 Test - 3D petrol station.jpg : the four-panel sheet that will be shown to the user, with captions.
Known issues already noted by the author: the bollard (U-shaped rail on the island end) looks flattened; a faint light strip on the canopy underside near the front post; a dark wedge at the top right of push-side; edge rims around the SAM pumps and the red car; ground and road still painted; queued cars not yet upright cut-outs; no 3D lamps yet.`

const SCHEMA = {
  type: 'object',
  properties: {
    verdict_A: { type: 'string', description: 'pass / partial / fail with one-sentence reason' },
    verdict_B: { type: 'string', description: 'pass / partial / fail with one-sentence reason' },
    new_problems: { type: 'array', items: { type: 'object', properties: {
      what: { type: 'string' }, where: { type: 'string', description: 'which file and roughly where in the picture' },
      severity: { type: 'string', enum: ['blocks the test', 'visible in film', 'minor'] },
      cheap_fix_idea: { type: 'string' } }, required: ['what', 'where', 'severity', 'cheap_fix_idea'] } },
    caption_problems: { type: 'array', items: { type: 'string' } },
    overall: { type: 'string', description: 'two or three plain sentences' },
  },
  required: ['verdict_A', 'verdict_B', 'new_problems', 'caption_problems', 'overall'],
}

phase('Critique')
const [visual, honesty] = await parallel([
  () => agent(`${CONTEXT}

Your job: an independent, sceptical visual critic. Open every picture listed. Judge pass marks A and B yourself by looking (zoom by reading the files; you can also use python with PIL in Bash to crop and enlarge regions into your own temporary files under ${DIR}/critic-visual/ and Read those). Look especially at: the near post's straightness top to bottom in the 3D push vs the plain push; whether the canopy front edge stays straight; whether anything doubles (a ghost copy of a post or pump visible behind the real one); seams where a box meets the painted room; colour or brightness jumps between the boxes and the room; floating objects; anything that would look wrong in a moving film. List NEW problems not in the known list (do not repeat known ones unless they are worse than described). Do not edit any project files.`, { label: 'critic:visual', phase: 'Critique', schema: SCHEMA, effort: 'medium' }),
  () => agent(`${CONTEXT}

Your job: an independent honesty checker. Open the four-panel sheet and the stills behind it. Check each caption says only what the pictures actually show and what was actually done (for example: the caption must not claim the ground or road is 3D; "posts and canopy stay straight" must be visibly true in panel 4; "posts and canopy bend" must be visibly true in panel 3; panel 2 must truly be the 3D version). Also read the scene code /home/user/work/paper-pop-up-film-kit/paper-film/scenes/station-proxies-test.js and its header note, and /home/user/work/paper-pop-up-film-kit/paper-film/scenes/painted-projection.js header and the shadowCatcher/projectedMaterial functions, and report any place where the plain-language notes at the top of those files say something the code does not do (caption_problems is fine for both). Then give your own verdicts for A and B. Do not edit any files.`, { label: 'critic:honesty', phase: 'Critique', schema: SCHEMA, effort: 'medium' }),
])
return { visual, honesty }
