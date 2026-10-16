"""What this does: measures the film's sound instead of trusting it, so the sound faults this project found by ear and by
hand (logs 04-34) stop the step that made them. Each command prints PASS or FAIL lines and exits 1 on a failure, so the
mix scripts and finish_film.sh call them as gates:
  length     an audio or film file is as long as asked, within 0.05 s (lesson 5: loudnorm switched to 192,000 samples a
             second and the mix came out 3 s short); name the step so the failure says where it happened;
  loudness   the ENCODED file's integrated loudness and true peak (ffmpeg ebur128, peak=true): a narrated film -15 LUFS
             +/- 0.5, a music-only clip -14, true peak at most -1 dBTP; when the peak is over, the limiter ceiling to use;
  alignment  the film's sound against the mix at every page's first word (check_sound_alignment.py's own sum): at most
             2 ms off and a match of at least 0.8 (lesson 15: the limiter's 5 ms look-ahead);
  gaps       how far the music sits under the voice, from the voice-only and ducked-music-only stems of the mix: per
             page, the level (mean square, K-weighted as loudness meters weigh it) over all its word spans, and the music
             in every pause of 0.5 s or more; about 18 dB under while she speaks and about 12 in pauses (logs 04, 07, 10);
  duck       finds the music level for ANY soundtrack: renders the stems with mix_narration_over_music.sh at a level,
             measures the gap while she speaks, moves the level by (gap - 18) dB and repeats until within 1 dB;
             --louder 3 for "slightly louder" (decision 12: the user's 'slightly' was 3 dB);
  voice      the voice steadiness gate after recording: a page whose typical pitch is more than 1.5 semitones from the
             chapter's median is to be recorded again; the spread of typical pitch across pages passes up to 2.6 (2.2
             accepted on chapter 2, 3.0 not on chapter 1); words 5 semitones higher or 6 dB louder than their page are
             listed for a person (the accepted chapter 2 has 4-12 such words a page, so they cannot send a page back);
  mouth      a paper mouth's QUIET and LOUD levels from the voice itself (40th and 90th percentile of voiced 40 ms slices);
  music-start  the stretch of a soundtrack for a music-only clip: a window of the clip's length, its 3 s loudness close
             to the mood's level and steady, started where the music starts a phrase, with its fades.
Every command takes --json, --out FILE, --report FILE and --settings FILE (kit/film-settings.json), and names the
settings it used.

Use:
  python3 -I sound_gates.py length FILE --expected SECONDS [--step NAME] [--stream audio|any]
  python3 -I sound_gates.py loudness FILE [--music-only] [--limiter-limit 0.84]
  python3 -I sound_gates.py alignment FILM.mp4 MIX.wav TIMELINE.json
  python3 -I sound_gates.py gaps VOICE_STEM.wav MUSIC_STEM.wav TIMELINE.json
  python3 -I sound_gates.py duck MUSIC NARRATION.wav TIMELINE.json [--music-level DB] [--louder DB]
  python3 -I sound_gates.py voice WORD_TIMES.json [--recordings-from DIR]
  python3 -I sound_gates.py mouth NARRATION.wav [--timeline TIMELINE.json]
  python3 -I sound_gates.py music-start MUSIC --seconds CLIP_SECONDS [--mood quiet|lively] [--top 5]
"""
import argparse
import json
import math
import os
import re
import statistics
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True   # the gates import their sibling tools; leave no __pycache__ in the kit
HERE = os.path.dirname(os.path.abspath(__file__))
CALCULATORS = os.path.join(os.path.dirname(HERE), 'calculators')
for folder in (CALCULATORS, HERE):
    if folder not in sys.path:
        sys.path.insert(0, folder)
from settings import load_settings  # noqa: E402
from calculator_output import add_output_options, finish, run_main  # noqa: E402

