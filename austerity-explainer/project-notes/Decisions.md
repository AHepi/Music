# Decisions

What this file is: every decision about the austerity explainer, newest at the bottom. Your own
words are quoted exactly. Decisions Claude made on its own are marked "Claude's call" so you can
overturn any of them in one line. Changes to the project must follow this file.

## 2026-10-11

1. **The request** (your words): "Can you make a explainer video of the origins of austerity from
   Clara Matteo's book The Capital Order from the perspective of MMT. It needs to be easy to
   understand, yet thorough. And do not use the term MMT."
   Points you want covered (your words): "Where it came from / Why it was proposed / Where it was
   tested / What happened / What does Thatcher have to do with it. / Why nations need social spending
   to develop. / What this has to do with New Zealand and Australia / What really causes inflation:
   Spending, Money minting, or something else? / What austerity did to the people. / Why you lose
   bargaining power / Why it's oppressive."
   Structure (your words): "You decide how it all fits together."

2. **Style**: "A Old scrapbook (Recommended)".
3. **Shape**: "Tall phone screen" (1080 wide by 1920 tall).
4. **Length of the whole film**: "About 15 to 20 minutes".
5. **Sound**: "Narrator voice + quiet music (Recommended)". The voice comes from your ElevenLabs
   account; no credits are spent at length without your approval of the cost.
6. **Start small** (your words, after asking "Is this too big?"): "How about starting with the history
   of austerity first? Where it came from and why it was implemented?"
   So the first piece is a test chapter of about 2 to 3 minutes covering "where it came from" and
   "why it was proposed".

7. **Soundtrack and voice** (your words): "Use this soundtrack and my custom made voice called
   Manila", then "Sorry Malina".
   - Soundtrack: your file "Tension and Gravity" (6 minutes 0 seconds). Your original upload is left
     untouched; the project works on a copy in `soundtrack/` (chapter 1's original working folder; not in
     this repository).
   - Voice: your ElevenLabs voice "Malina" (voice id JNDHNvYV2jhVoAQjIjY6), model eleven_v4.
   - This replaces the music the skill would have composed and the voice auditions.

8. **Tone** (your words): "The script needs to be more conversational. It's way too formal and
   like I'm listening to a lecture. It needs to be a little less formal and a little more urgent
   like Naomi Klein." You also supplied your "Steven Pinker Teaching and Writing Toolkit"; the
   rewrite follows it. (Kept in `downloads/pinker-toolkit/` in chapter 1's original working folder, not in this
   repository; read as guidance, never changed.)

9. **Inflation needs its own explanation** (your words): "Yeah that will need explaining in the
   next video. Because it quite evidently makes no sense that money minting = Inflation. It depends
   on where and how the money is spent."

### Claude's calls (overturn any in one line)

- Chapter 2 becomes "what really causes inflation", straight after chapter 1, because chapter 1
  ends by saying a country can't run out of its own money and the viewer's next question is
  "won't that cause inflation?". Chapter 1's last line will point to it instead of to Britain and
  Italy, which move to chapter 3.
- The inflation chapter shows the honest edge too: creating money can push prices up when the
  spending chases things the economy can't make more of. Where and how it is spent is the hinge.

- Malina's recordings use delivery cues in square brackets ([conversational], [urgent] and so on)
  and Mattei is written in phonetic symbols so she says it the Italian way (mat-TEH-ee).
- The script sounds like Naomi Klein in spirit only (urgency, direct questions, stakes up front);
  none of her wording or coined phrases is used.

- Music level: about 18 dB under Malina while she speaks and about 12 dB under in the pauses,
  with the speech frequencies of the music softened a little. Measured, not guessed (see
  `tools/mix_voice_over_music.sh`).
- The soundtrack plays from its beginning and fades out over the last 4 seconds of the chapter.
- Whole-mix loudness: about -15 LUFS (a common level for phone video), peaks kept under clipping.

- The author's name is spelled Clara E. Mattei in the film (the book's spelling).
- The money view is never named. When the film needs to point to it, it says "economists who study
  how modern money works".
