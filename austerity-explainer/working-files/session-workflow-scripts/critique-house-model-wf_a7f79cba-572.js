export const meta = {
  name: 'critique-house-model',
  description: 'Two independent critics (model maker, film director) judge the redesigned card villa against the old plain house and list concrete improvements',
  phases: [{ title: 'Critique', detail: 'two critics with different lenses' }],
}
const S = '/home/user/work/chapter-2/stills'
const CONTEXT = `A narrated explainer film (1080 x 1920, cinematic card-model look) shows a small 3D card house twice on page 8: on a dark model table beside card factories at "things we can't make more of in a hurry" (about 188-190 s), and on a painted New Zealand suburban street (villas, picket fences) at "house prices rose about thirty percent in twelve months" (about 195-198 s), with a price tag climbing a post beside it. The owner said of the OLD house: "that 3d house is sparse in detail. It doesn't stand out as visually complete." It has just been redesigned as a card villa.
OLD house stills: ${S}/fix-p8-d/still-197.90.jpg and ${S}/fix-p8-d/sheet.jpg (look for the house). NEW house stills: ${S}/house-b/crops.jpg (close crops of both appearances), ${S}/house-b/still-189.20.jpg, ${S}/house-b/still-197.90.jpg, ${S}/house-a/sheet.jpg (an earlier pass with the windows hidden, now fixed). The model's code is the paperHouse function in /home/user/work/paper-pop-up-film-kit/paper-film/scenes/models.js. Look at the images with the Read tool. Do not edit any files.`
const SCHEMA = { type: 'object', properties: {
  complete_now: { type: 'boolean', description: 'does the new house read as visually complete and finished in the film?' },
  strengths: { type: 'array', items: { type: 'string' } },
  improvements: { type: 'array', items: { type: 'object', properties: {
    priority: { type: 'string', enum: ['high', 'medium', 'low'] }, what: { type: 'string' }, how: { type: 'string', description: 'concrete change in paperHouse (geometry, colour, size, position)' } }, required: ['priority', 'what', 'how'] } },
  verdict: { type: 'string' },
}, required: ['complete_now', 'strengths', 'improvements', 'verdict'] }
phase('Critique')
const lenses = [
  { key: 'model maker', prompt: `You are a professional architectural model maker who builds card and paper models. Judge the new house as a model: proportions, believable New Zealand villa details (weatherboards, bay window, gable, verandah, iron roof, chimney), craftsmanship, what still looks unfinished or wrong (gaps, floating parts, odd joins, scale), and what 2-5 details would most raise it.` },
  { key: 'film director', prompt: `You are a film director and information designer. Judge the new house as a shot: does it read instantly as "a house" at phone size, does it hold its own against the painted street and the card factories, does it look finished and in the same world as the rest, does the light make it read, and does it carry the idea (a home people want; prices up 30%)? List the 2-5 changes that would most improve it on screen.` },
]
const results = await parallel(lenses.map((l) => () => agent(`${CONTEXT}\n\n${l.prompt}`, { label: l.key, phase: 'Critique', schema: SCHEMA, effort: 'medium' }).then((r) => r && ({ lens: l.key, ...r }))))
return results.filter(Boolean)
