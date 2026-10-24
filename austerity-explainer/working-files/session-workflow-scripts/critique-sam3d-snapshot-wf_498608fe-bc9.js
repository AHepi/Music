export const meta = {
  name: 'critique-sam3d-snapshot',
  description: 'Independent critique of the SAM 3D petrol station test before it is shown',
  phases: [{ title: 'Critique' }],
}
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/sam3d'
const K = '/home/user/work/paper-pop-up-film-kit'
const SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string' },
    works: { type: 'array', items: { type: 'string' } },
    problems: { type: 'array', items: { type: 'object', properties: { problem: { type: 'string' }, where: { type: 'string' }, severity: { type: 'string', enum: ['major', 'minor'] }, fix: { type: 'string' } }, required: ['problem', 'severity'] } },
    claims_checked: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'works', 'problems'],
}
const context = `Context: a test for a narrated explainer film made of painted pictures in 3D. Painting 409 (a 1973 petrol station at night, chapter 2 page 7) is normally shown as a "painted room with depth" (the painting pushed back by a depth map, so a camera can move a little). For this test, SAM 3D (fal-ai/sam-3/3d-objects, 2 US cents) turned five things in the painting (red car, teal car, three pumps) into separate 3D models with painted surfaces. They were placed using SAM's layout (fitted to the painting: outline match 0.95 car, 0.85 mean), the five objects were painted out of the background with Flux 3 edit (about 10 US cents, used only inside the object outlines), each model was slid along its line of sight until it stands on the painted ground, and each was tinted to the painted object's average colour (now within about 5 of 255).
Files: snapshot sheet "${S}/22 Snapshot - SAM 3D petrol station.jpg" (1 painting as in the film; 2 same view with 3D models; 3 camera pushed in), full-size stills ${S}/render-a/original/still-190.00.jpg, ${S}/render-f/painting/still-190.00.jpg, ${S}/render-g/push-in/still-190.00.jpg, larger moves ${S}/render-f/moved/still-190.00.jpg and ${S}/render-f/side/still-190.00.jpg; the clean background ${K}/assets/reliefs/sam-3d-test/409-petrol-station-clean.jpg; the scene code ${K}/paper-film/scenes/sam-3d-petrol-station-test.js; the layout ${K}/assets/models/sam-3d-test/layout.json. Look at pictures with the Read tool (crop with Python/Pillow to inspect details). Read-only: change no files.`
phase('Critique')
const [look, facts] = await parallel([
  () => agent(`${context}
You are a film director and painter. Judge the pictures honestly for the person deciding whether to use this method in their films: do the 3D models sit in the painting as if they belong (style, brushwork, light, shadows, contact with the ground, scale, perspective)? What gives them away? Is the camera-moved view (3) good enough to use in a film, and what tears or looks wrong (look at the canopy, kiosk, posts, background cars, the teal car's underside, the car's wheels and shadow)? Name the 3 most important fixes, each concrete. Be specific about where in the picture.`, { label: 'director and painter', phase: 'Critique', schema: SCHEMA, effort: 'medium' }),
  () => agent(`${context}
You are a skeptical technical checker. Verify the claims above that can be checked from the files: are the models where the painted objects were (overlay or compare picture 1 and 2 around each object; measure offsets in pixels)? Do the colours match (measure mean colour inside each object's mask, masks at ${K}/assets/reliefs/sam-3d-test/mask-1.png to mask-5.png at 1536x2736, scaled to the 1080x1920 stills)? Does anything poke through the ground or float (look at wheels and pump bases at full size)? Read the scene code and say whether its placement and colour handling would work for another painting, or what is hard-wired. Note anything in the snapshot sheet's captions that overstates the result. List each check you ran and its result.`, { label: 'technical checker', phase: 'Critique', schema: SCHEMA, effort: 'medium' }),
])
return { look, facts }
