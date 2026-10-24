# What this does: adds log 33 (chapter 2 rewritten for newcomers) to the project story, and updates
# "Where things stand", the word list, the next step and the traps; adds lessons 126 to 131, a status
# section and a workflow note. Run once.
R = '/home/user/Music/austerity-explainer/project-notes/'
STORY = R + 'Austerity explainer - project story.md'


def edit(path, pairs):
    s = open(path).read()
    for old, new in pairs:
        assert s.count(old) == 1, (path, s.count(old), old[:70])
        s = s.replace(old, new, 1)
    open(path, 'w').write(s)
    print('updated', path.split('/')[-1])


LOG33 = '''33. **Rewriting chapter 2 for newcomers** (decisions 38 and 39). You kept the notice corner ("Yes keep
    it") and asked: "could you rewrite a script to be more introduction friendly. I've had a few people get
    lost trying to understand the last video because it moves to quickly and uses terms that your average
    person isn't familiar with. Keep the writing in the voice of Naomi Klein. See if this attachment helps
    with pedagogy and prose" (the attachment: your Steven Pinker Teaching and Writing Toolkit).
    - **My reading of the request** (Decisions, item 39): "the last video" is chapter 2, "what really causes
      inflation". "The voice of Naomi Klein" means her spirit, as in decision 8: urgency, direct questions,
      the stakes first, who gains and who pays; never her words, titles or coined phrases. Facts come only
      from chapter 2's checked research ledger. The toolkit (teach for understanding, write for readers, a
      clarity workflow) guided every step. It stays out of the repository, as before.
    - **Why people got lost, measured on the recording** ("01 Newcomer audit of the recorded chapter 2"):
      - Malina read it at 164 words a minute, against the 140 planned. The three fastest pages carried the
        most new things or the main idea.
      - It opened by pointing back to chapter 1 ("So... go back to the shell factory").
      - The rule the chapter teaches came only once, 3 minutes in, as one 28-word sentence.
      - Eight real cases in about 4 and a half minutes, jumping back and forth in time 11 times.
      - 48 words a newcomer might not know, and "price" used for six different things.
      - Each "..." pause gave under a second: no time to think.
    - **Seven places where the recorded script says a little more than the ledger allows** ("04 Fact
      choice", section 6). The two that matter: page 8 drops "looking back" from the review's verdict and
      puts the review next to house prices, which it didn't discuss; page 10's "is raising its interest
      rate again" should be dated, in the past tense. The other five are small, or on screen only. The
      film already sent is unchanged.
    - **How the rewrite was made** (three rounds, 22 helpers, about 3 hours 20 minutes; every step is in
      "33 Chapter 2 for newcomers - working files"):
      - Round 1: the audit, a teaching plan, a voice brief, a choice of facts, then three drafts from
        different angles (one picture first; the viewer's own question; people first).
      - Round 2: three judges (will a newcomer follow it; voice and sound; truth and rules). "One picture
        first" scored best for newcomers (7.5 of 10) and was combined with the best parts of the others.
        Three fresh testers (imagined newcomers, facts, rules and voice) then found 6 must-fixes, for
        example the rule said that new money gets things made, where the research speaks of money that
        is spent. A reviser fixed them.
      - Round 3: four fresh testers. The newcomer tester saw only what a viewer hears and sees, and a
        skeptic compared the script with the recording. They found 4 must-fixes: "Spent on what?" was
        never tied to its test; "building new homes" was heard as a building boom; the script gave our
        Reserve Bank's view with no source (the ledger has America's); and Mattei's view was said more
        strongly than her own words. A fixer made the confirmed fixes, a re-checker read all 45 changed
        sentences (no factual errors), and a last fixer made two more.
      - Then I made three small wording changes the last fixer had left open, re-opened Powell's speech
        and Stats NZ's June 2022 release, and added their exact words to the ledger (C2-M17, C2-N02).
    - **What the new script does** ("33 Script - chapter 2 - what really causes inflation - for
      newcomers"):
      - Example: page 3 asks the viewer to picture two factories, each standing for a whole country. In
        the quiet factory, workers wait at the gate; new money is spent, the workers go in, "More
        money... and more things to buy. So prices barely move." In the flat-out factory everyone is
        already busy; the same money arrives: "What happens to prices? Have a guess." Britain at war,
        Glasgow's homes, Japan and New Zealand are then each placed on that picture out loud.
      - One idea: whether new money pushes prices up depends on whether it's spent, and on what.
      - Four real cases in time order, three guesses held about 4 seconds, the rule said twice in the same
        words, every unfamiliar word explained or left out, about 28 spoken figures instead of 37,
        sentences of about 9 words.
      - The stakes in the first 30 seconds; the usual cure and who pays for it ("many people with
        loans... and people put out of work"); America's central bank's view in one fair line, then
        Mattei's, marked as hers.
      - Left for later chapters: Germany 1923, the Bank of England after 2008, oil in 1973, Britain 1920,
        New Zealand house prices.
      - About 7 and a quarter minutes at Malina's measured speed (the recording: about 4 and a half).
        Ready cuts of 32 words are listed.
      - The pictures are planned from the paintings and pieces already made: no new paintings.
    - **The narration file** ("33 Narration script - chapter 2 for newcomers.json") is ready to record, in the
      same form as before. Not recorded.
    - **Added for later chapters:** a newcomer section in the writing rules (section 4); in the film plugin
      (version 1.2.0), a new step, `test-script-with-newcomers`, and a newcomer section in its
      scriptwriting guide. The new step was tried only with stand-in helpers (it starts each helper in
      the right order and refuses to start without its inputs), not yet on a real script.
    - **Not checked, or unsure:**
      - No real newcomer has heard it. The testers' listeners were imagined by helpers.
      - Malina hasn't read it, so the length is an estimate.
      - Whether ElevenLabs lets Malina's speed be set lower: not checked.
      - The picture notes are plans; nothing is drawn or filmed, and 16 pages means new page files.
      - Three sources are still to open: Glasgow's builders gone to the war, why petrol and diesel went
        up in 2026, and any New Zealand Reserve Bank statement on job losses.
    - **Cost:** nothing on fal or ElevenLabs. About 3 hours 20 minutes of helper time.'''

