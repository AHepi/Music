"""What this does: tests paper-film/tools/check_page_layout.mjs (the slim page pose sampler) on recorded page events: the
small test chapter clean and with its planted faults, chapter 2 for newcomers pages 3 to 5 (round 4's film found only its
planned jumps there), and old chapter 2 (shipped in log 20), where it finds two labels drawn over each other on page 8.
Needs node (skipped without it); no browser. Fixtures: tests/fixtures/page-timing.
Run: python3 kit/calculators/tests/test_check_page_layout.py
"""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES, skip  # noqa: E402

HERE = os.path.join(FIXTURES, 'page-timing')
TOOL = os.path.join(os.path.dirname(CALCULATORS), 'paper-film', 'tools', 'check_page_layout.mjs')
NODE = shutil.which('node')
if not NODE:
    skip('page layout checker', 'node is not installed')
check = Checker('page layout: pops, effects after their moment, held shots, overlaps')


def run(name, *extra):
    done = subprocess.run([NODE, TOOL, os.path.join(HERE, name), '--json', *extra], capture_output=True, text=True, timeout=300)
    try:
        return done.returncode, json.loads(done.stdout)
    except json.JSONDecodeError:
        return done.returncode, {'problems': [], 'verdicts': {}, 'error': done.stderr[-400:]}


def where(result, check_name, verdict='fail'):
    return [p for p in result['problems'] if p['check'] == check_name and p['verdict'] == verdict]


helped = subprocess.run([NODE, TOOL, '--help'], capture_output=True, text=True, timeout=60)
check.true('--help answers with a usage note (house rule)', helped.returncode == 0 and 'Usage' in helped.stdout and 'What this does' in open(TOOL).read()[:40])

code, clean = run('events-test-clean.json.gz')
check.true('the clean test chapter: nothing to fix, exit 0', code == 0 and clean['verdicts'].get('fail') == 0 and clean['verdicts'].get('look') == 0,
           details=json.dumps(clean.get('verdicts')) + clean.get('error', ''))
check.true('the report names the film-settings.json values it used', 'page_timing.layout.pop_frames_max' in clean.get('settings_used', {}))

code, faults = run('events-test-faults.json.gz')
found = {
    'a spark left on from an earlier frame (lesson 29)': [p for p in where(faults, 'effects after their moment') if 'Mesh#2' in p['what']],
    'a held-shot key kept during the slide': where(faults, 'held key during a move'),
    'NO SPARE drawn over the fading question (round 3)': [p for p in where(faults, 'overlaps at events') if 'NO SPARE' in p['what']],
    'an arrow shown for one frame (log 27)': [p for p in where(faults, 'pops') if 'only 1 frame' in p['detail']],
    'a tag jumping across the frame (log 27)': [p for p in where(faults, 'pops') if 'jumps' in p['detail']],
    'a hold with no held-shot key': where(faults, 'hold without a key', 'look'),
}
check.equal('the planted faults each caught', {k: bool(v) for k, v in found.items()}, {k: True for k in found},
            recorded='paper-film/scenes/page-events-test.js ?variant=faults', proves='each check fires on its planted case (plants, not recorded cases)')
check.equal('and nothing else fails on the faults chapter (exit 1)', (code, faults['verdicts'].get('fail')), (1, 5))

code, works = run('events-pages-3-5.json.gz')
check.true('chapter 2 for newcomers, pages 3-5: nothing to fix', code == 0 and works['verdicts'].get('fail') == 0,
           details='; '.join(p['detail'] for p in works['problems'] if p['verdict'] == 'fail'),
           recorded='scratchpad redesign/round4-result.json film.summary: "the only jumps are the planned ones", "NO SPARE never overlaps the question", '
                    '"held shots never move"', proves='agrees with what round 4 found on the filmed pixels (find_jumps.py), from the page code alone')
held = where(works, 'held shots', 'pass')
check.equal('pages 3-5 return a held-shot key on every hold and none while sliding', len(held), 3, recorded='page-3.js and page-4.js: still: sliding ? false : still')
same = [p for p in where(works, 'effects after their moment', 'pass')]
check.true('pages 3-5 come out the same drawn out of order (lesson 29)', bool(same), details=same[0]['detail'] if same else '')

code, old = run('events-old-chapter-2.json.gz')
overlap = [p for p in where(old, 'overlaps at events') if p['page'] == 8 and 'FLAT OUT' in p['what'] and 'PRICES UP' in p['what']]
check.true('old chapter 2, page 8: the PRICES UP label drawn over FLAT OUT', bool(overlap), details=overlap[0]['detail'] if overlap else 'not found',
           recorded='seen in this helper\'s render of 187.70 s (log 35): the PRICES UP plate covers the F of FLAT OUT ("ELAT OUT")',
           proves='a fault in a shipped chapter that no round recorded; confirmed by eye on one rendered frame, not by this test')
holds = where(old, 'hold without a key', 'look')
check.true('old chapter 2 shows holds without held-shot keys (it was made before held shots, log 34)', len(holds) > 20, details=f'{len(holds)} holds')
check.finish()
