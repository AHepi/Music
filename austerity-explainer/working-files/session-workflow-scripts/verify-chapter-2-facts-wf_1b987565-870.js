export const meta = {
  name: 'verify-chapter-2-facts',
  description: 'Independently re-verify every fact in the chapter 2 narration and planned on-screen numbers, adversarially, then check for gaps',
  phases: [
    { title: 'Verify', detail: 'one skeptical checker per topic group, fresh primary sources' },
    { title: 'Gaps', detail: 'one critic reviews all verdicts for gaps, contradictions and needed changes' },
  ],
}

const LEDGER = '/home/user/Music/austerity-explainer/chapter-2-inflation/18 Research - chapter 2 - what really causes inflation.md'
const SCRIPT = '/home/user/Music/austerity-explainer/chapter-2-inflation/19 Script - chapter 2 - what really causes inflation.md'

const GROUPS = [
  { key: 'britain-war', title: 'Britain in the First World War (pages 2 and 3)', claims: [
    'Narration: "Britain, 1915. Unemployment, the share of workers without a job, is under one percent." On screen: UNDER 1% and a panel of 100 dots with one empty.',
    'Narration: "The war is paid for partly with new money." (British WWI finance relied partly on money creation: Treasury bills, currency notes, bank credit.)',
    'Narration: "Submarines are sinking supply ships, and factories are turned over to war work." (U-boats sank merchant ships carrying food and materials; industry converted to munitions.)',
    'Narration: "So more money is chasing fewer things to buy... and by the end of the war, prices have roughly doubled since it began." On screen: bars labelled 1914 = x1 and 1918 = x2 under PRICES.',
    'Narration: "Britain at war was close to the second factory... short of workers, materials and machines." (Britain at full employment, with shortages of labour, materials and machine capacity.)',
  ]},
  { key: 'glasgow', title: 'Glasgow rent strikes, 1915 (page 4)', claims: [
    'Narration: "In 1915, workers poured into Glasgow for war work, and landlords pushed rents up... by as much as a quarter." On screen: GLASGOW 1915 and +25%.',
    'Narration: "By November, about twenty thousand households were refusing to pay the rise." On screen: a counter to 20,000 HOUSEHOLDS.',
    'Narration: "Within weeks, Parliament froze rents." (Increase of Rent and Mortgage Interest (War Restrictions) Act 1915; check its date relative to the November 1915 peak, and that it froze rents at pre-war levels.)',
    'Narration: "Homes can\'t be built in a hurry." (General claim: housing supply is slow to expand; check it is fair for wartime Glasgow, where building had largely stopped.)',
  ]},
  { key: 'japan-boe', title: 'Japan from 2013 and the Bank of England after 2008 (page 5)', claims: [
    'Narration: "Japan, twenty thirteen. Its central bank, the bank that creates the yen, sets out to double the money it has created, in two years." (Bank of Japan QQE, April 2013: double the monetary base in two years.) On screen: JAPAN 2013, x2 MONEY, IN TWO YEARS.',
    'Narration: "If new money on its own pushed prices up, they\'d soar. For eight years, they barely move... about half a percent a year." On screen: a chart with a flat prices line and about 0.5% A YEAR. Check: average Japanese CPI inflation over roughly 2013-2021 (or the QQE period) was about 0.5% a year, and whether "eight years" is fair.',
    'Narration: "After the 2008 crash, the Bank of England, Britain\'s central bank, creates hundreds of billions of pounds." (QE from March 2009: £200bn by early 2010, £375bn by 2012, £895bn by 2020.) On screen: HUNDREDS OF BILLIONS, BANK OF ENGLAND / AFTER 2008.',
    'Narration: "Its own study finds the new money pushed up the prices of shares and other investments... and the gains went to whoever owned the most." (Bank of England 2012 paper "The distributional effects of asset purchases": asset prices including equities rose; holdings skewed, top 5% of households held about 40% of the assets.) On screen: credit BANK OF ENGLAND STUDY, 2012; GAINS TO THE BIGGEST OWNERS. Check the wording "the gains went to whoever owned the most" is a fair summary of what the Bank itself said.',
  ]},
  { key: 'germany-1923', title: 'Germany, 1923 (page 6)', claims: [
    'Narration: "Germany, 1923. Prices are already racing." (German inflation was already rapid in 1922 before the Ruhr occupation of January 1923.)',
    'Narration: "Then French and Belgian soldiers march into the Ruhr, Germany\'s coal and steel heartland." (Occupation from 11 January 1923.)',
    'Narration: "The government tells workers to stop work in protest... and keeps paying them, with new money." (Passive resistance; the government financed it by printing money.)',
    'Narration: "By November, one American dollar costs more than four trillion German marks." On screen: a split-flap counter reading 4,200,000,000,000 and MARKS FOR ONE DOLLAR. Check the exact rate (e.g. 4.2 trillion on 20 November 1923) and its date.',
    'Narration: "This time, new money really did push prices up... while less and less was being made." (Output fell in 1923.)',
  ]},
  { key: 'oil-1973', title: 'The 1973 oil shock (page 7, first half)', claims: [
    'Narration: "Late 1973. Prices are already climbing when the price of oil nearly quadruples, in about three months..." On screen: LATE 1973, a counter $2.90 -> $11.65 A BARREL, NEARLY x4. Check the prices, which price series (posted price of Arabian Light?), the dates (October 1973 to January 1974), and whether "in about three months" is fair.',
    'Narration: "...and almost everything made or moved with fuel gets dearer. So sometimes the cause isn\'t spending. It\'s costs." (Cost-push inflation; check that US/world inflation was already rising before the embargo, as the narration says "prices are already climbing".)',
  ]},
  { key: 'new-zealand', title: 'New Zealand, 2021 to October 2026 (pages 7, 8 and 10)', claims: [
    'Narration (page 7): "And here? The latest figures say prices rose four point one percent in the year to June. Leave fuel out... and it\'s two point nine." On screen: 4.1% PRICES, 2.9% WITHOUT FUEL, STATS NZ, YEAR TO JUNE 2026. Today is 12 October 2026; check that the June 2026 quarter CPI is 4.1% annual and still the latest release (September quarter due 22 October 2026), and that 2.9% excluding fuel (petrol and other vehicle fuels) is what Stats NZ or a reliable bank report says.',
    'Narration (page 8): "In twenty twenty-one, our unemployment hit its lowest since records began." On screen: 3.2% UNEMPLOYMENT, LOWEST ON RECORD, NEW ZEALAND 2021. (December 2021 quarter, HLFS since 1986.)',
    'Narration (page 8): "House prices rose about thirty percent in twelve months." On screen: +30% IN 12 MONTHS. (REINZ HPI 2021.)',
    'Narration (page 8): "An independent review of the Reserve Bank says the support from the bank and the government together was right at first... but too strong, for too long." On screen: INDEPENDENT REVIEW / RESERVE BANK, credit INDEPENDENT REVIEW, SEPTEMBER 2026, stamps RIGHT AT FIRST and TOO STRONG, FOR TOO LONG. Check the review exists (Orphanides and Archer, released about 22 September 2026), its exact wording, and that it refers to the combined monetary and fiscal stimulus.',
    'Narration (page 10): "Here, our central bank, the Reserve Bank, pushed its interest rate from a quarter of a percent to five and a half percent by twenty twenty-three, to bring prices down." On screen: a dial 0.25% -> 5.5%, 2023.',
    'Narration (page 10): "Since the end of twenty twenty-one, unemployment has climbed from three point two percent to five point six." On screen: a counter 3.2% -> 5.6% UNEMPLOYMENT. Check the latest HLFS release (June 2026 quarter, released August 2026) is 5.6% and still the latest as of 12 October 2026.',
    'Narration (page 10): "And this year, the Reserve Bank is raising its interest rate again." On screen: the dial moving 2.25% -> 2.75%, 2026, RISING AGAIN. Check the OCR path: 2.25% from 26 November 2025, raised to 2.5% in July 2026 and 2.75% on 2 September 2026; next decision 28 October 2026.',
  ]},
  { key: 'britain-1920-mattei', title: 'Britain 1920-21 and Mattei (page 9)', claims: [
    'Narration: "Britain, 1920. The Bank of England pushes its interest rate, the price of borrowing, up to seven percent." On screen: BRITAIN 1920, a dial 6% -> 7%. (Bank Rate 7% from 15 April 1920, from 6% set November 1919.)',
    'Narration: "Loans cost more, and people spend less. Within a year, unemployment jumps from about two percent to eleven percent." On screen: bars 2% (1920) -> 11% (1921) UNEMPLOYMENT. Check the series (Bank of England millennium dataset / Feinstein annual averages) and whether monthly insured-unemployment figures tell the same story.',
    'Narration: "Prices do fall... but people pay with their jobs." (UK prices fell in 1921-22.)',
    'Narration: "Mattei argues that was part of the point. With fewer jobs to go round, she says, workers lose the power to ask for more." On screen: the book THE CAPITAL ORDER, credit CLARA E. MATTEI, THE CAPITAL ORDER (2022), MATTEI: PART OF THE POINT. Check that Mattei (The Capital Order, University of Chicago Press, 2022, and her interviews/articles) does argue that austerity and dear money in 1920-21 deliberately disciplined workers by creating unemployment, so attributing this view to her is accurate.',
  ]},
]

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    group: { type: 'string' },
    claims: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' },
      verdict: { type: 'string', enum: ['confirmed', 'confirmed with nuance', 'wrong', 'could not verify'] },
      what_the_sources_say: { type: 'string' },
      sources: { type: 'array', items: { type: 'object', properties: { url: { type: 'string' }, what: { type: 'string' }, opened: { type: 'boolean' } }, required: ['url', 'what', 'opened'] } },
      problem: { type: 'string', description: 'empty if none' },
      fix: { type: 'string', description: 'concrete change to narration or on-screen words, or empty' },
      severity: { type: 'string', enum: ['none', 'minor', 'should fix', 'must fix'] },
    }, required: ['claim', 'verdict', 'what_the_sources_say', 'sources', 'problem', 'fix', 'severity'] } },
    other_notes: { type: 'string' },
  },
  required: ['group', 'claims', 'other_notes'],
}

