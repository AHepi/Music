# 33 Audit - chapter 2 script - newcomer listening

Source: Clara E. Mattei, The Capital Order (2022).

**What this is:** a check of chapter 2 ("what really causes inflation") exactly as Malina recorded
it. It marks every point where a first-time viewer would get lost on one hearing at normal speed,
and why. It uses the teaching audit and the revision checks from your Steven Pinker Teaching and
Writing Toolkit. It changes nothing. The rewrite comes next.

**Files read:** the recorded script (19 Script), the research ledger (18 Research), the outlines
(18 Outlines), chapter 1 as recorded (07 Script), the voice and writing rules (01 Rules), the house
rules (06), the toolkit's three parts, the opening notes of page-1.js to page-10.js, and the
word-by-word timings of the recording (`chapter-2-inflation/narration/timeline.json`).

**What is measured and what is guessed:** the speed, the pauses and the word counts are measured
from the recording. The three listeners are imagined. What each one knows is my assumption, and no
real newcomer has heard the film yet. The toolkit is clear that imagining a newcomer is not the same
as testing one, so section 8 gives a short listener test to run on real people.

The three listeners:

- **S**: a 17-year-old school student. Quick, used to phone video, has heard of inflation and
  probably the Reserve Bank. Born around 2009, so "the 2008 crash" is history. Knows little about
  the First World War or 1970s oil.
- **B**: a 60-year-old retired builder who left school at 16. Knows building, mortgages, interest
  rates and "the Reserve Bank put rates up". Likely believes printing money causes inflation. Slower
  with decimals and big abstract numbers heard at speed.
- **E**: an adult whose first language isn't English. Thinks fast, but idioms, words with two
  meanings, long sentences and quick speech in a New Zealand accent all cost them.
- **All**: all three.

---

## 1. What the recording measures

**Speed.** Malina speaks at **164 words a minute** on average. The project plans for 140. Chapter
1 ran at about 156 (about 520 words in about 3 minutes 20 seconds of speech).

| Page | Words | Seconds of speech | Words a minute | Load items | Load items per 10 seconds |
|---|---|---|---|---|---|
| 1 the question | 53 | 18.2 | 174 | 3 | 1.6 |
| 2 Britain 1915 | 59 | 20.9 | 169 | 10 | 4.8 |
| 3 two factories | 79 | 30.2 | 157 | 6 | 2.0 |
| 4 Glasgow 1915 | 49 | 19.0 | 154 | 9 | 4.7 |
| 5 Japan and Bank of England | 92 | 31.8 | 173 | **17** | 5.3 |
| 6 Germany 1923 | 64 | 26.1 | 147 | 10 | 3.8 |
| 7 oil 1973 and New Zealand now | 60 | 22.9 | 158 | 13 | **5.7** |
| 8 "So yes", New Zealand 2021 | 77 | 26.5 | **175** | 10 | 3.8 |
| 9 Britain 1920 | 75 | 28.5 | 158 | 12 | 4.2 |
| 10 New Zealand now | 81 | 27.6 | **176** | 10 | 3.6 |
| **Total** | **689** | **251.7** | **164** | **100** | 4.0 |

(The brief said about 620 words. Counted as written, with the numbers spelled out as Malina says
them, it is 689.)

- The three fastest pages (5, 8 and 10) carry the most load or the main idea. Page 8 holds the one
  sentence the whole chapter depends on, and it is the second-fastest page.
- **Pauses are short.** Each "..." gives about half a second to a second, counting the word itself.
  That is no longer than an ordinary full stop. No pause inside any page lasts more than about a
  second. The gaps between pages are 1.4 to 1.6 seconds. Nothing gives a listener time to take in a
  lesson before the next fact arrives.
- **The arithmetic of slowing down.** At 140 words a minute, the same 4 minutes 12 seconds of speech
  holds about **587 words**, about 100 fewer than now. That is before a single explanation is added.
  If the rewrite adds the explanations below (perhaps 80 to 120 words) and keeps the film near
  4.5 minutes, about 180 to 220 words of the present content must go. That is two or three whole
  cases, not a trim of words.

**Load, counted.** Every item is one thing the listener must take in: a change of place, a year or
date, a number, or a term or reference a newcomer may not know. Each is tagged by hand at the moment
Malina says it. The counting script is `count_listener_load.py` in this folder, and its output is
`load-counts.txt`.

