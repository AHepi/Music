export const meta = {
  name: 'inflation-chapter-outlines',
  description: 'Research what really causes inflation, then draft, critique and revise three outlines for chapter 2 of the austerity explainer',
  phases: [
    { title: 'Research', detail: 'four sourced fact ledgers: history, cases, New Zealand now, how inflation works' },
    { title: 'Draft', detail: 'three outlines from three different angles' },
    { title: 'Critique', detail: 'each outline checked against the facts, the rules and chapter 1, then revised' },
  ],
}

const BRIEF = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/chapter-2-brief.md'
const LEDGER_FORMAT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/in_ch1/austerity-explainer-chapter-1/research/02 Research - chapter 1 - where austerity came from.md'

const RESEARCH_SCHEMA = {
  type: 'object',
  properties: {
    entries: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          claim: { type: 'string', description: 'precise claim with numbers, dates, units' },
          plain: { type: 'string', description: 'plain spoken version a narrator could say' },
          sources: { type: 'array', items: { type: 'string' }, description: 'URLs actually opened or seen in search results, with publisher' },
          confidence: { type: 'string', enum: ['high', 'medium-high', 'medium', 'low'] },
          contested_or_simplified: { type: 'string' },
        },
        required: ['id', 'claim', 'plain', 'sources', 'confidence', 'contested_or_simplified'],
      },
    },
    could_not_verify: { type: 'array', items: { type: 'string' } },
    best_images_for_film: { type: 'array', items: { type: 'string' }, description: 'the most concrete, visual cases from this lane that would work as paper pop-up pictures, each tied to entry ids' },
  },
  required: ['entries', 'could_not_verify', 'best_images_for_film'],
}

const COMMON_RESEARCH = `You are researching facts for chapter 2 ("what really causes inflation") of a narrated explainer film. Read the brief first: ${BRIEF}. Copy the ledger style of chapter 1: ${LEDGER_FORMAT} (claim, plain version, source, confidence, contested or simplified).
Rules:
- Use WebSearch and WebFetch (load them with ToolSearch "select:WebSearch,WebFetch" if they are not already loaded). Prefer primary or authoritative sources (central banks, statistics agencies, IMF, BIS, peer-reviewed papers, major encyclopedias, the author's own interviews). Every entry needs at least one real URL you actually saw. Never invent a figure or a URL; if a figure can't be confirmed, put it in could_not_verify.
- Confidence: high = two good sources or one authoritative source; medium = one decent source; low = do not use without more checking.
- Note where a claim is contested, where it is an interpretation (say whose), and where a plain version simplifies.
- Aim for 12 to 20 entries, each one a fact a narrator might actually say in a 3-4 minute film for a general audience.
- Today is 12 October 2026. For recent figures, give the date and say whether it is an actual result or a forecast.
- Never use the words "MMT" or "Modern Monetary Theory" in the plain versions (you may name the school in the contested column for the record).`

