export const meta = {
  name: 'critique-notice-corner-still',
  description: 'Three critics judge the finished notice-corner still from different angles; a skeptic verifies their findings and writes the painter instructions',
  phases: [
    { title: 'Critique', detail: 'three critics, each a different angle' },
    { title: 'Verify', detail: 'a skeptic measures and filters every finding' },
  ],
}

const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner'
const K = '/home/user/work/paper-pop-up-film-kit'
const CONTEXT = `
You are reviewing one finished still of a 3D scene built in Blender for a short film: a pit village street at dusk on
1 May 1926, the first day of the British miners' lockout. A notice ("PITS WILL BE CLOSED ... NEW TERMS") is pasted on a
timber board on two posts; in front of it, a rusty brazier drum with a low coal fire, an empty kitchen chair with a lit
hurricane lantern on its seat, and a wooden pail. A gas lamp on a post stands behind the board. Far up the street on the
left: a handcart, coal sacks, dustbins, and street lamps. The colliery's gates are shut at the top of the street.
The frame is tall (1080 x 1920, for phones). Next, this frame is repainted by an image model (Flux 3 edit) in a painted
documentary-illustration style, copying the 3D picture's shapes and its light and dark; then the film shines that
painting back onto the 3D set and slides the camera 1.5 m toward the notice without turning. In the film, the notice
paper, the board's timber and its two posts keep their OWN 3D surfaces (not the painting), lit by the film page's own
lights (paper-film/scenes/notice-corner.js), and live flames, sparks and smoke are added on top of the drum.

Files (read them; do not edit anything outside your own work folder):
- The finished still: ${S}/final/composed-end-5.png
- The still before this round of fixes: ${S}/final/composed-end-4.png
- The picture the user liked, which this rebuilds: /home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg
- The automatic shot checker's report on the finished still: ${S}/final/report5/report.md (and marked.jpg beside it).
  It passes 32 of 38 checks. Open: the left half holds 36% of the picture's weight (aim 40-48%); the notice's bottom is
  only 0.08 warmer than its top (needs 0.10; but in the film the notice is lit by the film page's own light, which now
  copies Blender's warm light onto its bottom edge); four places differ from the liked picture on purpose.
- What Blender measured for this scene: ${S}/next/next26/facts.json (camera, lights, every prop's place and screen box).
- The scene script: ${K}/paper-film/blender/pit-village/assemble_notice_corner.py
- The film page: ${K}/paper-film/scenes/notice-corner.js
- The composing rules the scene follows: /home/user/Music/austerity-explainer/film-kit/07 Composing a shot.md
- The previous critics' findings and what was fixed since: "/home/user/Music/austerity-explainer/experiments/31 Notice corner - working files/reviews/second rebuild - two critics and a skeptic.json".
  Fixed since then: the notice light no longer reaches the house wall (it reaches only the notice and board); a sooty
  lining inside the drum (it first stuck out as an orange band and was refitted inside the wall); the chair darkened and
  no longer as bright as the notice; the gas lamp's glass amber and part see-through; the lamp post moved so its foot
  hides behind the board; the lantern glass amber and its own light no longer lights its frame; a second gas lamp added
  far up on the left; the dustbins moved so the handcart clearly overlaps them; one more dim lit window on the left.
- The plate (the bigger picture the painter repaints, drawn from where the slide starts, 1536 x 2730) is rendering now
  at ${S}/final/notice-corner-plate-2.png. If it exists when you finish, glance at it too; if not, judge the still.

Rules: do not run Blender (the computer is busy rendering). Python with numpy, opencv and PIL is fine for measuring.
Put any scripts and crops in your own work folder (given below). Spend no money: call no paid image or video service.
Write in plain everyday words, with places as fractions of the frame (0 across = left edge, 0 down = top).
Only report what you actually looked at or measured; say what you could not check.`

const FINDINGS = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: 'plain words: the verdict and the most important findings' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          where: { type: 'string', description: 'place in the frame as fractions, and which prop' },
          what: { type: 'string', description: 'what is wrong, with any measurement' },
          why: { type: 'string', description: 'why it matters for the film or the painting' },
          fix: { type: 'string', description: 'a concrete fix: a change in the 3D scene script (name the line or value) or words for the painter' },
          fix_kind: { type: 'string', enum: ['3d-before-painting', 'painter-words', 'film-page', 'leave'] },
          severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] },
        },
        required: ['title', 'where', 'what', 'why', 'fix', 'fix_kind', 'severity'],
      },
    },
    not_checked: { type: 'string' },
  },
  required: ['summary', 'findings', 'not_checked'],
}

