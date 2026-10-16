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
# Gates (narration-tools/sound_gates.py; the script stops with a FAIL line naming the step):
#   - the WAV and the MP3 must be as long as the narration, within 0.05 s (lesson 5);
#   - with a TIMELINE (5th argument), the music must sit 18 dB (+/- 1) under her voice while she speaks,
#     measured over every word span on the voice-only and music-only stems of this very mix. A new
#     soundtrack fails until its level is found: sound_gates.py duck MUSIC NARRATION TIMELINE prints the
#     MUSIC_LEVEL_DB to use.
# Use: mix_narration_over_music.sh MUSIC_FILE NARRATION_WAV OUTPUT_WAV OUTPUT_MP3 [TIMELINE.json]
#   MUSIC_LEVEL_DB=-12.5  another music level (the house level is below)
#   STEMS_DIR=folder      also write the voice-only and ducked-music-only stems there (voice.wav, music.wav)
#   STEMS_ONLY=1          write only the stems (sound_gates.py duck uses this), no mix
set -euo pipefail
music_file="$1"; narration_file="$2"; output_wav="$3"; output_mp3="$4"; timeline_file="${5:-}"
gates="$(dirname "$0")/sound_gates.py"

length_seconds=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$narration_file")
fade_start=$(python3 -c "print(max(0.0, float('$length_seconds') - 4.0))")
target_loudness="-15"; music_level_db="-11"; duck_threshold="0.08"; duck_ratio="2.5"
music_level_db="${MUSIC_LEVEL_DB:-$music_level_db}"

work_folder=$(mktemp -d); trap 'rm -rf "$work_folder"' EXIT
unlevelled_mix="$work_folder/unlevelled_mix.wav"
stems_dir="${STEMS_DIR:-}"
if [ -n "$timeline_file" ] && [ -z "$stems_dir" ]; then stems_dir="$work_folder/stems"; fi

sources="
[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur=${length_seconds}[voice];
[0:a]aresample=48000,asetpts=PTS-STARTPTS,volume=${music_level_db}dB,equalizer=f=2500:t=q:w=1.2:g=-4,apad=whole_dur=${length_seconds}[music];"
# ffmpeg 6.1's sidechaincompress stops 0.36-0.44 s before its inputs end (measured on chapter 2, 16 October 2026), which
# made the whole mix that much short; the ducked music is padded back to the narration's length (inside the 4 s fade-out)
duck="sidechaincompress=threshold=${duck_threshold}:ratio=${duck_ratio}:attack=30:release=1100:makeup=1,apad=whole_dur=${length_seconds}"
together="amix=inputs=2:duration=first:normalize=0,afade=t=in:st=0:d=0.8,afade=t=out:st=${fade_start}:d=4[out]"
if [ "${STEMS_ONLY:-}" = "1" ]; then
  [ -n "$stems_dir" ] || { echo "STEMS_ONLY needs STEMS_DIR" >&2; exit 2; }
  mkdir -p "$stems_dir"
  graph="$sources [voice]asplit=2[voice_key][voice_stem]; [music][voice_key]${duck}[music_stem]"
  outputs=(-map "[voice_stem]" -c:a pcm_f32le "$stems_dir/voice.wav" -map "[music_stem]" -c:a pcm_f32le "$stems_dir/music.wav")
elif [ -n "$stems_dir" ]; then
  mkdir -p "$stems_dir"
  graph="$sources [voice]asplit=3[voice_key][voice_for_mix][voice_stem]; [music][voice_key]${duck}[music_ducked];
[music_ducked]asplit=2[music_for_mix][music_stem]; [music_for_mix][voice_for_mix]${together}"
  outputs=(-map "[out]" -c:a pcm_f32le "$unlevelled_mix" -map "[voice_stem]" -c:a pcm_f32le "$stems_dir/voice.wav" -map "[music_stem]" -c:a pcm_f32le "$stems_dir/music.wav")
else
  graph="$sources [voice]asplit=2[voice_key][voice_for_mix]; [music][voice_key]${duck}[music_ducked]; [music_ducked][voice_for_mix]${together}"
  outputs=(-map "[out]" -c:a pcm_f32le "$unlevelled_mix")
fi

ffmpeg -hide_banner -loglevel error -y -t "$length_seconds" -i "$music_file" -i "$narration_file" -filter_complex "$graph" "${outputs[@]}"
if [ "${STEMS_ONLY:-}" = "1" ]; then echo "stems at music level ${music_level_db} dB -> $stems_dir"; exit 0; fi

measured_loudness=$(ffmpeg -hide_banner -nostats -i "$unlevelled_mix" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
gain_db=$(python3 -c "print(round(float('$target_loudness') - float('$measured_loudness'), 2))")
ffmpeg -hide_banner -loglevel error -y -i "$unlevelled_mix" -af "volume=${gain_db}dB,alimiter=limit=0.84:attack=5:release=60:level=disabled:latency=1" -ar 48000 -c:a pcm_s24le "$output_wav"
ffmpeg -hide_banner -loglevel error -y -i "$output_wav" -c:a libmp3lame -b:a 192k "$output_mp3"
echo "mix measured ${measured_loudness} LUFS, turned by ${gain_db} dB toward ${target_loudness} LUFS -> $output_wav and $output_mp3"

# gates: lengths, then the music under the voice when a timeline is given
python3 -I "$gates" length "$output_wav" --expected "$length_seconds" --step "the mix (WAV)"
python3 -I "$gates" length "$output_mp3" --expected "$length_seconds" --step "the mix (MP3)"
if [ -n "$timeline_file" ]; then
  python3 -I "$gates" gaps "$stems_dir/voice.wav" "$stems_dir/music.wav" "$timeline_file"
fi