const LANES = [
  {
    key: 'history', prefix: 'C2-H',
    prompt: `Lane: the history that continues chapter 1, 1914-1926, in Britain and Italy, and what Clara E. Mattei (The Capital Order, 2022) says about inflation.
Find: how much prices rose in Britain and Italy during and right after the First World War (cost-of-living figures), and what drove it (shortages, shipping losses, war spending, bank credit, the post-war boom of 1919-20); British wartime price and rent controls (for example the 1915 Glasgow rent strikes and the Rent Restriction Act 1915, food control and rationing 1917-18) and whether they held prices down; the 1920 "dear money" turn (Bank Rate to 7% in April 1920), the 1920-21 slump (unemployment, how far prices and wages fell), the Geddes Axe (1922) and the cut to council housing; the 1925 return to gold at the old rate and what it did to wages (the coal owners' wage cuts, the 1926 General Strike); Italy's post-war inflation and Mussolini's revaluation of the lira ("quota 90", 1926-27) with wage cuts by decree. And, as Mattei's own interpretation (marked as hers): what she argues about inflation, deflation and the "cure" being used to discipline workers. Use ids ${'C2-H01'}, C2-H02 ...`,
  },
  {
    key: 'cases', prefix: 'C2-C',
    prompt: `Lane: real cases that test "creating money causes inflation". Cover both sides honestly.
Find: Germany 1921-23 (reparations owed in gold marks or foreign currency, the French and Belgian occupation of the Ruhr in January 1923, passive resistance paid for by printing, what happened to output); Zimbabwe 2007-08 (collapse of farm and factory output, what preceded the printing); Japan (very large money creation by the Bank of Japan from 2013, and earlier from 2001, with inflation staying low for years); Britain and the United States after 2008 (central banks created hundreds of billions to buy bonds while consumer price inflation stayed mostly low, while asset prices such as houses and shares rose); the Second World War in Britain and the United States (very large government spending, rationing, price controls and savings drives that held inflation down, and the jump when controls ended); the 1973 oil shock (oil price roughly quadrupling) and 1979; the 2021-23 world inflation (energy and food after Russia's invasion of Ukraine, shipping and supply chains, the share explained by supply shocks versus demand, for example Bernanke and Blanchard 2023, and the IMF/ECB finding on how much rising profits contributed in the euro area). Also any evidence that wage-price spirals are rare (IMF 2022). Use ids C2-C01, C2-C02 ...`,
  },
  {
    key: 'now', prefix: 'C2-N',
    prompt: `Lane: New Zealand (and briefly Australia) 2020 to October 2026: what pushed prices up, who paid for bringing them down.
Find: New Zealand's consumer price inflation path (peak 7.3% in the year to the June 2022 quarter; when it came back inside the Reserve Bank's 1-3% target; the latest figure before 12 October 2026, which the brief's report puts at 4.1% for the year to the June 2026 quarter, 2.9% without fuel - verify); what drove it (petrol, construction costs and building materials, rents and housing, food, imported versus domestic inflation as Statistics New Zealand splits them); the Reserve Bank's money creation in 2020-22 (the Large Scale Asset Purchase programme, its size, the Funding for Lending programme) and house prices rising about 30% or more in 2021; the Official Cash Rate going from 0.25% to 5.5% (dates) and the 2023-24 recession and rising unemployment (peak figures); the Commerce Commission's grocery market study (2022) on supermarket profits; the Royal Commission on the pandemic response (March 2026) and the independent review of the Reserve Bank (22 September 2026) as summarised in the brief's report. Also the Reserve Bank's 2025-26 rate moves. Read the brief's report file for the figures it already sources and reuse its sources where possible, but verify key numbers. Use ids C2-N01, C2-N02 ...`,
  },
  {
    key: 'mechanism', prefix: 'C2-M',
    prompt: `Lane: how inflation works, in plain words, and the main views, fairly put.
Find sources for: what inflation is and how it is measured (a basket of goods; consumer price index); the three usual causes economists name - too much spending for what the economy can make (demand), rising costs (cost push, e.g. energy), and firms raising prices faster than costs (profit-led or "sellers' inflation", e.g. Isabella Weber and Evan Wasner 2023); why spending into an economy with idle workers and machines tends to raise output rather than prices, while spending past full capacity, or on things in fixed supply such as land, raises prices; the view of the economists the film draws on (a government that issues its own currency can't run out of it; its real limit is inflation, i.e. real resources; tools such as taxes to make room, targeted spending, price controls, buffer stocks - sources such as Abba Lerner, Functional Finance 1943; Stephanie Kelton, The Deficit Myth 2020); the mainstream counter-view fairly put (Milton Friedman's "inflation is always and everywhere a monetary phenomenon", the quantity theory, and why many economists today focus on spending relative to capacity and on expectations rather than the quantity of money); how central banks fight inflation by raising interest rates and that this works partly by slowing the economy and raising unemployment (central bank sources). Keep each plain version speakable. Use ids C2-M01, C2-M02 ...`,
  },
]

