# Austerity explainer - project story

## The goal

A 15 to 20 minute narrated explainer for a tall phone screen, made of painted pictures moved like
paper (the paper pop-up look you chose in log 12; the old-scrapbook look came first), telling where
austerity came from and what it does, from Clara E. Mattei's book *The Capital Order* (2022), seen
through the eyes of economists who study how modern money works (never named as MMT in the film).
Easy to understand, yet thorough; conversational and a little urgent. Narrated by your voice Malina,
over your soundtrack "Tension and Gravity".

Because the whole film is big, it is being built one chapter at a time. Chapter 1 is a test:
about 3 and a half minutes on where austerity came from and why it was put in place.

## Where things stand

- **Chapter 2, "what really causes inflation", has three outlines waiting for your choice**
  ("18 Outlines - chapter 2 - what really causes inflation"), built on a new research ledger of 72
  sourced facts ("18 Research - chapter 2 - what really causes inflation"). My pick is outline A, "Back
  to the shell factory". Nothing recorded, painted or spent yet.
- **Chapter 1 is finished in the paper look**: "13 Chapter 1 - where austerity came from - paper
  pop-up.mp4" (3 minutes 41 seconds), with captions ("13 Captions") and a cover picture ("13 Cover").
  All ten pages pop up, crash in and turn like a book on Malina's words; no hands.
- **A kit for new series is ready**: three zip files ("14 Paper pop-up film kit", parts 1 to 3) with every
  painting, the tools, this chapter as a worked example and step-by-step instructions, for the agent
  starting a series on the enclosures.
- **A one-page picture with origami props** ("15 One page"): a blank page at an angle on a dark desk,
  with a folded cottage, trees, crane and fence, lit by one low warm lamp. You liked the idea but not
  the beauty, so it led to the next one.
- **An open pop-up book** ("16 One page"): an open book floating in the dark, seen from the reader's
  chair, with a pop-up countryside cut from one ivory paper, lit by a reading lamp, moonlight and the
  cottage's glowing windows. Waiting for your view.
- **The narration is the steadier voice**, with the music a little louder ("10 Narration").
- The earlier scrapbook film (08), the five animated samples (10) and the page 3 test (11) are kept
  for the record; the new film replaces them.
- Spent so far: about US$5 in all (ElevenLabs about 75 US cents; fal about US$4.25: 90 cents for the
  five animated samples, 82 cents for the page 3 test, about US$2.55 for chapter 1's other paintings
  and cut-outs).

## How the pieces fit

**A concrete example first.** On page 3 Malina says "union membership doubles, to eight million."
That sentence comes from the script, which took the fact from research entry C1-08 (4.1 million
in 1914, 8.3 million in 1920). ElevenLabs recorded the page and reported that she starts saying
"doubles" 56.48 seconds into the chapter (with the steadier voice). Page 3's file asks for "doubles",
gets 56.48 seconds, and folds the second, bigger crowd up from flat 0.1 seconds before it, so the
crowd doubles as she says it. Your soundtrack plays underneath, dipping while she talks.

**The pieces, in order:**

1. **Research ledger** (`research/02 ...`): every fact, its source, how sure we are. Hands facts
   to the script.
2. **Narration text** (`narration/chapter-1-narration.json`): exactly what Malina reads on each
   page, with delivery cues. Hands it to ElevenLabs.
3. **Recording** (ElevenLabs, voice Malina): one recording per page, plus a transcript giving the
   time of every word. Hands both to the timing tools.
4. **Timing tools** (`tools/extract_word_times.py`, `tools/assemble_chapter_narration.py`): put the
   pages end to end with short pauses, level the voice, and write the chapter timeline. Hand the
   narration track to the mix and the word times to the drawing code.
5. **Mix** (`tools/mix_chapter_narration_over_music.sh`): lays Malina over your soundtrack, turns the
   music down under her voice, sets the loudness for phones. Hands the sound to the final film.
6. **Drawing code** (the anidoodle skill, scrapbook style): draws every page on its words (cards laid
   down, words typed, cut-out letters, engravings cut line by line, red pen, stamps), turns the pages,
   and makes a silent picture-only film. Hands it to the final film.
7. **Final film**: the pictures and the mixed sound joined into one video file, plus a captions file
   made from the same word times, and a cover picture.

**The paper look (now used for the whole chapter), in order:**

