---
name: film-and-finish
description: Plan the filming time, workers, pieces and stretches from a short measured profile, film a cinema-look (or paper-look) chapter in parallel stretches, join it with the mixed sound, make a sendable copy under 28 MB, captions and a cover picture, and measure (sound gates, jump finder) that the sound lines up, loudness is right and nothing jumps. Use when the pages are checked and critiqued.
---

# Film and finish

**Example.** Chapter 2: 8,110 frames, 35 stretches of up to 240 frames, two at a time on 4
processors (about 1.4-2.4 s a frame), about 3.5 hours; then about 10 minutes of finishing.
Built-and-painted pages film at very different speeds by what the camera does (chapter 2 for
newcomers, the Works, round 4, one worker): about 0.9 s a frame while the camera holds (the set is drawn
once, only flames, smoke and flicker each frame), about 4.3 s while it slides, and more in the first
stretch of each piece while its pages load. Pages 3 to 5 (2,283 frames) took 53 minutes.

Two preflight stages bracket this skill: `explainer-film-preflight film` before filming (it needs the page
events, the page files and a critique saved as JSON that is newer than every page file, with each finding
fixed or accepted, and a passed `pages` report; it also plans the filming) and `explainer-film-preflight
finish` after finishing (`--film`, `--mix`, `--timeline`; the sound gates, the jump finder with the planned
cuts, the push check). Run each and read the whole report. The rules behind them:
the kit's `docs/LLM tips and tricks.md`, sections 14 and 15.

## 1. Film (in the background)

Tell the person the estimated filming time before starting, and never film while Blender is drawing a plate
(about 1.8 times slower).

