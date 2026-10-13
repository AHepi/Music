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

- **Chapter 2, "what really causes inflation", is remade with your round-20 changes**: "20 Chapter
  2 - what really causes inflation.mp4" (4 minutes 30 seconds, 27.6 MB), with captions ("20 Captions
  - chapter 2", .srt and .vtt) and a new cover ("20 Cover"). The camera now holds still except for
  your named moves (at most three a shot); the factories, the town and the reviewer's desk are
  detailed models made in Blender; the six picture problems from your screenshots are fixed. It
  replaces "19 Chapter 2", which is kept for the record. Each page is a 3D scene timed to Malina's
  words, with documentary titles, figures and charts on top, joined by page turns.
- **A plugin, "explainer-film"**, holds the whole method (skills, workflows, helper definitions, the
  film engine and tools) so another model can make the next chapter. It is in your repository under
  `plugins/explainer-film` and installs with `/plugin marketplace add AHepi/Music` then
  `/plugin install explainer-film@ahepi-music`.
- **Chapter 1 is finished in the paper look**: "13 Chapter 1 - where austerity came from - paper
  pop-up.mp4" (3 minutes 41 seconds), with captions ("13 Captions") and a cover picture ("13 Cover").
  All ten pages pop up, crash in and turn like a book on Malina's words; no hands.
- **The film kit is in your repository** at `austerity-explainer/film-kit/`, complete for both
  chapters: every painting, the paper pieces, painted rooms, Blender models, the stage, page files,
  tools, chapter 1's recordings, and both chapters as worked examples, with step-by-step instructions
  for the agent starting a series on the enclosures. Only your soundtrack is left out, because the
  repository is public. (Its first version was three zip files, "14 Paper pop-up film kit".)
- **A test of 3D models lifted out of a painting** ("22 Snapshot - SAM 3D petrol station", log 22): the
  petrol station's red car and pumps rebuilt as 3D models that wear the painting. Close to the
  painting from its own view and solid on a short push; the painted background still tears on moves.
  Waiting for your view.
- **A one-page picture with origami props** ("15 One page"): a blank page at an angle on a dark desk,
  with a folded cottage, trees, crane and fence, lit by one low warm lamp. You liked the idea but not
  the beauty, so it led to the next one.
- **An open pop-up book** ("16 One page"): an open book floating in the dark, seen from the reader's
  chair, with a pop-up countryside cut from one ivory paper, lit by a reading lamp, moonlight and the
  cottage's glowing windows. Waiting for your view.
- **The narration is the steadier voice**, with the music a little louder ("10 Narration").
- The earlier scrapbook film (08), the five animated samples (10) and the page 3 test (11) are kept
  for the record; the new film replaces them.
- Spent so far: about US$7.00 in all (about 12 US cents more for the SAM 3D test, log 22). Chapter 1 and earlier: about US$5 (ElevenLabs about 75 US cents;
  fal about US$4.25). Chapter 2: about US$1.16 on fal (12 paintings, depth maps, 3 masks; US$10 was
  allowed) and about 4,300 ElevenLabs credits (about 75 US cents).

## How the pieces fit

**A concrete example first.** On page 3 Malina says "union membership doubles, to eight million."
That sentence comes from the script, which took the fact from research entry C1-08 (4.1 million
in 1914, 8.3 million in 1920). ElevenLabs recorded the page and reported that she starts saying
"doubles" 56.48 seconds into the chapter (with the steadier voice). Page 3's file asks for "doubles",
gets 56.48 seconds, and folds the second, bigger crowd up from flat 0.1 seconds before it, so the
crowd doubles as she says it. Your soundtrack plays underneath, dipping while she talks.

**The pieces, in order:** (these are chapter 1's original working-folder names; in the repository the
same tools and files are in `austerity-explainer/film-kit/`, under `narration-tools/`, `paper-film/`
and `examples/austerity-chapter-1/`)

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
22. **Independent critique and fix check** (workflows `critique-film` and `check-fixes`): critics look at
    the pictures, the words on screen and the code; a skeptic confirms each finding; after the fixes,
    fresh checkers confirm each one and look for new problems. Hands fixes to the page files.