MIX_SCRIPT = os.path.join(HERE, 'mix_narration_over_music.sh')
RATE = 48000
# the K-weighting of ITU-R BS.1770 at 48 kHz (a high shelf, then a high pass), the weighting loudness meters use
K_WEIGHTING = ('biquad=b0=1.53512485958697:b1=-2.69169618940638:b2=1.19839281085285:a0=1:a1=-1.69065929318241:a2=0.73248077421585,'
               'biquad=b0=1:b1=-2:b2=1:a0=1:a1=-1.99004745483398:a2=0.99007225036621')


# ------------------------------------------------------------------------------------------------- measuring
def duration_seconds(path, stream='any'):
    """ffprobe's duration: of the file, or of its first audio stream."""
    if stream == 'audio':
        out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=duration', '-of', 'csv=p=0', path],
                             capture_output=True, text=True).stdout.strip()
        if out and out != 'N/A':
            return float(out)
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True)
    if out.returncode != 0 or not out.stdout.strip():
        raise SystemExit(f'sound_gates: ffprobe cannot read {path}: {out.stderr.strip()[-200:]}')
    return float(out.stdout.strip())


def loudness_of(path):
    """Integrated loudness (LUFS), loudness range and true peak (dBTP) of the file as it is, by ffmpeg's ebur128."""
    report = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-map', 'a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                            capture_output=True, text=True).stderr
    summary = report[report.rfind('Summary:'):]
    integrated = re.search(r'I:\s+(-?[\d.]+|-inf) LUFS', summary)
    peak = re.search(r'True peak:\s+Peak:\s+(-?[\d.]+|-inf) dBFS', summary)
    lra = re.search(r'LRA:\s+(-?[\d.]+) LU', summary)
    if not integrated or not peak:
        raise SystemExit(f'sound_gates: ebur128 gave no summary for {path}')
    return {'integrated_lufs': float(integrated.group(1)), 'true_peak_dbtp': float(peak.group(1)),
            'loudness_range_lu': float(lra.group(1)) if lra else None}


def samples(path, weighted=False, start=None, seconds=None):
    """Mono samples at 48 kHz (float32), K-weighted when asked."""
    import numpy
    command = ['ffmpeg', '-v', 'error']
    if start is not None:
        command += ['-ss', str(start)]
    if seconds is not None:
        command += ['-t', str(seconds)]
    command += ['-i', path, '-ac', '1', '-ar', str(RATE)]
    if weighted:
        command += ['-af', K_WEIGHTING]
    command += ['-f', 'f32le', '-']
    raw = subprocess.run(command, check=True, capture_output=True).stdout
    return numpy.frombuffer(raw, dtype=numpy.float32).astype('float64')


def energy_db(x, spans):
    """The level (dB) of the samples over a set of spans taken together: 10 log10 of their mean square."""
    import numpy
    total, count = 0.0, 0
    for a, b in spans:
        piece = x[int(a * RATE):int(b * RATE)]
        total += float(numpy.sum(piece * piece))
        count += len(piece)
    return None if count < RATE // 100 else float(10 * numpy.log10(total / count + 1e-20))


