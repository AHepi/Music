# What this does: writes section 2 of the shot plan (the shots, page by page) from shots.json, so the plan
# and the shot list can never disagree. Then puts it into the plan where the line <<PAGES>> stands.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
shots = json.load(open(os.path.join(HERE, '..', 'shots.json')))

TITLE = {1: 'The question', 2: 'Who can create new money', 3: 'The quiet factory', 4: 'The flat-out factory, the first guess',
         5: 'The rule', 6: 'Britain at war', 7: "Glasgow's homes", 8: 'Japan, the second guess', 9: 'Japan, the answer',
         10: 'New Zealand, the third guess', 11: 'New Zealand, the answer', 12: 'The usual cure', 13: 'Who pays, here',
         14: 'Two views', 15: 'Back at the checkout', 16: 'Spent on what?'}
TEACH = {
 1: "inflation is prices in general going up, the whole basket; the warning; why it matters (the usual cure makes many loans cost more and can put people out of work).",
 2: "here, the Reserve Bank can create new money (and tries to stop prices going up too fast); economists who study how modern money works argue that our government can't run out of its own money, but it can run out of workers, materials and machines.",
 3: "the two-factories picture, each one standing for a whole country; the quiet factory has spare workers; new money spent there gets more things made, so prices barely move.",
 4: "in the flat-out factory every worker and machine is busy and no one waits at the gate; the same new money is spent there; what happens to prices?",
 5: "why prices go up when nothing is spare (more money, the same things to buy, so businesses can ask more); the rule, which most economists agree on.",
 6: "a real case close to the flat-out factory: millions went to fight; soon fewer than one worker in a hundred was out of work; ships were sunk; the war was paid for partly with new money. More money and fewer things to buy, so prices roughly doubled.",
 7: "the picture works for one kind of thing, homes; war workers came to Glasgow, where there were already too few homes; builders and materials went to the war; landlords raised rents, up to a quarter in places; about twenty thousand families refused the extra; Parliament brought rents on small homes back.",
 8: "Japan in 2013; Japan's version of our Reserve Bank planned to double the money it had created, in two years; if the warning is right, prices should go up fast. Guess.",
 9: "prices barely moved for about eight years, about half a percent a year on average; one reason: most of the new money sat in the banks, and in our picture never reached the factory; so what matters is whether it is spent, and on what.",
 10: "here, from 2020, the Reserve Bank created new money and the government spent more, including help paying wages; by the end of 2021 about three in a hundred were out of work. Which factory was New Zealand closer to?",
 11: "close to the flat-out factory; prices went up fast, partly because more was being spent and partly because of prices overseas, like oil; at the peak the biggest push came from the price of building new homes, and rents.",
 12: "the Reserve Bank raises its interest rate; interest is the extra you pay back when you borrow; many loans cost more, so people have less to spend; businesses sell fewer things and hire fewer people; prices go up more slowly, usually not down; in the picture, the flat-out factory slows and more workers wait at the gate.",
 13: "the Reserve Bank raised its interest rate again and again from late 2021 into 2023; many loans cost more and jobs got harder to find; nearly six in a hundred were out of work by the middle of 2026, up from about three, and the interest rate isn't the only reason; who pays: many people with loans, and people put out of work.",
 14: "America's version of our Reserve Bank says the cure would probably mean fewer jobs, unfortunate but not the goal; Mattei argues that fewer jobs are the cure's main goal: with more workers waiting at the gate, people with jobs have less power to ask for higher wages.",
 15: "a hundred-dollar basket in June 2025 cost about a hundred and four a year later, and would have cost about a hundred and three if petrol and diesel prices hadn't changed; petrol and diesel push up almost everything made or moved, in both factories; so part of what you felt came from petrol and diesel.",
 16: "the rule again, in the same words; the two questions to ask next time.",
}
import re
def say(word):
    m = re.match(r"^(.*?)(?: \((\d)\))? \(([\d.]+) s\)$", word)
    if word.startswith('('):
        return word.strip('()')
    w, n, at = m.groups()
    return f'"{w}"' + (f" ({n})" if n else "") + f", {at} s"
def end(event):
    return event if event.endswith(('.', '?', '!', '...')) else event + '.'
LONG = {"top band (about 0.05 to 0.22 down), left-aligned from 0.06 across, kept left of 0.90": "top band",
        "top band, second line under the first": "under it",
        "small line under the card above": "small, under it",
        "small credit, left, about 0.75 down (above the strip where phone apps show captions)": "small credit",
        "100-dot panel in the top band, left, 0.06 to 0.45 across": "100-dot panel, top band"}
def short(where):
    for k, v in LONG.items():
        where = where.replace(k, v)
    return where
COST = {'plain': "about 0.8 s a frame held", 'fx': "about 1.05 to 1.5 s a frame held (live effects)"}

out = []
pages = sorted({s['page'] for s in shots})
for p in pages:
    ps = [s for s in shots if s['page'] == p]
    out.append(f"### Page {p} - {TITLE[p]} ({ps[0]['start']:.1f} to {ps[-1]['end']:.1f} s)\n")
    out.append(f"**Must teach:** {TEACH[p]}\n")
    for s in ps:
        out.append(f"**Shot {s['shot']} - {s['view']}, {s['subject'][0].lower() + s['subject'][1:]} ({s['start']:.1f} to {s['end']:.1f} s, about {s['seconds']:.0f} s).**")
        if s['move'] == 'none':
            out.append("- Move: none (held).")
        else:
            out.append(f"- Move: {s['move']}")
        out.append("- Events, each on its spoken word:")
        for b in s['beats']:
            out.append(f"  - {say(b['word'])}: {end(b['event'])}")
        if s['cards']:
            out.append("- Words on screen: " + "; ".join(f"**{c['text']}** ({short(c['where'])})" for c in s['cards']) + ".")
        live = s['effects']
        kind = 'fx' if live else 'plain'
        eff = ", ".join(live) if live else "none live"
        cost = COST[kind] + ("; about 5.6 to 7 s a frame during the slide" if s['move'] != 'none' else "")
        out.append(f"- Light effects: {eff}. Cost: {cost}.")
        out.append("")
text = "\n".join(out)
plan_path = os.path.join(HERE, '..', 'shot-plan.md')
plan = open(os.path.join(HERE, 'template.md')).read()
if '<<PAGES>>' in plan:
    plan = plan.replace('<<PAGES>>', text.rstrip() + "\n")
    open(plan_path, 'w').write(plan)
    print('inserted', len(text), 'characters')
else:
    print('no <<PAGES>> marker; nothing done')