| 30 seconds of film | Places | Years/dates | Numbers | Terms/references | All |
|---|---|---|---|---|---|
| 0:00-0:30 | 1 | 1 | 1 | 5 | 8 |
| 0:30-1:00 | 1 | 1 | 1 | 6 | 9 |
| 1:00-1:30 | 2 | 2 | 2 | 3 | 9 |
| **1:30-2:00** | 2 | 2 | **5** | **7** | **16** |
| 2:00-2:30 | 3 | 2 | 1 | 7 | 13 |
| 2:30-3:00 | 2 | 2 | 4 | 5 | 13 |
| 3:00-3:30 | 1 | 1 | 2 | 7 | 11 |
| 3:30-4:00 | 2 | 1 | 3 | 6 | 12 |
| 4:00-4:30 | 0 | 3 | 4 | 2 | 9 |
| **Whole film** | **14** | **15** | **23** | **48** | **100** |

That is a new number or date about every 6.6 seconds of speech, and a new place every 18 seconds.
From 1:30 to 2:00 (Japan, then the Bank of England) the listener gets two countries, two years
running backwards, five numbers and seven unfamiliar terms in 30 seconds.

**The film zigzags in time and place.** The years in the order they're heard: 1915, the end of the
war (1918, not said), 1915, 2013, 2008, 1923, 1973, 2026, 2021, 1920, 1921, 2023, 2021, 2026. Time
changes direction **8 times**, and the country changes **7 times** (Britain, Japan, Britain,
Germany, an unnamed place, New Zealand, Britain, New Zealand). The page headings that would explain
the order ("test one", "test two", "test three", "the honest edge", "things you can't make more of
in a hurry") are in the script file only. Malina never says them, so the listener never hears that
three tests are coming.

**Reading on top of listening.** Going by the page files' opening notes, the words that appear on
screen run to about 9 on page 5, about 10 on page 7 and about 11 on page 8. Each of those pages
lasts 23 to 32 seconds. On a phone, the viewer reads all that while Malina talks at 165 to 175
words a minute. (These counts are rough, read from the notes, not from the film.)

---

## 2. Page by page, sentence by sentence

Each sentence is quoted as recorded. Under it: who gets lost, and why.

### Page 1 - the question (0:01-0:19)

1. "So... won't creating new money just cause inflation?"
   - **All (newcomers):** "So" points back to something they never heard: chapter 1's idea that a
     country can't run out of its own money. Without it, "creating new money" sounds like a strange
     or reckless plan. Who creates it? Why would anyone? **B** already answers "yes, obviously".
   - "inflation" comes before its meaning, but the meaning follows six seconds later. That's fine.
2. "You've felt it at the checkout." Clear.
3. "The same basket of shopping costs more than it did a year ago." The clearest sentence in the film.
4. "That's inflation... prices in general, going up."
   - **E:** "in general" can sound like a passing remark ("prices generally go up") rather than the
     point (all prices together, the whole basket).
5. "Not one price tag. The whole basket."
   - A good set-up, but it never pays off. Its point (one price rising, like fuel, isn't inflation on
     its own) is exactly what page 7 needs, and page 7 never reaches back to it.
6. "To see what really drives it, go back to the shell factory."
   - **All (newcomers):** what shell factory? "Go back" assumes they've been there (chapter 1, page 2).
   - **E:** "shell" first suggests a sea shell, not an artillery shell. "Drives it" (causes it) is a
     figure of speech.

### Page 2 - Britain, 1915 (0:21-0:42)

1. "Britain, 1915."
   - **S, E:** no bridge from the "shell factory". Nobody has said there's a war on, and won't for
     another seven seconds.
2. "Unemployment, the share of workers without a job, is under one percent."
   - The definition sits between "Unemployment" and "is", so the listener has to hold the subject
     while taking in the definition.
   - **E:** "share" here means a part. On page 5, "shares" means part-ownership of companies. Same
     sound, two meanings, in one film.
3. "The war is paid for partly with new money."
   - **All:** which war? "The First World War" is never said in chapter 2.
   - **All (newcomers):** new money from whom? The idea that a government or its central bank creates
     money is chapter 1's.
4. "Submarines are sinking supply ships, and factories are turned over to war work."
   - **E:** "turned over to" is an idiom.
   - **S:** whose submarines? (A small gap; it doesn't block the point.)
5. "So more money is chasing fewer things to buy... and by the end of the war, prices have roughly
   doubled since it began."
   - **E:** "chasing" is a figure of speech. "It" means the war.
   - Inside one sentence the time jumps to 1918 and back to 1914, neither of them said.
   - **Risk:** this first case seems to answer page 1's question "yes, new money causes inflation". A
     newcomer can take that answer away before page 3 turns it.

### Page 3 - two factories (0:43-1:14)

1. "Now picture two factories." Clear. A good move.
2. "In the first, the machines stand idle, and workers wait at the gate." **E:** "idle".
3. "New money arrives... the workers go in, and more shells come out."
   - **All:** arrives from where, and who brings it? Buyers? The government ordering shells? Money
     that just "arrives" is magic, and the mechanism (someone spends it on the factory's goods)
     goes unsaid.
   - **E:** "shells" again.
4. "Prices barely move." Clear (**E**: "barely").
5. "In the second, every machine and every worker is already flat out."
   - **E:** "flat out" is an idiom (busy to the limit). **S** and **B** know it.
6. "The same money arrives... but no more shells can be made." Clear.
7. "So buyers bid against each other, and prices climb."
   - **E:** "bid against" comes from auctions.
   - **All:** which prices? The factory makes shells, but page 1 was about the shopping basket. The
     film never links the two: the workers and machines making shells can't also make shopping, so
     spending chases the shopping that's left. A newcomer can hear this as being about the price
     of shells.
8. "Britain at war was close to the second factory... short of workers, materials and machines."
   - A good link back to page 2.
   - **Main gap:** the rule itself is never said in words. New money makes more things when workers
     and machines are idle, and higher prices when they're already flat out. The page shows it but
     doesn't say it, and the page file's notes suggest the words on screen don't say it either. A
     listener can't carry a picture forward the way they can carry a sentence.

### Page 4 - Glasgow, 1915 (1:15-1:34)

1. "Homes work the same way."
   - **All:** the same way as what? The listener must work out "like the flat-out factory: you can't
     make more quickly". The point that would tell them ("Homes can't be built in a hurry") comes
     17 seconds later, at the end. Heard once, the point needs to come first.
2. "In 1915, workers poured into Glasgow for war work, and landlords pushed rents up... by as much
   as a quarter."
   - **S, E:** where is Glasgow? (Scotland, in Britain. Not said.)
   - **E:** "poured" is a figure of speech. "By as much as a quarter" is a fraction heard at speed.
3. "By November, about twenty thousand households were refusing to pay the rise."
   - **E:** "the rise" (a noun meaning the increase) and "households".
   - **All:** this is a rent strike, but the film doesn't use the word or say why they refused.
4. "Within weeks, Parliament froze rents."
   - **E:** "froze" is a figure of speech. **S, E:** which Parliament? A New Zealander may think of ours.
   - This is a second story inside the example (people fought back and won a cap on rents). Its
     point is never said, and it pulls attention from the page's lesson.
5. "Homes can't be built in a hurry."
   - This is the point, but there's no new money anywhere on this page. A newcomer can't see why it
     belongs in a film about new money. The missing link: more people, chasing the same number of
     homes, just as more money chased the same shells.

### Page 5 - Japan 2013 and the Bank of England after 2008 (1:35-2:07): the heaviest page

1. "So test it."
   - **All:** test what? The rule was never stated, so "it" points at nothing the listener can name.
2. "Japan, twenty thirteen."
   - **All:** a jump of 98 years and half the world, with no bridge.
3. "Its central bank, the bank that creates the yen, sets out to double the money it has created,
   in two years."
   - 21 words, with a definition squeezed between "Its central bank" and "sets out". A sentence that
     has to be heard twice.
   - **All (newcomers):** "the bank that creates the yen" and "the money it has created" both rest on
     chapter 1's idea that a central bank creates money.
   - **B:** may know the Reserve Bank but won't link "central bank" to it, because the Reserve Bank
     isn't named until page 8 and isn't explained until page 10.
4. "If new money on its own pushed prices up, they'd soar."
   - **E:** an imagined case ("if... they'd") plus an uncommon verb ("soar"). Has to be heard twice.
5. "For eight years, they barely move... about half a percent a year."
   - Two numbers.
   - **Lesson missing:** why didn't prices move? The ledger's notes give the mainstream answer: most
     of the new money sat in the banks and wasn't spent (C2-C06, C2-XB03, said as the economists'
     view). That's the very point the chapter needs: "spent on what?". **B**, who believes printing
     money causes inflation, is left with a puzzling fact instead of a reason to change his mind.
6. "After the 2008 crash, the Bank of England, Britain's central bank, creates hundreds of billions
   of pounds."
   - **All:** back five years and back to Britain, with no "and" and no "the same in Britain".
   - **S:** "the 2008 crash" happened around when she was born. **E:** "crash" (a car crash?).
   - Another definition squeezed into the middle. "Hundreds of billions" is too big to picture.
7. "Its own study finds the new money pushed up the prices of shares and other investments... and
   the gains went to whoever owned the most."
   - **S, E:** "shares", "investments", "gains". **E:** "shares" collides with page 2's "share".
   - **All:** "whoever owned the most" — the most what?
   - **Worst risk on the page:** the film has used "prices" to mean shopping prices. Hearing that the
     new money "pushed up the prices", a newcomer can conclude "so it did cause inflation", the
     opposite of the test's point. The lesson is never said: the money went into things the richest
     own, not into the shopping basket, so shopping prices stayed flat. It depends what it's spent on.

### Page 6 - Germany, 1923 (2:09-2:35)

1. "Germany, 1923."
   - **All:** back 85 years, a new country, no bridge, and no spoken "second test".
2. "Prices are already racing." **E:** "racing" is a figure of speech.
3. "Then French and Belgian soldiers march into the Ruhr, Germany's coal and steel heartland."
   - Three new places at once. **E:** "heartland". The Ruhr is explained, which is good.
4. "The government tells workers to stop work in protest... and keeps paying them, with new money."
   - Clear, and the key sentence of the page. ("In protest" against the soldiers is left to the
     listener, which is fine.)
5. "By November, one American dollar costs more than four trillion German marks."
   - **All:** a dollar "costing" marks is the value of German money, not a shop price. The step
     between (German money became nearly worthless, so prices in shops went through the roof) is
     missing. Has to be heard twice.
   - **S, E:** "marks" means school marks to many; Germany's old money isn't explained.
   - **B, E:** "four trillion" is beyond picturing. The ledger allows a picture that can be felt: a
     loaf of bread cost billions (C2-C03).
6. "This time, new money really did push prices up... while less and less was being made."
   - The lesson is said. Good.
   - It isn't tied back to the second factory, though, so the listener has to make the link alone.
   - **Risk:** four trillion is the most vivid number in the film, and it backs the very claim the
     chapter questions. A newcomer who keeps only one thing may keep this, and keep it as "printing
     money causes inflation" unless "less and less was being made" is driven home.

### Page 7 - oil in 1973, and New Zealand now (2:36-2:59)

1. "Late 1973."
   - **All:** where? No place is named. Forward 50 years.
2. "Prices are already climbing when the price of oil nearly quadruples, in about three months...
   and almost everything made or moved with fuel gets dearer."
   - 25 words. **B, E:** "quadruples". **E:** "dearer" (a New Zealand and British word).
   - **All:** whose prices were already climbing? (The ledger says America.) Two different "prices"
     sit in one breath: shopping prices and the price of oil.
3. "So sometimes the cause isn't spending."
   - **All:** "spending" is a new name. Until now the film has said "new money". Is spending the same
     thing? The listener has to guess.
4. "It's costs."
   - **All:** costs of what? To whom? It means the cost of making and moving things, which businesses
     pass on. Unsaid.
5. "And here?"
   - "Here" means New Zealand, now: a 53-year jump in two words. **E** may miss it.
6. "The latest figures say prices rose four point one percent in the year to June."
   - **B, E:** "in the year to June" is how statisticians talk. Whose figures? A decimal.
7. "Leave fuel out... and it's two point nine."
   - **All:** what does it mean to leave fuel out of a price figure? Is 2.9 good or bad?
   - **Lesson missing:** much of the rise came from one price tag, fuel. That's a cost, not new money
     being spent. This is the payoff for page 1's "Not one price tag", and it's never made.

### Page 8 - "So yes", New Zealand 2021 (3:01-3:27)

1. "So yes... new money can push prices up, when it's spent where workers and machines are already
   flat out, or on things we can't make more of in a hurry."
   - **The most important sentence in the film.** It is said once, at 175 words a minute, 28 words
     long, with two conditions. It comes three minutes into the film, after all the tests that were
     meant to test it.
   - **All:** "So yes" — yes to what? The question was asked three minutes ago. Opening with "yes"
     makes the chapter's main rule sound like a concession, as if the narrator were giving ground
     rather than stating the rule.
   - **E:** "flat out", "in a hurry". **All:** has to be heard twice.
2. "In twenty twenty-one, our unemployment hit its lowest since records began."
   - **All:** back five years with no bridge. Why 2021? Nobody has mentioned the pandemic, or that the
     Reserve Bank and the government put large sums into the economy.
3. "House prices rose about thirty percent in twelve months."
   - Clear on its own. But house prices aren't in the shopping basket, and the film doesn't say so,
     so a newcomer will take this as inflation. (The research ledger warns: keep them apart.)
   - Its link to the rule (homes are a thing we can't make more of in a hurry) isn't said.
4. "An independent review of the Reserve Bank says the support from the bank and the government
   together was right at first... but too strong, for too long."
   - 26 words.
   - **S, E:** "independent review" (**E:** a film review?).
   - **All:** "Reserve Bank" is used here and only explained on page 10, 40 seconds later.
   - **All:** "the support" — support for what? "The bank" — which bank? "Too strong" — a strong what?
   - **Lesson missing:** this is the rule happening at home. New money was spent while nearly
     everyone already had a job. The page never says that prices in the basket rose then (7.3 percent
     in a year by mid-2022, C2-N01), so the listener has no inflation figure for New Zealand's own
     example.

### Page 9 - Britain, 1920 (3:29-3:57)

1. "So what's the usual cure?" Clear enough (the cure for rising prices).
2. "Britain, 1920." **All:** back 101 years, no bridge.
3. "The Bank of England pushes its interest rate, the price of borrowing, up to seven percent."
   - The definition sits inside "pushes... up".
   - "The price of borrowing" is a fifth kind of "price" in the film.
   - **S** gains from the definition. **B** knows interest rates.
4. "Loans cost more, and people spend less." Clear.
5. "Within a year, unemployment jumps from about two percent to eleven percent."
   - **All:** a step is missing. People spend less, so businesses sell less, so they stop hiring and
     lay people off. Without it, "spend less" to "unemployment" is a leap.
   - The ledger's own wording, "from about two in a hundred to more than one in ten" (C2-H08), is
     easier to picture than two percentages.
6. "Prices do fall... but people pay with their jobs." **E:** "pay with their jobs" is an idiom.
7. "Mattei argues that was part of the point."
   - **All (newcomers):** who is Mattei? Chapter 2 never introduces her. Chapter 1 did, as "Economist
     Clara E. Mattei".
   - **All:** "that" could mean the falling prices or the lost jobs. Has to be heard twice.
8. "With fewer jobs to go round, she says, workers lose the power to ask for more."
   - **E:** "go round" is an idiom. "She says" breaks the sentence in the middle.
   - **All:** more what? (Pay. Unsaid.)

### Page 10 - New Zealand now (3:59-4:26)

1. "Here, our central bank, the Reserve Bank, pushed its interest rate from a quarter of a percent
   to five and a half percent by twenty twenty-three, to bring prices down."
   - **30 words, the longest sentence in the film:** a change of place, a definition squeezed in,
     two numbers, a year and a reason.
   - The Reserve Bank is finally explained, two pages after it was first used.
   - **E:** "a quarter of a percent". When did the rises start? (2021. Unsaid.)
2. "Since the end of twenty twenty-one, unemployment has climbed from three point two percent to
   five point six."
   - **B, E:** two decimals straight after two other numbers. In a New Zealand accent some vowels
     shift (the project's accent notes mention "bed" toward "bid"), which makes spoken decimals
     like "five point six" harder for a second-language listener. That's a likely risk; I haven't
     tested it.
   - **All:** put next to the interest rate, this sounds as if the rate rises caused the whole
     increase. The ledger says not to imply that (C2-XD05: unemployment also rose while the rate was
     being cut).
3. "And this year, the Reserve Bank is raising its interest rate again."
   - **All:** why? (Fuel prices. The ledger's C2-N12 notes this.) It's never linked to page 7's fuel
     point. Linked, it would make the chapter's sharpest point: a cure aimed at spending, used on a
     rise driven by fuel costs. The ledger notes that this choice is itself debated, so it would
     need saying as a question, not a verdict.
4. "So next time someone tells you new money causes inflation... ask them." Clear.
5. "Spent on what?"
   - **All (newcomers):** the rule squeezed into three words, and the first time this phrase is said.
     A listener who missed page 8's long sentence can't unpack it.
6. "And who pays to stop it?" Clear. It ties back to page 9.

---

## 3. Patterns across the script

**References a newcomer lacks (from chapter 1):**

- "So..." and "creating new money" (page 1)
- "the shell factory" (page 1)
- "paid for partly with new money" (page 2)
- "the bank that creates the yen" / "the money it has created" (page 5)
- Mattei (page 9)

The word "austerity", the series' subject, is never said either. A newcomer won't know this chapter
belongs to a series about it. That's minor, but it's why the "usual cure" matters.

**One name for each thing, broken in three places:**

- **New money** is also "creating new money", "the money it has created", "spending" (page 7) and
  "the support" (page 8): five names for one thing.
- **"Price" means six different things:**
  - shopping prices (inflation): pages 1-4, 6, 9 and 10
  - the prices of shares and investments: page 5
  - the price of oil, which is a cost: page 7
  - house prices, which aren't in the basket: page 8
  - "the price of borrowing", the interest rate: page 9
  - what a dollar "costs" in marks, the value of German money: page 6
  
  For a newcomer, a price going up means inflation every time, so pages 5 and 8 can teach the
  opposite of what they mean.
- **The central bank** is "central bank", "the bank that creates the yen", "the Bank of England,
  Britain's central bank", "the bank" (page 8), "the Reserve Bank" (page 8, unexplained) and "our
  central bank, the Reserve Bank" (page 10).
- Kept well: "workers", "flat out", "unemployment", "things we can't make more of in a hurry".

**Words with two meanings (for E especially):** share / shares; marks (money or school marks);
review (an official check or a film review); shells (artillery or sea); crash (the economy or a
car); cure (medicine); support (help, or something holding up); the rise (a noun).

**Figures of speech and New Zealand or British words (hard for E):** drives it, turned over to,
chasing, flat out, bid against, poured into, the rise, froze, in a hurry, soar, racing, heartland,
dearer, leave fuel out, pay with their jobs, go round, part of the point, ask for more.

**Definitions squeezed into the middle of a sentence (5):** unemployment (page 2), the central bank
(page 5), the Bank of England (page 5), the interest rate (page 9) and the Reserve Bank (page 10).
On paper this saves words. By ear, the listener has to hold the start of the sentence while taking
in the definition, then find the verb again.

**Sentences that have to be heard twice:**

- page 5's Japan sentence (21 words) and its "if... they'd soar"
- page 5's Bank of England sentence (two jumps plus a definition)
- page 6's dollar-in-marks sentence
- page 7's oil sentence (25 words)
- page 8's rule (28 words) and its review sentence (26 words)
- page 9's "that was part of the point"
- page 10's opening (30 words)

**Examples whose lesson isn't said:**

- Glasgow: how it links to new money, and what the rent freeze means
- Japan: why prices didn't move
- the Bank of England: where the money went
- New Zealand's 4.1 and 2.9: one price tag, fuel
- New Zealand 2021: this is the rule at home

Set up but never paid off: "Not one price tag" (page 1).

**Jumps with no bridge:** Glasgow to Japan (only "So test it"), Japan to the Bank of England,
Britain 2008 to Germany 1923, Germany to 1973, 1973 to New Zealand ("And here?"), and New Zealand
2026 back to 2021. Bridges that work: the question at the start of page 9, and "This time" on
page 6.

**"The honest edge":** never spoken; it's a page heading only. Its idea arrives as "So yes...",
which a newcomer can hear as the narrator taking back the argument.

---

## 4. Accuracy notes (small, but they must carry into any rewrite)

The toolkit checks truth before style. None of these is wrong enough to have sent the film back,
but each matters for a rewrite.

- **Page 7, "Prices are already climbing":** no place is named, so a listener hears "everywhere".
  The ledger supports this for the United States only (C2-XC01: "Inflation outside the US also rose
  before the embargo but was not checked here"). Name America.
- **Page 8, the review:** the ledger wording is "with the benefit of hindsight... too strong for
  too long" (C2-XC04), and its plain version keeps "in hindsight". The recorded line drops it. Keep
  it.
- **Page 10, "is raising its interest rate again":** the ledger asks for "has started raising", not
  "is raising now", since the Governor hinted at a pause (C2-XD04). And don't set the unemployment
  rise beside the rate rises as if they caused all of it (C2-XD05).
- **Page 8, "about thirty percent in twelve months":** right for the twelve months to mid-2021. Over
  calendar 2021 it was nearer a quarter (C2-XC03). The present wording is fine. A rewrite must not
  turn it into "in twenty twenty-one, house prices rose thirty percent".
- **Japan's reason (if a rewrite adds it):** "most of the money sat in the banks" is the mainstream
  economists' explanation (C2-C06, C2-XB03). Others disagree. Say it as theirs.

---

## 5. The main claim, and whether the script lets a newcomer say it back

**The one sentence a newcomer should be able to say back:**

> Creating new money only pushes up everyday prices when it's spent on things we can't make more of
> in a hurry, because the workers and machines are already flat out, or because homes can't be
> built fast; so the real question is "spent on what?"

(The follow-on that the last two pages carry: the usual cure, dearer borrowing, is paid for with
people's jobs, and Mattei argues that's part of the point.)

**Does the current script let them? Mostly not.** These are my predictions, untested:

- The rule is said in full only once, at 3:01, at 175 words a minute, as a 28-word sentence that
  opens like a concession ("So yes...").
- The three tests come before the rule they test, and two of the cases (the Bank of England and New
  Zealand's fuel figure) never say what they show.
- The last line, "Spent on what?", is the rule in three words. A newcomer who missed page 8 can't
  unpack it.

What each listener probably says back:

- **S, the student:** has the best chance. The two-factories picture is strong. She may say "it
  depends whether the factories are already busy", but probably not the homes half, or the link to
  "spent on what?".
- **B, the builder:** likely keeps his belief. Germany's four trillion marks is the most vivid thing
  in the film and seems to prove it, and Japan's flat prices are a puzzle without a reason. He will
  get "homes can't be built in a hurry" and "the cure costs jobs".
- **E, the second-language adult:** likely loses the thread at page 5 (1:35 to 2:07: two countries,
  two years running backwards, five numbers, seven unfamiliar terms in 32 seconds). Afterwards they
  keep the cases as separate stories, without the rule that joins them.

---

## 6. Ten repairs, worst first

1. **Give newcomers a starting point (page 1).**
   - Drop "So..." and "go back to the shell factory".
   - In one plain line, say who creates new money and why the question comes up. Use chapter 1's
     idea, said as "economists who study how modern money works say": a government that issues its
     own money can't run out of it; its real limit is workers, materials and machines (C2-M12).
   - Name the First World War before Britain 1915.
   - Introduce Mattei by her full name and job before her claim on page 9.
2. **Say the rule in plain words at the two factories, then keep it word for word.**
   - On page 3, say it as a statement: new money mostly makes more things when workers and machines
     are idle, and higher prices when they're already flat out, or when it's spent on things we
     can't make more of in a hurry, like homes (C2-XA03, C2-M09; keep "mostly").
   - Repeat the same words after each test and just before "Spent on what?".
   - Turn page 8's "So yes" into a callback, not the first time the rule is said.
3. **Fewer stops, in a sensible order, with a spoken bridge at each.**
   - One place and one year per page.
   - Name the tests aloud ("First test...").
   - At each jump, say why we're going there ("Now the opposite: a country that created huge
     amounts of money...").
   - Cut or merge cases so the film stops zigzagging (8 changes of direction now). The strongest
     candidates are the Bank of England after 2008 (its lesson needs the most explaining and it
     repeats Japan's point) and 1973 oil (no place named, and New Zealand's fuel figure makes the
     same "costs" point at home).
4. **Slow down: write for 140 words a minute, and give every lesson room.**
   - Measured: 164 words a minute, with pauses no longer than a full stop.
   - Keep the length, and the script must lose about 100 words before adding anything. Add the
     explanations, and about 180 to 220 words of today's content must go (which is why repair 3
     cuts whole cases). The other choice is to let the film run longer.
   - End each lesson with its own short sentence followed by "...".
   - If Malina's voice settings offer a slower speed, try it on one page first. I haven't checked
     whether they do for this voice model.
5. **Say each example's lesson right after it, and pay off what's set up.**
   - The Bank of England (if kept): the new money pushed up shares, things the richest own, not the
     shopping basket, so shopping prices stayed flat (C2-XB05).
   - Japan: why prices stayed flat, said as the mainstream view (C2-C06).
   - New Zealand fuel: one price tag pushed up the whole basket; without it, two point nine
     (C2-N05, C2-XC05). That pays off "Not one price tag".
   - Glasgow: more people, the same number of homes (C2-XB01).
   - Germany: the second factory at its worst.
6. **Set up New Zealand's own story before judging it (page 8).**
   - Explain the Reserve Bank at first use.
   - Name the pandemic, and say what was done: the Reserve Bank created new money to buy about
     fifty-three billion dollars of government debt (C2-N06).
   - Give what happened to the shopping basket: seven point three percent in a year by mid-2022, the
     fastest in thirty-two years (C2-N01).
   - Keep house prices separate and say they're not in the basket (C2-N08).
   - Keep the review's "in hindsight" (C2-XC04).
7. **One name for each thing, and keep the different "prices" apart.**
   - One name for new money being spent: no "spending", no "the support".
   - The central bank idea defined once, then the same short names.
   - Whenever a "price" isn't in the shopping basket (shares, houses, a dollar in marks, the
     interest rate), say so or use another word ("what German money was worth").
   - Don't call the interest rate "the price of borrowing". Say "the extra you pay back on a loan",
     or similar.
8. **Finish the chain from interest rates to jobs, and keep Mattei's view as hers.**
   - Higher interest rate, then loans cost more, then people and businesses spend less, then
     businesses hire fewer people, then unemployment rises (C2-XD01, C2-M17).
   - Make "that" concrete: "Mattei argues the lost jobs were part of the point" (C2-H18, C2-XD02).
   - On page 10, don't let the order imply that rate rises caused all of the rise in unemployment
     (C2-XD05). Say the Reserve Bank "has started raising" its rate (C2-XD04). Ask, as a question,
     whether that cure fits a rise driven by fuel (C2-N12 notes it's debated).
9. **Fewer numbers, said as people or pictures.**
   - Keep a number only when its lesson comes in the same breath.
   - Drop durations that carry no point ("in two years", "eight years", "about three months").
   - Say percentages as people where the ledger does: fewer than one in a hundred out of work
     (C2-H02); from about two in a hundred to more than one in ten (C2-H08).
   - Never put two pairs of decimals back to back (page 10).
   - Give four trillion marks a picture the ledger allows: a loaf of bread cost billions (C2-C03).
10. **Plain words, and define first, then use.**
    - Replace the figures of speech and the two-meaning words listed in section 3 ("flat out" can
      stay, explained once in plain words).
    - Split each squeezed-in definition into two sentences ("The Reserve Bank is our central bank.
      It...").
    - Break up the 25-to-30-word sentences on pages 5, 7, 8 and 10.

---

## 7. What wasn't checked

- No real newcomer has heard the film. The three listeners are my assumptions.
- I checked the narration only. I didn't watch the film; the words on screen are counted from the
  page files' opening notes.
- The new-number and term counts depend on my tagging (in `count_listener_load.py`). Someone else
  might tag a few items differently. The pattern (page 5 heaviest, pages 5, 7 and 8 densest per
  second) wouldn't change.

---

## 8. A listener test to run on real newcomers (after one watch, no replay)

1. In one sentence: does creating new money always push prices up? When does it, and when doesn't
   it? *(Strong answer: not always; it does when it's spent on things we can't make more of
   quickly, because workers and machines are already busy, or on things like houses.)*
2. Japan doubled the money its central bank had created. What happened to prices? Why might that
   be?
3. A town has lots of builders out of work. The government pays them with new money to build
   houses. Do prices go up much? What if every builder in the country is already busy? *(The most
   useful question: it tests whether they can use the rule on a case the film never showed.)*
4. Who paid for bringing prices down in Britain in 1920? What does Mattei say about it, and is that
   her view or a plain fact?

The misconception to listen for: "Yes, printing money causes inflation, look at Germany."

---

## Traps

- The 140 words a minute in the rules is a plan, not what the voice does. Measure each new recording
  from its word times before trusting the length.
- The page headings ("test one", "the honest edge") are invisible to a listener. Any signpost has
  to be spoken.
- "Price" is the most dangerous word in this chapter. Each time it's used for something outside the
  shopping basket, a newcomer hears "inflation".
- Cutting a case also cuts its pictures. Pages 5 and 7 hold built 3D scenes and paintings (the noodle
  counter, the Bank of England plaza, the 1973 forecourt). Check what is lost before choosing.
- Re-recording any page moves every later time, so the timing, the mix and the film are all made
  again.
- The 2026 New Zealand figures change on 22 October (inflation), 28 October (interest rate) and
  4 November (unemployment). Re-check them before recording.
