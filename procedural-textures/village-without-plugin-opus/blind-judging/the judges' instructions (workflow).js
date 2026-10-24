export const meta = {
  name: 'village-blind-judging',
  description: 'Three independent judges score fifteen anonymous village pictures (three makers, five views) without knowing who made which',
  phases: [{ title: 'Judge', detail: 'three lenses, blind' }],
}

const J = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-blind-judging/pictures'
const LENSES = [
  { key: 'photo', text: 'PHOTOGRAPHIC REALISM: would each picture pass as a real photograph? Judge shapes, surfaces, light, scale, plants and trees, ground, and any give-away computer-graphics faults (repeats, blobs, clean surfaces, floating or sunken objects, odd black shapes, flat light).' },
  { key: 'request', text: 'THE REQUEST: the person asked for "a village in the forest. Needs unkept dirt roads like they\'ve been driven down by horse and carriage, an empty stable, a few cottages, some scattered mediaeval props." Judge how well each picture delivers that: are the roads unkept dirt worn by horses and carts (ruts, hoof prints, mud, puddles, weeds), is the stable empty and believable, do the cottages and props read as mediaeval, does it sit in a forest?' },
  { key: 'film', text: 'FILM SET USE: you are an art director choosing a backdrop for a documentary film. Judge composition, light and mood, depth, how believable and lived-in the place is (dirt, wear, damage, weathering, plants growing where they would), and what you would have to fix before using it.' },
]
const SCHEMA = {
  type: 'object',
  properties: {
    pictures: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          score_out_of_10: { type: 'number' },
          strongest_point: { type: 'string' },
          most_visible_faults: { type: 'string' },
        },
        required: ['file', 'score_out_of_10', 'strongest_point', 'most_visible_faults'],
      },
    },
    best_per_view: {
      type: 'array',
      items: {
        type: 'object',
        properties: { view: { type: 'string' }, best_letter: { type: 'string' }, why: { type: 'string' } },
        required: ['view', 'best_letter', 'why'],
      },
    },
    overall_note: { type: 'string' },
  },
  required: ['pictures', 'best_per_view', 'overall_note'],
}

phase('Judge')
const results = await parallel(LENSES.map(lens => () => agent(
  `You are judging 15 pictures of three computer-made forest villages, shown in five views. The folder ${J} holds them, named <view>_<letter>.jpg: for each view there are three pictures, A, B and C, each from a different maker. The letters are shuffled between views, so A in one view is not necessarily the same maker as A in another. You do not know who made which, and you must not try to find out: open only the 15 picture files in that folder with the Read tool and read nothing else on this computer.
Your lens: ${lens.text}
Look at every picture carefully, at full size. Score each picture from 1 to 10 on your lens only (10 = flawless), name its strongest point and its most visible faults in plain words, pick the best of A, B and C for each view and say why, then give a short overall note. Be strict and specific; scores should spread where the pictures differ.`,
  { label: `judge: ${lens.key}`, phase: 'Judge', schema: SCHEMA }
).then(r => (r ? { lens: lens.key, ...r } : null))))

return { results: results.filter(Boolean) }