8. **Paintings** (fal, Flux 3): one background per page, and each figure or object painted on its own
   on plain grey, checked on contact sheets. Hands the pictures to the cutting step.
9. **Cutting** (fal's background remover, then `paper-film/tools/prepare_paper_pieces.py` reading the
   cut list `paper-film/scene-data/chapter-1-cut-list.json`): cuts each figure out with a paper margin,
   matches its colours to the backgrounds, repairs what the remover missed, prints labels (the book's
   title, TAX, ROYAL COMMISSION), splits speaking figures into face, jaw and mouth. Hands paper pieces
   to the stage.
10. **Paper stage** (`paper-film/stage/`): a small 3D world with one lamp, where every picture is a
    sheet of paper standing a little in front of its page; it also makes words, printed cards,
    posters, dust and smoke. Hands finished frames to the filming tool.
11. **Page files and chapter scene** (`paper-film/scenes/chapter-1/page-1.js` to `page-10.js`, with
    `paper-kit.js` and `chapter-1.js`): each page file says, from Malina's word times, when each piece
    folds up, slides, drops, crashes or folds away; the chapter scene stacks the sheets, turns each
    page just after its last word and moves the camera. Example: on "tanks" (65.96 seconds into the
    chapter) the tank lands, the camera shakes and dust bursts out.
12. **Filming** (`paper-film/tools/film-chapter-1.sh`, using `render-paper-film.mjs`): films one page
    at a time and joins the pages into a silent film. Hands it to the finishing step.
13. **Finishing** (`tools/finish_chapter_1_paper_film.sh`, `tools/make_captions.py`,
    `tools/check_sound_alignment.py`): joins the mix, makes the copy small enough to send, writes the
    captions, and measures that sound and pictures line up.

**Chapter 2, so far (the same pieces as chapter 1, one step earlier):**

14. **Research ledger for chapter 2** (`chapter-2-inflation/18 Research - chapter 2 - what really
    causes inflation.md`): 72 facts in four parts (C2-H the history after chapter 1, C2-C real cases,
    C2-N New Zealand now, C2-M how inflation works), each with its source and how sure it is. Written
    from the research results (`chapter-2-inflation/research-and-outlines-raw.json`) by
    `tools/write_research_ledger.py`. Hands facts to the outlines.
15. **Outlines** (`chapter-2-inflation/18 Outlines - chapter 2 - what really causes inflation.md`):
    three ways to tell the chapter, page by page, each fact tied to a ledger id. The one you choose
    becomes the script, which then follows the same path as chapter 1 (recording, timing, mix,
    paintings, paper pieces, page files, filming, finishing).

**Chapter 2 in the cinema look (a concrete example first).** On page 3 Malina says "and prices climb"
at 66.98 seconds. Page 3's file asks for "climb", and at that moment the flip counter on the second
card factory flips from £1.25 to £1.60 to £2.00 while coins stack up beside it and a red label
PRICES CLIMB draws its line to the counter; the camera is already close on the counter, with the
factory behind it softly out of focus. Every moving thing in the film is timed like that, to a word.

16. **Script** (`chapter-2-inflation/19 Script - chapter 2 - what really causes inflation.md`): the
    words Malina recorded, each page with the research ids its facts come from. Hands the words to
    the recording.
17. **Recording and sound** (`chapter-2-inflation/narration/`, `mix/chapter-2-mix.mp3`): ten
    recordings, their transcripts (the time of every word), the chapter timeline and the mix over
    your soundtrack. Hands the word times to the pages and the mix to the finishing step.
18. **Painted rooms with depth** (`chapter-2-inflation/pictures/`): 11 new paintings plus four from
    chapter 1, each with a distance picture, turned into rooms the camera can move a little way into;
    and 29 cut-out pieces. Hands them to the pages.
19. **Cinema stage and page files** (`chapter-2-inflation/film-code/`): the stage draws each page as a
    3D scene with lens blur, glow and a film finish, with flat documentary graphics on top, and joins
    pages with a page peel. The ten page files say what happens on each word. Hands pictures to the
    filming.
20. **Filming and finishing** (`film-code/tools/film-chapter-parallel.sh`, then the kit's
    `finish_film.sh`, `make_captions.py` and `check_sound_alignment.py`): films the chapter in 35
    short stretches, two at a time, joins them, adds the mix, squeezes a sendable copy, writes the
    captions and checks the sound lines up.
