"""What this does: tests narration-tools/sound_gates.py and the gates it adds to the plugin kit's mix scripts,
finish_film.sh and add_music_bed.sh, on the project's real sound: chapter 2's levelled narration, mix and delivered
films, chapter 1's recordings (its narration track is rebuilt from them with assemble_chapter_narration.py), the
soundtrack, and the music-only clips of logs 27, 29 and 32. None of these audio or video files is in the plugin (the
user's rule): the test reads them where the project keeps them and skips what it cannot find (exit 77 if it finds none):
the project (FILM_PROJECT, or austerity-explainer next to the plugins folder) for chapter 2's sound and films, the
project's working files (FILM_WORKING_FILES) for chapter 1's recordings and the music-only clips, and the soundtrack
"Tension and Gravity.mp3" from FILM_SOUNDTRACK, the film kit's assets/soundtrack or the working files.
Each check names the number got, the number the project recorded and where, and says whether it proves something or
only repeats. Where a way of measuring was CHOSEN to match a record (the music under the voice, the mouth's quiet
level, the music picker), the check says so, and the other chapter is the hold-out.
Run: python3 kit/calculators/tests/test_sound_gates.py   (about four minutes)
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, skip, project_folder, film_kit_folder, working_files_folder, PROJECT_WORDS  # noqa: E402
from settings import load_settings  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
TOOLS = os.path.join(KIT, 'narration-tools')
sys.path.insert(0, TOOLS)
import sound_gates as gates  # noqa: E402

PROJECT = project_folder() or '(project not found)'
WORKING = working_files_folder() or '(working files not given)'
SOUNDTRACKS = [os.environ.get('FILM_SOUNDTRACK', ''), os.path.join(film_kit_folder() or PROJECT, 'assets', 'soundtrack', 'Tension and Gravity.mp3'),
               os.path.join(WORKING, 'in_ch1', 'austerity-explainer-chapter-1', 'soundtrack', 'Tension and Gravity.mp3')]
SOUNDTRACK = next((p for p in SOUNDTRACKS if p and os.path.exists(p)), None)
CH2_NARRATION = os.path.join(PROJECT, 'chapter-2-inflation', 'narration', 'chapter-2-narration.flac')
CH2_RECORDINGS = os.path.join(PROJECT, 'chapter-2-inflation', 'narration', 'recordings')
CH2_MIX = os.path.join(PROJECT, 'chapter-2-inflation', 'mix', 'chapter-2-mix.flac')
CH2_FILMS = sorted(glob.glob(os.path.join(PROJECT, 'chapter-2-inflation', 'deliver', '*Chapter 2 - what really causes inflation.mp4')))
CH2_MASTER = CH2_FILMS[-1] if CH2_FILMS else ''   # its pictures only, cut to 25 s (the master was the same frames, larger)
CH1_RECORDINGS = os.path.join(WORKING, 'in_ch1', 'austerity-explainer-chapter-1', 'narration', 'recordings')
CH2_TIMELINE = os.path.join(KIT, 'examples', 'inflation-chapter-2', 'timeline.json')
CH1_WORD_TIMES = os.path.join(KIT, 'examples', 'austerity-chapter-1', 'word-times.json')
CH2_WORD_TIMES = os.path.join(KIT, 'examples', 'inflation-chapter-2', 'word-times.json')
MUSIC_ONLY = {'log 27 house': os.path.join(WORKING, 'house', 'music-37s.wav'), 'log 29 lockout': os.path.join(WORKING, 'plan3', 'lockout-music.wav'),
              'log 32 notice corner': os.path.join(WORKING, 'plan3', 'corner', 'recheck', 'audio.wav')}
if not project_folder():
    skip('sound gates', PROJECT_WORDS)
if not (SOUNDTRACK and os.path.exists(CH2_NARRATION)):
    skip('sound gates', 'the soundtrack "Tension and Gravity.mp3" or chapter 2\'s narration is not on this machine (audio stays out of the '
         'repository; name the soundtrack with FILM_SOUNDTRACK, or give the working files with FILM_WORKING_FILES)')

check = Checker('sound gates: lengths, loudness, alignment, music under the voice, voice, mouth, music start')
settings = load_settings()
WORK = tempfile.mkdtemp()
ENV = dict(os.environ, FILM_SETTINGS=settings.path)


def run(command, **extra):
    return subprocess.run(command, capture_output=True, text=True, env=dict(ENV, **extra))


def gate(*args):
    return run([sys.executable, '-I', '-B', os.path.join(TOOLS, 'sound_gates.py')] + list(args) + ['--json'])


def mix(script, narration, out_name, timeline=None, **extra):
    out = os.path.join(WORK, out_name)
    return run(['bash', script, SOUNDTRACK, narration, out + '.wav', out + '.mp3'] + ([timeline] if timeline else []), **extra), out + '.wav'


timeline2 = json.load(open(CH2_TIMELINE))
try:
    # 1. the length gate on the real chain: the film kit's mix comes out short on this machine; the plugin's does not
    film_kit_mix = os.path.join(PROJECT, 'film-kit', 'narration-tools', 'mix_narration_over_music.sh')
    if os.path.exists(film_kit_mix):
        _, old_wav = mix(film_kit_mix, CH2_NARRATION, 'film-kit-mix')
        short = json.loads(gate('length', old_wav, '--expected', str(timeline2['chapter_seconds']), '--step', 'film kit mix').stdout)
        check.true(f'the film kit\'s mix of chapter 2 is {timeline2["chapter_seconds"] - short["seconds"]:.2f} s short and the gate fails it',
                   not short['passes'], details=f'{short["seconds"]:.3f} s against {timeline2["chapter_seconds"]:.3f} s',
                   recorded='lesson 5 (a mix came out 3 s short); here ffmpeg 6.1\'s sidechaincompress ends early',
                   proves='a real fault the gate catches (the delivered mix was full length, made on 12 October)')
    result, new_wav = mix(os.path.join(TOOLS, 'mix_narration_over_music.sh'), CH2_NARRATION, 'plugin-mix', CH2_TIMELINE)
    lines = [l for l in result.stdout.splitlines() if l.startswith(('PASS', 'FAIL', 'LOOK'))]
    check.true('the plugin\'s mix of chapter 2 with its timeline: every gate passes (lengths, music under the voice, alignment)',
               result.returncode == 0 and not any(l.startswith('FAIL') for l in lines), details=' | '.join(lines)[:300] + result.stderr[-200:])
    import numpy

    def stereo(path):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '2', '-ar', '48000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
        return numpy.frombuffer(raw, dtype=numpy.float32).reshape(-1, 2)
    ours = stereo(new_wav)
    if os.path.exists(film_kit_mix):
        theirs = stereo(old_wav)
        n = len(theirs) - 48000 * 4
        check.close('the plugin\'s mix against the film kit\'s, sample by sample, before the last 4 s: largest difference', float(numpy.abs(ours[:n] - theirs[:n]).max()),
                    0.0, 1e-7, proves='the gates and the length fix change nothing else in the mix')
    if os.path.exists(CH2_MIX):
        delivered = stereo(CH2_MIX)
        n = min(len(ours), len(delivered)) - 48000 * 4
        check.within('the plugin\'s mix against the delivered chapter-2-mix.flac: correlation', float(numpy.corrcoef(ours[:n, 0], delivered[:n, 0])[0, 1]), 0.99999, 1.0,
                     recorded='chapter-2-inflation/mix/chapter-2-mix.flac (made 12-13 October)', proves='the soundtrack, narration and chain are the ones the project used')
    del ours
    tone = os.path.join(WORK, 'tone.wav')
    for seconds, asked, ok in ((23.04, 23.0, True), (20.0, 23.0, False)):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'sine=frequency=220:duration={seconds}', '-ar', '48000', tone], check=True)
        got = gate('length', tone, '--expected', str(asked))
        check.equal(f'{seconds} s delivered for {asked} s asked: {"passes" if ok else "fails"}', got.returncode, 0 if ok else 1,
                    recorded='lesson 5 (23 s asked, 23.04 s delivered; the first check 3 s short)', proves='the tolerance of 0.05 s')

    # 2. loudness of what was delivered, and of the music-only clips
    for film in CH2_FILMS:
        got = json.loads(gate('loudness', film).stdout)
        check.true(f'{os.path.basename(film)[:2]} sendable copy: {got["integrated_lufs"]} LUFS, true peak {got["true_peak_dbtp"]} dBTP: passes',
                   got['loudness_passes'] and got['true_peak_passes'], recorded='logs 19-20: -15.0/-15.1 LUFS, true peak -1.5 to -1.8',
                   proves='the gate passes the films the user accepted')
    for name, path in MUSIC_ONLY.items():
        if not os.path.exists(path):
            check.note(f'{name}: the music-only clip is not on this machine (it is in the working files: FILM_WORKING_FILES), not checked')
            continue
        got = json.loads(gate('loudness', path, '--music-only').stdout)
        if name.startswith('log 32'):
            check.true(f'{name}: {got["integrated_lufs"]} LUFS passes the loudness; its true peak {got["true_peak_dbtp"]} dBTP does not',
                       got['loudness_passes'] and not got['true_peak_passes'], recorded='log 32 (raised to -14, measured -13.7)',
                       proves='a finding: the kept clip is 0.1 dB over the -1 dBTP limit; add_music_bed.sh now aims at -1.5')
        else:
            check.true(f'{name}: {got["integrated_lufs"]} LUFS fails (target -14)', not got['loudness_passes'],
                       recorded='logs 27 and 29 (-17 and -17.7; log 32\'s helper found -17.7 faint on a phone)', proves='the gate fails what the project found too quiet')

    # 3. alignment: the delivered film, and the 5 ms of lesson 15
    narration = CH2_NARRATION
    if CH2_FILMS and os.path.exists(CH2_MIX):
        got = json.loads(gate('alignment', CH2_FILMS[-1], CH2_MIX, CH2_TIMELINE).stdout)
        check.true(f'the delivered film against its mix: largest offset {got["largest_offset_ms"]} ms', got['passes'] and got['largest_offset_ms'] == 0,
                   recorded='logs 13, 19, 20 (0.00 ms at every page)', proves='repeats the record with the same sum (check_sound_alignment.py)')
    late = os.path.join(WORK, 'late.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', new_wav, '-af', 'alimiter=limit=0.84:attack=5:release=60:level=disabled', late], check=True)
    got = json.loads(gate('alignment', late, narration, CH2_TIMELINE).stdout)
    check.true(f'a limiter without latency=1 makes the mix {got["largest_offset_ms"]} ms late against the narration: fails',
               not got['passes'] and 4.5 <= got['largest_offset_ms'] <= 5.5, recorded='lesson 15 (5 ms late; 0.00 ms after latency=1)',
               proves='the mix script\'s new alignment gate (against the narration) catches it')
    got = json.loads(gate('alignment', new_wav, narration, CH2_TIMELINE).stdout)
    check.true(f'the plugin\'s mix against the narration: {got["largest_offset_ms"]} ms', got['passes'], recorded='lesson 15')

    # 4. the music under the voice: chapter 1 (where it was measured) and chapter 2 (hold-out)
    stems = {}
    ch1_narration = None
    if os.path.isdir(CH1_RECORDINGS):
        build = os.path.join(WORK, 'ch1')
        os.makedirs(os.path.join(build, 'downloads', 'malina', 'chapter1-steady-accent'))
        for page in range(1, 11):
            os.symlink(os.path.join(CH1_RECORDINGS, f'page{page}.mp3'), os.path.join(build, 'downloads', 'malina', 'chapter1-steady-accent', f'page{page}.mp3'))
        ch1_narration, ch1_timeline = os.path.join(build, 'narration.wav'), os.path.join(build, 'timeline.json')
        subprocess.run([sys.executable, '-I', os.path.join(TOOLS, 'assemble_chapter_narration.py'), CH1_WORD_TIMES, ch1_narration, ch1_timeline,
                        '--pauses', '1.7,1.4,1.1,1.5,1.5,1.3,1.5,1.4,1.6'], cwd=build, check=True, capture_output=True)
        rebuilt = json.load(open(ch1_timeline))
        check.close('chapter 1\'s narration rebuilt from its recordings: peak', rebuilt['narration_peak'], 1.008, 0.0005,
                    recorded='examples/austerity-chapter-1/timeline.json (narration_peak 1.008)', proves='the same track the music was measured against')
    for name, track, timeline_path in (('chapter 1', ch1_narration, ch1_narration and ch1_timeline), ('chapter 2', CH2_NARRATION, CH2_TIMELINE)):
        if not track:
            check.note(f'{name}: recordings not found (chapter 1\'s are in the working files: FILM_WORKING_FILES), not measured')
            continue
        for level in (-14, -11):
            folder = os.path.join(WORK, f'stems-{name[-1]}{level}')
            gates.render_stems(SOUNDTRACK, track, level, folder)
            stems[(name, level)] = gates.music_gaps(os.path.join(folder, 'voice.wav'), os.path.join(folder, 'music.wav'), json.load(open(timeline_path)), settings)
            shutil.rmtree(folder)
    if ('chapter 1', -11) in stems:
        check.close('chapter 1 at music level -14: dB under while she speaks', stems[('chapter 1', -14)]['gap_while_speaking_db'], 21, 1,
                    recorded='decision 12 (about 21 before the user asked for it slightly louder)',
                    proves='only that the measure was chosen well: it was picked from three because it gives these figures')
        check.close('chapter 1 at -11: dB under while she speaks', stems[('chapter 1', -11)]['gap_while_speaking_db'], 18, 1,
                    recorded='decision 12 and log 10 (about 18)', proves='as above (chosen to match)')
        check.close('chapter 1 at -11: dB under in pauses of 0.5 s or more', stems[('chapter 1', -11)]['gap_in_pauses_db'], 12, 1,
                    recorded='logs 07 and 10 (about 12 in pauses)', proves='as above (chosen to match)')
    check.close('chapter 2 at -11: dB under while she speaks', stems[('chapter 2', -11)]['gap_while_speaking_db'], 18, 1,
                recorded='chapter 2 shipped at -11 (logs 19-20); its gap was never measured', proves='the hold-out: the same measure on another narration')
    check.close('chapter 2: the gap moves 3 dB when the level moves 3 dB', stems[('chapter 2', -14)]['gap_while_speaking_db'] - stems[('chapter 2', -11)]['gap_while_speaking_db'],
                3.0, 0.3, proves='the loop can step straight to the level (the voice drives the ducking, so the gap is linear in the level: skeptic log 35)')
    for name, track, timeline_path in (('chapter 1', ch1_narration, ch1_narration and ch1_timeline), ('chapter 2', CH2_NARRATION, CH2_TIMELINE)):
        if not track:
            continue
        got = json.loads(gate('duck', SOUNDTRACK, track, timeline_path, '--music-level', '-14').stdout)
        check.true(f'{name}: the loop from -14 finds MUSIC_LEVEL_DB {got["music_level_db"]} in {len(got["passes"])} passes (by hand: -11)',
                   got['found'] and abs(got['music_level_db'] + 11) <= 0.6 and len(got['passes']) <= 3,
                   recorded='decision 12 (-14 to -11, found by trying four settings in logs 04-10)', proves='the level is found without hand-searching')
    got = json.loads(gate('duck', SOUNDTRACK, CH2_NARRATION, CH2_TIMELINE, '--louder', '3').stdout)
    check.close('"slightly louder" (--louder 3): the level found', got['music_level_db'], -7.5, 0.6,
                recorded='decision 12 (the user\'s "slightly" was 3 dB)', proves='repeats the 3 dB rule through the loop')

    # 5. voice steadiness
    if os.path.isdir(CH2_RECORDINGS):
        got = json.loads(gate('voice', CH2_WORD_TIMES, '--recordings-from', CH2_RECORDINGS).stdout)
        check.true(f'chapter 2: spread {got["spread_semitones"]} semitones passes and no page is sent back', got['spread_passes'] and not got['rerecord'],
                   recorded='decisions item 20 (2.2 semitones, accepted)', proves='the gate passes the accepted narration (same measure as compare_voice_steadiness.py)')
        raised = [len(p['raised_words']) for p in got['pages']]
        check.note(f'chapter 2 words 5+ semitones over their page: {min(raised)} to {max(raised)} a page, all in an accepted narration, so they are listed, not sent back')
    if os.path.isdir(CH1_RECORDINGS):
        got = json.loads(gate('voice', CH1_WORD_TIMES, '--recordings-from', CH1_RECORDINGS).stdout)
        check.true(f'chapter 1: spread {got["spread_semitones"]} semitones fails; pages {sorted(map(int, got["rerecord"]))} sent back',
                   not got['spread_passes'] and sorted(map(int, got['rerecord'])) == [1, 2, 10],
                   recorded='decisions item 20 (chapter 1 sounded unsteady: 3.0)', proves='the gate fails the narration the project judged unsteady and names its pages')

    # 6. the mouth's levels: fitted on chapter 1 (where -25 and -11 were set by eye), checked on chapter 2
    got = json.loads(gate('mouth', CH2_NARRATION, '--timeline', CH2_TIMELINE).stdout)
    check.close('chapter 2: QUIET from the 25th percentile of voiced slices', got['quiet_db'], -25, 3, recorded='make_mouth_track.py QUIET_DB -25 (lesson 24)',
                proves='a weak hold-out: fitted on chapter 1, same narrator at the same level (the design\'s 40th percentile gave -19.6)')
    check.close('chapter 2: LOUD from the 90th percentile', got['loud_db'], -11, 3, recorded='make_mouth_track.py LOUD_DB -11', proves='the design\'s percentile, unchanged')

    # 7. where to start the music under a 13 s quiet clip
    got = json.loads(gate('music-start', SOUNDTRACK, '--seconds', '13', '--mood', 'quiet').stdout)
    starts = [c['use_start'] for c in got['best'][:3]]
    check.true(f'the 216 s the notice corner uses is among the top three starts ({starts})', any(abs(s - 216) <= 2 for s in starts),
               recorded='log 32 (music from 3 min 36 s, chosen by its loudness)', proves='only repeats: the quiet level and the section snap were tuned on this one case')

    # 8. finish_film.sh and add_music_bed.sh, end to end on small clips
    if os.path.exists(CH2_MASTER):
        silent = os.path.join(WORK, 'silent25.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', CH2_MASTER, '-t', '25', '-map', '0:v', '-vf', 'scale=270:480', '-c:v', 'libx264',
                        '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', silent], check=True)
        mix25 = os.path.join(WORK, 'mix25.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', new_wav, '-t', '25', '-c:a', 'pcm_s24le', mix25], check=True)
        short_timeline = dict(timeline2, pages=[p for p in timeline2['pages'] if p['first_word_at'] < 24])
        timeline25 = os.path.join(WORK, 'timeline25.json')
        json.dump(short_timeline, open(timeline25, 'w'))
        finish = os.path.join(TOOLS, 'finish_film.sh')
        done = run(['bash', finish, silent, mix25, os.path.join(WORK, 'master.mp4'), os.path.join(WORK, 'send.mp4'), '2', timeline25])
        lines = [l for l in done.stdout.splitlines() if l.startswith(('PASS', 'FAIL', 'NOT'))]
        check.true(f'finish_film.sh with a timeline: {len(lines)} gates, all pass, exit 0', done.returncode == 0 and len(lines) >= 6 and all(l.startswith('PASS') for l in lines),
                   details=' | '.join(lines)[:300] + done.stderr[-200:])
        without = run(['bash', finish, silent, mix25, os.path.join(WORK, 'master.mp4'), os.path.join(WORK, 'send.mp4'), '2'])
        check.equal('finish_film.sh without a timeline makes the files but ends with exit 3 (alignment not checked)', without.returncode, 3)
        loud = os.path.join(WORK, 'loud25.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mix25, '-af', 'volume=6dB', '-c:a', 'pcm_f32le', loud], check=True)
        too_loud = run(['bash', finish, silent, loud, os.path.join(WORK, 'master.mp4'), os.path.join(WORK, 'send.mp4'), '2', timeline25])
        check.true('a mix 6 dB too loud stops finish_film.sh at the loudness gate', too_loud.returncode == 1 and 'FAIL  loudness' in too_loud.stdout,
                   details=[l for l in too_loud.stdout.splitlines() if l.startswith('FAIL')][:2])
    clip = os.path.join(WORK, 'grey13.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=gray:s=270x480:r=30:d=13', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', clip], check=True)
    bed = run(['bash', os.path.join(KIT, 'paper-film', 'tools', 'add_music_bed.sh'), clip, SOUNDTRACK, os.path.join(WORK, 'bed.mp4'), '216', '-14', '0.8', '1.5'])
    lines = [l for l in bed.stdout.splitlines() if l.startswith(('PASS', 'FAIL'))]
    check.true('add_music_bed.sh from 216 s: length, loudness and true peak all pass', bed.returncode == 0 and len(lines) == 3 and all(l.startswith('PASS') for l in lines),
               details=' | '.join(lines), recorded='log 32 (the same stretch at -14 measured -13.7 LUFS)', proves='with loudnorm aimed at -1.5 dBTP the encoded peak stays under -1')
    help_run = run([sys.executable, '-I', '-B', os.path.join(TOOLS, 'sound_gates.py'), '--help'])
    check.true('sound_gates.py answers --help and opens with its note', help_run.returncode == 0 and 'usage' in help_run.stdout
               and open(os.path.join(TOOLS, 'sound_gates.py')).read().startswith('"""What this does'))
finally:
    shutil.rmtree(WORK, ignore_errors=True)
check.finish()
