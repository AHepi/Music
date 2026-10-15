# Rules - voice, tone and writing style

**What this is:** the rules used to write and record chapter 1 of "Where austerity came from", in one
place: how Malina's voice is generated, the tone of the narration, and the writing style taken from
your Steven Pinker Teaching and Writing Toolkit. Each rule says where it came from: your own words
(quoted exactly) or a call made during the project. Source for the story: Clara E. Mattei,
*The Capital Order* (2022).

## A quick example first

The first draft of page 1 (formal, like a lecture):

> Austerity. Cut public spending. Make borrowing dear. Hold wages down. It's sold as common sense.
> But the economist Clara E. Mattei traced modern austerity back to a particular moment: the years
> right after the First World War.

After your note on tone and the Pinker toolkit (as recorded):

> You've heard the speech. Times are tough. Tighten your belts. Cut spending, push up interest
> rates, hold wages down. Sounds like common sense... But austerity has a birthday. Economist Clara
> E. Mattei dug through the archives and found it, right after the First World War. And she argues
> it was never really about budgets. It was about stopping something.

What changed: it opens with something the viewer has already heard; it talks to them ("you"); a
concrete picture ("austerity has a birthday") comes before the idea; the stakes come up front ("it
was about stopping something"); and Mattei's interpretation is said as hers ("she argues").

---

## 1. Voice generation (Malina, in ElevenLabs)

**The voice**
- Your words: "Use this soundtrack and my custom made voice called Manila", then "Sorry Malina".
- Voice: Malina, voice id `JNDHNvYV2jhVoAQjIjY6`. Model: `eleven_v4`.
- Malina is a designed voice labelled only "English"; it has no accent setting of its own.

**The accent**
- Your words: "the audio randomly switches accents in the beginning of the video. And there's random
  shouting." and "Maybe research standard New Zealand phonemes ... and avoid the shouting this time."
- Every page opens with exactly one accent instruction: `[in a warm, steady New Zealand accent]`.
- No other delivery cues at all. The earlier mixed cues ([urgent], [wry], [serious]) pushed the voice
  up and down between pages and caused the shouting.
- Your verdict on the result: "it sounds a bit Australian. It'll do for now."
- No voice-level "accent rules" could be found in ElevenLabs' documentation (checked 11 October 2026).
  Pronunciation rules exist, but they fix one word at a time and need ElevenLabs Studio or a fuller
  connection. If one word keeps coming out wrong, a pronunciation rule for that word is the fix.
- The New Zealand sounds to listen for when judging a take (the "fush and chups" vowel, "bed" toward
  "bid", no R after vowels, and so on) are in `research/09 Research - New Zealand accent.md`. They
  are a listening guide, not something sent to ElevenLabs.

**Writing the text for the voice**
- No capital letters for emphasis anywhere: in v4, capitals make the voice push.
- Pauses are written as an ellipsis ("Sounds like common sense... But"), not as a [pause] cue.
- Names the voice might get wrong are written in sound symbols. Mattei is `/məˈteɪi/` (said
  muh-TAY-ee, the English way); the Italian spelling of the sounds pulled the accent around that word.
- Each page is recorded on its own, so one page can be re-recorded without touching the others.
- Malina reads at about 140 words a minute. Cost: about 1 credit per letter; chapter 1 (about 520
  spoken words) took about 4,200 credits, about 75 US cents.
- Spending: confirm the estimate with you before recording at length.

**After recording**
- Download every recording straight away: ElevenLabs links stop working after 2 hours.
- Ask ElevenLabs for the transcript of each recording (free); it gives the time of every word.
- `tools/extract_word_times.py` (in the repository: `film-kit/narration-tools/extract_word_times.py`) refuses a transcript that doesn't match the script, and moves each
  page's first word back to where the voice really starts (ElevenLabs can place it up to 0.3 s late
  after a long accent instruction).
- Always listen to a take before building on it: an accent instruction is followed, not guaranteed.
- Re-recording one page moves every time after it, so the timing, mix and film are all made again.

**Loudness and music**
- Every page is set to the same loudness (-16 LUFS, a measure of how loud speech sounds) by a plain
  volume change, not a compressor, so Malina's delivery stays as she recorded it.
- Your words: "Can up the music slightly." The music sits about 18 dB under Malina while she speaks
  and comes up in the pauses (it ducks automatically), with the speech frequencies of the music
  softened a little. Measured, not guessed.
- Your soundtrack "Tension and Gravity" is loud and dense (about -13 LUFS): it must always be turned
  down under Malina. It plays from its start and fades over the last 4 seconds.
- The whole mix: about -15 LUFS (usual for phone video), loudest peak under -1 dB, sound lined up
  with the pictures to the millisecond (the limiter's delay is compensated).

## 2. Tone

- Your words: "The script needs to be more conversational. It's way too formal and like I'm
  listening to a lecture. It needs to be a little less formal and a little more urgent like Naomi
  Klein."
- Conversational: talk to the viewer ("you've heard the speech"), short spoken sentences, questions
  the viewer would ask.
- Urgent: stakes up front, direct questions, a clear "why this matters to you".
- Like Naomi Klein in spirit only: urgency, direct questions, stakes first. None of her wording or
  coined phrases is used.
- Warm and steady in the voice (the accent instruction), urgent in the words. The urgency comes from
  the writing, never from shouting.

**What the narration must and must not say**
- Your words: "from the perspective of MMT ... And do not use the term MMT." The money view is never
  named. When the film needs to point to it, it says "economists who study how modern money works".
- Your words on inflation: "it quite evidently makes no sense that money minting = Inflation. It
  depends on where and how the money is spent." That gets its own chapter (chapter 2), including the
  honest edge: new money can push prices up when the spending chases things the economy can't make
  more of.
- Mattei's own interpretations (austerity's real purpose, "the capital order") are said as hers:
  "Mattei argues", "Ask Mattei, and her answer is blunt", "That's the argument Mattei makes".
