#!/usr/bin/env bash
# What this does: lays a narration recording over a music track the way the film will.
# The voice is set to a steady loudness; the music is turned down, its middle frequencies (where
# speech sits) are softened, and it dips further whenever the voice speaks ("ducking"), then
# comes back up in the pauses. The mix is faded in and out, measured, and turned up or down to a
# loudness suited to phones, with a limiter so no peak clips.
#
# The loudness step (loudnorm) silently switches audio to 192,000 samples a second; everything
# after it must be converted back to 48,000 or lengths come out wrong.
# Measured on the first sound check (2026-10-11): with these settings the music sits about 18 dB
# under the voice while she speaks and about 12 dB under in the pauses.
#
# Use: mix_voice_over_music.sh MUSIC_FILE VOICE_FILE OUTPUT_FILE VOICE_START_SECONDS LENGTH_SECONDS [MUSIC_START_SECONDS]
set -euo pipefail
music_file="$1"; voice_file="$2"; output_file="$3"; voice_start_seconds="$4"; length_seconds="$5"; music_start_seconds="${6:-0}"

voice_delay_ms=$(python3 -c "print(int(round(float('$voice_start_seconds') * 1000)))")
fade_start=$(python3 -c "print(max(0.0, float('$length_seconds') - 4.0))")
target_loudness="-15"     # whole mix, in LUFS: a common level for phone video
music_level_db="-14"      # how far the music is turned down overall
duck_threshold="0.08"     # how loud the voice must be before the music dips
duck_ratio="2.5"          # how strongly the music dips under the voice

work_folder=$(mktemp -d)
trap 'rm -rf "$work_folder"' EXIT
unlevelled_mix="$work_folder/unlevelled_mix.wav"

# 1. the mix itself, at its natural level
ffmpeg -hide_banner -loglevel error -y -ss "$music_start_seconds" -t "$length_seconds" -i "$music_file" -i "$voice_file" -filter_complex "
[1:a]pan=stereo|c0=c0|c1=c0,loudnorm=I=-16:TP=-2:LRA=11,aresample=48000,adelay=${voice_delay_ms}|${voice_delay_ms},apad=whole_dur=${length_seconds}[voice];
[voice]asplit=2[voice_key][voice_for_mix];
[0:a]aresample=48000,asetpts=PTS-STARTPTS,volume=${music_level_db}dB,equalizer=f=2500:t=q:w=1.2:g=-4,apad=whole_dur=${length_seconds}[music];
[music][voice_key]sidechaincompress=threshold=${duck_threshold}:ratio=${duck_ratio}:attack=30:release=1100:makeup=1[music_ducked];
[music_ducked][voice_for_mix]amix=inputs=2:duration=first:normalize=0,afade=t=in:st=0:d=0.8,afade=t=out:st=${fade_start}:d=4[out]" \
  -map "[out]" -c:a pcm_s24le "$unlevelled_mix"

# 2. measure it, then turn it to the target loudness with a limiter catching the peaks
measured_loudness=$(ffmpeg -hide_banner -nostats -i "$unlevelled_mix" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
gain_db=$(python3 -c "print(round(float('$target_loudness') - float('$measured_loudness'), 2))")
ffmpeg -hide_banner -loglevel error -y -i "$unlevelled_mix" -af "volume=${gain_db}dB,alimiter=limit=0.84:attack=5:release=60:level=disabled:latency=1" -ar 48000 -c:a libmp3lame -b:a 192k "$output_file"
echo "mix measured ${measured_loudness} LUFS, turned by ${gain_db} dB toward ${target_loudness} LUFS -> $output_file"
