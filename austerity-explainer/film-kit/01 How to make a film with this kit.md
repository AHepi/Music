# How to make a film with this kit

**What this is:** the whole path from a script to a finished tall-screen film in the paper pop-up
look, with the exact commands, settings, times and costs used for "Where austerity came from"
(the worked example in `examples/austerity-chapter-1/`). Run every command from inside the kit
folder (`austerity-explainer/film-kit/` in the repository; `paper-pop-up-film-kit/` in the old zips).

## A concrete example first

On page 3 of the example, the narrator says "union membership doubles, to eight million." The
recording of page 3 was transcribed, so the word times say she starts "doubles" 56.48 seconds into
the chapter. The page file `paper-film/scenes/austerity-chapter-1/page-3.js` asks for
`at('doubles')`, gets 56.48, and folds a second, bigger crowd up from flat 0.1 seconds before it, so
the crowd doubles as she says it. The soundtrack plays underneath, dipping while she talks. Every
picture in the film is placed the same way: by a spoken word.

## How the pieces fit (each step hands something to the next)

| Step | Tool | Takes | Hands on |
|---|---|---|---|
| 1. Script | you | research | `narration-script.json`: the exact words of each page |
| 2. Recording | ElevenLabs (voice Malina) | each page's text | `recordings/pageN.mp3` and `transcripts/pageN-words.json` |
| 3. Word times | `narration-tools/extract_word_times.py` | transcripts, script, recordings | `word-times.json` (seconds within each page) |
| 4. Timeline | `narration-tools/assemble_chapter_narration.py` | word times | `narration.wav` and `timeline.json` (seconds within the chapter) |
| 5. Mix | `narration-tools/mix_narration_over_music.sh` | narration, music | `mix.wav` (and an mp3 to listen to) |
| 6. Paintings | fal, Flux 3; `paper-film/tools/save_fal_paintings.py` | prompts from `04 Painting prompts.md` | backgrounds and cut-out subjects on plain grey, with a ledger |
| 7. Masks | fal, BiRefNet; `paper-film/tools/download_fal_masks.py` | each cut-out painting | `masks/NNN-name-mask.png` |
| 8. Paper pieces | `paper-film/tools/prepare_paper_pieces.py` | cut list, paintings, masks | `paper-film/pieces/<chapter>/` with `pieces.json` |
| 9. Mouths | `paper-film/tools/make_mouth_track.py` | narration track | how far a jaw opens on each frame |
| 10. Page files | you, from the template | timeline, pieces | `paper-film/scenes/<chapter>.js` and `<chapter>/page-N.js` |
| 11. Checks | `render-paper-film.mjs --stills`, contact sheets, `check-shadows.mjs` | the scene | single frames to look at |
| 12. Filming | `paper-film/tools/film-chapter.sh` | the scene | `paper-film/out/<chapter>-silent.mp4` |
| 13. Finishing | `narration-tools/finish_film.sh`, `make_captions.py`, `check_sound_alignment.py` | silent film, mix, timeline | the master, a copy under 28 MB, captions, measurements |

## What you need

- **Node.js 18 or newer** with npm. In `paper-film/`: `npm install` (installs three.js 0.169.0,
  playwright-core 1.48.2 and the Inter font 5.1.0, the exact versions in `package-lock.json`).
- **Chromium**, for the hidden browser that draws the frames. The tools look for it in this order:
  the `PAPER_FILM_BROWSER` setting (a path to the program), Playwright's own downloaded browser
  (`npx playwright-core install chromium` inside `paper-film/` if you have none), then the usual places
  (`/usr/bin/chromium`, Google Chrome). It runs with software graphics, so no graphics card is needed.
- **Python 3.9 or newer** with numpy, opencv (`opencv-python-headless`) and Pillow.
- **ffmpeg and ffprobe** (with libx264 and libmp3lame).
- **A bold font for words printed on objects**: DejaVu Sans Bold is looked for in the usual places;
  otherwise set `PAPER_FILM_LABEL_FONT` to any bold .ttf file.
- **Paid services** (through their connectors): ElevenLabs for the voice and transcripts, fal for
  paintings and cut-out masks. Confirm costs with the user before spending (see `06`).

## Step by step

### 1. Script

Research first; every fact needs a source before it goes into the script. Write the narration as
pages of about 10 to 30 seconds each, one idea per page, and plan what appears on which words
(see `examples/austerity-chapter-1/plan.md`). Put the exact words in a narration script file, like
`examples/new-chapter-template/narration-script.json`:
- every page's text opens with the accent instruction `[in a warm, steady New Zealand accent]` and
  has no other delivery cues (mixed mood cues made the voice jump between pages);
- no words in capitals (they make the voice push or shout); use "..." for a pause;
- a name the voice says wrongly can be written in phonetic symbols, with the plain spelling in
  `phonetic_names` (the example writes Mattei as `/məˈteɪi/`).

### 2. Recording (ElevenLabs connector)

- Voice **Malina**, voice id `JNDHNvYV2jhVoAQjIjY6`, model `eleven_v4`. Record **one page at a time**
  with `creative_generate_speech` (so one page can be re-recorded alone), on one flow.