- The author's name is spelled Clara E. Mattei (the book's spelling).
- Every fact must have a sourced entry in the research file before it goes into the script (the codes
  like [C1-10] point to it). A fact that only a blocked web page could confirm stays out.
- No drawn portraits of real people: they appear as typed name cards.
- Words on screen are short forms of what Malina says, never more (BUDGET SPEECH, ANY JOB / ANY WAGE).

## 3. Writing style (from your Steven Pinker Teaching and Writing Toolkit)

Your toolkit was included unchanged in `pinker-toolkit/` in the chapter 1 zip (not in this
repository; three parts: write for readers, teach for
understanding, and a clarity workflow). This is how it was applied to the narration.

- **Open with something the viewer already knows**, then turn it ("You've heard the speech ... But
  austerity has a birthday").
- **One plain name for each thing, kept all the way through**: workers, owners, the experts, the
  capital order. Never swap in a synonym; a new word makes a listener think it's a new thing.
- **A concrete case before each general idea**: Britain in 1915 running out of shells, not money,
  comes before the idea that a government's limit is real things, not money.
- **Assume an intelligent listener without the background** (the "curse of knowledge"): no
  unexplained terms; every necessary term explained at first use; actors and actions visible (who
  did what to whom), not hidden in abstract nouns.
- **Present the subject, not the writer**: point the viewer's attention at the thing in the world
  ("classic style"), no throat-clearing, no "in this video we will".
- **Familiar information first, new information last** in each sentence, so each sentence hands on to
  the next.
- **Make the link between sentences clear**: because, so, but, then. A listener can't re-read.
- **Read it aloud**: cut anything that trips the tongue or puts stress in the wrong place. For a
  narrator this matters double: what reads well can still sound wrong.
- **Keep the truth and the uncertainty**: never make a claim sound surer by dropping a qualification.
- **Final pass against banality**: replace stock phrases, generic uplift and plausible-sounding but
  unsupported claims with specific, sourced facts.
- **Transfer the principles, not the voice**: the narration should not imitate Pinker's own manner.
- Credit where due (from the toolkit): "classic style" is Thomas and Turner's; "curse of knowledge" is
  Camerer, Loewenstein and Weber's; Pinker applies both to writing.

## 4. Writing for newcomers (learnt rewriting chapter 2, log 33)

People got lost in the recorded chapter 2: it moved too fast and used words an ordinary viewer
doesn't know. These rules come from fixing that, using the toolkit's "teach for understanding" part.
Example: the recorded chapter 2 crammed eight real cases into about 4 and a half minutes, jumping
back and forth in time; the newcomer version uses one imagined picture (two factories) and four real
cases (Britain at war, Glasgow, Japan, New Zealand), in time order, and places each on the picture.

- **One idea per chapter, said in one sentence a viewer could repeat.** Chapter 2's: whether new
  money pushes prices up depends on whether it's spent, and on what.
- **One picture first, then the real cases.** Say what the picture stands for ("think of each one as
  a whole country"), and say aloud where each real case sits on it ("Britain at war was close to the
  flat-out factory"). Say where the picture stops working (money that is never spent).
- **About four real cases, in at most three places, with time running one way.**
- **Every unfamiliar word explained the first time, in a few plain words, or left out.** "Interest is
  the extra you pay back when you borrow." Words to avoid in chapter 2: unemployment (say "out of
  work"), central bank, rates, printing money.
- **One name for each thing, both ways:** never two words for one thing, and never one word for two
  things ("banks" meant both ordinary banks and the Reserve Bank; "costs" meant both prices and what
  it costs to make things).
- **"Before I tell you, guess" moments** at the end of a page, with the gap held about 4 seconds in
  the film. A written "..." gives less than a second, so the thinking time has to come from the film.
- **Short recaps in the same words each time**, so the second time feels like recognition.
- **Numbers:** never two new numbers in one sentence, except a "from... to" pair or a date with one
  figure ("By the middle of twenty twenty-six... nearly six in a hundred"). Give each a plain
  anchor ("about three in a hundred"), and use the same unit when two numbers are compared.
- **Short sentences**, about 8 to 10 words, and never an aside between a subject and its verb.
- **Plan the length at Malina's measured speed**, about 160 words a minute, not 140. The recorded
  chapter 2 ran at 164, and its fastest pages carried the main idea.
- **A rule is said only as strongly as its evidence:** "When new money is spent... and there are spare
  workers, materials and machines... it mostly gets more things made", because the research speaks of
  spending, and Japan's new money mostly wasn't spent.
- **Test with real newcomers before recording**: read the script to one or two people who don't know
  the subject and ask them the listener questions in the chapter's script file. Imagined listeners
  are only a first filter.
- **Naomi Klein in spirit, still:** the stakes in the first 30 seconds, the viewer's own question,
  who gains and who pays side by side, one fair line for the other side, then Mattei's view, marked
  as hers.

## Traps

- One accent instruction per page and nothing else in brackets: adding mood cues brings the accent
  drift and the shouting back.
- No capitals for emphasis, ever.
- Download recordings within 2 hours or they are lost.
- Never say "MMT" in the narration or on screen.
- Mattei's interpretations stay marked as hers, however urgent the wording gets.
- "Like Naomi Klein" means her urgency, never her words.
- Urgency lives in the writing; if the voice starts pushing, the text is asking it to (capitals, cues).
