export const meta = {
  name: 'verify-facts',
  description: 'Independently re-verify every fact in a narration script (and its planned on-screen words, its pictures and the words written on its props), adversarially, then settle disagreements and list fixes',
  whenToUse: 'After a script is written (before or after recording) and again once on-screen words, pictures and props are known. Pass the script path; optionally the research ledger, the page files, the stills or paintings, the prop-lettering list, and pre-made claim groups.',
  phases: [
    { title: 'Split', detail: 'one agent splits the script into topic groups of claims (skipped if groups are given)' },
    { title: 'Verify', detail: 'one skeptical checker per topic group, fresh primary sources' },
    { title: 'Gaps', detail: 'one reviewer settles disagreements, finds uncovered claims, lists fixes' },
  ],
}

// args: {
//   script: '/path/to/script.md'                       (required: the narration, page by page)
//   today: '12 October 2026'                           (required: so "latest" figures are judged right)
//   ledger: '/path/to/research-ledger.md'              (optional: what was claimed before; checkers must not trust it)
//   onScreen: 'where the on-screen words are, e.g. the page files paper-film/scenes/my-chapter/page-*.js' (optional)
//   pictures: 'the stills or paintings to look at for period accuracy, e.g. /path/to/out/p1/sheet.jpg, /path/to/paintings/*.png' (optional)
//   propLettering: '/path/to/prop-lettering.json' (optional: every word written on a built prop, as kit/calculators/list_prop_lettering.py --out writes it:
//                  {"strings": [{"text", "prop", "file", "line"}]})
//   audience: 'a general New Zealand audience'          (optional)
//   groups: [{ key, title, claims: ['...'] }]           (optional: skip the split; at most 8 groups)
//   effort: 'medium'                                    (optional, default 'medium')
// }
const A = args ?? {}
if (!A.script || !A.today) throw new Error('verify-facts needs args.script and args.today')
const EFFORT = A.effort ?? 'medium'
const AUDIENCE = A.audience ?? 'a general audience'

const GROUPS_SCHEMA = { type: 'object', properties: { groups: { type: 'array', items: { type: 'object', properties: {
  key: { type: 'string' }, title: { type: 'string' }, claims: { type: 'array', items: { type: 'string' } } }, required: ['key', 'title', 'claims'] } } }, required: ['groups'] }

let groups = A.groups
if (!groups) {
  phase('Split')
  const split = await agent(`Read the narration script at ${A.script}${A.onScreen ? ` and the on-screen words in ${A.onScreen} (every string drawn on screen, every number on counters, tags, dials and charts)` : ''}.${A.propLettering ? ` Also read ${A.propLettering}: every word written on a built prop (a notice, a sign, a newspaper, a shop or firm name), with the prop and the file it comes from. Each string is a claim the viewer sees.` : ''}${A.pictures ? ` Also look at these pictures with the Read tool: ${A.pictures}. What a picture shows is a claim too (a machine, a uniform, a heap of coal, the weather, a vehicle of the wrong era): list what a viewer would take as fact about that place and year.` : ''} List EVERY checkable factual claim (numbers, dates and their weekdays (30 April 1926 was a Friday), names, who did what, cause and effect, quotes, attributions), each as one line quoting what the viewer hears and/or sees (for a picture or a prop, say which picture or prop), and group them by topic into at most 7 groups of related claims (for example one historical episode per group; put the claims of the pictures and the props in their own group when there are any). A name written on a prop is either made up on purpose (then list it to be checked against real names, so it does not copy a real one by accident) or a real one (then check it is used correctly). Leave out opinions that are clearly attributed and pure questions. Do not edit any files.`, { label: 'split claims', phase: 'Split', schema: GROUPS_SCHEMA, effort: EFFORT })
  groups = (split?.groups ?? []).slice(0, 8)
  if (!groups.length) throw new Error('no claims found in the script')
}
log(`${groups.length} groups, ${groups.reduce((n, g) => n + g.claims.length, 0)} claims`)

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    group: { type: 'string' },
    claims: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' },
      verdict: { type: 'string', enum: ['confirmed', 'confirmed with nuance', 'wrong', 'could not verify'] },
      what_the_sources_say: { type: 'string' },
      sources: { type: 'array', items: { type: 'object', properties: { url: { type: 'string' }, what: { type: 'string' }, opened: { type: 'boolean' } }, required: ['url', 'what', 'opened'] } },
      problem: { type: 'string' }, fix: { type: 'string' },
      severity: { type: 'string', enum: ['none', 'minor', 'should fix', 'must fix'] },
    }, required: ['claim', 'verdict', 'what_the_sources_say', 'sources', 'problem', 'fix', 'severity'] } },
    other_notes: { type: 'string' },
  },
  required: ['group', 'claims', 'other_notes'],
}