def music_gaps(voice_stem, music_stem, timeline, settings):
    """How far the music sits under the voice, from the two stems, K-weighted. While she speaks: for each page, the voice's
    level over all its word spans against the music's level over the same spans (median over pages). In pauses: the
    voice's typical page level against the music's level in each silence of pause_min_seconds or more between words
    (median over pauses). This way of measuring was chosen from three because it reproduces chapter 1's recorded figures
    (log 10: about 21 dB at music level -14, about 18 at -11, about 12 in the pauses); word by word medians read 2 dB more."""
    shortest_pause = settings.value('sound_gates.pause_min_seconds')
    voice, music = samples(voice_stem, weighted=True), samples(music_stem, weighted=True)
    per_page, voice_levels = [], []
    for page in timeline['pages']:
        spans = [(w['start'], w['end']) for w in page['words']]
        v, m = energy_db(voice, spans), energy_db(music, spans)
        if v is not None and m is not None:
            per_page.append({'page': page['page'], 'gap_db': round(v - m, 2)})
            voice_levels.append(v)
    typical_voice = statistics.median(voice_levels)
    words = [w for page in timeline['pages'] for w in page['words']]
    in_pauses = []
    for a, b in zip(words, words[1:]):
        if b['start'] - a['end'] >= shortest_pause:
            m = energy_db(music, [(a['end'] + 0.05, b['start'] - 0.05)])
            if m is not None:
                in_pauses.append(typical_voice - m)
    gaps = [p['gap_db'] for p in per_page]
    return {'gap_while_speaking_db': round(statistics.median(gaps), 2), 'gap_in_pauses_db': round(statistics.median(in_pauses), 2) if in_pauses else None,
            'pages': per_page, 'pauses': len(in_pauses), 'typical_voice_db': round(typical_voice, 2),
            'page_gap_range_db': [round(min(gaps), 2), round(max(gaps), 2)]}


def render_stems(music, narration, level_db, folder, env_extra=None):
    """The voice-only and ducked-music-only stems, made by mix_narration_over_music.sh itself (the same filter chain)."""
    env = dict(os.environ, MUSIC_LEVEL_DB=str(level_db), STEMS_DIR=folder, STEMS_ONLY='1', **(env_extra or {}))
    run = subprocess.run(['bash', MIX_SCRIPT, music, narration, os.path.join(folder, 'unused.wav'), os.path.join(folder, 'unused.mp3')],
                         env=env, capture_output=True, text=True)
    if run.returncode != 0:
        raise SystemExit(f'sound_gates: the mix script failed: {(run.stdout + run.stderr).strip()[-400:]}')
    return os.path.join(folder, 'voice.wav'), os.path.join(folder, 'music.wav')


# ------------------------------------------------------------------------------------------------- voice and mouth
def page_recordings(word_times, recordings_from=None):
    for page in word_times['pages']:
        path = page['recording']
        if recordings_from:
            path = os.path.join(recordings_from, os.path.basename(path))
        yield page, path


def voice_gate(word_times, settings, recordings_from=None):
    """Typical pitch per page (compare_voice_steadiness.py's measure), its spread, and per word the raised (pitch) and
    loud (level) words of find_raised_voice.py and find_loud_words.py, judged against film-settings.json."""
    import warnings
    import numpy
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    from compare_voice_steadiness import pitches
    from find_raised_voice import load as load_16k, word_pitches
    from find_loud_words import load as load_48k, word_peak_levels
    raised_limit = settings.value('sound.raised_voice_semitones')
    loud_limit = settings.value('sound.loud_word_db')
    page_limit = settings.value('sound_gates.page_pitch_from_median_semitones')
    spread_limit = settings.value('sound_gates.pitch_spread_max_semitones')
    rows = []
    for page, path in page_recordings(word_times, recordings_from):
        if not os.path.exists(path):
            rows.append({'page': page['page'], 'missing': path})
            continue
        typical = float(numpy.median(pitches(path)))
        audio16 = load_16k(path)
        raised = []
        for word in page['words']:
            p = word_pitches(audio16, word['start'], min(word['end'], word['start'] + 0.7))
            if len(p) >= 3:
                up = 12 * math.log2(float(numpy.median(p)) / typical)
                if up >= raised_limit:
                    raised.append({'word': word['text'], 'at': word['start'], 'semitones': round(up, 1)})
        levels = word_peak_levels(load_48k(path), page['words'])
        middle = float(numpy.median([db for _, _, db in levels])) if levels else 0.0
        loud = [{'word': t, 'at': s, 'db_above': round(db - middle, 1)} for t, s, db in levels if db - middle >= loud_limit]
        rows.append({'page': page['page'], 'typical_hz': round(typical, 1), 'raised_words': raised, 'loud_words': loud})
    measured = [r for r in rows if 'typical_hz' in r]
    median_hz = statistics.median(r['typical_hz'] for r in measured)
    spread = 12 * math.log2(max(r['typical_hz'] for r in measured) / min(r['typical_hz'] for r in measured))
    rerecord = {}
    for r in measured:
        r['semitones_from_median'] = round(12 * math.log2(r['typical_hz'] / median_hz), 2)
        # only the page's typical pitch sends it back: raised and loud words are listed for a person, because the accepted
        # chapter 2 has 4-12 words a page 5 or more semitones over its typical pitch (natural intonation swings about 12)
        if abs(r['semitones_from_median']) > page_limit:
            rerecord[r['page']] = f'typical pitch {r["semitones_from_median"]:+.1f} semitones from the chapter\'s median (at most {page_limit})'
    return {'pages': rows, 'median_typical_hz': round(median_hz, 1), 'spread_semitones': round(spread, 2),
            'spread_passes': spread <= spread_limit, 'rerecord': rerecord,
            'missing': [r['missing'] for r in rows if 'missing' in r]}