const OUTLINE_SCHEMA = {
  type: 'object',
  properties: {
    title: { type: 'string', description: 'working title of the chapter' },
    angle: { type: 'string', description: 'one short name for the approach' },
    pitch: { type: 'string', description: 'two or three plain sentences: what the viewer goes through and what they come away knowing' },
    the_one_idea: { type: 'string', description: 'the single idea the viewer should remember, in one plain sentence' },
    how_it_explains_inflation_through_chapter_1: { type: 'string' },
    honest_edge: { type: 'string', description: 'where and how it admits creating money can push prices up' },
    estimated_seconds: { type: 'number' },
    estimated_spoken_words: { type: 'number' },
    pages: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          page: { type: 'number' },
          name: { type: 'string' },
          what_is_said: { type: 'string', description: 'the beat in plain words, 1-3 sentences' },
          sample_line: { type: 'string', description: 'one line of draft narration in the series voice, no capitals, pauses as ...' },
          on_screen: { type: 'string', description: 'what pops up, slides, crashes or folds, on which words' },
          words_on_screen: { type: 'array', items: { type: 'string' } },
          research_ids: { type: 'array', items: { type: 'string' } },
          reused_paintings: { type: 'array', items: { type: 'string' } },
          new_paintings: { type: 'array', items: { type: 'string' } },
        },
        required: ['page', 'name', 'what_is_said', 'sample_line', 'on_screen', 'words_on_screen', 'research_ids', 'reused_paintings', 'new_paintings'],
      },
    },
    page_1_full_draft: { type: 'string', description: 'the full narration of page 1 as it would be recorded, starting with [in a warm, steady New Zealand accent]' },
    mattei_claims_marked_as_hers: { type: 'array', items: { type: 'string' } },
    new_paintings_large: { type: 'number' },
    new_paintings_small: { type: 'number' },
    fal_cost_estimate_usd: { type: 'number' },
    strengths: { type: 'array', items: { type: 'string' } },
    weaknesses_and_risks: { type: 'array', items: { type: 'string' } },
  },
  required: ['title', 'angle', 'pitch', 'the_one_idea', 'how_it_explains_inflation_through_chapter_1', 'honest_edge', 'estimated_seconds', 'estimated_spoken_words', 'pages', 'page_1_full_draft', 'mattei_claims_marked_as_hers', 'new_paintings_large', 'new_paintings_small', 'fal_cost_estimate_usd', 'strengths', 'weaknesses_and_risks'],
}

const ANGLES = [
  {
    key: 'factory',
    prompt: `Angle A - "Back to the shell factory" (mechanism first, one concrete machine). Pick up from chapter 1's last question. Return to chapter 1's 1915 shell factory and use it, with the pay packet and price tag, as the one concrete model: new money arriving where there are idle workers and machines makes more things; the same money arriving where every machine is already running flat out, or chasing something nobody can make more of (land, houses, oil), pushes prices up. Then test that rule quickly on a few real cases from the research (for example one where huge money creation did not raise prices, one where prices exploded because production collapsed, one where costs not money drove prices). Close by asking who pays when governments "fight inflation" (interest rates, jobs), linking back to the "money" part of austerity from chapter 1.`,
  },
  {
    key: 'history',
    prompt: `Angle B - "What happened next" (the story continues, 1919 to today). Continue chapter 1's history: prices really did rise after the war - show why, from the research (shortages, shipping, controls lifted, the boom). Then the experts' cure: dear money, the 1920-21 slump, wages and prices pushed down, the council homes cut, back to gold in 1925 and the miners. Mattei's argument (marked as hers) about who the cure was really for. Then jump to "Sound familiar?": New Zealand 2021-2026 - what pushed prices up, where the pandemic money went (houses), and the cure again (interest rates, job losses). The rule (where and how money is spent) and the honest edge should come out of the story, not be lectured.`,
  },
  {
    key: 'cases',
    prompt: `Angle C - "Four price tags" (case files with verdicts). The politician from chapter 1 makes the claim "creating money causes inflation". The chapter puts it to the test on a handful of real price stories from the research (for example Germany 1923, Japan's decade of money creation with flat prices, the 1973 oil shock, New Zealand 2022), each a page with a verdict card answering: was it the money, a shortage, or who spent it on what? The rule (where and how money is spent) is built from the verdicts, with the honest edge as one of the verdicts. End by tying back to chapter 1: why the official story keeps blaming the money, and who pays for the cure.`,
  },
]

