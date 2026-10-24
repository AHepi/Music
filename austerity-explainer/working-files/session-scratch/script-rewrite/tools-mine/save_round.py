# What this does: turns a script-rewrite workflow's results (judges' verdicts, testers' findings, a
# fixer's notes) into plain markdown files for the repository, and copies the helpers' files across with
# this session's folder names replaced by SCRATCH, KIT and REPO.
# Use: python3 -I save_round.py round2|round3 OUT_FOLDER
import json, os, re, shutil, sys

SCRATCH = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
S = SCRATCH + '/script-rewrite'
KIT = SCRATCH + '/uploads/pinker-toolkit/Steven-Pinker-Teaching-and-Writing-Toolkit'
REPO = '/home/user/Music'
which, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)


def clean(text):
    return text.replace(KIT, 'KIT').replace(S, 'SCRATCH/script-rewrite').replace(SCRATCH, 'SCRATCH').replace(REPO, 'REPO')


def write(name, text):
    open(os.path.join(out, name), 'w').write(clean(text).rstrip() + '\n')


def findings_md(title, tested):
    lines = [f'# {title}', '', 'Source: Clara E. Mattei, *The Capital Order* (2022).', '']
    for t in tested:
        lines += [f'## {t["key"]}', '', t.get('summary', '(no result)'), '']
        for i, f in enumerate(t.get('findings', []), 1):
            lines += [f'{i}. **{f["severity"]}, page {f["page"]}:** "{f["quote"]}"',
                      f'   - Problem: {f["problem"]}', f'   - Suggested fix: {f["fix"]}']
        if t.get('not_checked'):
            lines += ['', f'**Not checked:** {t["not_checked"]}']
        lines += ['']
    return '\n'.join(lines)


def copy(src, name):
    if os.path.exists(src):
        write(name, open(src).read())


if which == 'round2':
    d = json.load(open(S + '/round2-result.json'))
    lines = ['# 06 Judges - three newcomer drafts of chapter 2', '',
             'Source: Clara E. Mattei, *The Capital Order* (2022).', '',
             'Three judges, each with one lens, scored the three drafts in "05 Three drafts" (first round) from 0 to 10.', '']
    for j in d['judged']:
        lines += [f'## {j["key"]}', '', j['summary'], '', '| Draft | Score |', '|---|---|']
        lines += [f'| {s["draft"]} | {s["score"]} |' for s in j['scores']]
        lines += ['']
        for s in j['scores']:
            lines += [f'### {s["draft"]}: strengths', '', s['strengths'], '', f'### {s["draft"]}: faults', '', s['faults'], '']
        lines += ['### Best parts to keep', '', j['best_parts_to_keep'], '', '### Must fix', '', j['must_fix'], '']
    write('06 Judges - three newcomer drafts.md', '\n'.join(lines))
    copy(S + '/work-combine/combined.md', '07 Combined script - the best draft with the best of the others.md')
    write('08 Test findings on the combined script.md',
          findings_md('08 Test findings on the combined script', d['tested']))
    copy(S + '/work-revise/final.md', '09 Revised script after testing.md')
    for tool in ('count_and_time.py', 'sound_scan.py'):
        copy(S + '/work-revise/tools/' + tool, tool)
elif which == 'round3':
    d = json.load(open(S + '/round3-result.json'))
    write('10 Final check - findings.md', findings_md('10 Final check - findings on the revised script', d['tested']))
    lines = ['# 11 Final check - what the fixer did, and the re-check', '',
             'Source: Clara E. Mattei, *The Capital Order* (2022).', '',
             '## What the fixer did with each finding', '', (d.get('fixed') or {}).get('fixes_made', '(the fixer failed)'), '']
    v = d.get('verified') or {}
    lines += ['## The re-check of every changed line', '', v.get('summary', '(no re-check)'), '']
    for i, f in enumerate(v.get('findings', []), 1):
        lines += [f'{i}. **{f["severity"]}, page {f["page"]}:** "{f["quote"]}"', f'   - Problem: {f["problem"]}', f'   - Suggested fix: {f["fix"]}']
    if d.get('last'):
        lines += ['', '## The last fix', '', d['last'].get('fixes_made', '')]
    write('11 Final check - fixes and re-check.md', '\n'.join(lines))
print('saved', which, 'to', out)