def mouth_levels(narration, settings, timeline=None):
    """QUIET and LOUD for make_mouth_track.py from the voice: percentiles of the voiced 40 ms slices' level (dBFS, the
    tool's own scale: RMS of 40 ms around a moment). Voiced = inside a word span when a timeline is given, else within
    voiced_below_peak_db of the loudest slice."""
    import numpy
    x = samples(narration)
    slice_length = int(0.04 * RATE)
    count = len(x) // slice_length
    levels = 20 * numpy.log10(numpy.sqrt((x[:count * slice_length].reshape(count, slice_length) ** 2).mean(axis=1)) + 1e-9)
    if timeline:
        inside = numpy.zeros(count, bool)
        for page in timeline['pages']:
            for w in page['words']:
                inside[int(w['start'] / 0.04):int(w['end'] / 0.04) + 1] = True
        voiced = levels[inside[:count] & (levels > levels.max() - settings.value('sound_gates.voiced_below_peak_db'))]
    else:
        voiced = levels[levels > levels.max() - settings.value('sound_gates.voiced_below_peak_db')]
    quiet_p, loud_p = settings.value('sound_gates.mouth_percentiles')
    return {'quiet_db': round(float(numpy.percentile(voiced, quiet_p)), 2), 'loud_db': round(float(numpy.percentile(voiced, loud_p)), 2),
            'voiced_slices': int(len(voiced)), 'percentiles': [quiet_p, loud_p]}


# ------------------------------------------------------------------------------------------------- the soundtrack's stretch
def short_term_loudness(path):
    """ffmpeg ebur128's short-term (3 s) loudness every 0.1 s: [(seconds, LUFS)]."""
    report = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    values = []
    for m in re.finditer(r't:\s*([\d.]+)\s+TARGET:.*?M:\s*(-?[\d.]+|-inf)\s+S:\s*(-?[\d.]+|-inf)', report):
        s = m.group(3)
        values.append((float(m.group(1)), float(s) if s != '-inf' else -120.0, float(m.group(2)) if m.group(2) != '-inf' else -120.0))
    return values