- Poll `creative_get_flow_run_status` until done and **download each recording at once**: the links
  stop working after 2 hours. Save as `recordings/page1.mp3`, `page2.mp3` ...
- Transcribe each recording with `creative_transcribe_audio` (model `eleven_scribe_v1`, `connect_from`
  the speech node; it is free) and save its word list as `transcripts/pageN-words.json`, a file with a
  top-level `"words"` list (each entry has `text`, `type`, `start`, `end`), like the example's.
- Costs: about 1 credit per letter of script. Chapter 1 (about 520 spoken words, roughly 3,000 letters)
  used about 4,200 credits in all, counting test recordings and re-recordings.
- Listen for accent drift and shouting. Tools that help: `compare_voice_steadiness.py` (how steady the
  voice sits across pages), `find_raised_voice.py` and `find_loud_words.py` (words that jump up).

### 3. Word times

```
python3 -I narration-tools/extract_word_times.py examples/austerity-chapter-1/transcripts \
  examples/austerity-chapter-1/narration-script.json word-times.json examples/austerity-chapter-1/recordings
```
It keeps the bracketed instruction apart from the spoken words, turns phonetic names back into plain
spelling, and moves each page's first word back to where the voice really starts (ElevenLabs can
place it up to 0.3 s late). `python3 -I narration-tools/print_word_times.py word-times.json` prints
every word with its time, for planning.

### 4. Timeline and narration track

```
python3 -I narration-tools/assemble_chapter_narration.py word-times.json narration.wav timeline.json \
  --pauses 1.7,1.4,1.1,1.5,1.5,1.3,1.5,1.4,1.6
```
Pages are laid end to end with a pause between one page's last word and the next page's first
(1.4 s unless `--pauses` gives one number per gap; longer where the page turn has more to do). The
first word comes 1.08 s in; the film ends 4 s after the last word. Each page is turned to -16 LUFS
loudness by a plain volume change. The timeline is what the page files read.

### 5. Mix

The soundtrack is not stored in the repository (it is public): copy "Tension and Gravity.mp3" into
`assets/soundtrack/` first (see the note there).
```
bash narration-tools/mix_narration_over_music.sh "assets/soundtrack/Tension and Gravity.mp3" narration.wav mix.wav mix.mp3
```
The music plays from its start 11 dB down, dips under the voice (about 18 dB under while she speaks,
about 12 in pauses), fades in over 0.8 s and out over the last 4 s; the whole mix is set to -15 LUFS
with peaks held under clipping. These levels were approved by the user ("music slightly louder"
than a first try at 14 dB down).

Steps 3 to 5 on the example's files reproduce the example's timeline, narration track and mix byte
for byte (checked when the kit was made).

### 6. Paintings (fal connector)

- Model `blackforestlabs/flux-3/text-to-image`, `output_format` png. Use the style words in
  `04 Painting prompts.md` exactly, every time, so pictures from different requests match.
- **Backgrounds**: aspect `9:16`, resolution `2k` (1536 x 2736), about 10 US cents each; the scene
  with nothing standing in it and the lower quarter empty.
