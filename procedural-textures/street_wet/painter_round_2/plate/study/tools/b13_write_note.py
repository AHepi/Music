# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Puts the study's note together: it reads the text parts in work/note_text (the prose, written by hand, with [[PLACEHOLDERS]] where a number or a table belongs), fills the placeholders from the
# study's own measurement files (so no number in the note is typed by hand), and writes "10 Research - sett relief and rubbish for the street.md" in the study folder. Plain Python.
# Run: python3 -I b13_write_note.py
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import b12b_tables as T  # noqa: E402

STUDY = os.path.abspath(os.path.join(HERE, '..'))
WORK = os.path.join(STUDY, 'work')
PARTS = os.path.join(WORK, 'note_text')
OUT = os.path.join(STUDY, '10 Research - sett relief and rubbish for the street.md')


def read(path, default=''):
    return open(path).read().rstrip('\n') if os.path.exists(path) else default


def load(folder, name='measurements.json'):
    p = os.path.join(WORK, folder, name)
    return json.load(open(p)) if os.path.exists(p) else {}


values = {}
r1, r7 = load('r01'), load('r07')
values['A_dry_main'] = f"{r1['main_A_dry']['road_mean']:.3f}"
values['C_dry_main'] = f"{r1['main_C_dry']['road_mean']:.3f}"
values['D_dry_main'] = f"{r1['main_D_dry']['road_mean']:.3f}"
values['E_dry_main'] = f"{r1['main_E_dry']['road_mean']:.3f}"
values['B_dry_lockout'] = f"{r1['lockout_A_dry']['road_mean']:.3f}"

tables = {name: getattr(T, name)() for name in ('diagnosis_table', 'diagnosis_main_table', 'baseline_table', 'solutions_close_table', 'solutions_main_table')}


def fence(text):
    return '```\n' + text.strip('\n') + '\n```'


values['REPORT_BASELINE'] = fence(read(os.path.join(WORK, 'logs', 'full_baseline_report_nopuddle.txt'), 'REPORT MISSING'))
values['REPORT_MILD1'] = fence(read(os.path.join(WORK, 'logs', 'full_mild1_report_nopuddle.txt'), 'REPORT MISSING'))
values['REPORT_QUICK_SELFTEST'] = fence(read(os.path.join(WORK, 'r13', 'report.txt'), 'REPORT MISSING'))
values['PUDDLE_SENTENCE'] = read(os.path.join(PARTS, 'puddle_sentence.txt'), 'PUDDLE SENTENCE MISSING')
for name in ('QUICK_BASE_RESULT', 'QUICK_MILD1_RESULT', 'SOL4_TEXT', 'HYBRID_PASS_SENTENCE', 'PIECES_COUNT_SENTENCE', 'QUICK_SCRIPT_SENTENCE'):
    values[name] = read(os.path.join(PARTS, name.lower() + '.txt'), name + ' MISSING')

order = ['00_head.md', '01_short_answer.md', '02_method.md', '03_diagnosis.md', '04_research_setts.md', '05_solutions.md', '06_lighting_test_set.md', '07a_rubbish_facts.md',
         '07b_rubbish_methods.md', '08_plan.md', '09_tested.md', '10_files.md']
text = '\n\n'.join(read(os.path.join(PARTS, f)) for f in order if os.path.exists(os.path.join(PARTS, f)))
for name, table in tables.items():
    text = text.replace(f'[[TABLE:{name}]]', table)
for name, value in values.items():
    text = text.replace(f'[[{name}]]', value)
left = sorted(set(re.findall(r'\[\[[^\]]+\]\]', text)))
open(OUT, 'w').write(text + '\n')
print('wrote', OUT, len(text.splitlines()), 'lines')
print('placeholders left:', left)
