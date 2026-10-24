export const meta = {
  name: 'lessons-audit',
  description: 'Check every lesson from the earlier sets (film project, coal mine, courtyard, textures, garden) against the plugin and list the missing ones with where they belong (read-only)',
  phases: [
    { title: 'Read', detail: 'four readers, one per group of lesson sources, each checks every lesson against the plugin' },
    { title: 'Merge', detail: 'remove doubles, rank by importance for building places, write the exact additions' },
  ],
}

const P = '/home/user/Music/plugins/explainer-film'
const A = '/home/user/Music/austerity-explainer'
const PT = '/home/user/Music/procedural-textures'
const OPTS = { model: 'sonnet', effort: 'xhigh' }

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them. The project's Claude Code plugin "explainer-film" (${P}) is meant to carry everything the project has learned, so that any model (often a smaller one such as Sonnet) given only the plugin and a plain request does things right without being told. The person asked: "You synthesized lessons from previous sets. Are they being used as well?" Your job is to find out, lesson by lesson. Other helpers are editing the plugin right now: you must NOT change any file anywhere (read only). Never read anything in ~/.runpod; never write in /home/user/Music/japanese-courtyard.
WHAT COUNTS: every lesson, trap, rule, decision or measured finding about building, dressing, lighting, composing, rendering, checking or reusing 3D places, sets, props and surfaces in Blender (and how they become film pictures: plates, painting over, the stage), plus how helpers should work (fresh checkers, verifying claims, money and card time, file and naming rules, how to talk to the person). Skip lessons only about narration, research, fact-checking or sound unless they also affect places.
FOR EACH LESSON: say whether the plugin carries it today (covered: quote the plugin file and line; partly: what is missing; missing), whether it is general (any place) or tied to one film or place, and how important it is for a model building a new place (high, medium, low), with a short why. Be exhaustive: go through the sources line by line, not by sampling. Search the plugin with grep for each lesson's key words before calling it missing.`

const LESSON = { type: 'object', properties: {
  lessons: { type: 'array', items: { type: 'object', properties: {
    lesson: { type: 'string' }, source: { type: 'string' }, in_plugin: { type: 'string', enum: ['covered', 'partly', 'missing'] },
    plugin_evidence: { type: 'string' }, general_or_specific: { type: 'string', enum: ['general', 'specific'] },
    importance: { type: 'string', enum: ['high', 'medium', 'low'] }, why: { type: 'string' },
  }, required: ['lesson', 'source', 'in_plugin', 'plugin_evidence', 'general_or_specific', 'importance', 'why'] } },
  summary: { type: 'string' },
}, required: ['lessons', 'summary'] }

phase('Read')
const GROUPS = [
  { key: 'film lessons', sources: `${A}/project-notes/Lessons.md (all 149 entries, including the Traps section) and ${A}/film-kit/"05 Lessons and traps.md"` },
  { key: 'film decisions and workflows', sources: `${A}/project-notes/Decisions.md (the person's exact words and the rules that came from them), ${A}/project-notes/Workflows.md, ${A}/project-notes/Glossary.md, and the parts of ${A}/project-notes/Status.md about sets, places and props` },
  { key: 'film story', sources: `${A}/project-notes/"Austerity explainer - project story.md" (every log, especially the ones about Blender sets, the pit village street, the Works, the checkout, the coal mine, the shot checker, the people test, plan 3, the composition test, the design review, the wet lockout shot): the failures and what fixed them` },
  { key: 'mine, courtyard, textures and garden', sources: `/home/user/Music/mine-scene ("Coal mine - project story.md", "Notes for the six builders.md", README.md, and the lessons in its code comments), /home/user/Music/japanese-courtyard ("Japanese courtyard - project story.md", README.md; read only), the summaries of the person's add-on rules in ${PT}/garden/addon, and "${PT}/Procedural textures - project story.md" (logs 1-31; check each lesson against the plugin as it is now)` },
]
const reads = await parallel(GROUPS.map(g => () => agent(`${COMMON}
YOUR SOURCES (group "${g.key}"): ${g.sources}. Go through them in full and check every lesson against the plugin (${P}: README, every skill and its reference files, agents, workflows, hooks, kit/docs including "LLM tips and tricks.md" and "paper-look - 05 Lessons and traps.md", kit/place-kit/README.md and its data, kit/film-settings.json).`, { ...OPTS, label: `read: ${g.key}`, phase: 'Read', schema: LESSON }).then(r => ({ group: g.key, result: r }))))

phase('Merge')
const MERGED = { type: 'object', properties: {
  counts: { type: 'string', description: 'how many lessons in all, covered, partly, missing, by group' },
  missing_that_matter: { type: 'array', items: { type: 'object', properties: {
    lesson: { type: 'string' }, sources: { type: 'string' }, importance: { type: 'string', enum: ['high', 'medium', 'low'] },
    where_in_plugin: { type: 'string', description: 'the plugin file (and section) it belongs in' }, text_to_add: { type: 'string', description: 'the exact plain-word text to add' },
    needs_code_or_check: { type: 'string', description: 'a kit check or calculator that would enforce it, or none' },
  }, required: ['lesson', 'sources', 'importance', 'where_in_plugin', 'text_to_add', 'needs_code_or_check'] } },
  answer_for_the_person: { type: 'string', description: 'plain words: are the earlier lessons being used, how many, which important ones are not' },
}, required: ['counts', 'missing_that_matter', 'answer_for_the_person'] }
const merged = await agent(`${COMMON}
YOUR STEP: MERGE. Four readers checked the lessons of the earlier sets against the plugin. Remove doubles (the same lesson from several sources), keep the general ones (and specific ones that teach something general), and rank what is missing or only partly carried by how much it matters to a model building a new place. For each, write the exact plain-word text to add and where it belongs in the plugin, and say whether a kit check could enforce it. Re-check, with grep in ${P}, every lesson you list as missing before you list it (the plugin is large; say what you searched for).
READERS: ${JSON.stringify(reads)}`, { ...OPTS, label: 'merge and rank', phase: 'Merge', schema: MERGED })

return { reads, merged }