- **Big figures and groups**: `21:9` (3136 x 1344) or `4:5` (1824 x 2288), `2k`, about 10 cents;
  **small objects**: `1:1`, `4:5` or `3:2` at `1k`, about 2.5 cents. Always on a plain flat light grey
  background (#cfcfcf), no floor, no cast shadow, the whole subject inside the picture.
- Submit up to 8 at a time (`submit_jobs`), collect with `wait_for_jobs`, then save them with their
  prompts: list them in a small JSON file and run
  `python3 -I paper-film/tools/save_fal_paintings.py assets/paintings/<chapter> new-paintings.json`
  (it downloads each as `NNN-name.png` and records it in `paintings.json`, like the example's ledger).
  Number them as the example does: 101+ backgrounds, 201+ figures, 301+ objects.
- **Check every painting** on a contact sheet before using it: wrong-era machines, symbols, flags,
  writing, extra fingers, a subject cut off at the edge. Re-paint failures (chapter 1 re-painted shells
  that looked like rifle cartridges).

### 7. Cut-out masks (fal connector)

- Model `fal-ai/birefnet/v2` with `model: "General Use (Dynamic)"`, `operating_resolution: "2304x2304"`,
  `mask_only: true`; input `image_url` = the painting's fal address. About a fifth of a cent each.
- Save each mask as `assets/paintings/<chapter>/masks/NNN-name-mask.png`:
  `python3 -I paper-film/tools/download_fal_masks.py assets/paintings/<chapter> NNN-name=MASK_ADDRESS ...`
- Check: `python3 -I paper-film/tools/contact_sheet_masks.py assets/paintings/<chapter> masks-check.jpg`
  lays every cut-out over magenta; anything dropped shows as magenta (chapter 1 lost a lectern, half an
  island and part of a coal heap; the cut list can repair each, see step 8).

### 8. Paper pieces

Write a cut list (copy `examples/austerity-chapter-1/cut-list.json`, which uses every option), then:
```
python3 -I paper-film/tools/prepare_paper_pieces.py examples/<chapter>/cut-list.json .
```
Each piece gets a narrow off-white paper margin, its colours nudged toward the backgrounds, and is
trimmed and saved as PNG; backgrounds are copied as JPEG. Options per piece: `margin`, `grade`,
`longest_side` (2048 for big figures, about 1024 for small objects), `leave_out_boxes`,
`add_polygons` (put back what the mask missed), `mask_threshold`, `labels` (words printed on an object,
for example a book's title or TAX on a price tag), `split_shapes` (each separate shape becomes its own
piece: shell-1 ... shell-7), `map_card` (print the picture on a rounded paper card), and `jaw` (a
speaking figure: face, jaw and dark mouth layers; read the outlines off a gridded close-up). Check with
`python3 -I paper-film/tools/contact_sheet_pieces.py paper-film/pieces/<chapter> pieces-check.jpg`.

### 9. Mouths

For a figure that speaks while the narrator talks:
```
python3 -I paper-film/tools/make_mouth_track.py narration.wav START_SECONDS END_SECONDS mouth-page-N.json
```
The jaw opens on louder syllables and closes in gaps (see `page-1.js` and `page-3.js` of the example).

### 10. Page files

Copy `paper-film/scenes/new-chapter-template.js` and the folder `new-chapter-template/` under the
chapter's name, set the pieces folder and timeline in the chapter file, and write one page file per
page. Everything about page files is in `03 How a page file works.md`.

### 11. Look before filming

```
node paper-film/tools/render-paper-film.mjs <chapter> stills-folder --stills 3.3 8.6 12.5
python3 -I paper-film/tools/contact_sheet_stills.py stills-folder stills-sheet.jpg
node paper-film/tools/check-shadows.mjs <chapter> 8.6 shadows.jpg
```
A still takes about a second. Check every entrance, word, mouth and page turn at full size, and look
for pieces cut off at the frame edge and for shapes left lying flat. Chapter 1 checked about 85
moments before filming. `node paper-film/tools/render-paper-film.mjs <chapter> --info` prints the
length, frame count and page edges.

### 12. Filming

```
bash paper-film/tools/film-chapter.sh <chapter>
```
It films one page at a time (each chunk runs from the end of the previous page turn to the end of
its own) and joins them into `paper-film/out/<chapter>-silent.mp4`. About 0.6 to 0.9 seconds a frame on
a 2-processor machine: chapter 1 (6,641 frames) took about 80 minutes. To re-film one page, delete its
chunk in `paper-film/out/<chapter>-chunks/` and run the script again. Run it in the background with
its output going to a log file, and check the log now and then.

### 13. Finishing

```
bash narration-tools/finish_film.sh paper-film/out/<chapter>-silent.mp4 mix.wav master.mp4 "NN Chapter title.mp4"
python3 -I narration-tools/make_captions.py timeline.json "NN Captions - chapter title"
python3 -I narration-tools/check_sound_alignment.py "NN Chapter title.mp4" mix.wav timeline.json
ffmpeg -ss 99.6 -i master.mp4 -frames:v 1 -q:v 2 "NN Cover - chapter title.jpg"
```
The master keeps full quality (about 290 MB for 3.7 minutes); the second file is squeezed under
28 MB (the chat's sending limit is 30 MB) as H.264 and AAC so anything plays it. Then measure:
frame count (`ffprobe -count_frames`), loudness and true peak (`ffmpeg -af ebur128=peak=true`;
chapter 1: -15.1 LUFS, -1.7 dB), and sound alignment (chapter 1: 0.00 ms at every page). Captions are
one line each (at most 42 letters), timed to the words, and never split after an initial like "E.".

## Time and cost of chapter 1 (3 minutes 41 seconds, ten pages)

| Item | Amount |
|---|---|
| Recording | about 4,200 ElevenLabs credits (about 75 US cents); transcripts free |
| Paintings | 47 (17 large at about 10 US cents, 30 small at about 2.5 cents), plus 8 for the first test page |
| Masks | 37, about a fifth of a cent each |
| Total fal spend for the chapter | about US$3.40 (including the test page) |
| Writing ten page files | the longest part of the work |
| Filming | about 80 minutes of computer time, no cost |
| Finishing and checks | about 10 minutes |

## Traps

- ElevenLabs download links expire after 2 hours: download every recording as soon as it is done.
- Re-recording any page moves every time after it: redo steps 3 to 5 and film the whole chapter again.
- A word spoken twice on a page must be asked for by which time it is spoken (`at('war', 2)`), or the
  picture lands on the first one. Check every lookup against the page's words.
- Paintings drift in style between requests unless the same style words are used every time.
- Video and image models add things nobody asked for (symbols, flags, wrong-era machines): check every
  painting before use.
- Changing `paper-kit.js`, `paper-chapter.js` or the stage changes every page: film everything again.
  Changing one page file needs only that page's chunk filmed again.
- The squeezed copy is for sending; upload the master wherever big files are accepted.