def music_start(path, seconds, mood, settings, top=5):
    """Windows of the clip's length ranked: mean 3 s loudness within the mood's band of its level (a percentile of the
    soundtrack's own loudness), steadiest first; each start moved back to the start of its section (the nearest change of
    section_change_db or more in the music's level within section_snap_seconds before it), so the clip starts where the
    music starts something, not mid-phrase. Tuned on one recorded case (log 32's 216 s); no other case was recorded."""
    values = short_term_loudness(path)
    if not values:
        raise SystemExit(f'sound_gates: no loudness readings from {path}')
    times = [t for t, _, _ in values]
    short = [s for _, s, _ in values]
    momentary = [m for _, _, m in values]
    audible = sorted(s for s in short if s > -70)
    level = audible[int(len(audible) * settings.value('sound_gates.music_mood_percentiles')[mood] / 100)]
    band = settings.value('sound_gates.music_mood_band_lu')
    change = settings.value('sound_gates.section_change_db')
    snap = settings.value('sound_gates.section_snap_seconds')
    length = int(round(seconds * 10))

    def window_ok(i):
        window = [s for s in short[i:i + length] if s > -70]
        if i < 0 or i + length > len(short) or len(window) < length * 0.9:
            return None
        mean = statistics.mean(window)
        return (mean, statistics.pstdev(window)) if abs(mean - level) <= band else None

    def section_start(i):
        """The steepest change of the 1 s mean of the momentary loudness within snap seconds before index i."""
        best, best_step = None, change
        for j in range(max(10, i - int(snap * 10)), i + 1):
            before = statistics.mean(momentary[j - 10:j])
            after = statistics.mean(momentary[j:j + 10])
            if abs(after - before) >= best_step:
                best, best_step = j, abs(after - before)
        return best

    candidates = []
    for i in range(0, len(values) - length, 10):
        found = window_ok(i)
        if found:
            candidates.append({'index': i, 'start': round(times[i] - 0.1, 1), 'mean_lufs': round(found[0], 2), 'spread_lu': round(found[1], 2)})
    candidates.sort(key=lambda c: c['spread_lu'])
    fades = settings.value('sound.music_only_fades_seconds')
    chosen, seen = [], set()
    for c in candidates:
        j = section_start(c['index'])
        if j is not None and window_ok(j):
            c['section_start'] = round(times[j] - 0.1, 1)
            c['fade_in'] = fades['in']
        else:
            c['section_start'] = None
            c['fade_in'] = settings.value('sound_gates.fade_in_without_onset_seconds')
        c['fade_out'] = fades['out']
        c['use_start'] = c['section_start'] if c['section_start'] is not None else c['start']
        key = round(c['use_start'])
        if key in seen:
            continue
        seen.add(key)
        chosen.append({k: v for k, v in c.items() if k != 'index'})
        if len(chosen) >= top:
            break
    return {'mood': mood, 'mood_level_lufs': round(level, 2), 'band_lu': band, 'windows_found': len(candidates), 'best': chosen}


