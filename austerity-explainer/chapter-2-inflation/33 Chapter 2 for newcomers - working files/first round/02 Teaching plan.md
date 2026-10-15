# 33 Teaching plan - chapter 2 for newcomers - working notes

**What this is:** a plan for rewriting chapter 2 ("what really causes inflation") so that a newcomer
can follow it. A newcomer here means someone who never saw chapter 1 and has no economics background.
It uses two parts of your Steven Pinker Teaching and Writing Toolkit: "teach for understanding" in its
design mode, and the "clarity workflow". This is a plan, not the script. Source for the series:
Clara E. Mattei, *The Capital Order* (2022). Every fact named here has an id (like C2-H01) in
`chapter-2-inflation/18 Research - chapter 2 - what really causes inflation.md`. No new facts are used.

**Status:** untested. No real viewer has tried this plan. The picture of the viewer below is a set of
guesses, each marked "Assumption", until someone asks the people who got lost (section 16).

## The plan in eight lines

1. Teach one idea, not eight cases: whether new money pushes prices up depends on what it's spent on.
2. Use four real cases plus one picture (the two factories), in three places, with time running one
   way: Britain 1915, then Japan 2013, then New Zealand 2020 to 2021, then New Zealand now.
3. Put Britain 1915 (new money, prices doubled) next to Japan 2013 (twice the money, prices flat), so
   the factory picture explains both. Then use the picture at home.
4. Explain every needed word the first time it's used, in a few plain words. Leave the rest out
   (section 6).
5. Two "before I tell you, guess" moments, each at the end of a page so the film can hold the pause.
   Three short recaps that use the same words each time.
6. About 5 minutes 30 seconds to 5 minutes 50 seconds, about 800 words, about 13 new ideas (one every
   25 seconds), about 24 spoken numbers (the recording has about 37).
7. Take Glasgow 1915, the Bank of England after 2008, Germany 1923, oil in 1973 and Britain 1920 out of
   this chapter. Each has a better home in a later chapter (section 14).
8. Reuse the paintings, 3D scenes and pieces already built. No new paintings are needed.

---

## 1. Why viewers got lost (measured on the recording)

Measured from the word times of Malina's recording (`chapter-2-inflation/narration/word-times.json`)
with a small script (`tools/measure_script_density.py` in this folder).

**She spoke faster than planned.** 689 words in 252 seconds of speech is about 164 words a minute.
Page by page it ran from 147 to 176. Pages 1, 2, 5, 8 and 10 were all above 168. The project's rules
plan for 140. Chapter 1 ran about 157 on the same count (523 words in 3 minutes 20 seconds).

| Page | Words | Seconds | Words a minute | Words a sentence | Spoken numbers |
|---|---|---|---|---|---|
| 1 the question | 53 | 18 | 174 | 6 | 0 |
| 2 shell factory | 59 | 21 | 169 | 10 | 3 |
| 3 two factories | 79 | 30 | 157 | 7 | 0 |
| 4 Glasgow | 49 | 19 | 154 | 8 | 3 |
| 5 Japan and Bank of England | 92 | 32 | 173 | 10 | 7 |
| 6 Germany | 64 | 26 | 147 | 8 | 3 |
| 7 oil and now | 60 | 23 | 158 | 7 | 6 |
| 8 honest edge | 77 | 27 | 175 | 13 | 3 |
| 9 Britain 1920 | 75 | 29 | 158 | 8 | 5 |
| 10 New Zealand now | 81 | 28 | 176 | 12 | 7 |

**Long sentences ran fastest.** Pages that averaged 10 to 13 words a sentence ran at 169 to 176 words
a minute. Pages that averaged 7 or 8 ran at 147 to 158. Page 1 is the exception. Each full stop adds
about 0.7 seconds. This is a pattern seen on ten pages, not a law.

**The "..." pauses barely register.** A word followed by "..." lasts 0.4 to 1.0 seconds. An
ordinary sentence end lasts about 0.9 seconds (word plus gap). So "..." gives a short beat, not a
pause long enough to think in. A real pause has to come from the gap between pages, which the film's
timeline sets.

**Too many numbers.** About 37 spoken numbers (years, percentages, amounts, lengths of time) in 4
minutes 25 seconds of speech: one every 7 seconds. Page 10 alone has 7.

**Too many jumps in place and time.** There are 11: Britain 1915, two imagined factories, Glasgow 1915,
Japan 2013, Britain 2008, Germany 1923, the world in 1973, New Zealand 2026, New Zealand 2021, Britain
1920, then New Zealand 2023 to 2026. They go backwards and forwards, so a viewer has to work out where
and when they are about every 24 seconds.

**Too many new ideas.** About 15 in 265 seconds, one every 18 seconds: inflation; new money; flat out;
the two factories; homes; money that isn't spent; who gains from shares; prices racing as less is
made; the mark against the dollar; rising costs; the honest edge; Covid support; the interest rate;
the cure; Mattei's argument.

**Words a newcomer meets unexplained, or explained too late:**

