export const meta = {
  name: 'house-sample-check',
  description: 'Independent check of the house sample stills before filming',
  phases: [{ title: 'Check', detail: 'two independent critics, medium effort' }],
}
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/house'
const K = '/home/user/work/paper-pop-up-film-kit'
const CONTEXT = `Context: a narrated explainer series for a tall phone screen (1080x1920) on Clara E. Mattei's book "The Capital Order" (austerity). The user (not a programmer) asked: "Ok do a sample video of the house and how it would work." "The house" is plan 2 in ${'/home/user/Music/austerity-explainer/experiments/26 Plans - the look from chapter 3 on.md'} (read its Plan 2 section): each chapter staged in one cut-away building of society: where it's decided at the top, what public money builds in the middle, work and home on the ground floor, the mine in the cellar, the street in front. This sample is about 37 seconds with NO narration (music only); words on screen carry it. It is a free test built from the series' existing paintings and cut-outs (no new paintings). Beats: 0-7 s Britain 1922, floors light up and are named; 8-11 s THE CUTS (scissors drop into the middle floor, scaffolding falls, builders and half-built houses go, the floor darkens, the school keeps half its light); 12-16 s camera moves in to the vault, BACK ON GOLD (1925), gold bars land with jolts; 16-20 s camera moves down through the house (dust falls from ceilings, the kitchen's pay packet shrinks); 20-23 s the mine's ceiling comes down, COAL OWNERS WANT LOWER PAY, LONGER HOURS; 23-26 s camera pulls back; 26-29 s 1926 THE GENERAL STRIKE: factory and mine go dark, chimney smoke stops, a crowd with blank placards fills the street; 29-32 s crowd fades, three miners stay out in snow, THE MINERS HELD OUT FOR MONTHS; 32-37 s ONE HOUSE / WHO DECIDES, WHO PAYS, and a note "A sample of the look for chapter 3. History not yet researched." then fade.
Files: stills (named still-TIME.jpg, TIME in seconds) in ${S}/s4/ and a contact sheet ${S}/s4/sheet.jpg; the code ${K}/paper-film/scenes/house-sample/page-1.js and house-set.js (read their header notes). You can render more stills yourself: cd ${K} && timeout 900 node paper-film/tools/render-paper-film.mjs house-sample ${S}/check-YOURNAME --stills 3.1 12.0 (times separated by spaces; about 2 seconds each). Do not edit any project file. Put scratch files only under ${S}/check-*/.`
const SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', description: 'two or three plain sentences: does the sample show how the house would work, and is it ready to film?' },
    problems: { type: 'array', items: { type: 'object', properties: {
      what: { type: 'string' }, where: { type: 'string', description: 'time in seconds and place in the frame' },
      severity: { type: 'string', enum: ['must fix before filming', 'should fix', 'minor'] }, fix: { type: 'string', description: 'a concrete, cheap fix' } },
      required: ['what', 'where', 'severity', 'fix'] } },
    strengths: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'problems', 'strengths'],
}
phase('Check')
const [look, rules] = await parallel([
  () => agent(`${CONTEXT}

Your job: a sceptical film director's check of the look and the storytelling. Look at every still (zoom into single stills where needed). Judge: does a viewer understand the house idea (who decides at the top, who pays at the bottom) without narration? Is each beat readable on a phone (sizes of words, figures, rooms)? Is the frame balanced and full? Do the camera moves land on something meaningful? Anything that looks broken (things floating, poking through walls, glowing outlines in dark rooms, things cut off by the frame edge, words over busy areas, black empty areas, a beat that happens off screen)? Render extra stills at moments between the given ones if you suspect a problem (for example the scissors landing around 8.2-8.6, the dust 16.5-19, the strike crowd 26.0-26.6, the very end 36-37). List problems ranked, each with a cheap concrete fix.`, { label: 'check:look', phase: 'Check', schema: SCHEMA, effort: 'medium' }),
  () => agent(`${CONTEXT}

Your job: the rules and facts check. (1) Every word shown on screen (read them in the stills and in draw2D in page-1.js): is each historical claim correct and fairly worded for Britain: spending cuts in 1922 (the "Geddes Axe"), the return to the gold standard in 1925, coal owners seeking lower pay and longer hours in 1925-26, the General Strike of May 1926, the miners holding out for months after it? Use web searches to confirm and give sources. Is "WHO DECIDES, WHO PAYS" an interpretation that must be attributed to Mattei under the house rule "Mattei's interpretations are said as hers", or is it fine as the sample's own framing given the honesty note? (2) House rules: no drawn portraits of real people (the cut-outs are invented figures from chapter 1: check none is a likeness of a real person); no political party colours or symbols (check the placards, flags, banners); never the letters M-M-T; no capitals for emphasis inside sentences (all-caps titles are allowed); words on screen readable (not in the bottom 380 px or the right 140 px for important words). (3) Anything in the visuals that is historically wrong for 1920s Britain and would mislead. List problems ranked, each with a cheap concrete fix (exact new wording if a word should change).`, { label: 'check:rules-and-facts', phase: 'Check', schema: SCHEMA, effort: 'medium' }),
])
return { look, rules }