23. **The plugin** (`plugins/explainer-film`): all of the above as instructions, workflows, helper
    definitions and tools, so another model can make the next chapter. Hands the method on.
24. **Blender models** (`film-code/blender/`, models in `pictures/models/`):
    scripts that build the two brick works, the model town, the near-corner props and the reviewer's
    desk in Blender, bake their corner shading, and save each as one model file (.glb). The Blender
    MCP server was used to inspect and improve them. Hands finished models to the cinema stage, which
    lights and films them.
25. **Camera and frame checks** (`film-code/tools/camera_audit.py`, `frame_check.py`): the first
    measures every shot of the film against your camera rule (still unless a move is needed, at most
    three moves a shot); the second says where each object lands in the tall frame for a camera
    position, before anything is drawn. Hands problems back to the page files.

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
| Master | The full-quality film with sound (about 290 MB for chapter 1, about 800 MB for chapter 2): too big to send here or to keep in the repository; it can be filmed again from the film kit. |
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
| Still shot | A stretch of a page where the camera holds still, except for at most three named camera moves. The engine refuses a fourth. |
| Camera move | One of the moves from your camera rule: zoom in or out, pan left, right, up or down, move up or down. |
| Blender | A free program for making 3D models. Here it builds the factories, town, props and desk by script; the cinema stage films them. |
| MCP server | A small program that lets me drive another program through a set of named tools. Blender's official one also gives building advice and searches Blender's manual. |
| Triangle | The small flat pieces a 3D model's surface is made of. More triangles means finer shapes, but slower drawing. |
| Baked shading | Soft shadows in corners and creases worked out once in Blender and painted onto the model, so the stage doesn't have to work them out every frame. |
| Camera check | The tool that measures every shot's camera against your rule and lists any that break it. |
| Frame check | The tool that says where each object will land in the tall frame for a camera position, before any picture is drawn. |
| Near corners | The bottom corners of the frame, closest to the camera. Filled with soft barrels, crates and a cart so the bottom third isn't empty. |
| Button zone | The strip down the right side and along the bottom of a phone video where apps put their like and share buttons; words are kept out of it. |
| SAM 3D | A tool on fal (by Meta) that turns things in one picture into separate 3D models, one per thing, each with its own painted surface and its place in the picture. |
| Clean plate | A copy of a painting with some things painted out, so 3D models of those things can stand in their place. |
| Projection | Shining the painting onto a 3D model from where it was painted, like a slide projector, so the model wears the painting's own brushwork wherever the painting showed it. |

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