| Page | Words | What goes wrong |
|---|---|---|
| 1 | "creating new money" | Who creates it, and how, is never said |
| 1 | "go back to the shell factory" | Only chapter 1 viewers know what that is |
| 2 | "paid for partly with new money" | Same problem: where new money comes from |
| 3 | "buyers bid against each other" | Who buys shells? The picture doesn't match (section 9) |
| 4 | "Parliament froze rents" | A new idea (controlling prices) that never comes back |
| 4 | "Homes can't be built in a hurry" | The point comes after the story instead of before it |
| 5 | "So test it" | Test what? The rule was never said in one sentence |
| 5 | "the money it has created" | Unclear what money that is |
| 5 | "the 2008 crash", "shares and other investments" | Not explained |
| 5 | "the gains went to whoever owned the most" | The link to prices is never said: the money went into shares, not the shopping |
| 6 | "the Ruhr", "German marks", "one American dollar costs four trillion marks" | The viewer has to work out that this means the mark was almost worthless |
| 7 | "the cause isn't spending. It's costs." | A whole second cause in seven words |
| 7 | "Leave fuel out... and it's two point nine" | 2.9 compared with what? The target of 1 to 3 percent is never given |
| 8 | "An independent review of the Reserve Bank" | The Reserve Bank isn't explained until page 10 |
| 8 | "the support from the bank and the government" | Support for what? Covid is never named |
| 9 | "/məˈteɪi/" | Who she is is never said in this chapter |
| 9 | "Prices do fall" | Can teach "the cure means prices go back down", which today's cure doesn't aim for |
| 10 | "is raising its interest rate again" | The research asks for "has raised" (C2-XD04) |

---

## 2. Who the viewer is

- Assumption: an adult New Zealander watching on a phone, often in a feed, who may stop at any page.
- Assumption: has not seen chapter 1. The brief says many won't have.
- Knows from everyday life: the checkout, petrol prices, rent, mortgages, the Covid lockdowns and
  the wage subsidy, the cost-of-living years, worry about jobs. Has heard "the Reserve Bank" on the
  news.
- Assumption: doesn't know what "creating new money" means or who does it, what a central bank does,
  how inflation is measured, or what raising an interest rate is for. Knows the World Wars only in
  outline.
- Assumption: takes in numbers slowly by ear. "Fewer than one in a hundred" lands better than "under
  one percent", and "a hundred dollars now costs about a hundred and four" lands better than "four
  point one percent".
- Assumption: may arrive holding one of the wrong ideas in section 7, picked up from politicians or
  social media, and may distrust a film that seems to say "printing money is fine".
- Can't re-read. Everything has to make sense on one hearing; the words on screen help.

**Questions to ask the people who got lost, before the new script is recorded** (they test the
guesses above): What is inflation? Where does new money come from? If the government created lots of
new money, what would happen to prices, and why? What does the Reserve Bank do?

## 3. What the viewer should be able to do afterwards

**Afterwards, the viewer can** say whether new money is likely to push prices up, and why, **when
given** a plain description of what the money is being spent on (for example: paying people to build
houses while every builder is already booked up, or while builders can't find work), **without**
using economics words.

Two smaller goals:

- Tell a price rise caused by spending apart from one caused by a cost, such as fuel.
- Say who pays when the usual cure (a higher interest rate) is used, and tell the part everyone agrees
  on (loans cost more, people spend less, fewer jobs) apart from Mattei's argument (that the cure
  works by weakening workers).

## 4. The central claim, in one sentence

Whether new money pushes prices up depends on what it's spent on: when there are spare workers,
materials and machines it mostly gets more made, and when they're all busy, or the money is chasing
things we can't make more of in a hurry, it mostly pushes prices up.

The stakes, said early: the usual cure for rising prices works by making us spend less, and it costs
some people their jobs. So it matters who's right.

## 5. The chain of causes, one link at a time

1. New money only affects prices once it's spent. [C2-C06, C2-XB03]
2. Spending means orders for things to be made, and wages for the people who make them. [the film's
   framing of C2-M05]
3. If there are spare workers, materials and machines, businesses fill the new orders. More gets
   made, and prices mostly hold. [C2-XA03, C2-M09]
4. If they're all already busy, the orders can't be filled any faster. More money meets the same
   amount of things, so prices go up. [C2-XA03, C2-M05; Britain 1915: C2-H01, C2-H02, C2-H03, C2-XA01]