const COMMON_DRAFT = `You are drafting one outline for chapter 2 ("what really causes inflation") of a paper pop-up explainer film. Read the brief first: ${BRIEF}. Also skim chapter 1's page plan and the rules file named in the brief, and the Pinker teaching SKILL.md named there.
Requirements:
- 9 to 11 pages, about 3 to 4 minutes, roughly 450-600 spoken words in all. Page 1 must pick up directly from chapter 1's last line ("won't creating it just cause inflation? That's next.").
- Explain inflation within the context of chapter 1: reuse its people, objects and ideas (the politician, the shell factory, the pay packet and price tag, the gold, the experts' advice to "stop creating new money", the line "it can run out of workers, materials and machines").
- Hinge: the user's own point - it depends on where and how the money is spent - plus the honest edge (creating money can push prices up when the spending chases things the economy can't make more of).
- Every factual sentence must cite research ids from the ledger below. Use only facts in the ledger; if a beat needs a fact the ledger lacks, say so in weaknesses_and_risks instead of inventing it.
- Follow the narration rules in the brief exactly (never "MMT"; Mattei's views marked as hers; one plain name per thing; concrete case before each idea; explain every term at first use; no capitals; pauses as ...; no real person drawn).
- On-screen words: few, short forms of what is said.
- Prefer reusing chapter 1's paintings; list new ones needed, and estimate fal cost (about 10 US cents per background or big figure, 2.5 cents per small object).
- Be candid in weaknesses_and_risks.`

const CRITIQUE_PROMPT = (outline, researchJson) => `You are the critic and reviser for one outline of chapter 2 ("what really causes inflation") of a paper pop-up explainer film. Read the brief: ${BRIEF}, and the rules file it names.
Check the outline below through four lenses, then return a REVISED outline in the same structure with the problems fixed:
1. Facts: every factual sentence traces to a ledger id that really supports it (check the ledger below); nothing overclaimed; contested points and Mattei's interpretations marked; no fact used that is low confidence or in could_not_verify; numbers spoken exactly as the ledger supports.
2. Rules: never "MMT"; "economists who study how modern money works" used for that view; Mattei marked as hers; one plain name per thing kept throughout (list any synonyms you removed); concrete case before each idea; every term explained at first use; no capitals; pauses as ...; conversational and a little urgent without shouting; no real person drawn.
3. The brief: it explains inflation within chapter 1's story; it makes the user's point (it depends on where and how the money is spent) clearly; it includes the honest edge fairly; page 1 picks up from chapter 1's last line; 3-4 minutes.
4. Making it: the pictures can be made as painted paper pieces (no cartoon movement, no hands); few words on screen; reuse of chapter 1 paintings; a realistic fal cost.
Keep the outline's own angle - don't turn it into a different outline. Put what you changed and why into weaknesses_and_risks as items starting "Changed:", and any problem you could not fix as items starting "Still open:".

Research ledger (JSON):
${researchJson}

Outline to critique (JSON):
${JSON.stringify(outline)}`

phase('Research')
const research = await parallel(LANES.map(l => () =>
  agent(`${COMMON_RESEARCH}\n\n${l.prompt}`, { label: `research:${l.key}`, phase: 'Research', schema: RESEARCH_SCHEMA, effort: 'medium' })
    .then(r => r ? { lane: l.key, ...r } : null)
))
const lanes = research.filter(Boolean)
log(`Research lanes returned: ${lanes.map(l => `${l.lane} (${l.entries.length} entries)`).join(', ')}`)
const researchJson = JSON.stringify(lanes)

phase('Draft')
const results = await pipeline(
  ANGLES,
  a => agent(`${COMMON_DRAFT}\n\n${a.prompt}\n\nResearch ledger (JSON):\n${researchJson}`, { label: `draft:${a.key}`, phase: 'Draft', schema: OUTLINE_SCHEMA, effort: 'medium' }),
  (draft, a) => draft
    ? agent(CRITIQUE_PROMPT(draft, researchJson), { label: `critique:${a.key}`, phase: 'Critique', schema: OUTLINE_SCHEMA, effort: 'medium' })
        .then(revised => ({ angle: a.key, draft, revised }))
    : null,
)

return { research: lanes, outlines: results.filter(Boolean) }
