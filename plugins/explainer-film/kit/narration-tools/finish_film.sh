#!/bin/bash
# What this does: turns a silent paper film into the finished film files.
#   1. the master: the silent pictures joined with the chapter mix (narration over music), pictures
#      copied untouched, sound at high quality. Keep it for uploading anywhere that takes big files.
#   2. the sendable copy: the same film squeezed to fit a size limit (28 MB unless you say otherwise;
#      the limit for sending files in a Claude chat is 30 MB), in two passes so the bits go where the
#      picture is busiest, with ordinary H.264 video and AAC sound so any phone or computer plays it.
# Then it checks both with narration-tools/sound_gates.py, and stops with a FAIL line when a gate fails:
#   - each file's sound is as long as the mix, within 0.05 s (lesson 5);
#   - the sendable copy, as encoded, is -15 LUFS +/- 0.5 with a true peak of at most -1 dBTP (encoding raises
#     peaks, so the encoded file is measured, not the WAV);
#   - the sendable copy is no bigger than the size limit;
#   - with the TIMELINE (6th argument), the sound lines up with the mix at every page's first word within
#     2 ms (lesson 15: the limiter's look-ahead made it 5 ms late). Without a timeline the files are made but
#     the script ends with exit 3 and says the alignment was not checked.
#
# Use: bash finish_film.sh SILENT.mp4 MIX.wav MASTER_OUT.mp4 SENDABLE_OUT.mp4 [SIZE_LIMIT_MB] [TIMELINE.json]

set -eu
SILENT="$1"; MIX="$2"; MASTER="$3"; SEND="$4"; LIMIT_MB="${5:-28}"; TIMELINE="${6:-}"
SOUND_KBPS=128
GATES="$(dirname "$0")/sound_gates.py"

ffmpeg -hide_banner -loglevel error -y -i "$SILENT" -i "$MIX" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k \
  -movflags +faststart "$MASTER"
echo "master: $MASTER"

# video rate: what is left of the size limit after the sound, with 3% kept spare for the container
SECONDS_LONG=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SILENT")
VIDEO_KBPS=$(python3 -c "print(int(($LIMIT_MB * 8000 * 0.97) / $SECONDS_LONG - $SOUND_KBPS))")
echo "squeezing to about ${LIMIT_MB} MB: video ${VIDEO_KBPS} kbps, sound ${SOUND_KBPS} kbps"

PASSLOG=$(mktemp -d)/pass
ffmpeg -hide_banner -loglevel error -y -i "$SILENT" -map 0:v -c:v libx264 -preset slow -tune film -b:v "${VIDEO_KBPS}k" \
  -pass 1 -passlogfile "$PASSLOG" -pix_fmt yuv420p -an -f null /dev/null
ffmpeg -hide_banner -loglevel error -y -i "$SILENT" -i "$MIX" -map 0:v -map 1:a -c:v libx264 -preset slow -tune film -b:v "${VIDEO_KBPS}k" \
  -pass 2 -passlogfile "$PASSLOG" -pix_fmt yuv420p -c:a aac -b:a "${SOUND_KBPS}k" -movflags +faststart "$SEND"
echo "sendable copy: $SEND ($(du -h "$SEND" | cut -f1))"

# gates
MIX_SECONDS=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MIX")
python3 -I "$GATES" length "$MASTER" --expected "$MIX_SECONDS" --stream audio --step "the master's sound"
python3 -I "$GATES" length "$SEND" --expected "$MIX_SECONDS" --stream audio --step "the sendable copy's sound"
python3 -I "$GATES" loudness "$SEND"
SIZE_OK=$(python3 -c "import os; print(1 if os.path.getsize('$SEND') <= $LIMIT_MB * 1e6 else 0)")
if [ "$SIZE_OK" != "1" ]; then echo "FAIL  the sendable copy is $(du -h "$SEND" | cut -f1), over ${LIMIT_MB} MB"; exit 1; fi
echo "PASS  the sendable copy fits ${LIMIT_MB} MB"
if [ -n "$TIMELINE" ]; then
  python3 -I "$GATES" alignment "$SEND" "$MIX" "$TIMELINE"
else
  echo "NOT CHECKED  sound alignment: give the chapter's TIMELINE as the 6th argument (lesson 15)"
  exit 3
fi