edit(STORY, [
    ('\n## Next step\n', '\n' + LOG33 + '\n\n## Next step\n'),
    ('## Where things stand\n\n', '''## Where things stand

- **Chapter 2 rewritten for newcomers** (log 33): "33 Script - chapter 2 - what really causes inflation -
  for newcomers" and its narration file, ready to record. One idea, one picture (two factories), four
  real cases in time order, three guesses, every unfamiliar word explained; about 7 and a quarter
  minutes. Tested in two rounds by fresh helpers (imagined newcomers, facts, rules and voice, a skeptic)
  and fixed; not yet heard by a real newcomer, recorded or filmed.
'''),
    ('''  and the frame is balanced. Waiting for your view.''', '''  and the frame is balanced. You kept it ("Yes keep it", decision 38).'''),
    ('| Music bed | A stretch of music laid under a clip that has no narration, faded in and out. |', '''| Music bed | A stretch of music laid under a clip that has no narration, faded in and out. |
| Newcomer | A viewer who hasn't seen chapter 1 and doesn't know the subject. |
| The quiet factory and the flat-out factory | Chapter 2's picture: two factories, each standing for a whole country. In the quiet one, workers wait at the gate; in the flat-out one, everyone is already working as hard as they can. |
| Guess | A question at the end of a page ("Have a guess"), with about 4 seconds held in the film so the viewer can think. |
| Recap | The main rule said again in exactly the same words, so the second time feels familiar. |
| Listener test | A few questions to ask a real newcomer after they hear the script, to see if the idea landed. |
| Words a minute | How fast Malina reads. Measured on chapter 2: 164 (planned: 140). |'''),
])

s = open(STORY).read()
i = s.index('## Next step\n')
j = s.index('\n## Traps', i)
s = s[:i] + '''## Next step

Read "33 Script - chapter 2 - what really causes inflation - for newcomers" aloud to one or two of the
people who got lost, then ask them the questions under "Before recording" in that file (question 3 is
the key one), and tell me what they say. After that, recording it costs about 6,300 ElevenLabs credits
(about US$1.10); I'll ask you before spending.
''' + s[j:]
open(STORY, 'w').write(s)
edit(STORY, [
    ('''- Chapter 2's newest figures go out of date soon:''', '''- The newcomer script (log 33) uses figures that change soon: page 15's basket (June 2025 to June 2026)
  and page 13's "nearly six in a hundred" out of work (the June 2026 quarter). Re-check them after 22
  October and 4 November, before recording.
- Chapter 2's newest figures go out of date soon:'''),
])

edit(R + 'Lessons.md', [('\n## Traps\n', '''
## 2026-10-15 (chapter 2 for newcomers, log 33)

126. **The narrator was faster than planned, and the fastest pages carried the main idea.** Malina read
    chapter 2 at 164 words a minute against the 140 planned, and the page with the one sentence the
    chapter depends on was the second fastest (175). Plan a chapter's length at her measured speed (about
    160) and give the main idea room (log 33).
127. **The rule was said more broadly than its evidence.** "New money mostly gets more things made" was
    contradicted by the film's own Japan case, where most new money was never spent; the research speaks of
    money that is spent. A fact tester caught it. Say a rule exactly as broadly as its evidence: "When new
    money is spent..." (log 33).
128. **One word for two things confuses as much as two words for one.** "Banks" meant both ordinary banks
    and the Reserve Bank; "pay" meant both wages and who carries the harm; "price" meant six things in the
    recording. Check the one-name rule both ways (log 33).
129. **A written pause is not thinking time.** Each "..." gave Malina under a second, no longer than a full
    stop. A guess needs about 4 seconds held in the film after the page ends (log 33).
130. **A tester who reads the notes understands too much.** The notes explain what the words leave out. The
    last newcomer tester was given only what a viewer hears and sees, and found the closing question
    "Spent on what?" had never been tied to its test (log 33).
131. **A line about our own Reserve Bank had only America's central bank behind it.** The ledger's support
    was Powell's speech, so the line now names America's. Check whose words stand behind a "they say"
    (log 33).

## Traps
'''), ('''- Line every painting up with its plate, and keep the painted shadows in the props-removed copy (lessons 122, 123).''',
       '''- Line every painting up with its plate, and keep the painted shadows in the props-removed copy (lessons 122, 123).
- Plan a script at the narrator's measured speed, and test it on someone who sees only what a viewer sees (lessons 126, 130).''')])

edit(R + 'Workflows.md', [('\n## Saving to the repository (your rule, decision 30)\n', '''
## Testing a script on newcomers (log 33)

- Write it with the newcomer rules (section 4 of "01 Rules - voice, tone and writing style"): one idea,
  one picture first, about four real cases in time order, guesses, recaps in the same words, every
  unfamiliar word explained.
- Run the plugin's `test-script-with-newcomers` step: four fresh helpers (imagined newcomers who see only
  what a viewer sees, a fact checker, a rules-and-voice reader, a skeptic), then a fixer that makes only
  confirmed fixes, then a re-check of every changed sentence.
- Then read it to one or two real newcomers with the script's listener questions, before paying to record.

## Saving to the repository (your rule, decision 30)
''')])
