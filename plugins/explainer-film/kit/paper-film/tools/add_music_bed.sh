#!/bin/bash
# What this does: lays a stretch of music under a silent film (a clip with no narration): it takes the
# music from START seconds for as long as the film runs, fades it in over FADE_IN seconds and out over the
# film's last FADE_OUT seconds, sets its loudness to LOUDNESS (LUFS, the loudness measure phones and video
# sites use; -14 is usual for phone video, and log 32's helper found -17.7 faint on a phone speaker), and
# writes the film with that sound (peaks kept under -1 dB). The music file is only read: it
# never goes into the repository.
# Gates (narration-tools/sound_gates.py): the clip's sound must be as long as the film (within 0.05 s) and, as encoded,
# within 0.5 of LOUDNESS with a true peak of at most -1 dBTP; the script stops with a FAIL line otherwise.
# To choose START by measurement (nobody can listen here): python3 -I narration-tools/sound_gates.py music-start MUSIC --seconds N
#
# Use: bash add_music_bed.sh SILENT_FILM.mp4 MUSIC_FILE OUT.mp4 [START=0] [LOUDNESS=-14] [FADE_IN=0.8] [FADE_OUT=1.5]
set -eu
film="$1"; music="$2"; out="$3"
start="${4:-0}"; loudness="${5:--14}"; fade_in="${6:-0.8}"; fade_out="${7:-1.5}"
length=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$film")
fade_at=$(python3 -c "print(max(0.0, $length - $fade_out))")
ffmpeg -y -hide_banner -loglevel error -i "$film" -ss "$start" -t "$length" -i "$music" \
  -filter_complex "[1:a]afade=t=in:st=0:d=$fade_in,afade=t=out:st=$fade_at:d=$fade_out,loudnorm=I=$loudness:TP=-1:LRA=11,aresample=48000[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest "$out"
echo "wrote $out ($length s, music from $start s)"
gates="$(dirname "$0")/../../narration-tools/sound_gates.py"
python3 -I "$gates" length "$out" --expected "$length" --stream audio --step "the music bed"
python3 -I "$gates" loudness "$out" --music-only --target "$loudness"
