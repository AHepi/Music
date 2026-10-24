#!/bin/bash
# What this does: turns the silent paper film of chapter 1 into the finished film files.
#   1. the master: the silent pictures joined with the chapter mix (Malina over your soundtrack),
#      pictures copied untouched, sound at high quality. Kept in the project (too big to send).
#   2. the sendable copy: the same film squeezed to fit under the 30 MB limit for sending files
#      here (two passes, so the bits go where the picture is busiest), with ordinary H.264 video
#      and AAC sound so it plays on any phone or computer.
#
# Use: bash finish_chapter_1_paper_film.sh OUTPUT_FOR_SENDING.mp4

set -eu
cd "$(dirname "$0")/.."
SILENT=paper-film/out/chapter-1-silent.mp4
MIX=mix/chapter-1-mix-steady-accent.wav
MASTER=paper-film/out/chapter-1-paper-master.mp4
SEND="$1"
VIDEO_RATE=880k     # chosen so the whole file is about 28 MB (3 min 41 s)
SOUND_RATE=128k

ffmpeg -hide_banner -loglevel error -y -i "$SILENT" -i "$MIX" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k \
  -movflags +faststart "$MASTER"
echo "master: $MASTER"

PASSLOG=$(mktemp -d)/pass
ffmpeg -hide_banner -loglevel error -y -i "$SILENT" -map 0:v -c:v libx264 -preset slow -tune film -b:v "$VIDEO_RATE" \
  -pass 1 -passlogfile "$PASSLOG" -pix_fmt yuv420p -an -f null /dev/null
ffmpeg -hide_banner -loglevel error -y -i "$SILENT" -i "$MIX" -map 0:v -map 1:a -c:v libx264 -preset slow -tune film -b:v "$VIDEO_RATE" \
  -pass 2 -passlogfile "$PASSLOG" -pix_fmt yuv420p -c:a aac -b:a "$SOUND_RATE" -movflags +faststart "$SEND"
echo "sendable copy: $SEND ($(du -h "$SEND" | cut -f1))"