5. Some things can't be made more of in a hurry even when the rest of the economy has room, such as
   homes. Money aimed at them mostly pushes their price up. [C2-M10 (the Royal Commission says "in
   part"), C2-N08, C2-XC03]
6. Money that sits unspent pushes no shop prices up. Japan doubled the money its central bank had
   created and prices barely moved; mainstream economists say much of it sat in the banks.
   [C2-XB03, C2-XB04, C2-C06]
7. Prices can also rise with no extra spending at all, when a cost that goes into almost everything
   rises, such as fuel. [C2-M06, C2-N05, C2-XC05]
8. The usual cure: the central bank raises its interest rate, the price of borrowing. Mortgages and
   loans cost more, people spend less, businesses hire fewer people, and prices rise more slowly.
   [C2-XD01, C2-M17]
9. So the cost of the cure falls on people with loans and people who lose their jobs. Central banks
   call the lost jobs an unfortunate cost. Mattei argues they're how the cure works: with fewer jobs
   to go round, workers can't ask for more. [C2-M17, C2-H18]
10. So whenever someone says new money causes inflation, ask two questions. Spent on what? And who
    pays to stop it?

Links 1 to 6 answer the viewer's question. Link 7 stops them taking it too far. Links 8 to 10 are the
stakes.

## 6. What the viewer needs to know first

"Known" means everyday knowledge. "Teach now" means explain it in a few plain words the first time
it's used. "Defer" means leave it out of this chapter (where it goes is in section 14).

**From chapter 1** (a newcomer hasn't heard any of this):

| What chapter 1 said | Status | How chapter 2 handles it |
|---|---|---|
| A country that issues its own money isn't a household; it can't run out of its own money | Teach now | One sentence, said as the view of "economists who study how modern money works" [C2-M12] |
| It can run out of workers, materials and machines | Teach now | Same sentence; this triple is the spine of the chapter |
| Britain 1915 ran short of shells, not money | Teach now | Told fresh as the first case (page 3), with no "remember" |
| "Push up interest rates" as part of austerity; "make borrowing expensive, so businesses slow down and jobs disappear" | Teach now | Taught fresh as "the usual cure" (page 11); returning viewers will recognise it |
| Central banks ("hand interest rates to central banks") | Teach now | Defined at first use (page 2) |
| Mattei, and that her views are hers | Teach now | One clause at first use (page 12): "the economist Clara E. /məˈteɪi/, whose book this series follows" |
| The word "austerity" and its three parts | Defer | Not needed in this chapter. If used, define it in one line |
| "The capital order", gold, the experts' conferences, "work more, consume less" | Defer | Not needed |
| Chapter 1's last line ("won't creating it just cause inflation?") | Teach now | Becomes page 1's question, asked fresh |

**New in chapter 2:**

| Thing | Status | How |
|---|---|---|
| Prices, shopping, petrol, rent, mortgages, Covid, jobs | Known | Use them as the concrete anchors |
| Inflation | Teach now | "Prices in general going up", shown with the basket [C2-XA04, C2-M01] |
| A percentage over a year | Teach now, once | "A basket that cost a hundred dollars a year ago costs about a hundred and four now" [C2-XA05; example prices labelled as examples] |
| New money | Teach now | "A country's central bank can create new money" [C2-N06, C2-XB03]. Never say it creates all money (C2-M15) |
| Central bank, the Reserve Bank | Teach now | "Our central bank, the Reserve Bank", on page 2, before it's used anywhere else |
| Unemployment | Teach now | "People who want work and can't find it"; give it as "one in a hundred" where possible |
| Spare workers, materials and machines; flat out | Teach now | The two factories |
| Things we can't make more of in a hurry | Teach now | Homes |
| Interest rate | Teach now | "The price of borrowing", then mortgages and loans |
| The Reserve Bank's target of 1 to 3 percent | Teach now | One clause, so that 2.9 percent means something [C2-N04, C2-M04] |
| An independent review; the Covid Royal Commission | Teach now | Each named once with what it is ("an independent review of the Reserve Bank, out this September") |
| Japan, the yen | Known | |
| Shares and other investments, "the 2008 crash" | Defer | Only needed for the Bank of England case |
| Exchange rates, marks, the Ruhr, reparations, hyperinflation | Defer | Only needed for Germany 1923 |
| Oil embargo, OPEC | Defer | Only needed for 1973 |
| Bonds, bank reserves, the monetary base, the OCR, CPI, tradables, GDP, recession, stimulus, demand, supply, capacity, output | Defer | Never needed; say "sat in the banks", "its interest rate", "the economy shrank", "support" |

## 7. Wrong ideas viewers may bring, and how the chapter meets each

| Wrong idea | What's true in it | How the chapter meets it | Ids |
|---|---|---|---|
| "Printing money always causes inflation." | It can: Britain 1915, and partly New Zealand 2021 | Britain and Japan side by side, then the rule. Never say "never"; say "mostly". Use "new money", never "printing" | C2-H01, C2-XB04, C2-XA03, C2-M09 |
| "The government is like a household, so it'll run out of money." | Households do run out | One sentence, said as the view of economists who study how modern money works; the real limit is workers, materials and machines. Don't argue it further (chapter 1 did) | C2-M12 |
| "Inflation is greedy shops or supermarkets." | There's a real debate about profits | Don't confirm or deny it here. The evidence needs its caveats (an accounting split; the New Zealand supermarket study measured 2015 to 2019 profits, not the price spike), so it goes to a later chapter. Avoid lines that sound like "shops just put prices up" | C2-C17, C2-M07, C2-M08, C2-N13 |
| "The cure is prices falling" / "when inflation comes down, prices go back down." | In 1920 to 1922 Britain, prices did fall | One plain line on the cure page: the aim is for prices to rise more slowly, not to fall. Move Britain 1920 ("prices do fall") to chapter 3 | C2-XD01, C2-N04 |
| "A higher interest rate is a harmless dial" / "it only hurts borrowers." | It's meant to slow spending | Walk the chain: loans cost more, people spend less, businesses hire fewer, jobs go | C2-XD01, C2-M17 |
| "Low unemployment is bad." (a risk the New Zealand 2021 page creates) | The review called 3.2 percent "unsustainable" | Say plainly that almost everyone who wanted a job had one; the only point is that few workers were spare. Say "unsustainable", if used at all, as the review's word | C2-N09 |
| "Inflation means one price going up, like petrol." | Petrol does feed the average | The basket comes first; later, 4.1 against 2.9 percent shows one price lifting the average | C2-XA04, C2-N05 |
| "The Reserve Bank handed the government money." | It did create new money | Say only "created new money". It bought bonds from investors in the market, not from the government | C2-N06 |
| "A central bank creates all of a country's money." | It can create new money | Say "can create". Most money is created by ordinary banks when they lend | C2-M15 |
| "Japan proves new money never matters." | Japan's prices did barely move | Japan comes after Britain (where it did matter) and before New Zealand 2021 (where it partly did), and the reason is given: the money wasn't spent | C2-C06 |
| "The two factories are two countries" (or two industries). | | Say they're two moments any economy can be in. New Zealand shows both, 2020 then 2021 | C2-N15 |

## 8. A concrete case for every big idea

| Idea | Case | Ids |
|---|---|---|
| Inflation is prices in general going up | The same basket costs about 4 percent more than a year ago | C2-XA04, C2-XA05, C2-N05 |
| New money exists, and a central bank can create it | Britain paid for its war partly with new money; Japan's central bank doubled the money it had created; our Reserve Bank created new money from March 2020 | C2-XA01, C2-XB03, C2-N06 |
| A country's limit is workers, materials and machines | Britain 1915: fewer than one in a hundred out of work, and supply ships sunk | C2-H02, C2-H03, C2-XA02 |
| Flat out means new money pushes prices up | Britain: prices roughly doubled by the end of the war | C2-H01 |
| Spare room means new money mostly gets more made | **No real case in the research** (see the gap below) | C2-XA03, C2-M09 |
| Things we can't make more of in a hurry | New Zealand house prices up about 30 percent in the year to mid-2021; the Royal Commission says the Covid response was part of the reason | C2-N08, C2-XC03, C2-M10 |
| Unspent money doesn't raise shop prices | Japan 2013 to 2021: about half a percent a year | C2-XB03, C2-XB04, C2-C06 |
| One economy can move from spare room to flat out | New Zealand: support "right at first" but "too strong for too long"; unemployment the lowest since records began | C2-XC04, C2-N15, C2-N09 |
| Costs can push prices up without extra spending | New Zealand, year to June 2026: 4.1 percent, 2.9 with petrol and diesel left out | C2-N05, C2-XC05, C2-M04, C2-M06 |
| The cure, and who pays | Reserve Bank interest rate from a quarter of a percent to five and a half; unemployment from 3.2 to 5.6 percent, 171,000 people | C2-N10, C2-XD03, C2-N11, C2-XD05, C2-XD01 |
| Mattei's reading of the cure | Her own words about interest rates and jobs (general, not about New Zealand) | C2-H18 |

**The gap.** The research has no real case of the quiet factory with figures: new money, more made,
prices steady. That half of the picture rests on the textbook principle (the IMF's explainer, C2-XA03,
and Keynes via Bell, C2-M09) and on the review calling the early Covid support "appropriate"
(C2-N15). The narration should say it as the mainstream view ("mainstream economists agree on this
much") and keep "mostly". A real case would need new research first; none was done for this plan.

## 9. The two factories: does the comparison hold?

**What it's meant to teach:** whether extra spending turns into more things or into higher prices
depends on whether there are spare workers, materials and machines.

**What maps to what:**

| In the picture | In the real economy |
|---|---|
| A factory | All the businesses in a country (or one moment of it) |
| Workers waiting at the gate | People who want work and can't find it |
| Machines standing still; piles of materials | Machines and materials nobody is using |
| Coins dropping into the yard | New money being **spent**, as new orders and wages |
| Shells coming out | Things made and work done |
| The price counter | Prices in general |
| The quiet factory | An economy with spare workers, materials and machines |
| The flat-out factory | An economy where almost everyone who can work has a job (Britain 1915; New Zealand late 2021) |

**What it lets the viewer work out:** "Will this new money push prices up?" becomes "Is anything
spare, and what is it being spent on?" That's the destination in section 3.

**Where it breaks, and what the script does about each:**

1. **Money only counts once it's spent.** The picture drops coins straight into the yard, but in
   Japan most of the new money never reached a factory at all. Use this on purpose: say in the
   picture that the money arrives "as new orders", so Japan fits the picture instead of looking like
   an exception.
2. **A real economy isn't one factory.** Some trades run out of room while others still have plenty,
   so prices can start rising before everything is busy (Keynes says so himself, C2-M09). It's a
   slope, not a switch. Say "mostly", never "only" or "never".
3. **Time.** The picture is instant. Restarting a quiet factory takes time, and building more room
   (new homes, new factories) takes years. That's why homes get their own line.
4. **Costs.** The picture's price only moves with orders, but fuel can push prices up in either
   factory. That's why page 10 is there.
5. **Who buys the shells.** In the war the government was the only buyer of shells, and the prices
   people felt were food and rent. So never say "buyers bid against each other for shells". Say
   "more money, but no more things, so the price goes up", and let Britain's case (fewer things to
   buy) carry the link to the shopping.
6. **What it leaves out:** what people expect prices to do, and the power of big firms to set prices
   (C2-M16, C2-M07). Not needed here; deferred.

**Verdict:** keep it. It fits the question exactly and is built from chapter 1's own line. With the
fixes above it explains both Britain and Japan.

**Names:** call them **the quiet factory** and **the flat-out factory**, and never change them (not
"idle", "busy", "full", "stretched" or "at capacity"). "Quiet" pictures stopped machines without
calling workers lazy; "flat out" is everyday New Zealand speech. The picture can show any product,
since the 3D set shows shells, but the narration doesn't need to name what's made.

## 10. "Before I tell you, guess" moments

Two only, each placed **at the end of a page**. Since "..." gives under a second, the thinking time
has to come from the gap between pages, held for about 3 seconds with the music up and the question
still on screen. In practice that means recording the question and the answer as two pages (or
leaving a set gap in the mix at that point).

1. **The flat-out factory** (end of page 4). The quiet factory has just filled its orders. "Now the
   second factory. Every worker, every machine, already flat out. The same new money arrives. Before I
   tell you... what do you think happens?" Most viewers will get this right. That's the point: they
   work out the rule themselves.
2. **Japan** (end of page 7). "If new money always pushed prices up... what would you expect? Have a
   guess." The dashed IF MONEY ALONE line already built on page 5 can climb during the pause, then the
   real flat line arrives on the next page. Being surprised here is what makes it stick.

No third guess. A guess about the fuel numbers would be an arithmetic quiz, not a test of the idea.

## 11. Short recaps

Use **the same words** each time, so the second and third times feel like recognition, not a new
idea.

1. **After the factories** (page 6), the rule: "When there are spare workers, materials and
   machines... new money mostly gets more made. When there aren't, or when it's spent on things we
   can't make more of in a hurry... it mostly pushes prices up."
2. **After Japan** (end of page 8): "So it's not how much new money there is. It's what it's spent
   on."
3. **The ending** (page 13): "Spent on what? And who pays to stop it?"

Page 2's sentence about workers, materials and machines doubles as a recap of chapter 1 for viewers
who saw it.

## 12. Pace budget

- **Length:** about 5 minutes 30 seconds to 5 minutes 50 seconds in all (5 minutes of speech at 160
  words a minute, 5 minutes 19 seconds at 150, plus about 29 seconds of gaps).
- **Speaking speed:** plan at 160 words a minute (measured), not 140. At 140, an 800-word script looks
  like 5 minutes 43 seconds of speech; it would really come out at about 5 minutes.
- **Words:** about 800 (the recording has 689), spread over 13 pages of 25 to 90 words.
- **New ideas:** about 13, one every 25 seconds or so (the recording: about 15, one every 18).
- **Cases:** four real ones plus the factory picture. Each real case needs about 30 to 45 seconds:
  where and when, one or two facts, then which factory it was. A 5 to 6 minute chapter can carry four,
  or five if one is a single line. The recording carried eight in 4 minutes 25 seconds, about twice
  what a newcomer can follow.
- **Places and times:** three places, and time runs one way: 1915, 2013, 2020 to 2021, now. The
  recording jumped 11 times, backwards and forwards.
- **Numbers:** about 24, against about 37. Never two new numbers in one sentence, except a "from... to"
  pair. Give each one a plain anchor ("fewer than one in a hundred").
- **Sentences:** aim for about 8 words, rarely over 12. The measured pages suggest this slows the
  delivery as well as easing the listening.
- **Pauses:** 2 guesses at about 3 seconds, 12 page turns at about 1.5 seconds, 4 seconds at the end.

## 13. The new running order

Times assume 160 words a minute plus the gaps above. The ids are the facts each page may use. "Pictures"
names what already exists in `film-kit/paper-film/scenes/inflation-chapter-2/` (from each file's
opening note).

| # | Page | The one new idea | Case and facts | Words, seconds | Check | Pictures reused |
|---|---|---|---|---|---|---|
| 1 | The question | Inflation is prices in general going up. Stakes: the cure costs jobs | The basket [C2-XA04, C2-XA05, C2-M01]; stakes [C2-M17, C2-XD01] | 65, 24 | | page-1: chamber and politician, checkout basket, $100 to $104.10 example tag, THE WHOLE BASKET |
| 2 | Where new money comes from | A central bank can create new money (ours is the Reserve Bank); the real limit is workers, materials and machines | [C2-N06, C2-M12, C2-XA01] | 60, 23 | Recap of chapter 1 | page-1 chamber and NEW MONEY, then page-3's three cut-outs (worker, materials, lathe) with their words; a card bank from page-9 labelled RESERVE BANK if wanted. Code only |
| 3 | Britain, 1915 | Flat out plus fewer things to buy means prices go up | [C2-H02, C2-XA01, C2-H03, C2-XA02, C2-H01] | 70, 26 | | page-2 as it is: hall, 100 dots, notes, ships, ABOUT ×2 |
| 4 | Two factories: the quiet one | Spare room means new money mostly gets more made | Picture; textbook view [C2-XA03, C2-M09] | 70, 26, then a 3-second hold | Guess 1 | page-3 set: works A |
| 5 | The flat-out factory | No room means new money mostly pushes prices up | Picture [C2-XA03, C2-M05]; "Britain at war was the flat-out factory" | 45, 17 | Answer to guess 1 | page-3 set: works B, counter, the three cut-outs |
| 6 | The rule, and homes | Things we can't make more of in a hurry | Film's framing, consistent with [C2-M10] | 50, 19 | Recap 1 | page-8 part A: YES, IT CAN on works B, the card house and its climbing tag (no figures) |
| 7 | Japan: the guess | | [C2-XB03] | 45, 17, then a 3-second hold | Guess 2 | page-5 part A: noodle counter, money stack doubling, ×2 MONEY / IN TWO YEARS, dashed IF MONEY ALONE line |
| 8 | Japan: the answer | Money that isn't spent doesn't push shop prices up | [C2-XB04, C2-C06] | 65, 24 | Recap 2 | page-5 part A: the real flat line, ABOUT ½% A YEAR |
| 9 | Here, 2020 to 2021 | One country can move from the quiet factory to the flat-out one | [C2-N06, C2-N09, C2-XC04, C2-N15, C2-N08, C2-XC03, C2-M10] | 90, 34 | Using the picture on a new case | page-8 parts B and C: New Zealand street, 3.2%, LOWEST SINCE 1986, card house +30%, the review desk and its two stamps; a short return to page-3's works B if wanted |
| 10 | Prices now | Rising costs, not spending | [C2-N05, C2-XC05, C2-M04, C2-M06, C2-N04] | 55, 21 | Tell the two causes apart | page-7 part B: New Zealand 2026 bars, 4.1% and 2.9%; add a 1 to 3% band. Code only |
| 11 | The usual cure | Interest rate means the price of borrowing; it works by making us spend less; prices rise more slowly, they don't fall | [C2-XD01, C2-M17, C2-N10, C2-XD03, C2-N11, C2-XD05, C2-XD04, C2-N12] | 80, 30 | | page-10 part A: the dial 0.25 to 5.5, the 100 dots 3.2 to 5.6, RISING AGAIN 2.25 to 2.75 |
| 12 | Who pays | Mattei's reading against the central banks' | [C2-H18, C2-M17] | 50, 19 | Tell her argument apart from the facts | page-9 part B without the 1920 and 1921 bars: dole queue, iron weight on the pay packet, her book with its credit |
| 13 | Spent on what? | | | 30, 11, then a 4-second fade | Recap 3; the question to use next time | page-10 part B: the politician, SPENT ON WHAT? and WHO PAYS TO STOP IT? |

**Page 9 is the heaviest.** It carries Covid, the new money, the record low unemployment, the review
and the houses. If it runs over about 35 seconds, split it in two: 9a (flat out, and the review) and
9b (homes, and the Royal Commission's "part of the reason").

**How the arc follows the toolkit's default order:**
1. Something the viewer has seen: the basket costs more, and the claim that new money causes it
   (page 1).
2. Linked to what they know: a country isn't a household, and its limit is people and things (page 2).
3. A concrete case: Britain 1915 (page 3).
4. The general idea: the two factories, then the rule (pages 4 to 6).
5. How it works, with no hidden steps: money has to be spent (Japan, pages 7 and 8), and one country
   can be in either factory (New Zealand, page 9).
6. The conclusion, its limits and what's uncertain: costs are a second cause (page 10); the cure and
   who pays, with Mattei's view said as hers (pages 11 and 12); the two questions (page 13). The
   uncertainty is carried by "mostly", "partly", the review's own judgement, and "Mattei argues".

### Example lines

These show that the budget fits and where the wording carries a fact or a qualification. Every fact
is checked against the ids above. They're starting points for the script writer, not the script.
They follow the voice rules: numbers written as said, "..." for a beat, no capitals for emphasis, no
bracket cues.

1. You've heard it. If the government creates new money... prices will shoot up. Sounds like common
   sense. And you've felt prices go up. A basket of shopping that cost a hundred dollars a year ago
   now costs about a hundred and four. Prices in general going up... that's called inflation. So does
   new money cause it? Sometimes. And it matters who's right. Because the usual cure for rising prices
   costs some people their jobs.
2. So where does new money come from? Not just from taxes. A country's central bank can create it.
   Ours is the Reserve Bank. Economists who study how modern money works say a country like ours
   can't run out of its own money. It's not a household. What it can run out of is workers, materials
   and machines. Britain found that out in a war.
3. Britain, nineteen fifteen. Almost everyone who can work has a job. Fewer than one in a hundred is
   out of work. The war is paid for partly with new money. And German submarines are sinking the ships
   that bring in food and materials. So there's more money... and fewer things to buy. By the end of
   the war, prices have roughly doubled.
4. Why? Picture two factories. In the first, half the machines stand still. Workers wait at the gate
   for a job. Call it the quiet factory. New money gets spent there, as new orders. The workers go in.
   The machines start up. More gets made... and the price hardly moves. Now the second factory. Every
   worker and every machine is already flat out. The same new money arrives. Before I tell you...
   what do you think happens?
5. It can't make any more. There's more money, but no more things. So the price goes up. Mainstream
   economists agree on this much. Britain at war was the flat-out factory. Short of workers, materials
   and machines.
6. So here's the rule. When there are spare workers, materials and machines... new money mostly gets
   more made. When there aren't, or when it's spent on things we can't make more of in a hurry, like
   homes... it mostly pushes prices up.
7. Let's test it. Japan, twenty thirteen. Japan's central bank sets out to double the money it has
   created... in just two years. If new money always pushed prices up... what would you expect? Have a
   guess.
8. Prices barely moved. For eight years, they rose about half a percent a year. Economists give a few
   reasons. A big one: most of that new money just sat in the banks. It never got spent in the shops.
   So it's not how much new money there is. It's what it's spent on.
9. Now, here. In twenty twenty, Covid hit. The Reserve Bank created new money, and the government
   spent to hold the economy up. By the end of twenty twenty-one, unemployment was three point two
   percent. The lowest since records began. Almost everyone who wanted a job had one. We'd moved from
   the quiet factory to the flat-out one. An independent review of the Reserve Bank, out this
   September, says the support was right at first... but too strong, for too long. And homes? House
   prices rose about thirty percent in a year. The Covid Royal Commission found the Covid response was
   part of the reason.
10. But not every price rise comes from spending. In the year to June, prices rose four point one
    percent. Leave out petrol and diesel... and it's two point nine. That's inside the Reserve Bank's
    target of one to three percent. When fuel costs more, almost everything that's made or moved
    costs more. That part isn't too much spending. It's a cost.
11. So what's the usual cure? The Reserve Bank raises its interest rate... the price of borrowing.
    Mortgages and loans cost more. People spend less. Businesses hire fewer people. And prices rise
    more slowly. Not fall... rise more slowly. From late twenty twenty-one, the Reserve Bank pushed
    its interest rate from a quarter of a percent to five and a half. Since then, unemployment has
    climbed from three point two percent to five point six. A hundred and seventy-one thousand people
    are looking for work. Not all of that is the interest rate. But central banks expect the cure to
    cost some jobs. And this year, the Reserve Bank has raised its interest rate again.
12. So who pays? People with loans... and people who lose their jobs. Central banks call that an
    unfortunate cost. The economist Clara E. /məˈteɪi/, whose book this series follows, sees it
    differently. She argues the cure works by putting people out of work. With fewer jobs to go round,
    workers can't ask for more.
13. So next time someone tells you new money causes inflation... ask them two things. Spent on what?
    And who pays to stop it?

The example lines come to 798 words in 115 sentences (about 7 words a sentence): 5 minutes of speech
at 160 words a minute. Pages 9 and 11 run long (104 and 113 words, about 40 seconds each, against
budgets of 90 and 80): trim them, or split each into two pages. Notes on the lines that carry a fact
or a qualification:
- Line 1: "about a hundred and four" is C2-XA05's "about four percent more", using example prices (the
  page-1 tag already says it's an example). "Some people" keeps C2-M17's "some pain".
- Line 2: "can create" (not "creates all", C2-M15); "a country like ours" (C2-M12 applies only where
  a country borrows in its own money, as New Zealand does).
- Line 3: "partly" (C2-XA01); "fewer than one in a hundred" for 1915 is right but only just (C2-H02,
  second fact check).
- Line 5: "mainstream economists agree" is C2-XA03's "mainstream textbook framing".
- Line 8: "a few reasons... a big one" keeps C2-C06's list of rival explanations.
- Line 9: the review does not mention house prices (C2-XC04), so the houses get their own source, the
  Royal Commission's "in part" (C2-M10). "About thirty percent" holds for the year to mid-2021 only
  (C2-XC03).
- Line 10: "that part" matters. Only the fuel part is a cost; never say the whole rise is "mostly
  fuel" (C2-M18 trap). "Leave out petrol and diesel" is Stats NZ's own measure (C2-XC05, second fact
  check).
- Line 11: "has raised" (C2-XD04). "Not all of that is the interest rate" (C2-XD05: unemployment also
  rose while the rate was being cut). 171,000 is the total looking for work, not the increase
  (C2-N11 trap).
- Line 12: "an unfortunate cost" is how central banks put it (C2-M17); the rest is Mattei's general
  argument (C2-H18), not something she said about New Zealand (C2-H19).

## 14. What to cut, merge or move to a later chapter

| Recorded page | Decision | Why | Where it goes |
|---|---|---|---|
| 1 The question | Keep and rebuild | Needs the premise for newcomers and the stakes; drop "go back to the shell factory" | New pages 1 and 2 |
| 2 Britain 1915 | Keep, and slow it down | The first real case | New page 3 |
| 3 Two factories | Keep, give it more time, and split it for a guess | The heart of the chapter | New pages 4 and 5 |
| 4 Glasgow 1915 | Cut the story; keep its idea | A fourth place, and a loose end (the rent freeze is never used again) | The idea ("homes can't be built in a hurry") goes to new pages 6 and 9. The story fits chapter 3 (Britain after the war) or a later chapter on what austerity did to people; its checked facts (C2-H04, C2-XB01, C2-XB02) and the page-4 street are ready |
| 5 Japan | Keep, and give it room | The case that breaks "always" | New pages 7 and 8 |
| 5 Bank of England after 2008 | Move to a later chapter | Needs "shares" and "the 2008 crash" explained, and adds a second point (who gains) | A later chapter on who gains (bargaining power, or what it did to people). C2-XB05, C2-XB06 and C2-C10 and page-5 part B are ready. This is the first thing to bring back if you want more "who gains" in this chapter |
| 6 Germany 1923 | Move to a later chapter | Five new names in 26 seconds (the Ruhr, French and Belgian soldiers, marks, the dollar rate, a trillion) | The chapter on where austerity was tested (Germany's 1923 to 1924 recovery was itself austerity, C2-C03), or a short "what about Germany?" clip. If you want the objection answered here, one line on page 6 at most: "Germany in nineteen twenty-three is the famous case. There, new money was paid out while less and less was being made." [C2-C02, C2-XC02]. Default: leave it out |
| 7 Oil in 1973 | Move to a later chapter | A fifth place, teaching what the New Zealand fuel figures teach | The 1970s and Thatcher chapter (C2-C14, C2-XC01) |
| 7 New Zealand fuel, 2026 | Keep, and move it to "now" | Current, local, and the second cause | New page 10 |
| 8 The honest edge, New Zealand 2021 | Keep, rebuilt as "one country, both factories" | Using the picture on the viewer's own country | New page 9 |
| 9 Britain 1920 | Move the case; keep the cure and Mattei's argument | A second trip to Britain, out of time order, and "prices do fall" | Chapter 3 (Britain and Italy in the 1920s): C2-H07, C2-H08, C2-H09, C2-H17, C2-XD02 and page-9's pictures are ready. The cure is told with New Zealand on new pages 11 and 12 |
| 10 New Zealand now, and the close | Keep; merge with the cure; fix the tense; add the qualification | | New pages 11 to 13 |

## 15. Writing it for the ear

**One plain name for each thing, all the way through:**

| Thing | Name | Never |
|---|---|---|
| Money a central bank creates | new money (create) | printing, money minting, stimulus, money supply |
| The rise in prices | "prices going up". "Inflation" only when quoting the claim, and in its definition | the cost of living, price growth |
| New Zealand's central bank | the Reserve Bank ("our central bank, the Reserve Bank" once, on page 2) | the bank, RBNZ |
| What the Reserve Bank raises | its interest rate, the price of borrowing | the OCR, the cash rate, the rate, **rates** (in New Zealand "rates" means council rates, which C2-N04 itself mentions) |
| The two pictures | the quiet factory, the flat-out factory | idle, busy, full, stretched, at capacity |
| What can run out | workers, materials and machines (always in that order) | resources, capacity |
| Homes and the like | things we can't make more of in a hurry | supply-constrained goods |
| Raising the interest rate to fight rising prices | the usual cure | tightening, austerity (unless defined) |
| Covid help | the support from the Reserve Bank and the government | stimulus |
| The September 2026 report | an independent review of the Reserve Bank | the Orphanides-Archer review |

**Sentences** (from "write for readers", applied):
- Familiar first, new last. "Almost everyone who can work has a job. Fewer than one in a hundred is
  out of work." Not: "Unemployment, the share of workers without a job, is under one percent."
- Don't split a subject from its verb with an aside. Not "Its central bank, the bank that creates the
  yen, sets out to...", but two sentences.
- End each case by naming its factory, so the viewer knows where to file it.
- Put a linking word wherever a listener could guess the wrong link: so, because, but, then.
- Say who did what: "The Reserve Bank raised its interest rate", not "rates went up".
- Make each kind of claim audible: a fact (said plainly), the textbook view ("mainstream economists
  agree"), a judgement ("an independent review says"), an argument ("Mattei argues"), the film's own
  picture ("picture two factories").
- Read every page aloud before recording. Cut anything that trips the tongue.
- Last pass against empty phrases: no stock uplift, no "in this video", nothing the ledger doesn't
  support.

**For Malina:**
- Write numbers as said, every time. The recording left "1915", "1923", "1973", "1920" and "2008" as
  digits; write "nineteen fifteen".
- "..." only at a real turn. It gives about half a second to a second; the long pauses are page
  gaps.
- No capitals for emphasis, nothing in brackets (the accent line is added later), Mattei written
  /məˈteɪi/. The Ruhr isn't needed if Germany moves.

**Naomi Klein in spirit only:**
- Stakes in the first 30 seconds: the usual cure costs people their jobs.
- Talk to "you", and ask the viewer's own questions out loud ("So where does new money come from?",
  "So who pays?").
- Real people and places: the people at work in Britain in 1915; New Zealanders through Covid; people
  with mortgages; 171,000 people looking for work.
- Keep asking who pays, and end on it.
- Urgency comes from facts and short sentences, never from shouting.
- None of her wording, titles or coined phrases. Avoid the word "shock" altogether: it's close to her
  best-known phrase, and it's jargon here anyway.
- "Who gains" is thinner once the Bank of England case moves out. It lives in Mattei's argument
  (workers can't ask for more) and in the closing question. Bringing the Bank of England back is the
  way to strengthen it.

**The Pinker toolkit:** the principles above, never Pinker's own voice or manner.

## 16. Did it work? A test with real viewers

The toolkit asks for evidence from real learners, not the writer's own feeling that it reads well. No
viewer has tried this plan. The best test is cheap: read the new script aloud (or play it) to one or
two of the people who got lost, before Malina records it, then ask:

| # | Question | A strong answer | A sign the wrong idea survived | What to change |
|---|---|---|---|---|
| 1 | When does new money push prices up, and when doesn't it? | Spare workers and machines, against everything already busy, or things we can't make more of quickly | "Always", or "when there's too much of it", with no mention of what it's spent on | Make page 6's rule slower and give it a picture |
| 2 | Britain in 1915 and Japan in 2013 both created new money. Why did prices double in one and barely move in the other? | Britain was flat out with fewer things to buy; Japan's money mostly wasn't spent | "Japan is different" | Strengthen page 8's "why" |
| 3 | **(the key one)** The government creates new money to pay builders to put up state houses. Will it push prices up? What would you want to know first? | "Are there builders who can't find work, or is everyone booked up?" | A flat yes or no | If question 1 passed but this one failed, the rule was memorised but not understood: make page 9 say "same country, two factories" more plainly |
| 4 | Prices rose 4.1 percent, and 2.9 without petrol and diesel. Was that new money? | Much of the extra was a cost (fuel), not extra spending | "Yes, the government spent too much" | Page 10 is too fast; give it more room |
| 5 | Who pays when the Reserve Bank raises its interest rate? Does everyone agree that's the point? | People with loans and people who lose jobs. "Mattei argues it"; central banks call it a cost | Saying Mattei's argument as plain fact | Make "she argues" louder on page 12 |

If anyone says the cure "makes prices go back down", strengthen page 11's "not fall... rise more
slowly". If only one question can be asked, ask question 3: it is the destination itself.

Afterwards, add a short self-test to the post or description (chapter 1's file has one), with answers
kept out of sight.

## 17. How the toolkit was used

- **Teach for understanding, design mode:** a destination the viewer can do, not "understand"; a
  learner model with assumptions marked; the expert's ideas unpacked (one-sentence claim, the chain of
  causes, the terms, what to teach now or defer, a case for every idea); the toolkit's default order
  (something seen, then something known, a case, the idea, how it works, then limits); the comparison
  test (section 9); checks at more than one level (guessing, recaps, using the idea on a new case,
  telling an argument from a fact); a plan for real-viewer feedback; and revising in two passes,
  facts and model first, wording second.
- **Clarity workflow:** ground truth (the ledger only), destination, model, closing the gaps, a test,
  shaping the prose, testing on a viewer, revising.
- **Write for readers:** familiar before new, fixed names, visible actors, linking words, reading
  aloud, a last pass against empty phrases.
- These steps are the toolkit's own workflow, not a teaching method Pinker published or tested. The
  "curse of knowledge" is Camerer, Loewenstein and Weber's term; "classic style" is Thomas and
  Turner's.

## What was checked and what wasn't

- **Checked:** every fact id named here against the ledger, including the qualifications in its last
  column and its Traps; the speaking speed and pause lengths, measured from the recording's word times
  (ElevenLabs' transcript times, not the audio itself); what each existing page shows (from each
  file's opening note, not by watching it).
- **Not checked:** no viewer has tried the plan. The example lines were checked against the ledger by
  me alone, not by the project's fact checkers. Whether Malina's voice model (eleven_v4) has a speed
  setting wasn't checked. The voice cost is only an estimate from chapter 1's rate: about 8 credits a
  word, so about 6,400 to 7,000 credits for about 800 words plus the accent lines, roughly US$1.10 to
  US$1.25. Confirm it with you before recording.

## Traps

- Plan by 160 words a minute, not 140, or the chapter will come out about 40 seconds short and feel
  rushed again.
- A "..." is not a pause long enough for a guess. Put each guess at a page end and set the hold in
  the timeline.
- The September-quarter price figure comes out on 22 October 2026, the next Reserve Bank decision is
  on 28 October, and the next unemployment figure is on 4 November. Re-check 4.1, 2.9, 5.6 and 171,000
  on the day of recording. The election is on 7 November: name no party, and keep the invented
  politician free of party colours.
- Never "mostly fuel" (C2-M18 trap). Only the fuel part is a cost.
- "Has raised", not "is raising" (C2-XD04).
- House prices aren't counted in the inflation figure. Keep them apart, and don't put the review's
  verdict next to the houses as if it caused them (C2-XC04).
- Never say a central bank creates all of a country's money (C2-M15), or that the Reserve Bank gave
  the government money (C2-N06).
- Never say "MMT". Mattei's views are always "she argues". Never use Naomi Klein's phrases.
- In New Zealand, "rates" alone means council rates. Always say "interest rate".
- On-screen words must stay short forms of what Malina says: if a line is cut from the narration, cut
  its words from the page too.