21. **Fact recheck** (`chapter-2-inflation/fact-recheck-2026-10-12.json`, summarised at the end of the
    research ledger): every spoken and on-screen fact checked again from fresh sources after
    recording. Hands any changes to the page files.

## Word list

| Word | Plain meaning |
|---|---|
| Austerity | Government cutting public spending, making borrowing dearer and holding wages down. |
| The capital order | Mattei's name for a world where a few own the land, factories and mines, and everyone else must work for a wage to live. |
| Research ledger | The list of every fact used, each with its source. |
| Page | One page of the film: one stretch of narration (about 10 to 30 seconds) with its own pictures. Chapter 1 has ten. |
| Delivery cue | A word in square brackets, like [urgent], that tells the voice how to say the next line. It is not spoken. |
| Ducking | Turning the music down automatically while the voice speaks, and back up in the pauses. |
| LUFS | A measure of how loud something sounds to people. About -15 is usual for phone video; more negative is quieter. |
| Credits | ElevenLabs' units of payment; about 1 credit per letter of script with this voice. |
| Transcript | ElevenLabs' written-out version of a recording, with the time each word starts and ends. |
| Page turn | The move from one page to the next. In the paper look the bottom-right corner lifts, rolls over showing the plain back of the paper, and uncovers the next sheet (log 11 calls it the page peel). In the scrapbook film the next page slid in from the right. |
| Rest | A moment where nothing new is drawn while Malina keeps talking. Planned, never longer than 1.7 seconds (2.5 on the end card). |
| Engraving | A picture made only of fine lines, like an old printed plate; here it is cut line by line on screen. |
| Captions file | A small text file (.srt) holding the words and when they are spoken; apps show them as subtitles. |
| Quality gate | The drawing skill's own checklist: the same picture every time, nothing forbidden in the code, and something visibly moving every second. |
| Style sample | A 6-second animated clip showing one possible look for the film. All five show the same scene so only the look differs. |
| fal | An online service that runs picture- and video-making programs; you pay per second of video made. |
| Video model | A program that makes a short video from a written description. It invents details, so every clip has to be checked. |
| Paper piece | A painted figure, object or word cut out like paper, with a narrow off-white margin, standing a little in front of its page. |
| Pop up | A piece folding up from lying flat to standing, hinged on its bottom edge, like a pop-up book. |
| Paper mouth | A figure's jaw cut out as its own piece, sliding down and up with the loudness of Malina's voice. |
| Lamp | The one light in the paper world, upper left; it gives every piece a soft shadow on the page behind. |
| Cut-out mask | A black-and-white picture marking which part of a painting is the figure; made by fal's background remover. |
| True peak | The loudest instant in the sound. Kept under -1 dB so phones don't distort it. |
| Sheet | One painted background printed on a sheet of paper, the page's backdrop. Most pages have one; pages 3 and 8 have two (one turns over to show the next), and the film ends on a plain dark one. |
| Cut list | The file that lists every painting and paper piece, with its paper margin, colour nudge, size and any repairs or printed words. The cutting tool works from it. |
| Chunk | One page's stretch of the film, filmed on its own and then joined to the others, so one page can be filmed again without the rest. |
| Master | The full-quality film with sound, kept in the project (about 280 MB, too big to send here). |
| Sendable copy | The film squeezed under the 30 MB limit for sending files here, in the most common video format so any phone or computer plays it. |
| Kit | The reusable copy of the tools, paintings and instructions for making other films in the paper look. |
| Folded prop | A paper object built as a real folded shape with flat faces (not a painted cut-out), so each fold is lit differently. |
| Distance picture | A grey picture of how far every point is from the camera (near dark, far light), drawn alongside a still so the finishing tool knows what to blur. |
| Background blur | Softening what is nearer or farther than the point in focus, the way a camera lens does close up; it makes a model look photographed. |
| Inflation | Prices in general going up over time, usually measured over a year: the whole shopping basket, not one price tag. |
| New money | Money a government or its central bank creates, rather than collects in tax or borrows from savers. |
| Central bank | The bank that issues a country's money and sets its main interest rate. New Zealand's is the Reserve Bank. |
| Interest rate | The price of borrowing. Raising it is the usual cure for inflation: loans cost more, people spend less. |
| Flat out | Every worker and machine already busy, so new money can't make more things, only push prices up. |
| Honest edge | The part of the chapter that admits creating money does push prices up when it's spent where nothing more can be made. |
| Outline | A page-by-page plan of a chapter: what Malina says and what appears, before any script is written. |
| Verdict card | In outline C, a paper card stamped with what caused each price rise: the money, a shortage, or where it was spent. |
| Cinema look | Chapter 2's look: each page is a real 3D scene with a camera that moves like a film camera, light, depth and film grain, with documentary graphics on top, still joined by page peels. |
| Painted room with depth | A painting pushed back into 3D using its distance picture, so the camera can move a little way into it and near things shift against far ones. |
| Card model | A simple 3D object built in code from flat card surfaces (factory, house, price tag, flip counter, dial), lit by the lamp like a real model. |
| Flip counter | A board of little flaps that flip to show a new price or number, like an old station departures board. |
| Hook | A few big words on screen, a short form of what Malina is saying. |
| Callout | A short label with a thin line pointing at something in the picture. |
| Dip to black | A very quick fade to black and back, used to hide a cut from one place to another within a page. |
| Page helper | A helper agent that builds one page file from the written guide, checks its stills and reports back. |
| Fact recheck | A second check of every fact, by checkers told to try to prove each one wrong from fresh sources. |

