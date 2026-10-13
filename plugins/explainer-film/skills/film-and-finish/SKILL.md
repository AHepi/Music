---
name: film-and-finish
description: Film a cinema-look (or paper-look) chapter in parallel stretches, join it with the mixed sound, make a sendable copy under 28 MB, captions and a cover picture, and measure that sound lines up and loudness is right. Use when the pages are checked and critiqued.
---

# Film and finish

**Example.** Chapter 2: 8,110 frames, 35 stretches of up to 240 frames, two at a time on 4
processors (about 1.4-2.4 s a frame), about 3.5 hours; then about 10 minutes of finishing.

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
Find what makes a page slow with `node paper-film/tools/profile_frame.mjs PAGE TIME`.

## 2. Finish

```
bash narration-tools/finish_film.sh paper-film/out/<chapter>-silent.mp4 mix.wav master.mp4 "NN Chapter title.mp4"
python3 -I narration-tools/make_captions.py examples/<chapter>/timeline.json "NN Captions - chapter title"
python3 -I narration-tools/check_sound_alignment.py "NN Chapter title.mp4" mix.wav examples/<chapter>/timeline.json
python3 -I paper-film/tools/make_cover.py FRAME.jpg "NN Cover - chapter title.jpg" --kicker "CHAPTER N" --title "LINE ONE|LINE TWO" --source "Source: ..."
```
(the cover frame: pull one from the film with a calm empty lower part; `make_cover.py` puts the
title there).

## 3. Measure and look (report the numbers)

- Frames and length: `ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,duration -of csv=p=0 FILM.mp4`
- Loudness and true peak: `ffmpeg -i FILM.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12`
  (aim about -15 LUFS, true peak under -1 dB).
- Sound alignment: the check above should say 0.00 ms (or a few ms) at every page.
- Contact sheet of the finished film at one frame every 2 seconds:
  `mkdir -p sheet && ffmpeg -i FILM.mp4 -vf fps=0.5 sheet/frame-%03d.jpg` then
  `python3 -I paper-film/tools/contact_sheet.py film-sheet.jpg 10 sheet/frame-*.jpg` and look at it
  (frame-001 is 0 s, frame-002 is 2 s, and so on).
- Size of the sendable copy (under 30 MB for sending in a chat).

Tell the user what was measured and what was not (nobody watched it at full speed; how it plays on
a phone).