const verifyPrompt = (g) => `You are an independent, skeptical fact checker for a narrated explainer film for ${AUDIENCE}. Today is ${A.today}. Your job is to try to PROVE EACH CLAIM WRONG with fresh research.${A.ledger ? ` Do not trust the project's own research notes (${A.ledger}); they only show what was claimed before.` : ''} The full script is ${A.script}.

Topic: ${g.title}
Claims (what the viewer hears and/or sees):
${g.claims.map((c, i) => `${i + 1}. ${c}`).join('\n')}
${A.pictures ? `The pictures, when a claim is about what one shows (look with the Read tool): ${A.pictures}\n` : ''}${A.propLettering ? `The words written on the built props, with their props and files: ${A.propLettering}\n` : ''}
How to work:
- Load the web tools first: ToolSearch with query "select:WebSearch,WebFetch". Use WebSearch (mode "standard"; "extended" for recent or hard-to-find facts) and open the best sources with WebFetch.
- Prefer primary sources (statistics offices, central banks, legislation, official histories, academic papers, the author's own words); say whether you opened each source or only saw it in search results.
- For a date, check its weekday too. For a name written on a prop, check whether it is real; a made-up one must not copy a real one by accident. For a picture, ask "was this in that place and that year?".
- Verdict per claim: confirmed / confirmed with nuance / wrong / could not verify. Rounding in speech ("about", "roughly") is fine if the numbers support it; on screen there is no "about", so check on-screen numbers exactly. A wrong number, date, direction, or a view attributed to the wrong person is not fine.
- If something is wrong or misleading, give the smallest concrete fix (prefer on-screen words; a narration change means re-recording), and a severity.
- Be concise. Do not edit any files.`

phase('Verify')
const results = await pipeline(groups, (g) => agent(verifyPrompt(g), { label: `verify:${g.key}`, phase: 'Verify', schema: VERDICT_SCHEMA, effort: EFFORT }))
const done = results.filter(Boolean)
const missing = groups.filter((g, i) => !results[i]).map((g) => g.key)
if (missing.length) log(`No result from: ${missing.join(', ')}`)

const FIX = { type: 'object', properties: { page: { type: 'string' }, what: { type: 'string' }, fix: { type: 'string' }, evidence: { type: 'string' } }, required: ['page', 'what', 'fix', 'evidence'] }
const CRITIC_SCHEMA = { type: 'object', properties: {
  must_fix: { type: 'array', items: FIX }, should_fix: { type: 'array', items: FIX },
  gaps: { type: 'array', items: { type: 'string' } },
  summary: { type: 'string', description: 'plain-language summary for a non-programmer' },
}, required: ['must_fix', 'should_fix', 'gaps', 'summary'] }

phase('Gaps')
const critic = await agent(`You are the final reviewer of a fact check of a narrated explainer film (${AUDIENCE}; today is ${A.today}). Independent checkers each tried to refute one group of claims; their verdicts are below. Read the script (${A.script})${A.ledger ? ` and the research notes (${A.ledger})` : ''}${A.propLettering ? `, the words on the props (${A.propLettering})` : ''}${A.pictures ? ` and look at the pictures (${A.pictures})` : ''}.
1. Where a verdict is thin, contradicts another, or rests only on search snippets for a number shown on screen, check it yourself (ToolSearch "select:WebSearch,WebFetch") and settle it.
2. List any factual claim in the script that no group covered; check those that matter.
3. Produce must_fix (wrong facts or numbers), should_fix (misleading wording or numbers needing a tweak), and gaps (still unverified, or due to change soon). For each fix, say whether on-screen words alone can fix it or a narration page must be re-recorded.
Write the summary in plain everyday language. Do not edit files.
${missing.length ? `No verdicts came back for: ${missing.join(', ')}; check those claims yourself.` : ''}
Groups checked: ${groups.map((g) => g.title).join('; ')}
Verdicts:
${JSON.stringify(done, null, 1)}`, { label: 'final review', phase: 'Gaps', schema: CRITIC_SCHEMA, effort: EFFORT })

return { groups, verdicts: done, critic }