## Log (added to, never rewritten)

01. **Style chosen.** Drew three style samples. You chose the old scrapbook, a tall phone screen,
    15 to 20 minutes, and a narrator with quiet music. You asked if it was too big; we agreed to
    build a 2 to 3 minute test chapter first.
02. **Researched chapter 1.** 29 facts, each with a source. Some websites refused automated
    reading; facts only they could confirm were left out.
03. **First script.** Written in a formal voice. Not sent; replaced by 05 after you said it
    sounded like a lecture.
04. **Voices and sound.** Recorded three stock narrators reading the opening (about 12 US cents of
    credits) before you chose Malina; those are not used. Recorded the formal opening in Malina and
    mixed it over your soundtrack. Two problems fixed on the way: the mix came out 3 seconds short
    (a sample-rate change inside the loudness step), and the music dipped 31 dB under the voice,
    nearly vanishing; it now sits about 18 dB under while she speaks. Replaced by 05.
05. **Conversational rewrite.** Rewrote the script using your Pinker toolkit (start from what the
    listener knows, one plain name for each thing, a concrete case before each idea) and a more
    urgent tone. Recorded the new opening in Malina with delivery cues, with Mattei said the
    Italian way (mat-TEH-ee). Checked: the cues were not read aloud, and the word timings match
    the real pauses in the recording. New sound check made.

06. **Test picture.** Drew page 5 (the capital order) as a real page of the film: cut-out title,
    an engraved temple with two columns, two typed cards naming what each column stands for, red-pen
    arrows, a red-pen crack and "COULD FALL?". Close-ups at double size found three engraving faults
    (shadows ruled like graph paper, a doorway like chain-link fence, flat columns with a spiky top);
    all three fixed and re-checked. The page keeps its words clear of where phone apps put their
    buttons and captions, which leaves the bottom of the page quiet on purpose.

07. **Narration recorded and timed.** You said "Do it." Recorded pages 2 to 10 in Malina, one page
    at a time (about 2,950 credits, by the length of the text), downloaded them straight away, and
    got a transcript of each (free) for the time of every word. Checked: no delivery cue was read
    aloud (each lasts under a fifth of a second and sits in a pause), and the word times match the
    real pauses in the recordings. Laid the pages end to end with pauses of 1.1 to 1.7 seconds,
    levelled each page to the same loudness, and mixed them over your soundtrack: the music sits about
    18 to 21 dB under her voice while she speaks and about 12 dB under in the pauses (measured page by
    page). One problem fixed: levelling pushed the voice's peaks past full scale; the final limiter now
    holds them at -1.6 dB. Sent "07 Narration preview". Wrote "07 Script - chapter 1 - as recorded".