**Plan it first, from measured costs** (`kit/calculators/plan_budget.py`; the round 4 table alone missed
round 5's filming of the same frames by half, a short profile got all three rounds within about 5%):
`plan_budget.py profile-commands EVENTS.json --scene <chapter>` prints a few short pieces to film (one
held stretch per view, each slide); film them, then `plan_budget.py measure paper-film/out/profile-*.log
--events EVENTS.json --out rates.json` and `plan_budget.py filming EVENTS.json --scene <chapter> --rates
rates.json` print the minutes, workers, piece size, lazy loading, memory and disk, and the
FILM_FROM/FILM_TO command of every stretch under 2 hours. EVENTS.json comes from
`node paper-film/tools/page_events.mjs <chapter> EVENTS.json`. Watch a run with
`plan_budget.py status paper-film/out/<chapter>-chunks` (running, stalled or stopped).

```
cd KIT && nohup setsid bash paper-film/tools/film-chapter-parallel.sh <chapter> 2 240 > paper-film/out/<chapter>-filming.stdout 2>&1 < /dev/null &
```
- Progress: `paper-film/out/<chapter>-filming.log` (one line per finished stretch). Wait with a
  background command that loops until the log says `joined:` or `chunks missing` OR the filming
  script is no longer running (`pgrep -f film-chapter-parallel.sh`): a cloud machine can restart and
  silently end background jobs (chapter 2 lost 90 minutes that way). Check the log's last time too.
- Check the FIRST finished stretch at once (pull frames with
  `ffmpeg -ss SECONDS -i paper-film/out/<chapter>-chunks/chunk-00000-to-00205.mp4 -frames:v 1 f.jpg`)
  so a problem does not waste hours.
- On a 2-processor machine use 1 worker (2 is no faster); on 4, use 2; 3 is not worth it.
- If it stops, run the same command again: finished stretches are kept. To re-film a page after a
  fix, delete that page's `chunk-*.mp4` files and run it again.
- Result: `paper-film/out/<chapter>-silent.mp4`.

**Long films in a cloud session:** background commands are stopped after 2 hours, and a film with
detailed models can take 5 hours (chapter 2's model pages drew at 12 to 15 seconds a picture, the
others at about 2.7). Film in stretches that each fit: `FILM_FROM=<frame> FILM_TO=<frame> bash
paper-film/tools/film-chapter-parallel.sh SCENE 2 240` (page edges in frames come from
`render-paper-film.mjs SCENE --info`); finished pieces are kept, and the last stretch joins them.
The cloud machine can also restart without warning. Each chunk is filmed in pieces of 60 frames
(`PIECE_FRAMES`), each kept when finished, so a restart or a stopped job loses at most one piece per
worker: run the same command again and it carries on. Because of that, a stretch may simply be
everything left (`FILM_FROM=<frame>` with no `FILM_TO`), run again after each stop.
Find what makes a page slow with `node paper-film/tools/profile_frame.mjs PAGE TIME` (or
`PROFILE_SCENE=SCENE node paper-film/tools/profile_frame.mjs - TIME` for a whole scene).

**Lazy chapters** (long chapters of heavy painted sets, `buildCinemaChapter({ ..., lazy: true })`): a
piece of film builds only the pages it shows, and loading one painted set takes 20 to 30 seconds and over
2 GB. Film them with bigger pieces so each loads its pages once:
`PIECE_FRAMES=240 bash paper-film/tools/film-chapter-parallel.sh <chapter> 2 240`.

## 2. Finish

```
bash narration-tools/finish_film.sh paper-film/out/<chapter>-silent.mp4 mix.wav master.mp4 "NN Chapter title.mp4" 28 examples/<chapter>/timeline.json
python3 -I narration-tools/make_captions.py examples/<chapter>/timeline.json "NN Captions - chapter title"
python3 -I paper-film/tools/make_cover.py FRAME.jpg "NN Cover - chapter title.jpg" --kicker "CHAPTER N" --title "LINE ONE|LINE TWO" --source "Source: ..."
```
(the cover frame: pull one from the film with a calm empty lower part; `make_cover.py` puts the
title there). `finish_film.sh` checks what it made with `narration-tools/sound_gates.py` and stops on a
FAIL line: each file's sound as long as the mix (within 0.05 s), the sendable copy as encoded at -15 LUFS
+/- 0.5 with a true peak of at most -1 dBTP, its size under the limit, and its sound within 2 ms of the
mix at every page's first word. Without the timeline (6th argument) it makes the files but ends with
exit 3: the alignment was not checked. Report the PASS lines' numbers to the person.

**A clip without narration** (a test of a place, a sample for the person): lay music under it with
`bash paper-film/tools/add_music_bed.sh SILENT.mp4 MUSIC OUT.mp4 [START] [LOUDNESS=-14]` (fades in and
out, -14 LUFS, peaks under -1 dB; -17.7 was found faint on a phone speaker, log 32). The music file is
only read; never put it into a repository. Choose START by measurement, since nobody can listen here:
`python3 -I narration-tools/sound_gates.py music-start MUSIC --seconds CLIP_SECONDS --mood quiet`. The
script then checks the clip's length, loudness and true peak, and stops on a FAIL line.

## 3. Measure and look (report the numbers)

- Frames and length: `ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,duration -of csv=p=0 FILM.mp4`
- Loudness and true peak: `python3 -I narration-tools/sound_gates.py loudness FILM.mp4` (finish_film.sh
  runs it; -15 LUFS +/- 0.5, true peak at most -1 dBTP; `--music-only` for -14).
- Sound alignment: finish_film.sh's alignment line should say 0.00 ms (at most 2) at every page.
- Sudden jumps between frames (a painting switching over, a prop popping, a flash):
  `python3 -I paper-film/tools/find_jumps.py FILM.mp4 SHEET.jpg 4 CUT_SECONDS ...` lists every frame
  whose change is far bigger than its neighbours', and reports the times you name as planned cuts
  (page turns, time cuts) as planned; it also makes a sheet of two frames a second to look at the motion.
  Don't type the cut times by hand: `python3 calculators/plan_page_timing.py check EVENTS.json` prints the
  planned cuts and the whole `find_jumps.py` command (`--film-start S` for a filmed piece that starts later
  in the chapter). Any jump that is not a planned cut is a must-fix.
- Before pushing or sending files: `python3 calculators/plan_budget.py push PATHS` refuses audio and video
  (none goes in the repository), a file over 90 MB (GitHub refuses 100 MB) and anything that looks like a
  key, and packs the rest into pushes and chat-sized parts. It also fails on an email-like string in a script that
  makes web requests, and on a dollar sign eaten by the shell ("bin/bash", or "US/" and a digit, in a money file:
  US$0.048 once became US/bin/bash.048). Write files with prices through the file-writing tool or a quoted
  here-document (`<<'EOF'`), never with `echo`.
- Contact sheet of the finished film at one frame every 2 seconds:
  `mkdir -p sheet && ffmpeg -i FILM.mp4 -vf fps=0.5 sheet/frame-%03d.jpg` then
  `python3 -I paper-film/tools/contact_sheet.py film-sheet.jpg 10 sheet/frame-*.jpg` and look at it
  (frame-001 is 0 s, frame-002 is 2 s, and so on).
- Size of the sendable copy (under 30 MB for sending in a chat).

- **A fresh helper judges the clip in motion** (skill `check-and-critique`, section 5): stills cannot show a shadow
  that fades in when the move starts, a floating barrel, a one-frame colour change or a pale outline that appears only
  once the camera moves. It writes the clip critique, and `explainer-film-preflight finish --clip-critique FILE` needs it
  (newer than the film, every "must fix" finding fixed or accepted).
- **Banding in a dark sky.** A big dark plain sky can show faint contour steps (banding) when its contrast is raised 3
  to 10 times, as in any 8-bit video (seen on the wet lockout clip). Do not promise it is absent, and do not film again
  to chase it unless a viewer would see it at normal contrast.

Tell the person what was measured and what was not (nobody watched it at full speed; how it plays on
a phone).
