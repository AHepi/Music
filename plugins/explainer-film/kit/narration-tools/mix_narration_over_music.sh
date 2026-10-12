#!/usr/bin/env bash
# What this does: lays a whole chapter's narration track over the soundtrack, the same way as the
# sound checks (tools/mix_voice_over_music.sh), except the narration arrives already levelled
# (tools/assemble_chapter_narration.py turns every page to -16 LUFS), so it is not re-levelled here.
#   - the soundtrack plays from its start, 11 dB down (was 14 until you asked for it slightly louder),
#     with the speech frequencies softened a little;
#   - it dips under Malina's voice automatically (about 18 dB under while she speaks, about 12 in pauses);
#   - fades in over 0.8 s, out over the last 4 s;
#   - the whole mix is set to -15 LUFS, with a limiter keeping peaks under clipping (its own 5 ms
#     look-ahead delay cancelled, so the sound stays exactly on the pictures' timing).
# Writes a WAV master (for joining to the pictures) and an MP3 (for listening).
# Use: mix_chapter_narration_over_music.sh MUSIC_FILE NARRATION_WAV OUTPUT_WAV OUTPUT_MP3
set -euo pipefail
music_file="$1"; narration_file="$2"; output_wav="$3"; output_mp3="$4"

length_seconds=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$narration_file")
fade_start=$(python3 -c "print(max(0.0, float('$length_seconds') - 4.0))")
target_loudness="-15"; music_level_db="-11"; duck_threshold="0.08"; duck_ratio="2.5"

work_folder=$(mktemp -d); trap 'rm -rf "$work_folder"' EXIT
unlevelled_mix="$work_folder/unlevelled_mix.wav"

ffmpeg -hide_banner -loglevel error -y -t "$length_seconds" -i "$music_file" -i "$narration_file" -filter_complex "
[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur=${length_seconds}[voice];
[voice]asplit=2[voice_key][voice_for_mix];
[0:a]aresample=48000,asetpts=PTS-STARTPTS,volume=${music_level_db}dB,equalizer=f=2500:t=q:w=1.2:g=-4,apad=whole_dur=${length_seconds}[music];
[music][voice_key]sidechaincompress=threshold=${duck_threshold}:ratio=${duck_ratio}:attack=30:release=1100:makeup=1[music_ducked];
[music_ducked][voice_for_mix]amix=inputs=2:duration=first:normalize=0,afade=t=in:st=0:d=0.8,afade=t=out:st=${fade_start}:d=4[out]" \
  -map "[out]" -c:a pcm_f32le "$unlevelled_mix"

measured_loudness=$(ffmpeg -hide_banner -nostats -i "$unlevelled_mix" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
gain_db=$(python3 -c "print(round(float('$target_loudness') - float('$measured_loudness'), 2))")
ffmpeg -hide_banner -loglevel error -y -i "$unlevelled_mix" -af "volume=${gain_db}dB,alimiter=limit=0.84:attack=5:release=60:level=disabled:latency=1" -ar 48000 -c:a pcm_s24le "$output_wav"
ffmpeg -hide_banner -loglevel error -y -i "$output_wav" -c:a libmp3lame -b:a 192k "$output_mp3"
echo "mix measured ${measured_loudness} LUFS, turned by ${gain_db} dB toward ${target_loudness} LUFS -> $output_wav and $output_mp3"