08. **Chapter 1 drawn and made into a film.** Drew pages 1 to 4 and 6 to 10 and re-timed page 5, so
    every card, typed word, cut-out letter, engraving line, red-pen mark and stamp lands on the word
    it belongs to. Three new engravings: five 1915 field-gun shells, an Italian factory (a red flag
    goes up at "take over their factories"), and three gold bars (the red pen draws a padlock at "a
    limit they chose"). Pages turn by laying the next one over the last. Close-ups found and fixed:
    marks tied to the wrong word where a word is spoken twice on a page; a cut-out T that read as I
    ("THREE PARIS"); a stamp covering the last letter of MATTEI; a candle poking into the header; two
    cut-out rows colliding; a flag too small to read; shells and gold bars small and off-centre.
    Rendered the 6,524 frames (19 minutes) and joined them with the mix. Found the sound 5 milliseconds
    late (the limiter's look-ahead) and corrected it: now 0.00 ms at every page. Loudness -15.0 LUFS,
    true peak -1.5 dB after encoding. The skill's quality gate: 13 of 14 checks pass. A typing pause it
    took for a freeze is now declared as a rest. The one check still failing flags 18 stretches of
    about a second where the only movement is a thin red-pen line or small typing beside a planned rest;
    the check looks at the picture at a quarter of its size, where those marks hardly show. Not fixed,
    because the marks are deliberate and making them bigger would change the look. Made a captions file
    from the word times and a cover picture (page 5). The first film file (37 MB) was too big to send
    here (30 MB limit), so the sent copy is compressed to 25 MB; side by side with the original, the
    engraving lines look the same. Re-checked the sent copy: sound lines up (0.00 ms), -15.1 LUFS,
    true peak -1.8 dB, all 6,524 frames.

09. **Voice fix, tested on pages 1 to 4.** You heard the accent switch early in the film, and
    shouting, and suggested New Zealand accent rules in ElevenLabs. I looked: ElevenLabs' documentation
    has no accent rules for a voice (only pronunciation rules that fix one word at a time, which this
    connection can't attach) but its newest model follows an accent instruction written into the script.
    Measured the old recordings: pages sat at very different voice heights (page 3 about 5 semitones above
    page 4), matching the mixed mood cues ([urgent], [serious] and so on); capitals added pushed emphasis.
    Rewrote the narration: the same New Zealand accent instruction opens every page, no other cues, no
    capitals, Mattei said in English sounds. Researched the sounds of standard New Zealand English as a
    listening guide ("09 Research - New Zealand accent"). Re-recorded pages 1 to 4: the gap in voice height
    between pages fell from 5.3 to 1.8 semitones. Not settled by measuring: whether it sounds New Zealand,
    and whether every push is gone; the voice still rises on some words (as it did before), which may be
    ordinary emphasis. Sent "09 Voice test". Fixed on the way: the timing tool read the words inside the
    long accent instruction as spoken words; it now treats everything in brackets as the instruction.

10. **Whole chapter re-recorded; louder music; five looks.** You said the voice "sounds a bit
    Australian. It'll do for now", asked for the music "slightly" up, and asked for five 2D animation
    styles from fal that bring out discontent and conflict, with few colours but not simple drawing.
    Recorded pages 5 to 10 like the test, got their word times (free), and fixed an old problem on the
    way: ElevenLabs placed each page's first word up to 0.32 seconds late; the timing tool now moves it
    to where the voice really starts (nine pages corrected). Raised the music 3 dB: measured about 18 dB
    under Malina while she speaks (was about 21). Sent "10 Narration". Made five 6-second samples of
    the same scene (Glasgow, 1919) with fal's MiniMax video model, about 90 US cents: revolutionary
    poster (red, black, cream), charcoal lithograph (soot black, sepia), linocut print (black, off-white,
    rust), painted gouache (slate blue, grey, ochre), graphic-novel night (blue-grey with red). Removed
    their own sound (one had a made-up shouted line). Checked frame by frame and found faults the real
    film must avoid: all five drew Second World War tanks and had a tank face the crowd (the research
    says troops and tanks came after the clash); the linocut put a symbol like a hooked cross on a
    placard; the night sample added a real movement's red-and-black flag. Not yet remade: the film
    itself, which waits on your choice of look.

11. **Paper pop-up test, page 3.** You showed four pictures from a history channel and asked for
    still painted images moved like paper or card on a surface, with no hands: pop-ups, book page
    turns, a paper mouth, things crashing in (a tank crashing into a cheering crowd), and few plain
    words that only help memory. Looked up what makes cut-out and pop-up animation read as paper
    ("11 Research - paper pop-up style"). Painted eight pictures with fal (Glasgow square, two crowds,
    soldiers, a First World War tank, a pithead, a miner, a report), about 82 US cents with the
    cut-outs; checked each one (the tank came out the right shape this time; a small pale fin on its
    roof that could read as a flag was cut away). Built a paper stage: every picture is a sheet in a
    small 3D world with one lamp, filmed by a hidden browser. Problems found and fixed on the way: no
    shadows at all (flat sheets lit from the front cast none until set to cast from both faces); the
    smoothest soft shadows do not work in the hidden browser, so softened plain ones are used; shadows
    too small to see, then word shadows so big they read as a second word; a page turn that swung like
    a door and left white strips (now a corner peel, with pieces folding away first); a mouth like a
    black bar (now a narrower jaw that opens on louder syllables); dust hidden behind the crowd.
    Filmed the test (23 seconds, about 12 minutes of computer time) on Malina's page 3 words with the
    new mix: -15.0 LUFS, 19 MB.

12. **Look approved; chapter planned.** You said "This is great!" about the page 3 test. Planned all ten
    pages in the paper look: what flips up, slides, drops or folds away on which word, and the few
    words on screen ("12 Plan - chapter 1 in paper pop-up"). About 70 pictures to paint, about US$5
    (up to US$8 with re-paints). Nothing painted yet.

13. **Chapter 1 made and filmed in the paper look.** You said "Do it!". Painted 47 pictures with fal
    (8 page backgrounds, 8 big figures, 30 objects, 1 re-paint), about US$2.55 with the cut-outs, and
    checked every one on contact sheets. Two failed: the shells looked like rifle cartridges
    (re-painted as artillery shells and cut into seven separate shells) and a new tank came out an odd
    shape (page 3 keeps the approved one). Laying every cut-out over magenta showed what the background
    remover had dropped: the politician's lectern (put back), Sardinia on the map of Italy (the map is
    now printed on a small paper card) and part of a coal heap (kept with a lower threshold). Rebuilt
    the cutting tool to work from one cut list for the whole chapter (page 3's pieces came out
    identical to the approved test, checked pixel by pixel). Wrote one file per page and a chapter
    scene that stacks the sheets like a book, turns each page 0.3 seconds after its last word (pieces
    fold away first) and moves the camera. Checked about 85 single moments at full size before filming
    and fixed: three words spoken twice looked up by their first time ("war", "get", "prices"); dust
    that lingered after its page; knocked-down pieces showing as pale blobs; pieces cut off at the frame
    edge; a falling word washed out by dust and a ghost shadow; a division by zero in a walk. Filmed
    6,641 frames one page at a time (about 80 minutes; two at once was no faster). After filming, a
    close look found the worker's cap peeking over the slammed door on page 6: made the door taller and
    filmed page 6 again (10 minutes). The joins between pages run smoothly (measured frame to frame).
    Sent copy: 3 minutes 41 seconds, 1080 x 1920, 6,641 frames, 28.2 MB, -15.1 LUFS, true peak -1.7 dB;
    sound lines up to 0.00 ms at the first word of every page (measured against the mix). The full-
    quality master (290 MB) stays in the project. New captions from the steady-accent word times (121
    lines, none longer than 42 letters; "Clara E. Mattei" is no longer split at the "E."). Cover: page 5.
    Not checked: how it feels to watch at full speed on a phone (I can only look at single frames), and
    whether every entrance lands where you would want it.

14. **A kit for new series.** You said "This is fantastic." and asked for the assets and reusable tools in a
    zip with clear instructions, for another agent to start a series on the enclosures. Made
    `kit/paper-pop-up-film-kit/`: the paper film tools made general for any series (page turns, camera
    and filming work from any list of page files; the film script finds where pages end by itself; the
    browser and label font are found on any computer; the narration tools take their pauses and folders
    as settings), this chapter as the worked example, a template for a new chapter, the 53 paintings as
    high-quality JPEG with their 43 masks and the exact prompt of each (recovered from fal's request
    history), your soundtrack, and seven instruction files (a plain start page for you; the full path
    from script to film for the agent; the look in your own words; how a page file works; painting
    prompts; lessons; your rules for running a project). Packed as three zips under the 30 MB limit
    (20.8, 17.5 and 24.8 MB). Tested: unzipped into an empty folder, installed, rebuilt the pieces and
    drew two moments, which match the example; the sound tools rebuild this chapter's sound byte for
    byte; the film script filmed and joined a page; the finishing script made a 26.5 MB copy with the
    sound lined up. Two mistakes in the kit's papers were caught on re-reading and fixed (the shells
    filed as a figure; a wrong word count). Not tested: another computer or operating system; the
    new-chapter template (it can only run once a new chapter has its recordings and paintings).

15. **A one-page picture with origami props.** You asked for "a blank page on and angle with the props
    like origami" and "some mood lighting to cast a shadow". Built it in the paper stage at no cost: an
    A4-shaped blank page turned at an angle on a dark wooden desk, its corner curling up; a folded
    cottage, three trees, a paper crane and a zig-zag fence standing on it; one low warm lamp from the
    front left making a pool of light and long shadows, with a faint cool light from behind. Took nine
    test pictures. Two things failed on the way: the trees came out almost black because they were
    shading themselves (fixed by changing how shadows are kept off a surface), and the crane did not
    read as a crane from above (turned side-on with wings raised, camera lowered). Checked the whole
    picture and close-ups. Not checked: how it looks on your phone screen.

16. **An open pop-up book.** You said "Yeah like that. But it's not aesthetically beautiful", and asked
    for an open book seen as if reading it at a desk (no desk), with intricate pop-ups whose shading
    sells the drama, leaving the look to me. Built it in the paper stage at no cost: a red cloth book
    with curved pages, small printed type and page numbers; rising from it, all in one ivory paper,
    three layers of hedged hills with a church, a paper moon with hanging stars, cypresses, a three-layer
    lacy oak, a cottage with scalloped shingles, cut windows and a smoke curl, a picket fence with roses,
    sheep and a grass strip. Warm reading lamp, cool moonlight, and a warm light inside the cottage
    glowing through its windows and open door. Finished like a photograph (window glow, very slight lens
    blur, soft corners, grain). Took 14 test pictures. Failures on the way, all fixed: the oak's leaves
    cut off by its sheet edge; the pages reading as upright walls; rings and criss-crossing shadows; a
    too-coarse distance picture and a blur that ate the detail; light leaking out of the back windows.
    Checked the whole picture and close-ups of the oak, moon, hills, cottage and sheep. Not checked: how
    it looks on your phone. Unsure: the sheep are still the weakest part (white on white; their shadows
    read more clearly than they do).

17. **Chapter 1 packed for handing over.** The research, notes, decisions, tools and rules behind
    chapter 1 were packed into one zip ("17 Chapter 1 - research notes, decisions, tools and rules").
    (Recorded here from the zip you uploaded; the session that made it isn't available, so this entry
    has no more detail.)

18. **Chapter 2 researched; three outlines.** You asked for part two on inflation, explained within
    the first video, with about three outlines before anything is made, up to US$10 on fal for
    paintings and ElevenLabs only for speech, and every helper at medium effort. Set the project up
    in your repository (chapter 1's notes, research, scripts and rules, copied from the zip). Four
    research helpers gathered 72 sourced facts (the history after chapter 1, real cases, New Zealand
    now, how inflation works); 43 more claims they could not confirm were left out. Three outlines
    were drafted from three angles (back to the shell factory; what happened next; five price tags)
    and each was checked against the facts, your rules and chapter 1, then fixed. The checks caught,
    among others: a line saying today's price rise is "mostly fuel" (wrong: without fuel it's still
    2.9%); "too strong for too long" put on the wrong report; Britain's money creation shown beside a
    0% inflation figure that really came from falling fuel and food prices; and Germany in 1923 said
    to "stop" making coal and steel (the sources say only that output fell). Ten helpers in all, about
    17 minutes. No cost. Not checked: Mattei's book itself; official Reserve Bank and Statistics New
    Zealand pages, which refused automated reading (their figures come from bank and news reports and
    your deficits report). A pull request couldn't be opened, because the repository has only this one
    branch.

## Next step

Tell me which outline to make (A, B or C, or a mix you name).

## Traps

- The latest New Zealand inflation figure (4.1%, year to June 2026) may be replaced on 22 October 2026:
  check it on the day chapter 2 is recorded.
- Mattei's interpretations stay marked as hers ("Mattei says", "her answer"), however urgent the
  wording gets.
- Your soundtrack is loud and dense (about -13 LUFS); it must always be turned down under Malina.
- ElevenLabs download links expire after 2 hours: recordings are downloaded straight away.
- Re-recording one page moves every time after it, so the whole chapter's timing, mix and film are
  made again (about 25 minutes of computer time, no extra cost beyond the recording).
- The film's first frame is page 1's empty parliament, before the politician folds up. Where an app
  lets you pick a cover, use "13 Cover".
- The sent film is squeezed to fit under 30 MB. For uploading to a video site, the full-quality master
  (`paper-film/out/chapter-1-paper-master.mp4`, 290 MB) looks sharper; ask and I'll find a way to get it to you.