const verifyPrompt = (g) => `You are an independent, skeptical fact checker for a short documentary-style explainer film about inflation, made in New Zealand. Today is 12 October 2026. The narration has already been recorded, and on-screen words are being built now. Your job is to try to PROVE EACH CLAIM WRONG, using fresh research. Do not trust the project's own research notes: they are listed only so you know what was claimed before (${LEDGER}; the full script is ${SCRIPT}).

Topic: ${g.title}

Claims to check (each is what the viewer hears and/or sees):
${g.claims.map((c, i) => `${i + 1}. ${c}`).join('\n')}

How to work:
- Load the web tools first: call ToolSearch with query "select:WebSearch,WebFetch". Use WebSearch (mode "standard"; use "extended" for anything from 2025-2026 or hard to find) and open the best sources with WebFetch.
- Prefer primary sources (central banks, statistics offices, legislation, official histories, academic papers, the author's own words) and say whether you actually opened each source or only saw it in search results.
- For each claim decide: confirmed / confirmed with nuance / wrong / could not verify. Judge the claim as a plain-language summary for a general audience: rounding ("about", "roughly", "under one percent") is fine if the numbers support it; a wrong number, wrong date, wrong direction or a claim attributed to the wrong person is not.
- Check every on-screen number exactly (on screen there is no "about").
- If something is wrong or misleading, give the smallest concrete fix (prefer changing on-screen words; changing the narration means re-recording a page, so say so only if needed), and a severity.
- Be concise in the text fields. Do not edit any files.`