- Interpretations that are Mattei's own (austerity's real purpose, "the capital order") are said as
  hers ("Mattei argues", "Mattei calls it"), not as plain fact.
- No drawn portraits of real people. Real people appear as typed name cards. Reason: drawn
  likenesses of real people are easy to get wrong and can mislead.
- Each chapter is built as its own short film, then the chapters are joined into the full film.

10. **Go-ahead for chapter 1** (your words): "Do it." (to recording the rest of chapter 1 in Malina,
    estimated 3,000 credits, and drawing the other nine pages).

### Claude's calls for chapter 1 (overturn any in one line)

- Each page's narration was recorded on its own, so a page can be re-recorded without touching the
  others. Pages are separated by short pauses (1.1 to 1.7 seconds) for the page turn.
- Every page is turned to the same voice loudness (-16 LUFS) by a plain volume change, not by a
  compressor, so Malina's delivery is left as she recorded it.
- A new page is laid over the last one: it slides in from the right, its shadow falling on the page
  underneath. Every page keeps the same header strip (§1 WHERE IT CAME FROM) and a page number.
- Everything on a page appears on the word it belongs to; where nothing new is drawn while Malina
  speaks, the page rests (never longer than 1.7 seconds, except 2.5 seconds on the end card).
- Captions come as a separate file (.srt) instead of being burned into the picture, because phone
  apps put their own captions and buttons over the bottom of the screen; the words drawn on the
  pages already carry the key points. Most apps accept the file when you upload.
- The video opens on page 1 as it starts, not on a flash of a finished page. A finished page 5 is
  delivered as a separate cover picture for apps that let you choose one.
- Words on the pages are short forms of what Malina says, never more: BUDGET SPEECH, BORN AFTER
  1918, SHORT OF: MONEY / SHELLS, IGNORED, TAX PURCHASES, NOT WEALTH, ANY JOB / ANY WAGE.
- New engravings, same rules as the temple (one lamp, upper left): five 1915 field-gun shells, an
  Italian factory with a saw-tooth roof (a red flag goes up on it at "take over their factories"),
  and three gold bars (the red pen draws a padlock on them at "a limit they chose").

11. **Fix the voice** (your words): "This is great. But the audio randomly switches accents in the
    beginning of the video. And there's random shouting." and "I have an idea. There's a feature in
    eleven labs where you can add accent rules. Maybe research standard New Zealand phonemes, write
    them into the voices accent rules, regenerate audio, and avoid the shouting this time."

### Claude's calls for the voice fix (overturn any in one line)

- No voice-level "accent rules" turned up in ElevenLabs' documentation or in the connection this
  project uses. Instead, every page opens with one accent instruction, "[in a warm, steady New
  Zealand accent]", and has no other delivery cues. The New Zealand sounds are researched and kept
  as a listening guide (`research/09 Research - New Zealand accent.md`).
- No capital letters for emphasis anywhere in the narration (they make the voice push).
- Mattei is said in English sounds, "muh-TAY-ee", instead of the Italian way; the Italian phonetic
  spelling may have pulled the accent around that word.
- Re-record pages 1 to 4 first as a test; record the rest only once you approve how they sound.

12. **Voice accepted for now, louder music, a new look** (your words): "This is incredible. But it
    sounds a bit Australian. It'll do for now. Can up the music slightly. And for the video, use the
    fal plugin to generate a video in the style of 2d animation, stylized to accent discontent and
    conflict. Maybe a simplistic colour pallet but not simplistic drawn style. Could you maybe
    generate 5 different styles and I'll choose"

### Claude's calls for item 12 (overturn any in one line)

- Pages 5 to 10 recorded the same way as the approved test (one accent instruction, no other cues).
- Music raised 3 dB (from 14 dB down to 11 dB down before ducking). Measured result: about 18 dB
  under Malina while she speaks (was about 21), and about 2 dB louder in the pauses.
