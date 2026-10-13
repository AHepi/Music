#!/bin/bash
# What this does: turns a silent paper film into the finished film files.
#   1. the master: the silent pictures joined with the chapter mix (narration over music), pictures
#      copied untouched, sound at high quality. Keep it for uploading anywhere that takes big files.
#   2. the sendable copy: the same film squeezed to fit a size limit (28 MB unless you say otherwise;
#      the limit for sending files in a Claude chat is 30 MB), in two passes so the bits go where the
#      picture is busiest, with ordinary H.264 video and AAC sound so any phone or computer plays it.
#
# Use: bash finish_film.sh SILENT.mp4 MIX.wav MASTER_OUT.mp4 SENDABLE_OUT.mp4 [SIZE_LIMIT_MB]
# Then check it: python3 -I narration-tools/check_sound_alignment.py SENDABLE_OUT.mp4 MIX.wav TIMELINE.json

set -eu
SILENT="$1"; MIX="$2"; MASTER="$3"; SEND="$4"; LIMIT_MB="${5:-28}"
SOUND_KBPS=128

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
