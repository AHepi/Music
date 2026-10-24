export const meta = {
  name: 'critique-rebuilt-notice-corner',
  description: 'Two critics judge the rebuilt and relit notice corner against the liked picture and the shot checker; a skeptic merges',
  phases: [
    { title: 'Critique', detail: 'composition and light; what the tool missed' },
    { title: 'Merge', detail: 'a skeptic checks every claim and ranks the fixes before the paid repaint' },
  ],
}

const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner'
const CONTEXT = `
CONTEXT. We make short explainer films. This shot is a 1926 pit-village street built in 3D in Blender, at night, during the
miners' lockout: a printed lockout notice on a wooden board on two posts, an oil-drum fire (flames are drawn live in the film,
not in the picture), an empty chair with a lit hurricane lantern on its seat, a wooden pail, a gas lamp behind the board.
The user liked a picture an image program composed ("the reference") and asked for it to be rebuilt with our own props and
our sharp notice; then said the camera angle was wrong ("the lines don't converge the same way"), which was fixed by matching
the camera to the reference's landmarks. Four critics then found faults (chair facing the wrong way, everything near white,
a hard black wedge that turned out to be a render fault, the notice in the phone-button strip, a far lamp touching the board,
the left half a black empty mass); these were fixed in 3D, with a new tool, the shot checker, judging each round.
Files (all readable; open the pictures yourself):
  - the reference: /home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg
  - the first rebuild (before the fixes): ${S}/composed-end-2.png
  - NOW, rebuilt and lit (1080 x 1920): ${S}/final/composed-end-4.png
  - side by side: ${S}/final/31 Notice corner - before and after.jpg
  - the shot checker's report on NOW: ${S}/final/report/report.md and its marked picture ${S}/final/report/marked.jpg
  - the measured facts (camera, every prop's place and size, the lights, the flat-colour pictures): ${S}/final/facts/
  - the composing rules: /home/user/Music/austerity-explainer/film-kit/07 Composing a shot.md
  - the scene script: /home/user/work/paper-pop-up-film-kit/paper-film/blender/pit-village/assemble_notice_corner.py
What happens next: the plate (a bigger picture from the start of a 1.5 m camera slide toward the notice) is repainted by an
image program in the series' painted style (it keeps the plate's light and dark), and the painting is shone back onto the 3D
street so the camera can slide. So faults of light, shape and placement must be fixed in 3D BEFORE the paid repaint.
Rules: don't run Blender (a long render is using the machine), don't edit any file outside a new folder ${S}/critique-31-NAME
that you make, don't spend money. You may run Python on the pictures (numpy, OpenCV are installed). Give numbers and places
(fractions of the frame: 0 across is left, 0 down is top) for every claim. Say what you did not check.`

const FAULTS = {
  type: 'object',
  properties: {
    verdict: { type: 'string', description: 'three to six sentences' },
    faults: { type: 'array', items: { type: 'object', properties: {
      fault: { type: 'string' }, where: { type: 'string' }, why_it_matters: { type: 'string' },
      fix: { type: 'string', description: 'concrete: which setting or object in the scene script, and by how much' },
      severity: { type: 'string', enum: ['must fix before painting', 'fix if cheap', 'leave'] },
    }, required: ['fault', 'where', 'why_it_matters', 'fix', 'severity'] } },
    tool_check: { type: 'string', description: 'is each problem in the shot checker report real? anything visible it missed?' },
    not_checked: { type: 'string' },
  },
  required: ['verdict', 'faults', 'tool_check', 'not_checked'],
}

const LENSES = [
  { key: 'composition-and-light', prompt: `${CONTEXT}

LENS: COMPOSITION AND LIGHT against the reference and the rules. Does NOW keep what made the reference work (every strong thing
pointing at the notice corner; the notice the biggest bright thing; a cream notice on a dark board; warm light from the fire
and lantern, lit from below; a quiet but not empty left side)? Compare NOW with the reference and with the first rebuild,
region by region, with measured brightness and colour. Look hard at the things that still look off: the corner gas lamp's
glass (should be amber, darker than the notice), the drum's inside rim, the chair's seat, the notice's colour top to bottom.
Then judge the shot checker's report: is each listed problem real when you look at the picture? What does a person see that it
does not list?` },
  { key: 'before-the-repaint', prompt: `${CONTEXT}

LENS: WHAT WILL GO WRONG IN THE REPAINT AND THE SLIDE. Look at NOW and at the scene script as a painter and a film-maker would.
Which shapes will the painter smear or invent (thin parts, small bright spots, lettering); which surfaces are near pure white or
pure black (the painter loses detail there); what does the 1.5 m slide toward the notice uncover from behind the near props
(the drum, chair, pail, board posts, lamp post); is anything in the frame that the story of 1 May 1926 doesn't need, or is
anything missing that a person would expect? Then judge the shot checker's report the same way: real problems? anything missed?` },
]

phase('Critique')
const results = await parallel(LENSES.map(l => () => agent(l.prompt, { label: `critic:${l.key}`, phase: 'Critique', schema: FAULTS }).then(r => r ? { lens: l.key, ...r } : null)))
const found = results.filter(Boolean)

phase('Merge')
const merged = await agent(`${CONTEXT}

You are a skeptical senior reviewer. Two critics looked at NOW. Their findings are below. Open the pictures and files yourself
and check every claim; reject what the files don't support; merge duplicates. Rank what survives into: fix in 3D before the
paid repaint (each with the exact change in the scene script), ask the painter (exact words), and leave. Also say whether the
shot checker's remaining problems are real and whether it missed anything a viewer would notice.

FINDINGS:
${JSON.stringify(found, null, 1)}`, { label: 'skeptic', phase: 'Merge', schema: {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    fix_in_3d_before_repaint: { type: 'array', items: { type: 'string' } },
    ask_the_painter: { type: 'array', items: { type: 'string' } },
    leave: { type: 'array', items: { type: 'string' } },
    rejected: { type: 'array', items: { type: 'string' } },
    tool_verdict: { type: 'string' },
  },
  required: ['summary', 'fix_in_3d_before_repaint', 'ask_the_painter', 'leave', 'rejected', 'tool_verdict'],
} })
return { critiques: found, merged }