- The five samples all show the same scene (the Glasgow strike, 1919) so only the look changes:
  revolutionary poster, charcoal lithograph, linocut print, painted gouache, graphic-novel night.
  Made with fal's MiniMax video model (6 seconds each, tall, 768 x 1344), about 90 US cents in all.
  Their own sound is removed; the film keeps Malina and your soundtrack.
- In the real film, words and numbers on screen would be added by my own drawing code on top of the
  animation, because video models cannot be trusted to spell or count.
- In the real film, the Glasgow scene follows the research (troops and tanks arrive after the clash;
  nobody fired on the crowd), with tanks of the First World War shape, which the samples got wrong.

13. **The look: paper pop-up, not cartoon** (your words, with four reference pictures from the
    "Briefed History" channel: painted, semi-realistic stills in teal and amber):
    "I meant a style more like this. With still images with graphics like:
    - Flip into frame like a pop up book.
    - Transitions like flipping the page of a book.
    - speaking like a person is moving a fold of paper up and down in a flip book.
    - Occasional graphics like figures, objects and texts crashing onto the page to dramatize a point.
    - Just as an example: there could be civilians happy and cheering, then a tank crashes into frame, symbolising power and oppression.
    - How words appear depend on context. They should be minimal. They aren't dialogue or subtitles. They function more like hooks to emphasize the main points.
    - Words generally only appear to aid memory. They should pop into frame, and be unstylized.
    You may need to do some research on this particular style and best practices. It's important that they images are not animated like a cartoon. They should be animated like pieces of paper or cardboard being moved around on a surface without a hand. No hands!!!!"

### Claude's calls for item 13 (overturn any in one line)

- Tested on page 3 of chapter 1 (Glasgow, then the miners), timed to the new steady-accent
  narration and the louder music, before touching the rest of the chapter.
- Pictures: painted with fal's Flux 3 image model in the reference's spirit (painterly, slightly
  stylised, teal-blue shadows, amber light, small touches of dull red). Backgrounds are full pages;
  figures and objects are separate cut-outs. About 82 US cents for the eight pictures and cut-outs.
- Pieces keep a narrow off-white paper margin, so they read as cut paper. One lamp from the upper
  left gives every piece a soft shadow on the page behind it.
- Pop-ups fold up from their bottom edge with a quick settle. Pages turn by peeling from the bottom-
  right corner, showing the plain back of the page; pieces fold down flat before a page turns.
- The speaking figure's jaw is a separate paper piece that slides down and up with the loudness of
  Malina's voice (a cut-out puppet mouth), showing a dark mouth behind it.
- The tank "crashes" as your example says: it drops from above on the word "tanks", lands hard, the
  camera shakes, dust bursts out and the crowd jolts. It is shown as a symbol; the research still
  says troops and tanks came after the clash, and the narration does not claim otherwise.
- Words: plain heavy typeface (Inter), off-white, no outline or effect; they fold up like the other
  pieces. Page 3 uses 8 MILLION, 60,000, PUBLIC OWNERSHIP and IGNORED. The report's cover label
  (ROYAL COMMISSION) is part of the object, not a word hook.
- No real people are drawn: the miner, crowds and soldiers are invented figures.
- This look replaces the scrapbook look and the five animated samples (log 10) if you approve it.

14. **Paper pop-up look approved** (your words, after watching the page 3 test): "This is great!"
    The scrapbook look (log 08) and the five animated samples (log 10) are set aside. Next: all ten
    pages of chapter 1 in this look, planned in `scripts-and-plans/12 Plan - chapter 1 in paper pop-up.md`; the
    painting cost is confirmed with you before any is spent.

15. **Go-ahead for the whole chapter in the paper look** (your words): "Do it!" (to painting about
    70 pictures for about US$5, up to US$8, and making and filming all ten pages).

### Claude's calls for item 15 (overturn any in one line)

- 47 pictures were painted (45 used), not 70: one painting can serve several pages (the shell factory, the
  politician, the pay packet, the price tag and the gold bars each come back), and words, cards,
  signs, posters and the page 7 boards are drawn by code instead of painted. Spent about US$2.55.
