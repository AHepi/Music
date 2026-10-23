"""What this does: tests preflight.py (the stage runner behind bin/explainer-film-preflight) on the small fixtures that ship
with the plugin, so it runs on any machine with the plugin alone. It checks that each stage runs the calculators that
apply and reports their findings, that a known and accepted problem stops blocking only when it says who accepted it and
when, that a missing input stops the stage (exit 2) and names the file to make and the tool that makes it, that the
film stage needs a critique newer than every page file and a passed pages report, that --gate answers from the newest
report and closes when an input changes, and that a report whose inputs change while it runs is marked stale.
Run: python3 kit/calculators/tests/test_preflight.py   (about half a minute; the pages and film parts need node)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402

import preflight  # noqa: E402
from preflight import slug  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
PREFLIGHT = os.path.join(CALCULATORS, 'preflight.py')
WRAPPER = os.path.join(os.path.dirname(KIT), 'bin', 'explainer-film-preflight')
check = Checker('preflight: stages, accepted problems, missing inputs, the critique and the gate')
work = tempfile.mkdtemp(prefix='preflight-test-')


def run(*arguments, timeout=600):
    """Runs the preflight; returns (exit code, plain output, the report's JSON or {})."""
    done = subprocess.run([sys.executable, '-B', PREFLIGHT] + [str(a) for a in arguments], capture_output=True, text=True, timeout=timeout)
    reports = os.path.join(work, 'preflight-reports')
    stage = arguments[0]
    newest = preflight.newest_report(reports, stage) if os.path.isdir(reports) else None
    data = json.load(open(newest)) if newest and os.path.getmtime(newest) >= time.time() - timeout else {}
    return done.returncode, done.stdout + done.stderr, data


try:
    # ------------------------------------------------------------------------------------------------ list and example
    code, out, _ = run('script', '--list')
    check.true('--list names every stage and each input\'s maker', code == 0 and all(f'{s}:' in out for s in preflight.STAGES) and out.count('made by:') >= 40,
               details=f'exit {code}, {out.count("made by:")} makers listed', proves='a model can ask the preflight what each stage needs')
    code, out, _ = run('script', '--example-plan')
    plan = json.loads(out)
    check.true('--example-plan is a plan with every stage', all(s in plan for s in preflight.STAGES) and 'accepted' in plan, details=', '.join(plan))
    if os.path.exists(WRAPPER):
        wrapped = subprocess.run([WRAPPER, '--list'], capture_output=True, text=True, timeout=60)
        check.true('the wrapper bin/explainer-film-preflight runs the plugin kit\'s preflight', wrapped.returncode == 0 and 'script:' in wrapped.stdout,
                   details=f'exit {wrapped.returncode}')

    # ------------------------------------------------------------------------------------------------ script
    script = os.path.join(FIXTURES, 'script', 'newcomer-narration-script.json')
    word_times = os.path.join(KIT, 'examples', 'inflation-chapter-2', 'word-times.json')
    ledger = os.path.join(FIXTURES, 'budget', 'spend-ledger-logs-10-to-34.json')
    code, out, data = run('script', '--project', work, '--script', script, '--word-times', word_times, '--spend-ledger', ledger)
    fails = [f for c in data.get('checks', []) for f in c['findings'] if f['verdict'] == 'fail']
    check.true('script: the newcomer script is stopped only for its missing key page (exit 1)', code == 1 and len(fails) == 1 and 'key' in fails[0]['text'],
               details=out.splitlines()[0] if out else 'no output',
               recorded='test_lint_script.py: the newcomer script\'s only error is the missing key mark',
               proves='the stage runs lint_script.py before and blocks the paid recording on its error')
    check.true('script: the first lines say FAIL and block the paid step with its price', out.startswith('Preflight script (before recording the narration): FAIL')
               and 'Paid step BLOCKED' in out.splitlines()[1] and 'US$1.10' in out.splitlines()[1], details=' / '.join(out.splitlines()[:2]))
    check.close('script: the voice costs US$1.10 (6,287 credits)', data.get('cost_dollars'), 1.10, 0.005,
                recorded='test_plan_budget.py: credits 6,287, US$1.10 (counted by text length)', proves='only repeats lint_script.py\'s price')
    check.true('script: the allowance left is read from the spend ledger (US$19.15 of "full redesign", the step fits)',
               (data.get('allowance') or {}).get('left_dollars') == 19.15 and data['allowance']['fits'], details=json.dumps(data.get('allowance')),
               recorded='test_plan_budget.py: the US$20 allowance spent 0.85', proves='only repeats plan_budget.py ledger')
    timeline = os.path.join(data.get('work_folder', ''), 'estimated-timeline.json')
    check.true('script: the estimated timeline is kept next to the report', os.path.exists(timeline) and data['times'][0]['seconds'] > 300,
               details=json.dumps(data.get('times')))
    check.true('script: the report hashes its inputs (the script, word times, ledger and film-settings.json) and names each tool\'s version',
               len(data.get('inputs', {})) == 4 and any(p.endswith('film-settings.json') for p in data.get('inputs', {}))
               and all(len(c['version']) == 8 for c in data.get('checks', [])), details=json.dumps(list(data.get('inputs', {}))))
    accepted = os.path.join(work, 'accepted.json')
    json.dump([{'stage': 'script', 'check': 'key page', 'reason': 'test: the key page is marked later', 'who': 'the test', 'date': '2026-10-16'}],
              open(accepted, 'w'))
    code, out, data = run('script', '--project', work, '--script', script, '--word-times', word_times, '--accepted', accepted)
    check.true('script: with the key page accepted (who and date given) it passes, listing it as known', code == 0 and data['counts']['known'] == 1
               and data['counts']['fail'] == 0 and 'Known and accepted' in out, details=out.splitlines()[0])
    json.dump([{'stage': 'script', 'check': 'key page', 'reason': 'unsigned'}], open(accepted, 'w'))
    code, out, data = run('script', '--project', work, '--script', script, '--word-times', word_times, '--accepted', accepted)
    check.true('script: an accepted entry without who and date is not used (still exit 1, with a note)', code == 1 and data['counts']['known'] == 0
               and any('NOT used' in n and '"who"' in n for n in data.get('notes', [])), details=out.splitlines()[0])
    # the adversarial tester's holes (log 35): one loose entry must never open a paid step
    for label, entry in (('a one-letter "check" with "whenever" as its date', {'check': 'e', 'who': 'x', 'date': 'whenever'}),
                         ('a date after today', {'stage': 'script', 'check': 'key page', 'reason': 'test', 'who': 'the test', 'date': '2999-01-01'}),
                         ('no stage', {'check': 'key page', 'reason': 'test', 'who': 'the test', 'date': '2026-10-15'}),
                         ('no reason', {'stage': 'script', 'check': 'key page', 'who': 'the test', 'date': '2026-10-15'}),
                         ('a check that is only part of the name ("key")', {'stage': 'script', 'check': 'key', 'reason': 'test', 'who': 'the test', 'date': '2026-10-15'}),
                         ('a text of two letters and no check ("pa")', {'stage': 'script', 'text': 'pa', 'reason': 'test', 'who': 'the test', 'date': '2026-10-15'}),
                         ('a text that is only part of a word ("mark")', {'stage': 'script', 'check': 'key page', 'text': 'mar', 'reason': 'test', 'who': 'the test', 'date': '2026-10-15'})):
        json.dump([entry], open(accepted, 'w'))
        code, out, data = run('script', '--project', work, '--script', script, '--word-times', word_times, '--accepted', accepted)
        check.true(f'script: an accepted entry with {label} opens nothing (exit 1, the key page still to fix)', code == 1
                   and data['counts']['known'] == 0 and data['counts']['fail'] == 1, details=out.splitlines()[0])
    json.dump([{'stage': 'script', 'check': 'speed', 'reason': 'test: all speeds', 'who': 'the test', 'date': '2026-10-15'},
               {'stage': 'script', 'check': 'Key-Page', 'reason': 'test', 'who': 'the test', 'date': '2026-10-15'}], open(accepted, 'w'))
    code, out, data = run('script', '--project', work, '--script', script, '--word-times', word_times, '--accepted', accepted)
    broad = [m for m in data.get('missing', []) if m.get('unusable') and m['input'] == 'accepted']
    check.true('script: an entry that matches 5 findings (more than film-settings.json preflight.accepted_entry_most_findings, 3) stops the stage '
               '(exit 2); "Key-Page" still matches "key page" exactly', code == 2 and len(broad) == 1 and 'matches 5 findings' in broad[0]['unusable']
               and data['counts']['known'] == 1 and any('matched 5 finding(s)' in n for n in data.get('notes', [])),
               details=out.splitlines()[0], proves='a broad acceptance cannot wave a paid step through; each entry\'s count is listed')
    broken = os.path.join(work, 'broken.json')
    open(broken, 'w').write('{not json')
    code, out, data = run('script', '--project', work, '--script', script, '--word-times', word_times, '--accepted', broken)
    check.true('script: a broken accepted file stops the stage with a plain line (exit 2), not a Python error', code == 2 and 'Traceback' not in out
               and 'not valid JSON' in out, details=out.splitlines()[0])
    code, out, data = run('script', '--project', work, '--script', broken)
    check.true('script: a broken script file is "given but it cannot be used" (exit 2), not a Python error', code == 2 and 'Traceback' not in out
               and 'cannot be used' in out and 'not valid JSON' in out, details=out.splitlines()[0])

    # ------------------------------------------------------------------------------------------------ missing inputs
    code, out, data = run('plates', '--project', work)
    missing = [m['input'] for m in data.get('missing', []) if m['required']]
    check.true('plates with nothing given: exit 2, naming the check file, plate, plate facts, render log and shot report, each with its maker',
               code == 2 and missing == ['check', 'plate', 'plate_facts', 'render_log', 'shot_report'] and out.count('Make it:') >= 5
               and 'INPUTS MISSING' in out.splitlines()[0], details=f'exit {code}; missing {missing}',
               proves='a stage without its inputs says exactly which file to make and which tool makes it')
    code, out, data = run('script', '--project', work, '--script', os.path.join(work, 'no-such-script.json'))
    check.true('a named input that is not there is reported as given but not found (exit 2)', code == 2
               and data['missing'][0]['given_but_absent'] == [os.path.join(work, 'no-such-script.json')], details=out.splitlines()[0])

    # ------------------------------------------------------------------------------------------------ shots
    works = os.path.join(FIXTURES, 'works', 'works-place-facts.json')
    code, out, data = run('shots', '--project', work, '--place-facts', works, '--shot-list', os.path.join(FIXTURES, 'shot-planner', 'works-shots.json'),
                          '--shot', 'w1', 'w3', '--views', 'w1', 'w3', '--check-files', f'w1={os.path.join(FIXTURES, "works", "works-w1-shot-check.json")}')
    tools = [os.path.basename(c['tool']) for c in data.get('checks', [])]
    check.true('shots: the Works run place_facts, plan_shot, view_audit, plan_effects wind and plan_lights for each view',
               tools[:4] == ['place_facts.py', 'plan_shot.py', 'view_audit.py', 'plan_effects.py'] and tools.count('plan_lights.py') == 2,
               details=', '.join(tools))
    shot_fails = [f for c in data.get('checks', []) if c['tool'].endswith('plan_shot.py') for f in c['findings'] if f['verdict'] == 'fail']
    audit_fails = [f['text'] for c in data.get('checks', []) if c['tool'].endswith('view_audit.py') for f in c['findings'] if f['verdict'] == 'fail']
    check.true('shots: round 5\'s W1 and W3 pass the shot planner; the letters too small in W3 (the overview) fail in view_audit', not shot_fails
               and audit_fails and all(' in w3 ' in t for t in audit_fails), details=f'{len(audit_fails)} letter faults, all in w3',
               recorded='test_plan_shot.py (W1 and W3 as built); test_view_audit.py (PETROL in W3 far under 20 px)')
    check.true('shots: a check file without "kind_of_shot" is flagged to look at', any(f['check'] == 'kind_of_shot' for c in data['checks'] for f in c['findings']
                                                                                   if f['verdict'] == 'warn'), details='works-w1-shot-check.json')
    checkout = os.path.join(FIXTURES, 'checkout-c1', 'checkout-c1-place-facts.json')
    code, out, data = run('shots', '--project', work, '--place-facts', checkout, '--shot-list', os.path.join(FIXTURES, 'shot-planner', 'checkout-c1-shots.json'))
    slide = [f for c in data.get('checks', []) for f in c['findings'] if f['verdict'] == 'fail' and f['check'] == 'slide_magnification']
    check.true('shots: checkout C1\'s 0.7 m slide fails (1.317 times nearer against 1.286), the hold-out finding', code == 1 and len(slide) == 1
               and '1.317' in slide[0]['text'], details=slide[0]['text'][:160] if slide else out.splitlines()[0],
               recorded='test_plan_shot.py: the slide is 1.317 times nearer and fails; the longest safe slide 0.63 m')
    notice = os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json')
    code, out, data = run('shots', '--project', work, '--place-facts', notice)
    check.true('shots: the notice corner\'s accepted list is shown as known (4 entries, signed), and its slide is known, not failed',
               len(data.get('known_lists', [])) == 4 and all(k['signed'] for k in data['known_lists'])
               and any(f['verdict'] == 'known' and f['check'] == 'slide_magnification' for c in data['checks'] for f in c['findings']),
               details=out.splitlines()[0], recorded='notice-corner-place-facts.json accepted (decision 38: the user kept the shot)')
    worse_facts = json.load(open(notice))
    for entry in worse_facts['accepted']:
        if entry['rule'] == 'slide_magnification':
            entry['measured'] = 1.30          # accepted at 1.30; the slide now measures 1.4856: worse than accepted
    worse_path = os.path.join(work, 'notice-worse-place-facts.json')
    json.dump(worse_facts, open(worse_path, 'w'))
    json.dump([{'stage': 'shots', 'check': 'slide_magnification', 'reason': 'test: the user kept it', 'who': 'the test', 'date': '2026-10-14'}],
              open(accepted, 'w'))
    code, out, data = run('shots', '--project', work, '--place-facts', worse_path, '--accepted', accepted)
    slide = [f for c in data.get('checks', []) for f in c['findings'] if f['check'] == 'slide_magnification']
    check.true('shots: a slide grown worse than it was accepted at stays a failure even with an accepted entry for it (the entry never '
               'turns a "worse" finding back into known)', code == 1 and slide and all(f['verdict'] == 'fail' for f in slide),
               details=' / '.join(f'{f["verdict"]}: {f["text"][:80]}' for f in slide), recorded='tester log 35: worse/acc.json moved it to known')
    json.dump([{'stage': 'shots', 'check': 'slide_magnification', 'reason': 'test', 'who': 'the test', 'date': '2026-10-14', 'measured': 1.40}],
              open(accepted, 'w'))
    code, out, data = run('shots', '--project', work, '--place-facts', checkout, '--shot-list', os.path.join(FIXTURES, 'shot-planner', 'checkout-c1-shots.json'),
                          '--accepted', accepted)
    slide = [f for c in data.get('checks', []) for f in c['findings'] if f['check'] == 'slide_magnification']
    check.true('shots: an accepted entry with "measured" 1.40 makes checkout C1\'s slide (1.317) known', slide and slide[0]['verdict'] == 'known',
               details=' / '.join(f'{f["verdict"]}: {f["text"][:80]}' for f in slide))
    json.dump([{'stage': 'shots', 'check': 'slide_magnification', 'reason': 'test', 'who': 'the test', 'date': '2026-10-14', 'measured': 1.20}],
              open(accepted, 'w'))
    code, out, data = run('shots', '--project', work, '--place-facts', checkout, '--shot-list', os.path.join(FIXTURES, 'shot-planner', 'checkout-c1-shots.json'),
                          '--accepted', accepted)
    slide = [f for c in data.get('checks', []) for f in c['findings'] if f['check'] == 'slide_magnification']
    check.true('shots: accepted at 1.20, the slide now measures 1.317: worse than accepted, so it fails again', code == 1 and slide
               and slide[0]['verdict'] == 'fail' and 'worse than accepted' in slide[0]['text'], details=slide[0]['text'][-160:] if slide else out.splitlines()[0])
    # the Works' brazier smoke over man 2 (nested in plan_effects' output) reaches the report as a look
    code, out, data = run('shots', '--project', work, '--place-facts', works, '--shot-list', os.path.join(FIXTURES, 'shot-planner', 'works-shots.json'),
                          '--shot', 'w1', '--views', 'w1')
    smoke = [f for c in data.get('checks', []) if c['tool'].endswith('plan_effects.py') for f in c['findings'] if 'man-2' in f['text']]
    check.true('shots: the brazier smoke crossing man 2 in W1 is shown to look at (it used to be dropped from the report)',
               smoke and all(f['verdict'] == 'warn' for f in smoke), details=smoke[0]['text'][:120] if smoke else 'not in the report',
               recorded='tester log 35: plan_effects wind fire_smoke[1].problems never reached the shots report')
    # a view's page details: W3 serves a page that names only the No. 2 board; the drums are must-read but unnamed there
    plan_path = os.path.join(work, 'shots-plan.json')
    json.dump({'shots': {'place_facts': works, 'views': {'w3': {'named': ['no-2 board'], 'cards': {'lower': [0.06, 0.16, 0.94, 0.2365]}}}}},
              open(plan_path, 'w'))
    code, out, data = run('shots', '--project', work, '--plan', plan_path)
    audit = [c for c in data.get('checks', []) if c['tool'].endswith('view_audit.py')]
    audit_fails = [f['text'] for c in audit for f in c['findings'] if f['verdict'] == 'fail']
    drums = [f for c in audit for f in c['findings'] if 'PETROL' in f['text'] or 'DIESEL' in f['text']]
    wind = [c for c in data.get('checks', []) if c['tool'].endswith('plan_effects.py')]
    check.true('shots: with the page\'s named signs per view, unnamed drum letters in W3 are a look, not a failure; the word card given for W3 '
               'reaches plan_effects wind (its plume under the lower card fails)', audit and not any('PETROL' in t or 'DIESEL' in t for t in audit_fails)
               and drums and all(f['verdict'] == 'warn' for f in drums) and wind and '--card w3:lower=' in wind[0]['command'] and wind[0]['verdict'] == 'fail',
               details=f'{len(audit_fails)} letter failure(s) in w3; drums: {[f["verdict"] for f in drums]}; wind {wind[0]["verdict"] if wind else "not run"}',
               recorded='tester log 35: 7 of the 9 blocking failures were drum and crate letters nobody needs to read')
    open(broken, 'w').write('{not json')
    code, out, data = run('shots', '--project', work, '--place-facts', works, '--views', 'w1', '--check-files', f'w1={broken}')
    check.true('shots: a broken check file is "given but it cannot be used" (exit 2), not a Python error', code == 2 and 'Traceback' not in out,
               details=out.splitlines()[0])

    # ------------------------------------------------------------------------------------------------ plates: what proves a clean render
    plates = os.path.join(work, 'plates')
    os.makedirs(os.path.join(plates, 'facts'), exist_ok=True)
    plate = os.path.join(plates, 'works-w1-plate.png')
    shutil.copy(os.path.join(FIXTURES, 'effects-camera-light', 'busy-2-windows-79.00.png'), plate)    # a small stand-in picture
    empty_log = os.path.join(plates, 'empty.log')
    open(empty_log, 'w').close()
    dummy_report = os.path.join(plates, 'report.md')
    open(dummy_report, 'w').write('# report\n')
    works_log = os.path.join(FIXTURES, 'effects-camera-light', 'render-log-works-plates-round5-excerpt.log')
    plate_args = ['plates', '--project', work, '--check', os.path.join(FIXTURES, 'notice-corner', 'notice-corner-shot-check.json'), '--plate', plate,
                  '--plate-facts', os.path.join(plates, 'facts')]

    def plate_checks(data):
        return {c['title']: c for c in data.get('checks', [])}
    code, out, data = run(*plate_args, '--render-log', empty_log, '--shot-report', dummy_report)
    checks_by = plate_checks(data)
    log_check = checks_by.get('the plate rendered cleanly (plan_lights.py render-log)', {})
    report_check = checks_by.get('the shot checker\'s report: new problems only', {})
    check.true('plates: an empty render log is not a clean render, and a one-line made-up report is not the shot checker\'s (both fail)',
               code == 1 and log_check.get('verdict') == 'fail' and report_check.get('verdict') == 'fail', details=f'log {log_check.get("verdict")}, '
               f'report {report_check.get("verdict")}: ' + ' / '.join(f['text'][:90] for f in report_check.get('findings', [])),
               recorded='tester log 35: both passed as "clean render" and "light rules passed" (decision 37)')
    other_plate = os.path.join(plates, 'people-test-plate.png')
    shutil.copy(plate, other_plate)
    code, out, data = run(*[a if a != plate else other_plate for a in plate_args], '--render-log', works_log, '--shot-report', dummy_report)
    log_check = plate_checks(data).get('the plate rendered cleanly (plan_lights.py render-log)', {})
    check.true('plates: the clean log of another render (it never saves this plate) fails', log_check.get('verdict') == 'fail',
               details=' / '.join(f['text'][:120] for f in log_check.get('findings', []) if f['verdict'] == 'fail'))
    code, out, data = run(*plate_args, '--render-log', works_log, '--shot-report', dummy_report)
    log_check = plate_checks(data).get('the plate rendered cleanly (plan_lights.py render-log)', {})
    price = next((c for c in data.get('costs', [])), {})
    check.true('plates: the round 5 log that saves works-w1-plate.png passes; the price is worked out from the plate\'s own size (300 x 220 here)',
               log_check.get('verdict') == 'pass' and '300 x 220' in price.get('note', ''), details=f'{log_check.get("verdict")}; {price.get("note", "")[-120:]}')
    unsigned_folder = os.path.join(plates, 'unsigned')
    os.makedirs(unsigned_folder, exist_ok=True)
    json.dump({'about': 'check_shot.py: the problems, and the problems known', 'version': 'abcdef12', 'kinds': ['still_life'], 'problems': [],
               'known': [{'rule': 'rule5_subject_brightness_ratio', 'what': 'The subject is only 1.1 times the frame\'s mean (needs 1.8)',
                          'known': {'how': 'accepted', 'words': 'None (None, None)', 'entry': {'rule': 'rule5_subject_brightness_ratio'}}}]},
              open(os.path.join(unsigned_folder, 'known.json'), 'w'))
    found = preflight.shot_report_findings(unsigned_folder)
    check.true('plates: a problem the check file "accepted" without who and when counts as new (fail), not known', found and found[0]['verdict'] == 'fail',
               details=found[0]['text'][:140] if found else 'nothing', recorded='tester log 35: tester/unsigned/known.json came back "known"')
    json.dump({'problems': [], 'known': []}, open(os.path.join(unsigned_folder, 'known.json'), 'w'))
    found = preflight.shot_report_findings(unsigned_folder)
    check.true('plates: a known.json the shot checker did not write fails', found and found[0]['verdict'] == 'fail', details=found[0]['text'][:140] if found else 'nothing')

    # ------------------------------------------------------------------------------------------------ pages, film and the gate
    have_node = shutil.which('node') is not None
    if not have_node:
        check.note('pages and film parts skipped: node is not on this machine')
    else:
        events = os.path.join(work, 'events-pages-3-5.json.gz')
        shutil.copy(os.path.join(FIXTURES, 'page-timing', 'events-pages-3-5.json.gz'), events)
        code, out, data = run('pages', '--project', work, '--events', events)
        lookups = [f for c in data.get('checks', []) for f in c['findings'] if f['verdict'] == 'fail' and f['check'] == 'lookups']
        check.true('pages: pages 3 to 5 fail on 8 lookups without a "which time" and MACHINES readable 0.84 s (exit 1)', code == 1 and len(lookups) == 8
                   and data['counts']['fail'] == 9, details=out.splitlines()[0], recorded='test_plan_page_timing.py (8 lookups; MACHINES 0.84 s)')
        plan = {'pages': {'events': events},
                'accepted': [{'stage': 'pages', 'check': 'lookups', 'text': word, 'page': page, 'reason': 'each takes the right time (test)',
                              'who': 'the test', 'date': '2026-10-16'} for page, word in ((3, 'workers'), (3, 'machines'), (3, 'In'), (3, 'More'),
                                                                                         (5, 'spare'), (5, 'More'), (5, 'prices'), (5, 'up'))]
                + [{'stage': 'pages', 'check': 'readable', 'text': 'MACHINES', 'page': 3, 'reason': 'the cut stays (test)', 'who': 'the test',
                    'date': '2026-10-16'}]}
        plan_path = os.path.join(work, 'preflight-plan.json')
        json.dump(plan, open(plan_path, 'w'))
        code, out, data = run('pages', '--project', work)
        check.true('pages: with those nine accepted in the preflight plan it passes, all nine known', code == 0 and data['counts']['known'] == 9,
                   details=out.splitlines()[0], proves='the plan\'s accepted list reaches plan_page_timing.py and the preflight')
        code, out, _ = run('pages', '--project', work, '--gate')
        check.equal('gate: the passed pages report opens the gate', code, 0)
        pages_folder = os.path.join(work, 'scene')
        os.makedirs(pages_folder)
        for n in (3, 4, 5):
            open(os.path.join(pages_folder, f'page-{n}.js'), 'w').write(f'// page {n}\n')
        critique = os.path.join(work, 'critique.json')
        json.dump({'verdict': {'confirmed': [{'page': '3', 'time': '55.1', 'severity': 'must fix', 'what': 'MACHINES is cut too soon', 'fix': 'start it on "and"',
                                              'evidence': 'still 55.0', 'from': 'pictures'}], 'rejected': [], 'summary': ''}}, open(critique, 'w'))
        film_args = ['film', '--project', work, '--events', events, '--scene', 'inflation-chapter-2-newcomers', '--critique', critique,
                     '--page-files', pages_folder, '--processors', '4', '--free-memory-gb', '8', '--free-disk-gb', '40', '--blender-running', 'no']
        code, out, data = run(*film_args)
        titles = {c['title']: c['verdict'] for c in data.get('checks', [])}
        check.true('film: the critique is newer than the pages but its must-fix finding is open: blocked', code == 1
                   and titles.get('a critique newer than every page file, each finding fixed or accepted') == 'fail', details=out.splitlines()[0])
        check.true('film: the pages report came before the page files were written, so it must run again',
                   titles.get('a passed pages report on these events, newer than every page file') == 'fail', details=json.dumps(titles))
        filming = next((t for t in data.get('times', []) if t['what'] == 'filming'), None)
        check.true('film: the filming time is planned from the events (about 50 min from the table)', filming is not None and 2400 < filming['seconds'] < 3600,
                   details=json.dumps(filming), recorded='plan_budget.py filming on pages 3-5: 50.7 min with one worker (the table, a fallback)')
        json.dump({'verdict': {'confirmed': [{'page': '3', 'time': '55.1', 'severity': 'must fix', 'what': 'MACHINES is cut too soon', 'status': 'fixed'}]}},
                  open(critique, 'w'))
        code, out, data = run(*film_args)
        events_check = [f for c in data.get('checks', []) for f in c['findings'] if f['check'] == 'events newer than the pages']
        check.true('film: events made before the page files were edited are stale: filming is blocked until they are made again',
                   code == 1 and events_check and events_check[0]['verdict'] == 'fail', details=events_check[0]['text'][:140] if events_check else out.splitlines()[0])
        time.sleep(1.1)
        os.utime(events, None)                 # the events made again after the last page edit (the same content)
        run('pages', '--project', work)
        code, out, data = run(*film_args)
        titles = {c['title']: c['verdict'] for c in data.get('checks', [])}
        check.true('film: with the finding fixed, a fresh critique and a fresh passed pages report, filming is ready (exit 0)', code == 0
                   and 'Long step ready: filming the chapter' in out.splitlines()[1], details=' / '.join(out.splitlines()[:2]))
        # the critique-film workflow's own shapes (log 35's holes): an empty file, a hyphenated severity, findings under another key,
        # and a clean result whose critics' raw findings the skeptic rejected
        film_critique = lambda path: [a if a != critique else path for a in film_args]
        cases = (('an empty JSON {}', {}, 2, None),
                 ('findings kept under another key', {'items': [{'page': '3', 'severity': 'must fix', 'what': 'open finding in another key'}]}, 2, None),
                 ('an open "must-fix" (with a hyphen)', {'verdict': {'confirmed': [{'page': '3', 'time': '55', 'severity': 'must-fix', 'what': 'MACHINES unreadable',
                                                                                 'fix': 'x', 'evidence': 'y', 'from': 'z'}], 'rejected': [], 'summary': ''}}, 1, 'fail'),
                 ('an open finding with a severity the workflow never uses', {'verdict': {'confirmed': [{'page': '3', 'severity': 'urgent', 'what': 'x'}]}}, 1, 'fail'),
                 ('a clean result (confirmed: []) whose critics\' raw finding the skeptic rejected',
                  {'critics': [{'key': 'pictures', 'findings': [{'page': '3', 'time': '55', 'severity': 'must fix', 'what': 'a raw critic finding the skeptic rejected'}]}],
                   'verdict': {'confirmed': [], 'rejected': [{'what': 'a raw critic finding the skeptic rejected', 'reason': 'wrong'}], 'summary': 'nothing to fix'}}, 0, 'pass'))
        for label, content, wanted, verdict in cases:
            path = os.path.join(work, f'critique-{slug(label)}.json')
            json.dump(content, open(path, 'w'))
            code, out, data = run(*film_critique(path))
            titles = {c['title']: c['verdict'] for c in data.get('checks', [])}
            got = titles.get('a critique newer than every page file, each finding fixed or accepted')
            check.true(f'film: a critique with {label}: exit {wanted}' + (f', the critique check {verdict}' if verdict else ' ("not a critique-film result")'),
                       code == wanted and (verdict is None and 'not a critique-film result' in out or got == verdict), details=out.splitlines()[0])
        other_events = os.path.join(work, 'events-test-clean.json.gz')
        shutil.copy(os.path.join(FIXTURES, 'page-timing', 'events-test-clean.json.gz'), other_events)
        code, out, data = run(*[a if a != events else other_events for a in film_args])
        report_check = [f for c in data.get('checks', []) for f in c['findings'] if f['check'] == 'pages report on these events']
        check.true('film: a passed pages report made on OTHER events does not count: filming these events is blocked', code == 1 and report_check
                   and report_check[0]['verdict'] == 'fail', details=report_check[0]['text'][:140] if report_check else out.splitlines()[0],
                   recorded='tester log 35: filmtest2 filmed events-pages-3-5 on a report about events-test-clean')
        code, out, _ = run('pages', '--project', work, '--gate', '--events', other_events)
        check.true('gate: the pages gate stays closed for events the newest report was not made on', code == 1 and 'not made on' in out, details=out.strip())
        code, out, _ = run('pages', '--project', work, '--gate')
        check.equal('gate: the newest pages report (on the plan\'s events) still opens the gate', code, 0)
        plan_data = json.load(open(os.path.join(work, 'preflight-plan.json')))
        plan_data['accepted'] = plan_data['accepted'][:-1]          # one acceptance withdrawn
        json.dump(plan_data, open(os.path.join(work, 'preflight-plan.json'), 'w'))
        code, out, _ = run('pages', '--project', work, '--gate')
        check.true('gate: withdrawing an acceptance from the plan closes the gate (the plan is an input)', code == 1 and 'preflight-plan.json' in out, details=out.strip())
        os.utime(critique, (time.time() - 3600, time.time() - 3600))
        code, out, data = run(*film_args)
        check.true('film: a critique older than a page file blocks filming', code == 1 and any('older than' in f['text'] for c in data['checks'] for f in c['findings']),
                   details=out.splitlines()[0], proves='the critique must be newer than every page file')
        with open(events, 'ab') as handle:
            handle.write(b'\n')
        code, out, _ = run('pages', '--project', work, '--gate')
        check.true('gate: an input changed since the newest pages report closes the gate', code == 1 and 'changed' in out, details=out.strip())

    # ------------------------------------------------------------------------------------------------ stale and readers
    args = preflight.build_parser().parse_args(['script', '--project', work])
    trial = preflight.Run('script', args, {}, work)
    changing = os.path.join(work, 'changing.txt')
    open(changing, 'w').write('one')
    trial.register(changing)
    open(changing, 'w').write('two')
    summary = preflight.summarise(trial, dict(trial.input_paths), trial.hash_inputs())
    check.true('an input that changes while the stage runs makes the report STALE (blocked)', summary['verdict'] == 'stale' and summary['blocked'],
               details=json.dumps(summary['changed_inputs']))
    found = preflight.findings_from(None, 'PASS  loudness\nFAIL  true peak: -0.9 dBTP\nLOOK  page 2: listen\n', 1)
    check.equal('plain lines are read as findings when a tool writes no verdicts (sound_gates.py)', [f['verdict'] for f in found], ['pass', 'fail', 'warn'])
    found = preflight.findings_from({'problems': ['a word under 20 px']}, '', 0)
    check.equal('a "problems" list counts as a failure only when the tool exits non-zero', found[0]['verdict'], 'warn')
    found = preflight.findings_from(None, '8100 frames at 30 a second\nJUMP       12.37 s  change 41.2 (9.8 times the neighbours)\nplanned cut  20.10 s  change 60.1\n', 0)
    check.true('a jump outside the planned cuts (find_jumps.py\'s JUMP line) is a look for a person, not a block', [f['verdict'] for f in found] == ['warn'],
               details=json.dumps(found)[:200], recorded='tester log 35: the delivered, accepted film 20 showed 46 such jumps (its own moves and fades)')
    code, out, _ = run('script', '--list')
    check.true('--list names the film stage\'s scene (it is required)', '(r) --scene' in out.split('film:')[1].split('finish:')[0], details='film: ... --scene')
    code, out, _ = run('script', '--project', work, '--kit', os.path.join(work, 'no-such-kit'), '--script', script)
    check.true('a kit folder that is not there stops with exit 2 and a plain line', code == 2 and 'not a kit folder' in out, details=out.strip()[:160])
    timeline_broken = os.path.join(work, 'timeline-broken.json')
    open(timeline_broken, 'w').write('{not json')
    film_file = os.path.join(work, 'film.mp4')
    open(film_file, 'w').close()
    code, out, _ = run('finish', '--project', work, '--film', film_file, '--mix', film_file, '--timeline', timeline_broken)
    check.true('finish: a broken timeline is "given but it cannot be used" (exit 2), not a Python error', code == 2 and 'Traceback' not in out
               and 'not valid JSON' in out, details=out.splitlines()[0])
    found = preflight.findings_from(None, 'Traceback (most recent call last):\nKeyError: step', 1)
    check.true('a tool that stops with an error is a failure that says so', found[-1]['verdict'] == 'fail' and 'stopped with an error' in found[-1]['text'],
               details=found[-1]['text'])
finally:
    shutil.rmtree(work, ignore_errors=True)
check.finish()