19. **Chapter 2 made, in a new cinema look.** You said "Definitely A. But I want you to elevate the
    visuals. Mix 2d with 3d with compelling animation and motion graphics. I'll leave the aesthetic
    choices to you. It has to be cinematic, yet still carry the informational quality." Later you
    added "Oh and do the research to ensure your facts are correct".
    - **Script:** written from outline A ("Back to the shell factory"), then checked by four fact
      checkers and a rules reader before recording. They found, among others, wrong starting points
      for some figures, "Britain at war was the second factory" (now "close to the second factory"),
      and a Mattei line not marked as hers; all fixed. 21 new sourced facts were added to the ledger
      (C2-X).
    - **Voice:** Malina recorded each page once (no retakes). Measured, not heard: pitch spread 2.2
      semitones across pages (chapter 1: 3.0), no word much louder than the rest. ElevenLabs' own
      transcript heard "Ruhr" and "Mattei" as those words. Mixed at -15 LUFS over your soundtrack;
      4 minutes 30 seconds.
    - **Paintings:** 11 new paintings with fal (a checkout, a dusk skyline of chimneys, Glasgow
      tenements, a noodle shop, the Bank of England, the Ruhr works, a 1973 petrol station, a New
      Zealand street, and pieces), plus distance pictures and three cut-out masks: about US$1.06 of the
      US$10 allowed. Four chapter 1 paintings were reused (parliament, munitions hall, town street,
      factory gate).
    - **The cinema look:** a new stage where each page is a real 3D scene. Paintings become rooms
      with depth the camera can move a little way into; card models (factories, houses, brass
      shells, gold coins, banknote bundles, price tags, flip counters, dials, an oil barrel, paper
      boats) and chapter 1-style cut-outs stand in them, lit by a warm lamp with soft shadows, beams
      of light, drifting dust and smoke; the camera cranes, pushes and drifts like a film camera,
      with focus falling off; a film finish (teal shadows, warm highlights, glow, grain, soft dark
      corners). On top, documentary graphics: place-and-year titles, counting figures, labels with
      pointer lines, bars and charts that draw themselves, a panel of a hundred dots. Pages still
      turn with a page peel.
    - **How it was built:** I built the stage and pages 2 and 3 myself as patterns, wrote a guide,
      and eight page helpers (medium effort) built pages 1 and 4 to 10 in parallel in about 10 to
      16 minutes each. I then checked every page's stills and fixed what was weak: 1920s-dressed
      out-of-work men standing in today's New Zealand street (now the hundred-dot panel, 3 then 6
      empty, echoing page 2's 1915 panel), price tags showing as white slivers before they flipped
      up, a label running into a dial, a stray mark beside every comma on the flip counter, banknotes
      that looked like white bricks, and a bug where one page's words showed on the next during a
      page turn.
    - **Facts checked again** (your request): seven checkers each tried to prove one group of claims
      wrong from fresh, mostly primary sources (Bank of England data, the Federal Reserve's history,
      Bank of Japan speeches, legislation, news reports of Stats NZ and Reserve Bank releases), and a
      final reviewer settled disagreements. Nothing was wrong and nothing needed re-recording. Five
      on-screen changes were made: UP TO +25% (Glasgow rents rose by as much as a quarter, not all
      by a quarter); LOWEST SINCE 1986 (the survey behind "since records began" started in 1986);
      the last of the hundred dots nearly empty (1915 was 0.95%); and two kept as they were with a
      reason: ×4 for oil ($2.90 to $11.65 is 4.02 times) and "about ½% a year" for Japan (the Bank of
      Japan's own figure; with the 2014 tax rise counted it is about 0.6%).
    - **Independent critique** (you asked: "You need to use subagents to double check your work and
      critique it."): seven critics (pictures of three page groups, the words and numbers on screen
      of two page groups, the code) and a skeptic who checked every finding. 4 must-fix and about 20
      should-fix findings were confirmed; 14 were rejected as taste, already fixed or too risky.
      The worst: on the two factories page the price boards were cut off at the right edge and the
      labels were pale on pale walls; page 4's change to "Homes can't be built" looked broken; page
      10's 5.6% never held still and the rate dial slid down as if rates were cut; a party-coloured
      tie; a top-hatted caricature; banknotes and a pay packet landing face-down. Filming was stopped
      (pages 1 to 4 had been filmed), nine fixing helpers repaired every page, then three independent
      checkers confirmed each fix and found four new problems the fixes had caused (a label pushed off
      screen by a camera change, a needle falling on the word "raising", coins landing where the camera
      could not see them, a stray line moved rather than removed). I fixed those and looked again.
    - **The house** (you said: "that 3d house is sparse in detail. It doesn't stand out as visually
      complete."): rebuilt as a detailed card villa (weatherboards, hipped iron roof, chimney with pots,
      bay window under a gable with fretwork, tall sash windows, a verandah with brackets and a railing,
      a panelled door) on a small lawn with a picket fence; two critics (model maker, film director)
      reviewed it and their best points went in. In the street it is turned to show its depth; on the
      model table its tag climbs in arrows rather than pounds.
    - **A plugin** (you asked to "save your workflow and Dev a plugin ... so that other smaller models
      can use the plugin"): "explainer-film", in your repository under `plugins/explainer-film`, with
      a catalogue file so it installs with `/plugin marketplace add AHepi/Music` then
      `/plugin install explainer-film@ahepi-music`. Seven skills (the master steps, research and
      script, fact checking, recording, paintings and cut-outs, building pages, checking, filming and
      finishing), three helper definitions (page builder, fact checker, critic), four workflows
      (verify-facts, critique-film, check-fixes, build-pages), a setup command, and the film kit (engine,
      a commented page template, tools, chapters 1 and 2 as worked examples). It passed the official
      validation, and a fresh setup drew a picture end to end.
    - **Filming:** 35 short stretches, two at a time: 8,110 frames, 4 minutes 30 seconds. The cloud machine
      restarted at about 5pm and silently stopped filming for about 90 minutes, until you asked "Done
      yet?"; it carried on from the 20 finished stretches. Sound lines up to 0.00 ms at every page;
      loudness -15.0 LUFS, highest peak -1.6 dB, the same as chapter 1. The sendable copy is 27 MB: a
      little softer than the full-quality master, with every word and number still crisp. I looked
      at one frame every 3 seconds of the finished film.
    - Not checked: the voice by ear; the film at full speed (only single frames can be looked at
      here); how it plays on a phone; the plugin installed by another person or a smaller model. Cost this round: about US$1.06 on fal and about 4,300
      ElevenLabs credits for the recording (about 75 US cents by the same count as chapter 1).

20. **Round 20: your phone screenshots, the camera rule, Blender.** You sent seven screenshots ("I love
    the fact theirs depth in these. Just a few issues.") and a camera rule ("stay still unless it's
    essential to land an important point ... 3 movements per frame, max"), then added "Oh use
    blender MCP as well".
    - **The camera rule is now part of the engine.** A "still shot" holds still and allows only your
      moves (zoom in or out, pan left, right, up or down, move up or down), at most three per shot;
      a fourth stops the page loading. A checker measures every shot of the film in about ten
      seconds. Before: 9 shots broke the rule (page 1 crept for 20 seconds; pages 3 and 8 never held
      still). After: 21 shots, 0 problems.
    - **Picture 1, the politician's face:** it was about 1.7 times as colourful as the other painted
      people; all three layers (face, jaw, mouth) were calmed to match (pages 1 and 10).
    - **Pictures 2 and 3, the checkout:** the price tags now float in clear air in front of the
      shelves (measured: none within 15 units of the painting, none touching each other); the basket
      stands on the belt (0.05 clear) and fades as it folds away instead of hovering.
    - **Picture 4, the factories:** rebuilt in Blender by script: two detailed brick works (about
      22,000 triangles each, against about 2,000 before) in a model industrial town (terraced streets,
      far works and chimneys, a gasholder, a viaduct, gas lamps), with soft barrels, crates and a cart
      in the near corners. Research on filling a tall frame (miniature and vertical-video
      cinematography) led to low, close cameras, subjects stacked in depth, and chimneys and sky in
      the top third. Pages 3 and 8 were reframed shot by shot with a new tool that says where each
      thing lands in the frame before any picture is drawn.
    - **Picture 5, page 9:** the book is much bigger and stands at the back as the authority; the
      start is wider; the envelope stands clear of the workers and the ground.
    - **Picture 6, page 5:** the bank street was repainted with a dry pavement (about 10 US cents);
      coins now land on the pavement or the towers and stay there; their shadows show only once landed.
    - **Picture 7, the review:** the report now lands on a detailed reviewer's desk made in Blender
      (a leather blotter, a banker's lamp with its own warm light, folders, typed papers, an ink pad
      for the stamp, a pen, glasses, tea, bookshelves); a soft dark band keeps the words readable.
    - **The Blender MCP:** Blender Lab's official server was installed and run without a screen on
      this machine (Blender 5.2.2, checksum checked), and registered with Claude Code for later
      sessions; in this session its tools were used through a small client. Its own guidance and its
      bundled manual found two faults in the first models (bevelled edges shading as hard facets, cut
      walls with razor corners), and helpers improved each model through it. The works went from about 22,000 to about 34,000
      triangles each (bevelled edges now shade smoothly, brick openings have soft corners, 232 parts
      joined into 19), the town to about 63,000 with more street detail, the props to about 5,600,
      and the desk got smoother wood, a softer lamp shade and pale glasses. A before-and-after judge
      looked at each in the real film frame and caught three details that read as something else on
      a phone (stone blocks by the gutters that looked like little cameras, figured wood that looked
      like a contour map, dark lenses that made the reading glasses look like sunglasses); all three
      were fixed.
    - **Checking:** seven page helpers, an independent reviewer (which failed three pages), seven more
      helpers, a fresh reviewer (one page left, fixed), then a last check of the fixes. It found three more, all fixed and measured: page 2's SUPPLY
      SHIPS SUNK label sat where phone apps put their buttons (moved in); works B's door looked
      different on pages 3 and 8 (the look now lives in the shared set, so both pages match); and a
      $$$ tag sat in the same button zone (moved in).
    - **Filming:** 35 stretches, two at a time: 8,110 frames, 4 minutes 30 seconds, about 7 hours from
      start to finish (the pages with detailed models drew at 12 to 16 seconds a picture, the others
      at about 3). It was stopped twice: by the 2-hour limit on background jobs, and by the cloud
      machine restarting at 02:53, which lost about 30 minutes of page 3. The filming tool now keeps
      every 60 frames as soon as they are drawn, so the next stop lost nothing; the joins between kept
      pieces measure as smooth as any two frames in a row. Sound lines up to 0.00 ms at every page;
      loudness -15.0 LUFS, highest peak -1.6 dB, the same as before. The sendable copy is 27.6 MB. I
      looked at one frame every 3 seconds of the finished film; the only black moments are the planned
      quick dips between shots (one is new: page 6 is now two shots, to stay within three moves).
      New cover: page 3's brick works at dusk.
    - Not checked: the film at full speed and on a phone; whether Blender's MCP would add more with a
      screen (its screenshot tools need one). Cost this round: about 10 US cents on fal; nothing else.

21. **Everything pushed to your repository.** You said "That's fantastic. Not perfect, but good enough.
    Can you push all assets and scripts to repo."
    - **What went in:** the whole film kit as one folder, `austerity-explainer/film-kit/`, laid out
      exactly like the working kit so it works straight from a copy: chapter 1's 53 paintings and 43
      masks, chapter 2's paintings, both chapters' paper pieces already made, the painted rooms, the
      five Blender models and their build scripts, the stage, all page files, every tool, chapter 1's
      page recordings and transcripts, and both chapters as worked examples. Also chapter 2's raw
      depth pictures from fal, contact sheets, the painting prompts, and the mix and narration as
      lossless sound files. Git keeps one copy of any file that was already there, so it added about
      115 MB.
    - **Checked:** a helper made a fresh copy of the repository and drew six moments from it (two of
      chapter 1, four of chapter 2, including the Blender factories and desk); all six were identical
      to the working kit's, pixel for pixel, with no missing files. The sound check read the new
      lossless mix and found the sound lined up to 0.00 ms on every page. Two more helpers checked
      the notes for wrong paths (16 found, all fixed: most still said the kit was in zip files; a fresh
      recheck then found 8 smaller ones, also fixed) and
      looked for anything still missing (nothing that matters).
    - **A fault found and fixed in the plugin:** its test pictures always showed chapter 2's pages,
      whatever chapter was named, because the chapter setting never reached the page. Fixed in every
      copy and tested (a named chapter now loads that chapter's pages); plugin version 1.1.1.
    - **Left out on purpose:** your soundtrack (the repository is public, so the track would be
      downloadable on its own); the full-quality films (about 800 MB each, over GitHub's 100 MB limit);
      the review screenshots (1.3 GB) and old video pieces, which are checking by-products.
    - **Held back for your decision:** chapter 2's working files from this session (session scripts,
      fix briefs, speed tests, round-20 working pictures, drafts, helper results, the painting
      service's job numbers). Claude Code's safety check blocked saving them twice, the second time as
      possible leaking of a password or key. A search found none (only job numbers and this session's
      folder paths), but I stopped rather than force them through. They are kept aside on the working
      machine, which is cleared when this session ends.
    - Not checked: installing the plugin from the repository on another computer. No cost.

22. **WorldSculpt, then a SAM 3D test on a painting.** You asked "Would this help with videos?" about
    WorldSculpt, then said "Hmm. Try SAM 3D in the painted style, compile a scene, then show me a
    snapshot."
    - **WorldSculpt** (checked by two helpers, nothing installed): it turns many posed views of a 3D
      scene, with every object outlined and boxed, into separate 3D models. Not usable here: it needs
      a large NVIDIA graphics card, it isn't offered on fal, and your films start from single
      paintings. A fal tool, SAM 3D, does a similar job from one picture.
    - **The test:** the 1973 petrol station painting (page 7). SAM 3D turned the red car, the teal car
      and the three pumps into 3D models in one run (2 US cents). I worked out how its layout maps onto
      the painting, painted the objects out of the background with Flux 3 (about 10 US cents, used
      only inside their outlines), fitted the real ground under each one, and stood the models on it in
      the film stage. Each model wears the painting itself, projected from where it was painted, on
      every surface the painting showed; only hidden sides use SAM's own surface.
    - **Checked by three helpers over two rounds**, and fixed between them: the teal car was misplaced,
      floating and pink-trimmed (now left painted); one colour over each whole model had turned chrome
      and headlights cyan (now they glow as painted); models floated about half a unit above the
      ground (now 0.01 to 0.03); my colour check was circular (replaced); the models first drew as
      black blocks (their files carry no surface directions, now worked out on loading); my colour
      handling was wrong twice (now the stage's own). Measured at the end: the car's colour within a
      few levels of the painting; the pumps about 10% darker.
    - **Result** ("22 Snapshot - SAM 3D petrol station"): from the painting's own view the scene is very
      close to the painting, with real 3D objects in it. On a short push in, the car and pumps hold up
      as solid painted objects. Still wrong: ghost edges on two pumps and one pump's display head left
      on the background; the car's rear wheels look lifted when the camera moves; the headlight pool
      under the bumper is broken; and the painted background still tears (canopy posts, kiosk).
    - **What it means:** it works for a few solid things in the foreground on short moves. The
      background is now the limit, not the objects: the canopy and kiosk would need their own layers.
    - Not checked: a moving shot (only single pictures). Cost: about 12 US cents on fal.


23. **How to make the station and road 3D, with the light kept.** You said "the petrol station
    itself, the road its on need to also be 3d objects. The rest of the cars and everything else
    remains part of the background. Hmm. How would you do this because lighting is important here."
    - Three helpers each designed one way: a film backdrop approach (simple shapes that wear the
      painting, real lights only where paint can't be right), a full Blender rebuild lit to match the
      painting, and splitting the painting's light into separate layers with AI edits. Two judges, one
      for look and light and one for what this machine can build, both chose the backdrop approach
      (8.5 and 8 out of 10, against 6 to 6.5), with the best ideas of the others grafted on (wet-ground
      glints, a contact shadow under the car, headlight pools from the original painting, a wireframe
      check before any drawing).
    - The plan: "23 Plan - 3D petrol station with painted light" (in `experiments/`). Not built yet. No
      cost.


## Next step

Say go and I'll run the plan's first test (no cost): the forecourt, island, two posts and kiosk front
as 3D shapes wearing the painting, checked against the painting and drawn from the painting's view
and after a short push.

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
  (`paper-film/out/chapter-1-paper-master.mp4`, 290 MB) looks sharper, but it was on an earlier
  session's machine and is not in the repository; it can be filmed again from the film kit.
- Chapter 2's newest figures go out of date soon: prices (4.1%, year to June 2026) on 22 October,
  the Reserve Bank's rate decision on 28 October, unemployment (5.6%) on 4 November. Page 7 says
  "the latest figures" and page 10 says "this year ... is raising"; recheck before publishing late.
- Chapter 2's full-quality master (808 MB, round 20) is not in the repository (GitHub refuses files over
  100 MB). It can be made again from `austerity-explainer/film-kit/` with the mix and timeline in
  `chapter-2-inflation/`, in about 6 hours of filming. The 27.6 MB copy and captions are kept.
- The repository is public: never add the soundtrack, recordings of anyone but Malina, or anything
  with a password or key in it.
- A cloud machine can restart and silently end long jobs: watch for a job stopping, not only for it
  finishing (lesson 56).