const CRITICS = [
  { key: 'composition-and-light', angle: `Your angle: composition and light, judged by eye and by measurement against the picture the user liked.
What does the eye go to first, second, third? Does the notice win? Do the story props read as one group at the board?
Is the frame balanced (the left half feels too light by the checker)? Is there anything the checker cannot judge
(stacked columns, the chair standing right under the notice with its seat showing and the lantern lit, mood, a phone
screen's size)? Compare with the still before this round: is anything worse? Check each fix listed above actually holds.` },
  { key: 'before-the-repaint', angle: `Your angle: what the painter (an image model that copies shapes and light and dark) is likely to misread or garble,
and what would then break once the painting is shone back onto the 3D set and the camera slides. In particular look
at: the drum's mouth (it is now an even orange disc inside a pale rim: will it be painted as liquid, soup or a lid?),
thin parts (lantern handle, chair spindles, lamp arms), near-touching edges, flat even patches, very dark masses,
anything near white, the far street lamps, the shut gates and dark doorway. Then write the painter instructions you
would send (what to keep, what to paint how, what never to add), in one paragraph.` },
  { key: 'period-and-story', angle: `Your angle: does it look right for a British pit village at dusk on 1 May 1926, the first day of the lockout, and does
it tell that story? Check the props and the street for anything out of period or out of place (gas lamps lit at dusk,
lit windows, the colliery idle with gates shut, the notice's wording and look, the drum fire, the chair and lantern,
coal sacks while coal was scarce, the handcart). Does the empty chair with a lit lantern before the notice read as
a story (someone keeping watch, or someone gone)? Anything that confuses or distracts from the story?` },
]

phase('Critique')
const critiques = await parallel(CRITICS.map((c) => () =>
  agent(`${CONTEXT}\n\nYour work folder: ${S}/critique-32/work-${c.key} (create it).\n\n${c.angle}\n\nReturn your findings, worst first.`,
    { label: `critic:${c.key}`, phase: 'Critique', schema: FINDINGS })))

const got = critiques.map((r, i) => r ? { critic: CRITICS[i].key, ...r } : null).filter(Boolean)
log(`${got.length} critics reported ${got.reduce((n, r) => n + r.findings.length, 0)} findings`)

phase('Verify')
const VERDICT = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: 'plain words: is the still ready for the paid repaint, and what must change first' },
    confirmed: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' }, from: { type: 'string' }, evidence: { type: 'string', description: 'what you measured or saw yourself' },
          fix: { type: 'string', description: 'the exact fix: script line and value, or painter words, or film page change' },
          fix_kind: { type: 'string', enum: ['3d-before-painting', 'painter-words', 'film-page', 'leave'] },
          severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] },
        },
        required: ['title', 'from', 'evidence', 'fix', 'fix_kind', 'severity'],
      },
    },
    rejected: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, from: { type: 'string' }, why: { type: 'string' } }, required: ['title', 'from', 'why'] } },
    painter_instructions: { type: 'string', description: "the final words to send the painter, one paragraph, merging the critics' words and your own" },
    not_checked: { type: 'string' },
  },
  required: ['summary', 'confirmed', 'rejected', 'painter_instructions', 'not_checked'],
}
const verdict = await agent(`${CONTEXT}\n\nYour work folder: ${S}/critique-32/work-skeptic (create it).\n\nYou are the skeptic. Three critics reviewed the still; their findings are below as JSON.
For EVERY finding, check it yourself against the pictures and files (measure where you can). Reject what does not hold
up, what rests on a wrong reading of the scene (remember: in the film the notice and board keep their own surfaces and
are lit by the film page; flames are added live), or a fix that costs more than it buys. Check that every suggested
size or value fits the actual model: a previous skeptic's suggested drum lining was 0.365 m across its radius when the
drum is only 0.296 m, and it stuck out (measure from facts.json or the scene script; the drum's wall is 0.26 to 0.28 m
inside, 0.296 m outside, rim 0.856 m high). Rank what is confirmed: must-fix before the paid repaint, should-fix, minor.
Then write the final painter instructions.\n\nFindings:\n${JSON.stringify(got, null, 1)}`,
  { label: 'skeptic', phase: 'Verify', schema: VERDICT })

return { critiques: got, verdict }