const CRITIC_SCHEMA = {
  type: 'object',
  properties: {
    must_fix: { type: 'array', items: { type: 'object', properties: { page: { type: 'string' }, what: { type: 'string' }, fix: { type: 'string' }, evidence: { type: 'string' } }, required: ['page', 'what', 'fix', 'evidence'] } },
    should_fix: { type: 'array', items: { type: 'object', properties: { page: { type: 'string' }, what: { type: 'string' }, fix: { type: 'string' }, evidence: { type: 'string' } }, required: ['page', 'what', 'fix', 'evidence'] } },
    gaps: { type: 'array', items: { type: 'string' }, description: 'claims not checked, weak sources, or anything else unverified' },
    summary: { type: 'string', description: 'plain-language summary for a non-programmer: what was checked, what holds, what changes' },
  },
  required: ['must_fix', 'should_fix', 'gaps', 'summary'],
}

phase('Verify')
const results = await pipeline(GROUPS, (g) => agent(verifyPrompt(g), { label: `verify:${g.key}`, phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'medium' }))
const done = results.filter(Boolean)
const missing = GROUPS.filter((g, i) => !results[i]).map((g) => g.key)
if (missing.length) log(`No result from: ${missing.join(', ')}`)

phase('Gaps')
const critic = await agent(`You are the final reviewer of a fact check of a narrated explainer film about inflation (New Zealand audience; today is 12 October 2026). Seven independent checkers each tried to refute one group of claims. Their verdicts are below as JSON. The script is ${SCRIPT} and the project's research notes are ${LEDGER} (read both).

Do three things:
1. Go through every verdict. Where a checker's reasoning is thin, contradicts another checker, or rests only on search snippets for a number that appears on screen, do your own quick check (load web tools with ToolSearch "select:WebSearch,WebFetch") and settle it.
2. Read the whole script and list any factual claim that none of the groups covered (the groups were: Britain in WWI, Glasgow 1915, Japan and the Bank of England, Germany 1923, the 1973 oil shock, New Zealand 2021-2026, Britain 1920-21 and Mattei). Check any that matter.
3. Produce the final list: must_fix (wrong facts or numbers), should_fix (misleading wording or numbers that need a tweak), and gaps (what remains unverified). For each fix say whether it can be done in on-screen words only, or needs a narration page re-recorded.
Write the summary in plain everyday language for a non-programmer.
${missing.length ? `Note: no verdicts came back for: ${missing.join(', ')}; check those claims yourself.` : ''}

Verdicts:
${JSON.stringify(done, null, 1)}`, { label: 'critic', phase: 'Gaps', schema: CRITIC_SCHEMA, effort: 'medium' })

return { verdicts: done, critic }