# ------------------------------------------------------------------------------------------------- command line
def main():
    parser = argparse.ArgumentParser(description='Measures the sound and stops the step that got it wrong (see the note at the top).')
    sub = parser.add_subparsers(dest='command', required=True)
    p = add_output_options(sub.add_parser('length', help='is the file as long as asked?'))
    p.add_argument('file')
    p.add_argument('--expected', type=float, required=True)
    p.add_argument('--step', default='this step', help='the step that made the file, named in the report')
    p.add_argument('--stream', choices=['any', 'audio'], default='any', help='judge the whole file or its sound only')
    p = add_output_options(sub.add_parser('loudness', help='loudness and true peak of the encoded file'))
    p.add_argument('file')
    p.add_argument('--music-only', action='store_true', help='a clip with music and no narration (-14 LUFS)')
    p.add_argument('--target', type=float, help='another target, LUFS')
    p.add_argument('--limiter-limit', type=float, help='the limiter ceiling the mix used (default: film-settings.json sound.limiter)')
    p = add_output_options(sub.add_parser('alignment', help='the film\'s sound against the mix at every page'))
    p.add_argument('film')
    p.add_argument('mix')
    p.add_argument('timeline')
    p = add_output_options(sub.add_parser('gaps', help='how far the music sits under the voice, from the two stems'))
    p.add_argument('voice_stem')
    p.add_argument('music_stem')
    p.add_argument('timeline')
    p = add_output_options(sub.add_parser('duck', help='the music level that puts the music 18 dB under her voice'))
    p.add_argument('music')
    p.add_argument('narration')
    p.add_argument('timeline')
    p.add_argument('--music-level', type=float, help='the level to start from (default: film-settings.json sound.music_level_db)')
    p.add_argument('--louder', type=float, default=0.0, help='dB louder than the house gap ("slightly louder" = 3)')
    p.add_argument('--passes', type=int, default=4)
    p = add_output_options(sub.add_parser('voice', help='voice steadiness: pages and words to record again'))
    p.add_argument('word_times')
    p.add_argument('--recordings-from', help='read pageN.mp3 from this folder instead of the paths in the file')
    p = add_output_options(sub.add_parser('mouth', help='the paper mouth\'s QUIET and LOUD levels from the voice'))
    p.add_argument('narration')
    p.add_argument('--timeline')
    p = add_output_options(sub.add_parser('music-start', help='where to start a soundtrack under a music-only clip'))
    p.add_argument('music')
    p.add_argument('--seconds', type=float, required=True)
    p.add_argument('--mood', choices=['quiet', 'lively'], default='quiet')
    p.add_argument('--top', type=int, default=5)
    args = parser.parse_args()
    settings = load_settings(args.settings)
    lines, result, code = [], {}, 0

    if args.command == 'length':
        got = duration_seconds(args.file, args.stream)
        tolerance = settings.value('sound.length_tolerance_seconds')
        ok = abs(got - args.expected) <= tolerance
        result = {'file': args.file, 'step': args.step, 'seconds': round(got, 4), 'expected': args.expected, 'tolerance': tolerance, 'passes': ok}
        lines.append(f'{"PASS" if ok else "FAIL"}  length after {args.step}: {got:.3f} s against {args.expected:.3f} s asked '
                     f'(allowed {tolerance} s){"" if ok else " - an audio step changed the length (resample to 48000 after any loudnorm)"}')
        code = 0 if ok else 1
    elif args.command == 'loudness':
        measured = loudness_of(args.file)
        target = args.target if args.target is not None else settings.value('sound.music_only_lufs' if args.music_only else 'sound.mix_lufs')
        tolerance = settings.value('sound_gates.loudness_tolerance_lu')
        peak_max = settings.value('sound.true_peak_max_dbtp')
        loud_ok = abs(measured['integrated_lufs'] - target) <= tolerance
        peak_ok = measured['true_peak_dbtp'] <= peak_max
        limit = args.limiter_limit if args.limiter_limit is not None else settings.value('sound.limiter')['limit']
        result = dict(measured, file=args.file, target_lufs=target, tolerance_lu=tolerance, true_peak_max_dbtp=peak_max,
                      loudness_passes=loud_ok, true_peak_passes=peak_ok)
        lines.append(f'{"PASS" if loud_ok else "FAIL"}  loudness of {os.path.basename(args.file)}: {measured["integrated_lufs"]:.1f} LUFS '
                     f'(target {target} +/- {tolerance})')
        lines.append(f'{"PASS" if peak_ok else "FAIL"}  true peak: {measured["true_peak_dbtp"]:.1f} dBTP (at most {peak_max}; measured on the encoded file, '
                     'since encoding raises peaks)')
        if not peak_ok:
            lower = measured['true_peak_dbtp'] - peak_max + settings.value('sound_gates.true_peak_margin_db')
            new_limit = limit * 10 ** (-lower / 20)
            result['suggested_limiter_limit'] = round(new_limit, 3)
            lines.append(f'      lower the limiter by {lower:.1f} dB: alimiter limit={new_limit:.3f} (was {limit}), then encode the sound again')
        if not loud_ok:
            lines.append(f'      turn it by {target - measured["integrated_lufs"]:+.1f} dB (the mix\'s target_loudness, or add_music_bed.sh LOUDNESS)')
        code = 0 if loud_ok and peak_ok else 1
    elif args.command == 'alignment':
        from check_sound_alignment import mono_samples, offset_ms
        film, mix = mono_samples(args.film), mono_samples(args.mix)
        timeline = json.load(open(args.timeline))
        limit = settings.value('sound_gates.alignment_max_ms')
        match_min = settings.value('sound_gates.alignment_match_min')
        rows = []
        for page in timeline['pages']:
            shift, match = offset_ms(film, mix, page['first_word_at'])
            rows.append({'page': page['page'], 'offset_ms': round(float(shift), 3), 'match': round(float(match), 4)})
        worst = max(abs(r['offset_ms']) for r in rows)
        weakest = min(r['match'] for r in rows)
        ok = worst <= limit and weakest >= match_min
        result = {'pages': rows, 'largest_offset_ms': worst, 'weakest_match': weakest, 'passes': ok}
        lines.append(f'{"PASS" if ok else "FAIL"}  sound alignment: largest offset {worst:.2f} ms (at most {limit}), weakest match {weakest:.3f} (at least {match_min})')
        for r in rows:
            if abs(r['offset_ms']) > limit or r['match'] < match_min:
                lines.append(f'      page {r["page"]}: {r["offset_ms"]:+.2f} ms, match {r["match"]:.3f} (a filter with look-ahead adds delay: alimiter needs latency=1)')
        code = 0 if ok else 1
    elif args.command == 'gaps':
        timeline = json.load(open(args.timeline))
        result = music_gaps(args.voice_stem, args.music_stem, timeline, settings)
        target = settings.value('sound.music_under_voice_db')
        ok = abs(result['gap_while_speaking_db'] - target['while_speaking']) <= target['tolerance']
        band = settings.value('sound_gates.pause_gap_band_db')
        pause_ok = result['gap_in_pauses_db'] is None or band[0] <= result['gap_in_pauses_db'] <= band[1]
        result.update(passes=ok, pause_gap_in_band=pause_ok)
        lines.append(f'{"PASS" if ok else "FAIL"}  music under the voice while she speaks: {result["gap_while_speaking_db"]:.1f} dB '
                     f'(target {target["while_speaking"]} +/- {target["tolerance"]}; pages {result["page_gap_range_db"][0]:.1f} to {result["page_gap_range_db"][1]:.1f})')
        lines.append(f'{"PASS" if pause_ok else "LOOK"}  in pauses of {settings.value("sound_gates.pause_min_seconds")} s or more: '
                     f'{result["gap_in_pauses_db"]} dB (about {target["in_pauses"]}; band {band[0]}-{band[1]}; {result["pauses"]} pauses)')
        if not ok:
            lines.append(f'      run: python3 -I narration-tools/sound_gates.py duck MUSIC NARRATION TIMELINE (it finds the level for this soundtrack)')
        code = 0 if ok else 1
    elif args.command == 'duck':
        timeline = json.load(open(args.timeline))
        target = settings.value('sound.music_under_voice_db')
        wanted = target['while_speaking'] - args.louder
        level = args.music_level if args.music_level is not None else settings.value('sound.music_level_db')
        passes = []
        with tempfile.TemporaryDirectory() as folder:
            for _ in range(args.passes):
                voice, music = render_stems(args.music, args.narration, level, folder)
                gaps = music_gaps(voice, music, timeline, settings)
                passes.append(dict(gaps, music_level_db=round(level, 2)))
                miss = gaps['gap_while_speaking_db'] - wanted
                if abs(miss) <= target['tolerance']:
                    break
                level = round(level + miss, 2)
        last = passes[-1]
        ok = abs(last['gap_while_speaking_db'] - wanted) <= target['tolerance']
        result = {'passes': passes, 'music_level_db': last['music_level_db'], 'target_gap_db': wanted, 'found': ok}
        for i, p in enumerate(passes, 1):
            lines.append(f'  pass {i}: music_level_db {p["music_level_db"]:+.2f} -> {p["gap_while_speaking_db"]:.1f} dB under while she speaks, '
                         f'{p["gap_in_pauses_db"]} dB in pauses')
        lines.append(f'{"PASS" if ok else "FAIL"}  music level for this soundtrack: MUSIC_LEVEL_DB={last["music_level_db"]} '
                     f'({last["gap_while_speaking_db"]:.1f} dB under while she speaks; wanted {wanted} +/- {target["tolerance"]})')
        lines.append(f'      mix with: MUSIC_LEVEL_DB={last["music_level_db"]} bash narration-tools/mix_narration_over_music.sh MUSIC NARRATION OUT.wav OUT.mp3 TIMELINE')
        code = 0 if ok else 1
    elif args.command == 'voice':
        word_times = json.load(open(args.word_times))
        result = voice_gate(word_times, settings, args.recordings_from)
        spread_limit = settings.value('sound_gates.pitch_spread_max_semitones')
        lines.append(f'{"PASS" if result["spread_passes"] else "FAIL"}  spread of typical pitch across pages: {result["spread_semitones"]:.1f} semitones '
                     f'(at most {spread_limit}; chapter 2 measured 2.2 and was accepted, chapter 1 3.0 and was not)')
        for r in result['pages']:
            if 'typical_hz' in r:
                lines.append(f'  page {r["page"]:2d}: typical {r["typical_hz"]:.0f} Hz ({r["semitones_from_median"]:+.1f} semitones), '
                             f'{len(r["raised_words"])} raised, {len(r["loud_words"])} loud words')
        for page, why in result['rerecord'].items():
            lines.append(f'RE-RECORD page {page}: {why}')
        for r in result['pages']:
            words = [f'"{w["word"]}" +{w["semitones"]}' for w in r.get('raised_words', [])] + [f'"{w["word"]}" +{w["db_above"]} dB' for w in r.get('loud_words', [])]
            if words:
                lines.append(f'LOOK  page {r["page"]}: listen to ' + ', '.join(words[:8]) + (' ...' if len(words) > 8 else '')
                             + ' (higher or louder than the page; a person decides)')
        for path in result['missing']:
            lines.append(f'MISSING  {path}')
        lines.append('Fix steadiness in the script first (one identical cue on every page, no capitals, no mood cues), then re-record only these pages.')
        code = 0 if result['spread_passes'] and not result['rerecord'] and not result['missing'] else 1
    elif args.command == 'mouth':
        timeline = json.load(open(args.timeline)) if args.timeline else None
        result = mouth_levels(args.narration, settings, timeline)
        lines.append(f'Mouth levels for this voice: QUIET_DB = {result["quiet_db"]:.1f}, LOUD_DB = {result["loud_db"]:.1f} '
                     f'({result["percentiles"][0]}th and {result["percentiles"][1]}th percentile of {result["voiced_slices"]} voiced 40 ms slices); '
                     f'make_mouth_track.py has {settings.value("sound.mouth")["quiet_db"]} and {settings.value("sound.mouth")["loud_db"]}.')
    elif args.command == 'music-start':
        result = music_start(args.music, args.seconds, args.mood, settings, args.top)
        lines.append(f'Stretches of {args.seconds:.0f} s for a {args.mood} clip (3 s loudness within {result["band_lu"]} LU of '
                     f'{result["mood_level_lufs"]} LUFS, steadiest first; {result["windows_found"]} found):')
        for c in result['best']:
            lines.append(f'  START={c["use_start"]:.1f}  (mean {c["mean_lufs"]} LUFS, spread {c["spread_lu"]} LU; '
                         + (f'the music starts a section at {c["section_start"]} s' if c['section_start'] is not None else 'no section start nearby')
                         + f'; fade in {c["fade_in"]} s, out {c["fade_out"]} s)')
        if result['best']:
            c = result['best'][0]
            lines.append(f'  bash paper-film/tools/add_music_bed.sh FILM.mp4 MUSIC OUT.mp4 {c["use_start"]:.1f} '
                         f'{settings.value("sound.music_only_lufs")} {c["fade_in"]} {c["fade_out"]}')
    finish(f'sound_gates {args.command}', result, lines, settings, args)
    return code


if __name__ == '__main__':
    sys.exit(run_main(main, 'sound_gates'))