- Two paintings were thrown away: shells that looked like rifle cartridges (re-painted as artillery
  shells with copper bands, and cut into seven separate shells) and a new tank with an odd shape
  (page 3 keeps the approved tank).
- The map of Italy is printed on a small paper card instead of cut round its coast, so Sardinia and
  Sicily stay on it.
- Mattei's book appears as a plain red book with only its title and her name printed on it (it is not
  a copy of the real cover). A copy with no title is the government's account book on page 10.
- Page 1: the politician mouths the speech while Malina quotes it ("Times are tough ... hold wages
  down"); the iron weight lands on the pay packet and squashes it; a single artillery shell drops in
  on "First World War"; STOP WHAT? closes the page.
- Page 2: the stamp also crashes down on "takes charge" (before the factory, price tag and pay packet
  appear) and on Italy on "does the same". The shells come back on "organised for war" and give way to
  food, homes and a school on "what people need".
- Page 4: the strikers march off toward the factory and fold away as they go, then the red flag
  rises behind the roof.
- Page 6: the five advice cards are two-line printed cards of the same size, each knocking the last
  one flat; the place names are BRUSSELS 1920 and GENOA 1922 as two-line words.
- Page 7: the three parts are three dark boards, one above the other, each with its word. The pay
  packet "shrinks" by being swapped for a smaller one (a cut-out swap, not a stretch); TAX is printed
  on the tag; the factory smokes until "slow down".
- Page 8: the gold is lifted and slammed down on the pay packet and the price tag, which fold away
  under it. The kitchen sheet turns over to the shell factory on "It can run out of workers".
- Page 9: WORK MORE and CONSUME LESS are two posters slapped onto the wall one after the other, each
  on its own words.
- Page 10: the politician's jaw flaps three times silently after "Sound familiar?", as if he is
  starting the speech again. The price tag grows by being swapped for bigger ones. On "That's next."
  the politician folds away and the page corner lifts; about two seconds later the page turns over to
  a plain dark page, where the film ends as the music fades.
- Each page is filmed as its own chunk and the chunks are joined, so one page can be re-filmed alone.

16. **A reusable kit for a new series** (your words): "This is fantastic. Could you put at the assets
    and reusable scripts into a zip folder with clear instructions on how to use them in the future.
    I'm going to get another agent to start another series on the enclosures"

### Claude's calls for item 16 (overturn any in one line)

- The kit comes as three zip files, not one, because a file sent here can't be bigger than 30 MB:
  part 1 tools, instructions, the example chapter (words, recordings, timings, masks) and the
  soundtrack; part 2 the background paintings; part 3 the figure and object paintings. Unzipped
  together they make one folder.
- The paintings are high-quality JPEG copies (a quarter of the size, no visible difference); the PNG
  originals stay in this project. The paper pieces are not packed: the kit rebuilds them from the
  paintings in about 2 minutes, so they always match the cut list.
- The tools were made general for any series: the page turns, camera and filming work from any list
  of page files; the film script finds the page edges itself; the browser and label font are found on
  any computer; the narration tools take their pauses and folders as settings. Austerity chapter 1 is
  inside as the worked example, plus a template for a new chapter.
- The instructions are written for the other agent (the full path from script to finished film, with
  commands, settings, times and costs), with a plain-words start page for you, the look in your own
  words, the exact painting prompts, the lessons learned, and your rules for running a project.
- The two paintings that failed their checks (202 and 208) are left out of the kit.

17. **A one-page picture with origami props** (your words): "Can I get you to create one page
    graphics. Could you try a blank page on and angle with the props like origami. And maybe some mood
    lighting to cast a shadow. Just one page"

### Claude's calls for item 17 (overturn any in one line)

- Built in the paper stage (no paintings, no cost), so the props could move later: real folded shapes
  with flat faces, not painted cut-outs.
- Props: a cottage, three trees, a paper crane and a zig-zag fence, a countryside set that would also
  suit the enclosures series. Colours kept to cream, brick red, sage green and ochre.
- Lighting: one low warm lamp from the front left making a pool of light on the page and long
  shadows, a faint cool light from behind, the desk falling into darkness.
- The page is A4-shaped, turned at an angle on a dark wooden desk, with its bottom-right corner
  curling up a little.

18. **The one-page picture as an open pop-up book** (your words): "Yeah like that. But it's not
    aesthetically beautiful. Maybe like an open book, rotated slightly along the X axis so it looks
    like some sitting at a desk reading an actual book. But without the desk. That way, the origami
    still functions like pop ups. But this time, the pop ups have a lot of intricate details so the
    shading sells the drama. I'm going to have to defer to your aesthetic dicipline over mine."

### Claude's calls for item 18 (overturn any in one line)

- Every pop-up piece is cut from one ivory paper, as fine paper artists do, so light and shadow alone
  make the picture; colour only in the light (warm lamp, cool moon, glowing windows) and the book's
  deep red cloth cover.
- A night scene: a warm reading lamp from the front left, cool moonlight from behind, and a warm light
  inside the cottage glowing out through its cut windows and open door.
- The scene, back to front: three layers of hills with hedged fields and a church, a paper moon with
  hanging stars, three cypresses, a great oak in three lacy layers, the cottage (scalloped shingles,
  mullioned windows, a chimney with a smoke curl), a picket fence with a gate and roses, three sheep,
  and a strip of grass and daisies. Countryside again, so it can lead into the enclosures series.
- The ground is printed on the page (a pond, garden rows, tiny flowers, a stepping-stone path) and the
  bottom of each page carries a few lines of small type and a page number, so it reads as a real book.
- Finished like a photograph of a real model: a gentle glow round the lit windows, very slight lens
  blur on the nearest and farthest parts, soft dark corners and fine grain.

## 2026-10-12

19. **Chapter 2, on inflation: outlines first** (your words): "All subagents on medium effort.  No
    higher than medium." and "Could you generate part two on inflation. Explain inflation within the
    context of the first video. But propose about three different video outlines before getting
    started generating." and "You may use upto $10 in Fal to generate images and use eleven labs only
    for speech." and "So, start with the outlines."

### Claude's calls for item 19 (overturn any in one line)

- Before any outline, the facts were researched into a new ledger for chapter 2 (ids C2-H history,
  C2-C cases, C2-N New Zealand now, C2-M how inflation works), so no outline rests on a fact that
  later turns out wrong. Nothing was spent: research and outlines cost no fal or ElevenLabs credits.
- Three outlines, each from a different angle: back to the shell factory (how it works, shown with
  chapter 1's own factory); what happened next (the story from 1919 to New Zealand today); and four
  price tags (real cases, each with a verdict). Each was drafted, then checked against the facts, your
  rules and chapter 1, and revised.
- Every helper ran at medium effort, as you asked.
- Fal is for paintings and cut-outs only, within US$10; ElevenLabs only for Malina's speech (and its
  free transcripts, which give the time of every word).

20. **Chapter 2: outline A, made cinematic** (your words): "Definitely A. But I want you to elevate the
    visuals. Mix 2d with 3d with compelling animation and motion graphics. I'll leave the aesthetic
    choices to you. It has to be cinematic, yet still carry the informational quality."

### Claude's calls for item 20 (overturn any in one line)

- The script was written from outline A and checked by four fact checkers and one rules reader
  before recording; their fixes were made (dates and starting points, "close to the second
  factory", Mattei's view said as hers, the review's wording, numbers as said aloud).
- Malina was recorded once per page (one take each, no retakes), with the same accent instruction as
  chapter 1. Steadiness was checked by measurement, not by ear: pitch spread across pages 2.2
  semitones (chapter 1: 3.0), no word much louder than the rest. Mixed at -15 LUFS over "Tension and
  Gravity".
- The look: a "cinema stage" instead of chapter 1's flat paper pages. Each page is a real 3D scene:
  - Painted rooms with depth: each painting is given a distance picture (made by fal) and pushed back
    into 3D, so the camera can move a little inside it and near things shift against far ones.
  - Card models built in code (factories, houses, shells, coins, banknotes, price tags, flip
    counters, dials, oil barrel, paper boats) and chapter 1-style paper cut-outs standing in the rooms.
  - A camera that moves like a film camera: slow pushes and cranes, focus that falls off with
    distance, a little handheld drift, small shakes when something heavy lands.
  - Light: one warm lamp with soft shadows, beams through windows, drifting dust, smoke, a glow
    round bright things, and a film finish (teal shadows, warm highlights, grain, soft dark corners).
  - Documentary graphics on top (2D): place-and-year titles, big counting figures, labels with lines
    pointing at things, bars and line charts that draw themselves. Every word is a short form of
    what Malina says at that moment.
  - Pages hand over with a page peel, so it still feels like the same book as chapter 1.
- The centre of the chapter, the two factories, is built as a model set on a table in front of a
  painted skyline, used again on page 8.
- Fal was used for 11 new paintings (1k and 2k), distance pictures and cut-out masks only; about
  US$1.06 so far of the US$10 allowed.
- Eight page helpers built pages 1 and 4 to 10 in parallel from a written guide and the two finished
  pages (2 and 3), all at medium effort; I then checked every page's pictures myself.

21. **Check the facts again** (your words): "Oh and do the research to ensure your facts are correct"

### Claude's calls for item 21 (overturn any in one line)

- Seven independent checkers each tried to prove one group of claims wrong from fresh, mostly primary
  sources, including every number planned for the screen; a final reviewer settled disagreements and
  looked for claims no group covered. Nothing was wrong; nothing was re-recorded.
- Changed on screen: UP TO +25% (Glasgow), LOWEST ON RECORD with "Records began in 1986" (2021
  unemployment), the last of the hundred dots nearly empty (1915 was 0.95%). Kept: ×4 for oil
  ($2.90 to $11.65 is 4.02 times) and "about ½% a year" for Japan (the Bank of Japan's own figure).
- Left for you to watch: page 10 says the Reserve Bank "is raising" its rate; its next decision is
  28 October. New figures come out on 22 October (prices) and 4 November (unemployment).

22. **Independent critique** (your words): "You need to use subagents to double check your work and
    critique it."

### Claude's calls for item 22

- Seven critics and a skeptic before filming finished; filming was stopped and restarted after the
  fixes, rather than patching a half-filmed chapter.
- After the fixes, a second independent check confirmed each fix and caught four new problems the
  fixes had caused; those were fixed too.
- The politician's blue tie was recoloured charcoal (the critics read it as a possible party colour
  in an election period); the original picture is kept.
- The top-hatted "owners" caricature was removed (it added a claim the narration does not make); the
  gains are shown as coins pouring onto the taller tower of notes.

23. **A plugin** (your words): "I'm sorry to keep bothering you. But save your workflow and Dev a plugin
    when you're done. You may need to save your generic scripts as you go so that other smaller models
    can use the plugin."

### Claude's calls for item 23

- Named "explainer-film", kept in your repository (`plugins/explainer-film`) with a catalogue file at
  the root, so it installs with two commands. It holds instructions, workflows, helper definitions,
  the film engine and tools, and the two chapters as worked examples, but not your paintings,
  recordings or music (those stay in the project).
- Written step by step, with exact commands, costs and traps, so a smaller model can follow it.

24. **The house** (your words): "Just one critique, that 3d house is sparse in detail. It doesn't stand
    out as visually complete." and "Oh I saw that. Those shots look amazing. Thank you!"

### Claude's calls for item 24

- Rebuilt as a detailed New Zealand card villa with a small garden; reviewed by two critics before use.
- On the model table its price tag climbs in arrows (↑ to ↑↑↑) rather than pounds, so no currency is
  shown before the film reaches New Zealand; in the street it climbs in dollars.

25. **Round 20: the phone screenshots** (your words, with seven screenshots): "I love the fact theirs
    depth in these. Just a few issues. Picture number:
    1. His face is weirdly over saturated compared to other faces and pop ups.
    2 and 3. The price tags clip other objects and the bread basket clips the conveyor belt.
    4. These are great 3d perspectives but there is a sudden drop in visual quality. Keep the 3d, but
    you probably need to do some research on how to fill the frame. Also the model needs to be
    significantly higher quality. Blender has an official MCP to use for this. There are others as
    well. Take a look.
    5. The envelope clips the workers and the ground. Also the book probably needs to be significantly
    bigger because it's being treated as authority. Zooming out should fix the clipping issue and
    placing the book further back should leave space for the workers and envelope.
    6. The coins disappear through the ground and the both the notes and coins have no reflection.
    Maybe the source image shouldn't depict a wet ground.
    7. There's no detail again. It looks plain and boring.
    Maybe the blender MCP can help you with either fixing some of these issues or help you redesign
    how the visuals are created and arranged.
    The camera also sometimes moves around too much. It needs to stay still unless it's essential to
    land an important point. Then movement makes sense. Zoom out to make room, zoom in to narrow
    perspective or transition to the next frame when a particular object become the main focus, pan
    left or right to shift perspective, pan up to signal ideals, pan down to signal pressure. Move up
    to see the bigger picture, move down expose the minor details.
    3 movements per frame, max. If you need more, make more frames."

### Claude's calls for item 25

- **The camera rule is now part of the engine**: a "still shot" holds still and allows only the
  moves you named (zoom in or out, pan left, right, up or down, move up or down), at most 3 per shot;
  a fourth stops the page from loading. A checker measures every shot of the film. "Frame" was taken
  to mean a shot (from one cut to the next); where a page needed more moves it was cut into more shots.
- **Blender, without its MCP server**: Blender Lab's official MCP server and the community ones mostly
  pass Python instructions to a running Blender. Here Blender runs headless as a Python module, so the
  instructions go to it directly, with the same result and no extra pieces. Blender builds the
  models; the existing stage still films them (Blender's own renderer would need 80 to 200 hours on
  this machine).
- **New models**: two detailed munitions works, a model industrial town around them, a reviewer's
  desk, and foreground props. All are built by script, so a smaller model can change or reuse them.
- **The wet street was repainted dry** (about 10 US cents of the US$10 picture allowance), as you
  suggested, rather than faking reflections.
- **Seven page helpers, then reviewers, at medium effort**, as you set earlier.

26. **Use the Blender MCP as well** (your words): "Oh use blender MCP as well
    It'll teach you how to use it to get food detailed results"

### Claude's calls for item 26

- This replaces item 25's call "Blender, without its MCP server": the official server is now used.
- Installed Blender 5.2.2 (the full program, checksum checked) with Blender Lab's official MCP server
  and its add-on, running without a screen on this machine, and registered it with Claude Code for
  later sessions. In this session its tools are called through a small command-line client that
  speaks to the real server.
- Its guidance and its bundled manual and Python reference were turned into modelling notes; then
  one helper per model (the works, the town, the desk, the props) inspected each model through the
  server, rendered thumbnails, improved the model and checked it in the film's stage; a reviewer
  compared before and after, and any model that got worse keeps its old version.

27. **Chapter 2, round 20, accepted; push everything** (your words): "That's fantastic. Not perfect,
    but good enough. Can you push all assets and scripts to repo."

### Claude's calls for item 27

- The whole film kit went into the repository as one folder, `austerity-explainer/film-kit/`, in the
  same layout as the working kit, so it can be used straight from a clone: every painting of both
  chapters, the paper pieces already made, painted rooms, Blender models and their scripts, the
  stage, page files, tools, examples and chapter 1's page recordings. Files the repository already
  had are stored once by git, so the copy adds only what was new (about 115 MB).
- The repository is public, so the soundtrack "Tension and Gravity.mp3" was left out (a note in
  `film-kit/assets/soundtrack/` says where it goes); the finished films and chapter 2's mix already
  carry it under the voice.
- The full-quality films (about 800 MB each) were left out: GitHub refuses files over 100 MB, and
  storing them another way could cost money. They can be filmed again from the kit.
- Chapter 2's mix and narration went in as lossless .flac files (about half the size of .wav).
- Chapter 2's working files from this session (session scripts, fix briefs, speed tests, round-20
  working pictures, drafts, helper results, the painting service's job numbers) were held back:
  Claude Code's safety check blocked saving them twice, the second time as possible credential
  leakage. A search found no passwords or keys (only job numbers and this session's folder paths),
  but they wait for your decision rather than being forced through.
- Review screenshots (about 1.3 GB) and old video pieces were not pushed: they are checking
  by-products, not assets.

28. **WorldSculpt, then SAM 3D** (your words): "Would this help with videos?
    https://alaya-lab.github.io/WorldSculpt/" then "Hmm. Try SAM 3D in the painted style, compile a
    scene, then show me a snapshot."

### Claude's calls for item 28

- WorldSculpt was judged not usable here (graphics card, inputs, not hosted); SAM 3D on fal was tried
  instead, on page 7's petrol station.
- The background was repainted with Flux 3 edit (about 10 US cents, within the US$10 picture
  allowance) because a free paint-out smeared; only the parts inside the objects' outlines are used.
- The teal car was left painted after a checker found SAM had misplaced and miscoloured it.
- The models wear the painting projected from where it was painted, rather than SAM's own colours.
- The test stays a test: chapter 2's film is unchanged.

29. **The station and the road as 3D, light kept** (your words): "Yeah so the petrol station itself,
    the road its on need to also be 3d objects. The rest of the cars and everything else remains part
    of the background. Hmm. How would you do this because lighting is important here." then "Go"

### Claude's calls for item 29

- Plan 23, the film backdrop approach (simple shapes that wear the painting), was chosen by two judges
  from three designs.
- The painting's own light is kept exactly: no stage lamp on the background or the stand-ins; shadows
  of the car and pumps fall on a see-through ground.
- The first test left the forecourt and road painted (they didn't bend on a straight push), although
  the plan included the forecourt.
- The bollard, the queued cars and a proper repaint behind the station are left for a second test.
- The test stays a test: chapter 2's film is unchanged.

30. **Save everything but videos and audio** (your words): "That's ok. Just keep saving assets to
    repo. Everything but the videos and audio. Everything else goes to repo."

### Claude's calls for item 30

- Other people's work stays out even so (downloaded publications, Blender's manual, other authors'
  code), because the repository is public; the research ledger cites the publications.
- Installed software stays out (Blender, Python environments, downloaded tools).
- Files already in the repository aren't copied twice; big uploads go in batches under GitHub's limit.
- What the safety check stopped is left for your decision, not forced through.
- "That's ok" was not taken as a yes to spending on the second petrol station test.

31. **A design review, 3D research and plans, at maximum effort** (your words): "I need you to set two
    Opus 5.5 agents on max effort to do the following jobs' One to review the current outputs of the
    last video. Analysing aesthetic and design qualities, where things could be improved design wise,
    and propose a direction that is not only visually striking, but also narratively relevant. And
    how to fill the screen so it's balanced, doesn't feel empty and works with the story being told.
    The other one to scope the internet for free workflows or tools that can help replace the painted
    backdrop with fully 3d rendered scenes. Platforms like Tripo are viable too, but must be scoped.
    And look for VFX that might enhance the experience while remaining computationally cheap. This
    agent will need access to pictures to get an idea of what it's looking for. When those two are
    done, one more max Opus 5.5 agent to synthesize the results and put forward alternative plans"
    This overrides "no higher than medium" (item 19) for this job.

### Claude's calls for item 31

- The helpers could not spend money, sign up anywhere, or upload your pictures; they read public
  pages and ran free tests on this machine.
- The three reports are kept in `experiments/` as "26 Review", "26 Research" and "26 Plans".
- The picture allowance: US$10 from chapter 2's start, about US$1.28 spent since, so about US$8.70
  left (the helpers were told US$3 by mistake).

## Traps

- Your words in this file are quoted exactly, spelling included ("Clara Matteo", "a explainer").
  Do not tidy them.
- A decision made later overrides an earlier one only if it says so here.
