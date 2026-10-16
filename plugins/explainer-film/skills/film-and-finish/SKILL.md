---
name: film-and-finish
description: Film a cinema-look (or paper-look) chapter in parallel stretches, join it with the mixed sound, make a sendable copy under 28 MB, captions and a cover picture, and measure that sound lines up and loudness is right. Use when the pages are checked and critiqued.
---

# Film and finish

**Example.** Chapter 2: 8,110 frames, 35 stretches of up to 240 frames, two at a time on 4
processors (about 1.4-2.4 s a frame), about 3.5 hours; then about 10 minutes of finishing.
Built-and-painted pages film at very different speeds by what the camera does (chapter 2 for
newcomers, the Works, round 4, one worker): about 0.9 s a frame while the camera holds (the set is drawn
once, only flames, smoke and flicker each frame), about 4.3 s while it slides, and more in the first
stretch of each piece while its pages load. Pages 3 to 5 (2,283 frames) took 53 minutes.

## 1. Film (in the background)

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
bash narration-tools/finish_film.sh paper-film/out/<chapter>-silent.mp4 mix.wav master.mp4 "NN Chapter title.mp4"
python3 -I narration-tools/make_captions.py examples/<chapter>/timeline.json "NN Captions - chapter title"
python3 -I narration-tools/check_sound_alignment.py "NN Chapter title.mp4" mix.wav examples/<chapter>/timeline.json
python3 -I paper-film/tools/make_cover.py FRAME.jpg "NN Cover - chapter title.jpg" --kicker "CHAPTER N" --title "LINE ONE|LINE TWO" --source "Source: ..."
```
(the cover frame: pull one from the film with a calm empty lower part; `make_cover.py` puts the
title there).

**A clip without narration** (a test of a place, a sample for the user): lay music under it with
`bash paper-film/tools/add_music_bed.sh SILENT.mp4 MUSIC OUT.mp4 [START] [LOUDNESS=-14]` (fades in and
out, -14 LUFS, peaks under -1 dB; -17.7 was found faint on a phone speaker, log 32). The music file is
only read; never put it into a repository.

## 3. Measure and look (report the numbers)

- Frames and length: `ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,duration -of csv=p=0 FILM.mp4`
- Loudness and true peak: `ffmpeg -i FILM.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12`
  (aim about -15 LUFS, true peak under -1 dB).
- Sound alignment: the check above should say 0.00 ms (or a few ms) at every page.
- Sudden jumps between frames (a painting switching over, a prop popping, a flash):
  `python3 -I paper-film/tools/find_jumps.py FILM.mp4 SHEET.jpg 4 CUT_SECONDS ...` lists every frame
  whose change is far bigger than its neighbours', and reports the times you name as planned cuts
  (page turns, time cuts) as planned; it also makes a sheet of two frames a second to look at the motion.
- Contact sheet of the finished film at one frame every 2 seconds:
  `mkdir -p sheet && ffmpeg -i FILM.mp4 -vf fps=0.5 sheet/frame-%03d.jpg` then
  `python3 -I paper-film/tools/contact_sheet.py film-sheet.jpg 10 sheet/frame-*.jpg` and look at it
  (frame-001 is 0 s, frame-002 is 2 s, and so on).
- Size of the sendable copy (under 30 MB for sending in a chat).

Tell the user what was measured and what was not (nobody watched it at full speed; how it plays on
a phone).
