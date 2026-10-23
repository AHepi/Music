"""What this does: runs, for one stage of making a film, every calculator and check that applies, and writes one report
in plain words (and the same as JSON) that says pass, look or fail, what to fix first, what is already known and
accepted, the cost of the paid step this stage guards and the time it takes. A failure blocks the paid or long step
that follows (exit 1); a missing input stops the stage with the exact file to make and the tool that makes it (exit 2).
It spends nothing and changes no project file: it only reads, runs the kit's calculators, and writes its reports.

The nine stages, in the order a film is made (the names are fixed; the skills and docs name them):
  script   before recording the narration   lint_script.py before (cues, capitals, sentences, figures a minute, the
                                            main rule twice, key page, out-of-date facts), the estimated timeline, the
                                            voice's credits and dollars, and the spend ledger
  record   after recording                  lint_script.py after (a cue read aloud, words and names heard wrongly,
                                            silences, late words) and sound_gates.py voice (pages to record again)
  shots    before building or drawing a     place_facts.py check, plan_shot.py (camera, reach, slide, people, signs),
           place's views                    view_audit.py (letters, loud signs, heads, landmarks), plan_effects.py wind,
                                            plan_lights.py plan, plan_states.py plan, and each view's check file
  place    after the place is built, before place_audit_check.py check (every material and object has its surface
           its views are drawn              and wear treatments, real normal maps that point the right way, displacement,
                                            believable construction, sizes, plants off the wheel tracks; the audit is of
                                            THIS scene file), picture_measures.py check (with a style guard), and a fresh
                                            checker's result; the order is shots, build the place, place, then plates
  plates   before paying for paintings      plan_lights.py render-log, the shot checker's report (new problems only),
                                            paint_request.py preflight and price, model_lint.py, the spend ledger
  paint    after each painting arrives      after_painting.py check (line-up, figures, skin, style, behind painting)
  pages    while building pages             plan_page_timing.py check, check_page_layout.mjs, camera_audit.py,
                                            plan_effects.py lint (from page_events.mjs's events)
  film     before filming                   a critique newer than every page file with each finding fixed or accepted
                                            and a critic whose area starts with "history" (period accuracy of what is
                                            seen), a passed pages report newer than every page file, plan_budget.py filming
  finish   after finishing                  a clip critique newer than the film (a fresh helper judged the FILMED clip in
                                            motion: the film-critic agent's clip mode), sound_gates.py loudness, length
                                            and alignment, find_jumps.py with the planned cuts (when the memory allows:
                                            about 10 bytes a pixel of every frame at 270 x 480), plan_budget.py push
The plates stage also reads each plate's render record (PLATE.json beside the picture, written by explainer-film-place
render): a LOOK when plates of one place were drawn with different engines (EEVEE streets came out cold blue and Cycles
streets warm gold, and the painter follows the plate), and a LOOK for a Cycles plate, because the painting checks were
tuned on EEVEE plates. The paint stage passes the page's look.toe ("toe" in the plan) to after_painting.py --toe.

Known and accepted problems: the project keeps some problems on purpose. Each is written down once, with who accepted
it and when, and is then reported as KNOWN instead of failing every run:
  - a view's check file "accepted" list and a place facts file's "accepted" list (shown in the shots, plates and paint
    reports; the shot checker and plan_shot.py also read them);
  - the preflight plan's "accepted" list, or --accepted FILE: [{"stage": "pages", "check": "lookups", "text": "workers",
    "page": 3, "reason": "...", "who": "...", "date": "YYYY-MM-DD"}]. An entry is used only when it names its "stage",
    a "reason", "who" accepted it and the "date" (a real day written YYYY-MM-DD, not after today); otherwise it is not
    used and the report says why. "check" must equal the finding's check name (case, "-" and "_" do not matter); "text"
    must appear in the finding as whole words (at least 3 letters when no "check" is given); "page" and "view" narrow it;
    "measured" (the number accepted) makes the finding fail again once it grows past that number. Each entry may match
    only a few findings (film-settings.json preflight.accepted_entry_most_findings): a broader entry stops the stage
    (exit 2), so one loose entry can never wave a paid step through. The report lists how many findings each entry matched.
Only NEW failures block. A known item that has grown worse than it was accepted at fails again (the tools say so, and the
preflight never turns such a finding back into "known").

Inputs come from the command line (one place, view, painting or chapter) or from a preflight plan, a JSON file that
names a film's files once for every stage (default: PROJECT/preflight-plan.json). Paths in a plan are read from the
plan's own folder. Print an example with --example-plan; list each stage's inputs, what each is and which tool makes
it with --list.

Every run hashes its input files at the start and again at the end (a report whose inputs changed while it ran is
marked STALE), names every tool with its version (the first 8 letters of the file's sha1), and keeps each tool's own
JSON and plain output in a folder next to the report. The accepted file, the preflight plan and film-settings.json are
inputs too. --gate answers, without running anything, whether the newest report of a stage passed, was made on the same
inputs this command names (path for path, sha1 for sha1), and whether those inputs and the tools' versions are unchanged
since (for a script about to start a paid or long step).

Use:
  explainer-film-preflight STAGE [--project DIR] [--plan FILE] [inputs ...] [--accepted FILE] [--json]
  explainer-film-preflight STAGE --gate        did the newest report pass, and are its inputs unchanged? (exit 0 / 1)
  explainer-film-preflight --list              every stage's inputs, and which tool makes each
  explainer-film-preflight --example-plan      an example preflight plan
  (or: python3 kit/calculators/preflight.py ...; the wrapper is plugins/explainer-film/bin/explainer-film-preflight)
Reports go to PROJECT/preflight-reports/ (or --reports DIR; for the stage `place` with --place-audit, the preflight-reports folder beside the audit, so a run started from any folder, the plugin's own included, leaves nothing there): preflight-STAGE-DATE-TIME.md, the same as .json, and a
folder of the same name with every tool's output. Exit: 0 pass (perhaps with things to look at), 1 fail (or stale),
2 an input is missing or cannot be used (not there, not valid JSON, not the kind of file asked for, or an accepted entry
that matches too much).
"""
import argparse
import glob
import gzip
import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

DEFAULT_KIT = os.path.dirname(HERE)
STAGES = ['script', 'record', 'shots', 'place', 'plates', 'paint', 'pages', 'film', 'finish']
STAGE_WORDS = {
    'script': 'before recording the narration',
    'record': 'after recording',
    'shots': 'before building or drawing a place\'s views',
    'place': 'after building a place and before drawing its views (the order: shots, build the place, place, plates)',
    'plates': 'before paying for paintings',
    'paint': 'after a painting arrives',
    'pages': 'while building pages',
    'film': 'before filming',
    'finish': 'after finishing',
}
# the step each stage guards: (what, 'paid' | 'long' | None)
GUARDED = {
    'script': ('recording the narration with the voice service', 'paid'),
    'record': ('using these recordings (re-recording any page listed is paid)', 'paid'),
    'shots': ('building and rendering the place\'s views and plates', 'long'),
    'place': ('drawing this place\'s views and plates (the long step: a place that fails is drawn again)', 'long'),
    'plates': ('asking the painter for these paintings', 'paid'),
    'paint': ('using this painting (cutting it, state pictures, filming it); a failed painting needs a free fix or a paid re-ask', None),
    'pages': ('filming these pages (run the film stage next)', None),
    'film': ('filming the chapter', 'long'),
    'finish': ('sending or publishing the film', None),
}

# every input: (what it is, which tool makes it)
INPUTS = {
    'script': ('the narration script (JSON: pages and their text, the accent cue, main_rule, key pages)',
               'write it with the research-and-script skill; its format is in kit/narration-tools/lint_script.py\'s note, and '
               'kit/examples/new-chapter-template/narration-script.json is a start'),
    'word_times': ('an earlier word-times file of the SAME voice (to estimate the timeline before paying)',
                   'narration-tools/extract_word_times.py on an earlier recording; the kit ships examples/inflation-chapter-2/word-times.json'),
    'timeline': ('the chapter\'s timeline (every page\'s first word, last word and pause)',
                 'narration-tools/assemble_chapter_narration.py after recording (or the script stage\'s estimated-timeline.json before)'),
    'research_ledger': ('the research ledger\'s claims as JSON ({"claims": [{"id", "claim", "said_by", "valid_until"}]})',
                        'the check-facts skill; pages list the claim ids they rest on'),
    'spend_ledger': ('the spend ledger (allowances and every paid step so far)',
                     'write one entry per paid step ({"allowances": [...], "entries": [...]}; format in calculators/plan_budget.py\'s note)'),
    'transcripts': ('the folder of per-page transcripts the voice service returned (pageN-words.json)',
                    'the record-narration skill saves them with each page\'s recording'),
    'recordings': ('the folder of per-page recordings (pageN.mp3)', 'the record-narration skill'),
    'heard': ('a folder of speech-to-text transcripts of the recordings (to catch names said wrongly)', 'a speech-to-text pass over the recordings'),
    'narration': ('the joined narration (one audio file)', 'narration-tools/assemble_chapter_narration.py'),
    'place_facts': ('the place facts file (views, signs, emitters, figures, lights, surfaces, accepted problems)',
                    'the place\'s assemble script writes it; for a place measured with shot_facts.py: python3 calculators/place_facts.py '
                    'from-shot-facts --facts FACTS_FOLDER --check CHECK_FILE --place NAME --view VIEW --kind KIND --out FILE; check it with '
                    'python3 calculators/place_facts.py check FILE'),
    'shot_list': ('a shot list for plan_shot.py (subject, story things, kind of shot; format in calculators/plan_shot.py\'s note)',
                  'write it by hand; without one each view in the place facts is judged as built'),
    'check_files': ('each view\'s shot-check file (VIEW=FILE)',
                    'blender -b BASE.blend --python ASSEMBLE.py --python paper-film/blender/make_check_file.py -- --shot-list SHOT.json '
                    '--check-file OUT.json'),
    'state_plan': ('a page plan of held-shot state changes (format in calculators/plan_states.py\'s note)', 'write it by hand from the script'),
    'smoke': ('the page file (or smoke JSON) that sets the chimney smoke', 'the page that draws the place'),
    'check': ('the view\'s shot-check file (with "paint_as" words, "kind_of_shot", "figures", "accepted")',
              'blender ... --python paper-film/blender/make_check_file.py -- --shot-list SHOT.json --check-file OUT.json, then add '
              '"paint_as" words by hand'),
    'plate': ('the plate picture (the 3D render the painter repaints)', 'render the view\'s plate in Blender (build-and-paint-a-place skill)'),
    'plate_facts': ('shot_facts.py\'s folder for the PLATE\'s camera and lens (facts.json, ids.png, solo masks)',
                    'blender -b SCENE.blend --python paper-film/blender/shot_facts.py -- ... with the plate camera (check-shot.sh runs it)'),
    'render_log': ('the log Blender wrote while drawing the plate', 'render the plate with its output kept: blender -b ... > plate.log 2>&1'),
    'shot_report': ('the shot checker\'s report.md for this view (with known.json beside it)',
                    'BLEND=SCENE.blend paper-film/tools/check-shot.sh SHOT_SCRIPT CHECK_FILE OUT_FOLDER PLATE'),
    'helper_plate': ('the plate drawn without the figures (for the long-shadow check)', 'render the plate again with the figures hidden'),
    'style_picture': ('the style picture sent with the plate (the place\'s master painting; its real size sets the price)', 'the place\'s kept master painting'),
    'brief': ('the painting brief (a person\'s words for the place; see calculators/tests/fixtures/painting/*-brief.json)', 'write it by hand'),
    'real_names': ('a list of real people\'s names from the research', 'the research ledger'),
    'models': ('the .glb model files of the set and props', 'the make-3d-models skill (Blender export)'),
    'painting': ('the painting as the painter returned it', 'the paid painting step (after the plates stage passed and the user said yes)'),
    'behind': ('the behind painting as returned', 'the paid behind-painting step'),
    'near_list': ('the near list paint_request.py wrote (near-list.json)', 'python3 calculators/paint_request.py request ... --out-folder DIR'),
    'standard': ('the standard painting\'s style measures', 'calculators/after_painting.py style on the place\'s kept painting'),
    'events': ('the page events file (what every page does, 30 times a second)',
               'node paper-film/tools/page_events.mjs SCENE OUT.json --pages 3,4,5 (about a minute a page; or give --scene and --make-events here)'),
    'numbers_ledger': ('the numbers ledger ({"numbers": [{id, value, unit, qualifier, said, source}]})', 'the check-facts skill'),
    'timing_accepted': ('timing problems accepted on purpose ([{check, page, text, reason, who, date}])', 'write it by hand'),
    'camera_log': ('the camera log of the pages (render-paper-film.mjs SCENE --camera FILE.json 3)',
                   'node paper-film/tools/render-paper-film.mjs SCENE --camera FILE.json 3'),
    'page_files': ('the page files (a folder or a list of page-N.js)', 'the build-cinema-page skill'),
    'paper_pages': ('paper-look page files (their effects must go through kit.effect)', 'the build-cinema-page skill'),
    'critique': ('the critique of the pages as JSON, newer than every page file (findings marked "status": "fixed" or '
                 '"accepted" with "who" and "date" once dealt with)',
                 'run the critique-film workflow on the stills of every page and save its result as JSON'),
    'scene': ('the chapter scene\'s name (paper-film/scenes/NAME.js; plan_budget.py filming times its pages)', 'the chapter scene file (build-cinema-page skill)'),
    'rates': ('this film\'s measured seconds a frame (rates.json)',
              'python3 calculators/plan_budget.py profile-commands EVENTS --scene S, film those short pieces, then plan_budget.py measure LOGS --events EVENTS --out rates.json'),
    'film': ('the finished film (mp4)', 'narration-tools/finish_film.sh'),
    'clip_critique': ('a fresh helper\'s critique of the FILMED clip in motion, newer than the film: {"film": PATH, "looked_at": [...], "findings": '
                      '[{"time", "what", "severity", "status", "who", "date"}]} (each "must fix" finding fixed or accepted)',
                      'the film-critic agent in its clip mode (it watches the filmed clip and its contact sheets, and saves this file)'),
    'render_record': ('the place kit\'s render record of the plate (PLATE.json beside the picture: it names the engine)',
                      'explainer-film-place render --job JOB.json (it writes one beside every picture)'),
    'mix': ('the mixed sound (narration over music)', 'narration-tools/mix_narration_over_music.sh'),
    'send': ('the sendable copy of the film', 'narration-tools/finish_film.sh (its SEND output)'),
    'deliver': ('the files about to be pushed or sent', 'the finish step'),
    'planned_cuts': ('the planned cuts (plan_page_timing.py check\'s JSON, or the newest pages report)',
                     'python3 calculators/plan_page_timing.py check EVENTS --out timing.json (the pages stage keeps one)'),
    'place_audit': ('the place audit (place-audit.json: the facts about the finished Blender scene)',
                    'explainer-film-place audit --scene SCENE.blend --settings place-settings.json --out place-audit.json (explainer-film-place finish writes one too)'),
    'blend': ('the finished scene file the audit was made from (a changed file makes the audit stale)', 'explainer-film-place finish --scene SCENE.blend --save-as FINISHED.blend'),
    'place_settings': ('the place settings (place-settings.json)', 'explainer-film-place new-settings --scene SCENE.blend --place NAME --type TYPE --out place-settings.json'),
    'place_pictures': ('a folder of the place\'s preview pictures (JPG or PNG)', 'explainer-film-place render --job JOB.json (previews)'),
    'previous_pictures': ('a folder of the previous round\'s pictures of the same views (for the squint test)', 'the previous round\'s explainer-film-place render'),
    'style_guard': ('the style guard (style-guard.json: percentiles, detail energy per region, palette)', 'explainer-film-place measure PICTURE --make-guard --out style-guard.json (from the first honest picture; it is provisional until a person accepts it)'),
    'real_world_facts': ('the place\'s own real-world facts (number, source, confidence), on top of the kit\'s generic ones', 'the place-planner agent writes plan/real-world-facts.json'),
    'fresh_check': ('a fresh checker\'s result (claims it recomputed, problems, what it did not test)', 'the place-checker agent (workflow build-a-place, phase Check)'),
}
PATH_KEYS = (set(INPUTS) | {'events'}) - {'scene'}   # the scene is a name, not a file
# inputs that are not a stage's item (shown when one of them cannot be used)
OTHER_INPUTS = {
    'accepted': ('the problems accepted on purpose (a JSON list of entries, each with "stage", a "check" or "text", "reason", "who" and '
                 '"date" YYYY-MM-DD)', 'write it by hand (see --example-plan\'s "accepted")'),
    'plan': ('the preflight plan (JSON)', 'print an example with --example-plan'),
    'kit': ('the kit whose tools run (a folder holding calculators/, narration-tools/ and paper-film/)',
            'the plugin\'s own kit (plugins/explainer-film/kit), or explainer-film-setup\'s copy'),
}
LIST_KEYS = {'models', 'page_files', 'paper_pages', 'deliver', 'hollow', 'figures', 'views', 'shot_names', 'pages_list'}

# each stage: its inputs, required (r) or optional (o)
STAGE_INPUTS = {
    'script': {'script': 'r', 'word_times': 'o', 'timeline': 'o', 'research_ledger': 'o', 'spend_ledger': 'o'},
    'record': {'script': 'r', 'transcripts': 'r', 'recordings': 'o', 'heard': 'o', 'word_times': 'o', 'narration': 'o', 'timeline': 'o'},
    'shots': {'place_facts': 'r', 'shot_list': 'o', 'check_files': 'o', 'state_plan': 'o', 'smoke': 'o', 'timeline': 'o'},
    'place': {'place_audit': 'r', 'blend': 'o', 'place_settings': 'o', 'place_pictures': 'o', 'previous_pictures': 'o', 'style_guard': 'o',
              'real_world_facts': 'o', 'fresh_check': 'o'},
    'plates': {'check': 'r', 'plate': 'r', 'plate_facts': 'r', 'render_log': 'r', 'shot_report': 'r', 'helper_plate': 'o',
               'place_facts': 'o', 'brief': 'o', 'real_names': 'o', 'models': 'o', 'spend_ledger': 'o', 'style_picture': 'o',
               'blend': 'o', 'place_audit': 'o', 'place_settings': 'o', 'render_record': 'o'},
    'paint': {'painting': 'r', 'plate': 'r', 'check': 'r', 'plate_facts': 'r', 'behind': 'o', 'near_list': 'o', 'helper_plate': 'o',
              'standard': 'o'},
    'pages': {'events': 'r', 'numbers_ledger': 'o', 'timing_accepted': 'o', 'camera_log': 'o', 'timeline': 'o', 'place_facts': 'o',
              'paper_pages': 'o'},
    'film': {'events': 'r', 'scene': 'r', 'critique': 'r', 'page_files': 'r', 'rates': 'o'},
    'finish': {'film': 'r', 'mix': 'r', 'timeline': 'r', 'clip_critique': 'r', 'send': 'o', 'deliver': 'o', 'planned_cuts': 'o'},
}

FAIL_WORDS = {'fail', 'failed', 'error', 'refused', 'problem', 'stop', 'stale'}
WARN_WORDS = {'look', 'warn', 'warning', 'not checked', 'worse', 'borderline', 'not run'}
KNOWN_WORDS = {'known', 'accepted', 'allowed'}
PASS_WORDS = {'pass', 'passed', 'ok', 'fine'}
BIG_FILE_BYTES = 256 * 1024 * 1024
JSON_CHECK_BYTES = 64 * 1024 * 1024     # JSON inputs up to this size are read once first, so a broken one stops the stage plainly


# ------------------------------------------------------------------------------------------------ small helpers
def now_text():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def sha1_of_file(path):
    """The file's sha1; a file over 256 MB is hashed by its size, time and its first and last 8 MB (said in the report)."""
    digest = hashlib.sha1()
    size = os.path.getsize(path)
    with open(path, 'rb') as handle:
        if size <= BIG_FILE_BYTES:
            for block in iter(lambda: handle.read(1 << 20), b''):
                digest.update(block)
            return digest.hexdigest()
        digest.update(f'{size}:{os.path.getmtime(path)}'.encode())
        digest.update(handle.read(8 << 20))
        handle.seek(-8 << 20, os.SEEK_END)
        digest.update(handle.read(8 << 20))
    return 'quick:' + digest.hexdigest()


def sha1_of(path):
    """A file's sha1, or a folder's (every file in it, by name and content); None when it is missing."""
    if os.path.isfile(path):
        return sha1_of_file(path)
    if os.path.isdir(path):
        digest = hashlib.sha1()
        for folder, folders, files in sorted(os.walk(path)):
            folders.sort()
            for name in sorted(files):
                full = os.path.join(folder, name)
                digest.update(os.path.relpath(full, path).encode())
                digest.update(sha1_of_file(full).encode())
        return digest.hexdigest()
    return None


def version_of(path):
    try:
        return hashlib.sha1(open(path, 'rb').read()).hexdigest()[:8]
    except OSError:
        return 'missing'


def load_json(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt') as handle:
        return json.load(handle)


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:48] or 'check'


def verdict_of(word):
    w = str(word).strip().lower()
    if w in FAIL_WORDS or w.startswith('fail') or w.startswith('fix before'):
        return 'fail'
    if w in WARN_WORDS or w.startswith('look'):
        return 'warn'
    if w in KNOWN_WORDS:
        return 'known'
    if w in PASS_WORDS:
        return 'pass'
    return 'info'


def short(text, limit=600):
    text = ' '.join(str(text).split())
    return text if len(text) <= limit else text[:limit - 3] + '...'


def dollars_text(dollars):
    return f'US${dollars:,.2f}'


def minutes_text(seconds):
    if seconds is None:
        return 'unknown'
    if seconds < 90:
        return f'{seconds:.0f} s'
    if seconds < 5400:
        return f'{seconds / 60:.1f} min'
    return f'{seconds / 3600:.1f} h'


# ------------------------------------------------------------------------------------------------ reading a tool's findings
def leaf_verdicts(node, found, where=''):
    """Every dict with a "verdict" that holds no list of other verdicts (a single finding), with where it sits."""
    if isinstance(node, dict):
        children = any(isinstance(v, list) and any(isinstance(x, dict) and 'verdict' in x for x in v) for v in node.values())
        here = where
        if isinstance(node.get('name'), str) and children:
            here = node['name']
        if isinstance(node.get('verdict'), str) and not children and len(node) > 1:
            found.append((node, here))
        for key, value in node.items():
            if key in ('settings_used', 'said', 'samples', 'track'):
                continue
            leaf_verdicts(value, found, here)
    elif isinstance(node, list):
        for value in node:
            leaf_verdicts(value, found, where)


def finding_from_leaf(node, where):
    check = node.get('check') or node.get('rule') or node.get('name') or ''
    words = [node.get(k) for k in ('about', 'what', 'text') if isinstance(node.get(k), str) and node.get(k)]
    detail = node.get('detail') if isinstance(node.get('detail'), str) else ''
    text = ' '.join(words + ([detail] if detail and detail not in words else []))
    place = node.get('page')
    place = f'page {place}' if place not in (None, '') else (node.get('view') or where or '')
    found = {'verdict': verdict_of(node['verdict']), 'check': str(check), 'where': str(place), 'text': short(text or json.dumps(node)[:300]),
             'fix': short(node.get('fix') or '', 400)}
    if node.get('accepted_but_worse') or node.get('worse') is True:
        found['worse'] = True      # the tool says it has grown worse than it was accepted at: it must never become "known" again
    for key in ('measured', 'limit'):
        if isinstance(node.get(key), (int, float)) and not isinstance(node.get(key), bool):
            found[key] = node[key]
    return found


PLAIN_FAIL = ('FAIL', 'PROBLEM', 'RE-RECORD', 'MISSING', 'REFUSED', 'ERROR')
PLAIN_WARN = ('LOOK', 'WARN', 'JUMP')   # find_jumps.py's JUMP: a jump outside the planned cuts, for a person to look at on its sheet
PLAIN_PASS = ('PASS',)


def findings_from_plain(text):
    found = []
    for raw in text.splitlines():
        line = raw.strip()
        word = line.split(' ', 1)[0].rstrip(':') if line else ''
        if word in PLAIN_FAIL:
            found.append({'verdict': 'fail', 'check': '', 'where': '', 'text': short(line), 'fix': ''})
        elif word in PLAIN_WARN:
            found.append({'verdict': 'warn', 'check': '', 'where': '', 'text': short(line), 'fix': ''})
        elif word in PLAIN_PASS:
            found.append({'verdict': 'pass', 'check': '', 'where': '', 'text': short(line), 'fix': ''})
    return found


def findings_from(result, plain, code):
    """The findings of one tool run: from its JSON verdicts, its problem lists, or its plain lines, agreeing with its exit code."""
    found = []
    if isinstance(result, dict):
        leaves = []
        leaf_verdicts(result, leaves)
        found = [finding_from_leaf(node, where) for node, where in leaves]
        for key, verdict in (('problems', 'fail' if code else 'warn'), ('errors', 'fail'), ('warnings', 'warn'), ('notes', 'info')):
            value = result.get(key)
            if isinstance(value, list) and value and all(isinstance(v, str) for v in value):
                for v in value:
                    # a note that something was not checked is for a person to look at, not only to read
                    said = 'warn' if verdict == 'info' and re.search(r'\bnot (checked|run|compared)\b', v, re.I) else verdict
                    found.append({'verdict': said, 'check': '', 'where': '', 'text': short(v), 'fix': ''})
    plain_found = findings_from_plain(plain)
    if not found:
        found = plain_found
    elif not any(f['verdict'] in ('fail', 'warn') for f in found):
        found += [f for f in plain_found if f['verdict'] in ('fail', 'warn')]
    elif code and not any(f['verdict'] == 'fail' for f in found):
        found += [f for f in plain_found if f['verdict'] == 'fail']
    if code and not any(f['verdict'] == 'fail' for f in found):
        tail = [l for l in plain.strip().splitlines() if l.strip()][-6:]
        if isinstance(code, int) and code < 0:
            words = f'it was stopped by the system (signal {-code}; signal 9 is most often too little memory)'
        elif 'Traceback' in plain or code not in (1, 2):
            words = 'it stopped with an error'
        else:
            words = f'it exited {code} (a refusal or a failure)'
        found.append({'verdict': 'fail', 'check': 'the tool stopped' if 'stopped' in words else 'exit code', 'where': '',
                      'text': short(words + (': ' + ' | '.join(tail) if tail else ''), 900), 'fix': ''})
    seen, unique = set(), []
    for f in found:
        key = (f['verdict'], f['check'], f['where'], f['text'])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


# ------------------------------------------------------------------------------------------------ accepted problems
def day_of(text):
    """A day written YYYY-MM-DD, or None."""
    try:
        return datetime.strptime(str(text).strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def entry_is_signed(entry):
    """Who accepted it and when: a name, and a real day (YYYY-MM-DD) no later than today."""
    day = day_of(entry.get('date', ''))
    return bool(str(entry.get('who') or '').strip()) and day is not None and day <= date.today()


def entry_problem(entry):
    """Why an accepted entry of the preflight plan (or --accepted) cannot be used; '' when it can."""
    if not isinstance(entry, dict):
        return 'it is not an entry like {"stage", "check", "text", "reason", "who", "date"}'
    absent = [k for k in ('stage', 'reason', 'who', 'date') if not str(entry.get(k) or '').strip()]
    if absent:
        return 'it has no ' + ', no '.join(f'"{k}"' for k in absent)
    if entry['stage'] not in STAGES:
        return f'its "stage" {entry["stage"]!r} is not one of {", ".join(STAGES)}'
    day = day_of(entry['date'])
    if day is None:
        return f'its "date" {entry["date"]!r} is not a day written YYYY-MM-DD'
    if day > date.today():
        return f'its "date" {entry["date"]} is after today'
    key = entry.get('check') or entry.get('rule')
    text = str(entry.get('text') or '')
    if not key and not text:
        return 'it names neither a "check" nor a "text"'
    if not key and len(re.sub(r'[^A-Za-z0-9]', '', text)) < 3:
        return f'without a "check", its "text" {text!r} must hold at least 3 letters'
    return ''


def describe_entry(entry):
    parts = [f'{k} {entry[k]!r}' for k in ('stage', 'check', 'rule', 'text', 'page', 'view', 'tool') if entry.get(k) not in (None, '')]
    return '{' + ', '.join(parts) + '}' if parts else short(json.dumps(entry), 160)


def plain_name(text):
    return ' '.join(re.sub(r'[-_]+', ' ', str(text)).lower().split())


def has_words(needle, haystack):
    """True when `needle` appears in `haystack` as whole words (case does not matter)."""
    needle = ' '.join(str(needle).split()).lower()
    return bool(needle) and re.search(r'(?<![a-z0-9])' + re.escape(needle) + r'(?![a-z0-9])', ' '.join(str(haystack).split()).lower()) is not None


def check_names(finding):
    name = plain_name(finding.get('check', ''))
    names = {name}
    if ':' in name:                      # "shot checker: rule5 subject brightness ratio" also answers to the rule's own name
        names.add(name.split(':', 1)[1].strip())
    return names - {''}


def entry_matches(entry, finding, stage):
    if entry.get('stage') != stage:
        return False
    key = entry.get('check') or entry.get('rule')
    if key and plain_name(key) not in check_names(finding):
        return False
    words = f'{finding.get("where", "")} {finding.get("text", "")}'
    needles = ([str(entry['text'])] if entry.get('text') else []) + [str(t) for t in entry.get('things', []) or []]
    if any(not has_words(n, words) for n in needles):
        return False
    if entry.get('page') not in (None, '') and not has_words(f'page {entry["page"]}', finding.get('where', '')):
        return False
    if entry.get('view') not in (None, '') and not has_words(str(entry['view']), finding.get('where', '')):
        return False
    if entry.get('tool') and os.path.basename(str(entry['tool'])) != os.path.basename(finding.get('tool', '')):
        return False
    return True


WORSE_WORDS = ('worse than accepted', 'worse than that', 'counts again')


def said_worse(finding):
    """The tool itself says this kept problem has grown worse than it was accepted at."""
    words = f'{finding.get("text", "")} {finding.get("fix", "")}'.lower()
    return bool(finding.get('worse')) or any(w in words for w in WORSE_WORDS)


def grown_past(entry, finding, share):
    """True when an entry accepted at "measured" now measures more than `share` further past the finding's limit (the same
    sum as plan_shot.py and check_shot.py). Which way is "past" comes from the failing number itself: above its limit, a
    maximum; below it, a minimum."""
    accepted, measured, limit = entry.get('measured'), finding.get('measured'), finding.get('limit')
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (accepted, measured, limit)):
        return False
    if measured >= limit:
        return measured > accepted * (1 + share)
    return measured < accepted * (1 - share)


# ------------------------------------------------------------------------------------------------ one run of a stage
class Run:
    def __init__(self, stage, args, plan, plan_folder):
        self.stage, self.args, self.plan, self.plan_folder = stage, args, plan, plan_folder
        self.kit = os.path.abspath(args.kit or plan.get('kit') and self.resolve(plan['kit'], plan_folder) or DEFAULT_KIT)
        self.checks, self.missing, self.costs, self.times, self.known_lists, self.notes = [], [], [], [], [], []
        self.input_paths = {}
        self.allowance = None
        self.house = None
        self.plan_path = None
        self.started = time.time()
        self.stamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        project = os.path.abspath(args.project or (plan_folder if args.plan else os.getcwd()))
        beside_audit = os.path.join(os.path.dirname(os.path.abspath(args.place_audit)), 'preflight-reports') if stage == 'place' and getattr(args, 'place_audit', None) else None
        self.reports = os.path.abspath(args.reports or (self.resolve(plan['reports'], plan_folder) if plan.get('reports') else
                                                        beside_audit or os.path.join(project, 'preflight-reports')))
        self.name = f'preflight-{stage}-{self.stamp}'
        self.work = os.path.join(self.reports, self.name)
        self.settings_path = os.path.abspath(args.settings or os.environ.get('FILM_SETTINGS') or os.path.join(self.kit, 'film-settings.json'))
        self.accepted = self.load_accepted()
        self.entry_hits = [[] for _ in self.accepted]

    def register_fixed_inputs(self, plan_path=None):
        """The inputs every stage has: the preflight plan, the accepted file and the settings file (a withdrawn acceptance or a
        changed house number changes them, and so closes the gate)."""
        self.plan_path = os.path.abspath(plan_path) if plan_path and os.path.exists(plan_path) else None
        for path in (self.plan_path, self.args.accepted, self.settings_path):
            if path and os.path.exists(path):
                self.register(path)

    def house_number(self, key, default):
        """A number from film-settings.json (the default when the table or the key is not there)."""
        try:
            if self.house is None:
                from settings import load_settings
                self.house = load_settings(self.settings_path if os.path.exists(self.settings_path) else None)
            return self.house.value(key)
        except Exception:   # noqa: BLE001 - a missing table falls back to the default, which the report names
            return default

    # -- inputs
    @staticmethod
    def resolve(value, folder):
        if value in (None, '') or not isinstance(value, str):
            return value
        value = os.path.expanduser(value)
        return value if os.path.isabs(value) else os.path.normpath(os.path.join(folder, value))

    def load_accepted(self):
        entries = []
        for entry in self.plan.get('accepted', []) or []:
            entries.append((entry, 'the preflight plan'))
        if self.args.accepted:
            data = self.read_json('accepted', self.args.accepted, 'the accepted problems')
            listed = data.get('accepted') if isinstance(data, dict) else data
            if data is not None and not isinstance(listed, list):
                self.unusable('accepted', self.args.accepted, 'it is not a list of entries (nor {"accepted": [...]})')
                listed = []
            for entry in listed or []:
                entries.append((entry, os.path.basename(self.args.accepted)))
        used = []
        for entry, source in entries:
            problem = entry_problem(entry)
            if problem:
                self.notes.append(f'An accepted entry was NOT used ({source}): {problem}. The entry: '
                                  f'{short(json.dumps(entry) if not isinstance(entry, dict) else describe_entry(entry), 200)}. '
                                  'Each entry needs "stage", "reason", "who" and "date" (YYYY-MM-DD), and a "check" or a "text".')
                continue
            used.append(dict(entry, source=source))
        return used

    def read_json(self, key, path, needed_by):
        """A JSON input (gzip too); None, recorded as given but unusable (exit 2), when it is not there or not valid JSON."""
        try:
            return load_json(path)
        except FileNotFoundError:
            self.unusable(key, path, 'it is not there', needed_by)
        except IsADirectoryError:
            self.unusable(key, path, 'it is a folder, not a JSON file', needed_by)
        except (ValueError, UnicodeDecodeError, EOFError, OSError) as error:
            self.unusable(key, path, f'it is not valid JSON ({short(error, 160)})', needed_by)
        return None

    def unusable(self, key, path, problem, needed_by=''):
        """An input that was given but cannot be used: the stage stops with exit 2 and says what makes a good one."""
        what, make = INPUTS.get(key) or OTHER_INPUTS.get(key) or (key, '')
        self.missing.append({'input': key, 'option': '--' + key.replace('_', '-'), 'what': what, 'make': make, 'needed_by': needed_by or 'the preflight',
                             'required': True, 'why': '', 'given_but_absent': [], 'unusable': f'{path}: {problem}'})

    def items(self):
        """The stage's items (one place, view, painting or chapter each): the plan's, with the command line's inputs on top."""
        raw = self.plan.get(self.stage)
        items = raw if isinstance(raw, list) else [raw] if isinstance(raw, dict) else [{}]
        given = {k: v for k, v in vars(self.args).items() if k in PATH_KEYS | LIST_KEYS | ITEM_VALUE_KEYS and v not in (None, [], False)}
        out = []
        for item in items:
            item = dict(item or {})
            for key, value in list(item.items()):
                if key in PATH_KEYS and key not in LIST_KEYS and isinstance(value, str):
                    item[key] = self.resolve(value, self.plan_folder)
                elif key in ('models', 'page_files', 'paper_pages', 'deliver') and isinstance(value, list):
                    item[key] = [self.resolve(v, self.plan_folder) for v in value]
                elif key == 'check_files' and isinstance(value, dict):
                    item[key] = {v: self.resolve(p, self.plan_folder) for v, p in value.items()}
            for key, value in given.items():
                if key == 'views' and isinstance(item.get('views'), dict):
                    # --views picks from the plan's per-view details instead of dropping them
                    value = {v: item['views'].get(v, {}) for v in value}
                elif key in PATH_KEYS and key not in LIST_KEYS and isinstance(value, str):
                    value = os.path.abspath(os.path.expanduser(value))
                elif key in ('models', 'page_files', 'paper_pages', 'deliver'):
                    value = [os.path.abspath(os.path.expanduser(v)) for v in value]
                elif key == 'check_files':
                    value = {pair.split('=', 1)[0]: os.path.abspath(os.path.expanduser(pair.split('=', 1)[1])) for pair in value if '=' in pair}
                item[key] = value
            out.append(item)
        return out

    def label(self, item, index, count):
        name = item.get('name') or item.get('view') or (os.path.basename(item['place_facts']) if item.get('place_facts') else '') \
            or (os.path.basename(item['painting']) if item.get('painting') else '')
        return name or (f'item {index + 1}' if count > 1 else '')

    def need(self, item, key, needed_by, required=True, why=''):
        """The input's path if it is there; else records exactly what to make and how, and returns None."""
        value = item.get(key)
        values = value if isinstance(value, list) else [value] if value else []
        if values and all(isinstance(v, str) and (os.path.exists(v) or glob.glob(v)) for v in values):
            broken = False
            for v in values:
                for path in (glob.glob(v) or [v]):
                    self.register(path)
                    if path.endswith(('.json', '.json.gz')) and os.path.isfile(path) and os.path.getsize(path) <= JSON_CHECK_BYTES:
                        broken = self.read_json(key, path, needed_by) is None or broken
            return None if broken else value
        what, make = INPUTS.get(key, (key, ''))
        absent = [v for v in values if not (os.path.exists(v) or glob.glob(v))] if values else []
        self.missing.append({'input': key, 'option': '--' + key.replace('_', '-'), 'what': what, 'make': make, 'needed_by': needed_by,
                             'required': required, 'why': why, 'given_but_absent': absent})
        return None

    # -- running one tool
    def run_tool(self, title, tool, tool_args, kind='python', where='', timeout=None, json_out=True, settings=True):
        path = os.path.join(self.kit, tool)
        os.makedirs(self.work, exist_ok=True)
        number = len(self.checks) + 1
        base = os.path.join(self.work, f'{number:02d}-{slug(title)}')
        command = ([sys.executable, '-I', '-B', path] if kind == 'python' else ['node', path]) + [str(a) for a in tool_args]
        if json_out:
            command += ['--out', base + '.json']
        if settings and self.args.settings:
            command += ['--settings', os.path.abspath(self.args.settings)]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        if self.args.settings:
            environment['FILM_SETTINGS'] = os.path.abspath(self.args.settings)
        started = time.time()
        record = {'title': title, 'tool': tool, 'version': version_of(path), 'where': where,
                  'command': ' '.join(shlex.quote(c) for c in command), 'output_json': base + '.json' if json_out else None,
                  'output_text': base + '.txt'}
        if not os.path.exists(path):
            code, plain = 2, f'ERROR the kit has no {tool} (kit: {self.kit})'
        else:
            try:
                run = subprocess.run(command, capture_output=True, text=True, timeout=timeout or self.args.timeout, cwd=self.kit, env=environment)
                code, plain = run.returncode, run.stdout + (('\n' + run.stderr) if run.stderr.strip() else '')
            except subprocess.TimeoutExpired:
                code, plain = 'timeout', f'FAIL stopped after {timeout or self.args.timeout:.0f} s'
            except OSError as error:
                code, plain = 2, f'ERROR could not start it: {error}'
        record['seconds'] = round(time.time() - started, 2)
        record['exit'] = code
        with open(record['output_text'], 'w') as handle:
            handle.write(plain)
        result = None
        if json_out and os.path.exists(base + '.json'):
            try:
                result = load_json(base + '.json')
            except (ValueError, OSError):
                result = None
        record['result'] = result
        record['findings'] = findings_from(result, plain, 0 if code == 0 else (code if isinstance(code, int) else 3))
        for finding in record['findings']:
            finding['tool'] = os.path.basename(tool)
            if where and not finding['where']:
                finding['where'] = where
        self.apply_accepted(record['findings'])
        record['verdict'] = self.verdict_of_findings(record['findings'])
        self.checks.append(record)
        return record

    def add_check(self, title, findings, where='', tool='preflight.py'):
        """A check the preflight makes itself (no tool run)."""
        for finding in findings:
            finding.setdefault('tool', tool)
            finding.setdefault('fix', '')
            if where and not finding.get('where'):
                finding['where'] = where
        self.apply_accepted(findings)
        record = {'title': title, 'tool': tool, 'version': version_of(os.path.abspath(__file__)), 'where': where, 'command': '(inside the preflight)',
                  'seconds': 0.0, 'exit': 0, 'findings': findings, 'verdict': self.verdict_of_findings(findings), 'result': None}
        self.checks.append(record)
        return record

    def apply_accepted(self, findings):
        share = self.house_number('shot_planner.check_shot_accepted_worse_share', 0.05)
        for finding in findings:
            if finding['verdict'] not in ('fail', 'warn'):
                continue
            for index, entry in enumerate(self.accepted):
                if not entry_matches(entry, finding, self.stage):
                    continue
                if said_worse(finding):
                    finding['worse'] = True
                    self.notes.append(f'The accepted entry {describe_entry(entry)} matches a problem that has grown worse than it was accepted at; '
                                      f'it still counts: {short(finding["text"], 160)}')
                    break
                if grown_past(entry, finding, share):
                    finding['worse'] = True
                    finding['text'] += (f' (Accepted at {entry["measured"]} by {entry["who"]}, {entry["date"]}; it is now {finding["measured"]}: '
                                        'worse than accepted, so it counts again.)')
                    break
                finding['was'] = finding['verdict']
                finding['verdict'] = 'known'
                finding['accepted'] = {'reason': entry.get('reason', ''), 'who': entry['who'], 'date': entry['date'], 'source': entry.get('source', '')}
                self.entry_hits[index].append(finding)
                break

    def check_accepted_breadth(self):
        """After every tool ran: an accepted entry that matched more than a few findings is too broad. Its findings go back to
        what the tools said, and the stage stops (exit 2). Every entry's count is listed under Notes."""
        most = self.house_number('preflight.accepted_entry_most_findings', 3)
        for index, entry in enumerate(self.accepted):
            hits = self.entry_hits[index]
            self.notes.append(f'Accepted entry {describe_entry(entry)} ({entry.get("source")}, {entry["who"]}, {entry["date"]}): matched {len(hits)} finding(s)'
                              + ('' if hits else ' (none: it may be out of date; take it out once its problem is fixed)'))
            if len(hits) > most:
                for finding in hits:
                    finding['verdict'] = finding.pop('was', finding['verdict'])
                    finding.pop('accepted', None)
                self.unusable('accepted', entry.get('source', ''), f'the entry {describe_entry(entry)} matches {len(hits)} findings (at most {most}, '
                              'film-settings.json preflight.accepted_entry_most_findings): name the "check" exactly and add "page", "view" or a '
                              'longer "text", or write one entry per finding', 'the accepted problems')
        for check in self.checks:
            check['verdict'] = self.verdict_of_findings(check['findings'])

    @staticmethod
    def verdict_of_findings(findings):
        verdicts = {f['verdict'] for f in findings}
        return 'fail' if 'fail' in verdicts else 'warn' if 'warn' in verdicts else 'pass'

    def show_known(self, source, entries, where=''):
        """Accepted entries from a check file or place facts, shown as known in the report."""
        for entry in entries or []:
            self.known_lists.append({'source': source, 'where': where or entry.get('view', ''), 'rule': entry.get('rule') or entry.get('check', ''),
                                     'things': entry.get('things', []), 'reason': entry.get('reason', ''), 'who': entry.get('who', ''),
                                     'date': entry.get('date', ''), 'measured': entry.get('measured'), 'signed': entry_is_signed(entry)})

    def cost(self, what, dollars, note=''):
        self.costs.append({'what': what, 'dollars': round(float(dollars), 2), 'note': note})

    def step_time(self, what, seconds, note=''):
        self.times.append({'what': what, 'seconds': None if seconds is None else round(float(seconds), 1), 'note': note})

    # -- hashing
    def register(self, path):
        """An input file or folder: hashed the first time it is seen, before any tool reads it."""
        path = os.path.abspath(path)
        if path not in self.input_paths:
            self.input_paths[path] = sha1_of(path)

    def hash_inputs(self):
        return {path: sha1_of(path) for path in sorted(self.input_paths)}


ITEM_VALUE_KEYS = {'today', 'allowance', 'view', 'views', 'shot_names', 'page', 'scene', 'pages_list', 'exposure', 'hollow', 'figures',
                   'check_files', 'with_behind', 'processors', 'free_memory_gb', 'free_disk_gb', 'from_frame', 'to_frame', 'make_events', 'jumps',
                   'name', 'count_ground', 'blender_running', 'models_as_set', 'allow_quick', 'toe'}


# ------------------------------------------------------------------------------------------------ the stages
def stage_script(run, item, where):
    script = run.need(item, 'script', 'lint_script.py before')
    if not script:
        return
    arguments = ['before', script]
    if item.get('word_times') and run.need(item, 'word_times', 'lint_script.py before', required=False):
        arguments += ['--word-times', item['word_times']]
    elif item.get('timeline') and run.need(item, 'timeline', 'lint_script.py before', required=False):
        arguments += ['--timeline', item['timeline']]
    else:
        run.need(item, 'word_times', 'lint_script.py before', required=False,
                 why='without it no estimated timeline is made and the pages\' speeds are not judged')
    if item.get('research_ledger') and run.need(item, 'research_ledger', 'lint_script.py before', required=False):
        arguments += ['--ledger', item['research_ledger'], '--today', item.get('today') or datetime.now().strftime('%Y-%m-%d')]
    os.makedirs(run.work, exist_ok=True)
    timeline_out = os.path.join(run.work, 'estimated-timeline.json')
    arguments += ['--timeline-out', timeline_out]
    record = run.run_tool('script gate (lint_script.py before)', 'narration-tools/lint_script.py', arguments, where=where)
    result = record['result'] or {}
    if result.get('dollars') is not None:
        run.cost('the narration (voice service)', result['dollars'], f'{result.get("credits", 0):,.0f} credits: one per letter sent, the cue included')
    if result.get('timeline_seconds'):
        run.step_time('the chapter, as estimated from the script', result['timeline_seconds'],
                      f'saved as {timeline_out}' if os.path.exists(timeline_out) else '')


def spend_ledger_check(run, items):
    """After every item: the stage's whole cost against what is left of the allowance (the spend ledger of the first item that names one)."""
    item = next((i for i in items if i.get('spend_ledger')), items[0] if items else {})
    where = ''
    if not item.get('spend_ledger'):
        run.need(item, 'spend_ledger', 'plan_budget.py ledger', required=False, why='without it nothing checks the step against what is left of the allowance')
        return
    if not run.need(item, 'spend_ledger', 'plan_budget.py ledger', required=False):
        return
    total = sum(c['dollars'] for c in run.costs)
    arguments = ['ledger', item['spend_ledger'], '--next-cost', f'{total:.2f}']
    if item.get('allowance'):
        arguments += ['--allowance', item['allowance']]
    record = run.run_tool('the allowance left (plan_budget.py ledger)', 'calculators/plan_budget.py', arguments, where=where)
    result = record['result'] or {}
    if result.get('left_dollars') is not None:
        run.allowance = {'name': result.get('allowance'), 'left_dollars': result['left_dollars'], 'next_cost_dollars': total,
                         'fits': total <= result['left_dollars']}


def stage_record(run, item, where):
    script = run.need(item, 'script', 'lint_script.py after')
    transcripts = run.need(item, 'transcripts', 'lint_script.py after')
    if script and transcripts:
        arguments = ['after', script, '--transcripts', transcripts]
        for key, option in (('recordings', '--recordings'), ('heard', '--heard')):
            if item.get(key) and run.need(item, key, 'lint_script.py after', required=False):
                arguments += [option, item[key]]
        record = run.run_tool('the recordings against the script (lint_script.py after)', 'narration-tools/lint_script.py', arguments, where=where)
        result = record['result'] or {}
        if result.get('rerecord'):
            run.cost('re-recording ' + ', '.join(f'page {p}' for p in result['rerecord']), result.get('rerecord_dollars') or 0,
                     f'{result.get("rerecord_credits", 0):,.0f} credits')
    if item.get('word_times') and run.need(item, 'word_times', 'sound_gates.py voice', required=False):
        arguments = ['voice', item['word_times']]
        if item.get('recordings') and os.path.isdir(item['recordings']):
            arguments += ['--recordings-from', item['recordings']]
        run.run_tool('voice steadiness (sound_gates.py voice)', 'narration-tools/sound_gates.py', arguments, where=where)
    else:
        run.need(item, 'word_times', 'sound_gates.py voice', required=False,
                 why='the word times of THIS recording (narration-tools/extract_word_times.py) let the voice gate find pages to record again')
    if item.get('narration') and run.need(item, 'narration', 'sound_gates.py mouth', required=False):
        arguments = ['mouth', item['narration']] + (['--timeline', item['timeline']] if item.get('timeline') and os.path.exists(item['timeline']) else [])
        run.run_tool('the paper mouth\'s levels (sound_gates.py mouth)', 'narration-tools/sound_gates.py', arguments, where=where)


def place_views(run, place_facts):
    """The place facts and their view names; (None, []) when the file cannot be read (recorded: exit 2)."""
    facts = run.read_json('place_facts', place_facts, 'place_facts.py check, plan_shot.py, view_audit.py')
    if not isinstance(facts, dict):
        if facts is not None:
            run.unusable('place_facts', place_facts, 'it is not a place facts file (a JSON object with "views")')
        return None, []
    views = facts.get('views', [])
    names = [v.get('name') for v in views if isinstance(v, dict)] if isinstance(views, list) else list(views)
    return facts, [n for n in names if n]


def view_details(item):
    """Each view's page, from a plan's shots item: "views": {"w3": {"page": 9, "named": ["bank sign"], "cards": {"lower":
    [left, top, right, bottom]}}} (shares of the frame). A plain list of names gives no details."""
    views = item.get('views')
    return {k: (v if isinstance(v, dict) else {}) for k, v in views.items()} if isinstance(views, dict) else {}


def stage_shots(run, item, where):
    place_facts = run.need(item, 'place_facts', 'place_facts.py check, plan_shot.py, view_audit.py, plan_effects.py, plan_lights.py')
    if not place_facts:
        return
    facts, views = place_views(run, place_facts)
    if facts is None:
        return
    place = facts.get('place') or where
    run.run_tool('place facts are complete (place_facts.py check)', 'calculators/place_facts.py', ['check', place_facts], where=place)
    details = view_details(item)
    listed = list(details) or list(item.get('views') or []) or ([item['view']] if item.get('view') else [])
    unknown = [v for v in listed if v not in views]
    if unknown:
        run.unusable('views', ', '.join(unknown), f'the place facts have no such view (views: {", ".join(views)})', 'the shots stage')
        return
    chosen = listed or views
    if item.get('shot_list'):
        if run.need(item, 'shot_list', 'plan_shot.py', required=False):
            arguments = ['--place-facts', place_facts, '--shots', item['shot_list'], '--strict']
            if item.get('shot_names'):
                arguments += ['--shot'] + list(item['shot_names'])
            run.run_tool('camera, reach, slide and people (plan_shot.py)', 'calculators/plan_shot.py', arguments, where=place)
    else:
        run.need(item, 'shot_list', 'plan_shot.py', required=False, why='without a shot list each view is judged as built from its place facts')
        for view in chosen:
            run.run_tool(f'camera, reach, slide and people for {view} (plan_shot.py)', 'calculators/plan_shot.py',
                         ['--place-facts', place_facts, '--view', view, '--strict'], where=f'{place} {view}')
    # letters, loud signs, heads and landmarks: per view when the plan says which page each view serves (what the page
    # names decides which words must read there and which unnamed sign is too loud)
    timeline = item['timeline'] if item.get('timeline') and run.need(item, 'timeline', 'view_audit.py', required=False) else None
    per_view = any(d.get('page') is not None or d.get('named') is not None for d in details.values())
    if per_view:
        for view in chosen:
            d = details.get(view, {})
            arguments = ['audit', '--place-facts', place_facts, '--view', view]
            if d.get('named') is not None:
                arguments += ['--named', ','.join(d['named'])]
            if d.get('page') is not None and timeline:
                arguments += ['--timeline', timeline, '--page', str(d['page'])]
            elif d.get('page') is not None and d.get('named') is None:
                run.notes.append(f'{view}: the plan names page {d["page"]} but no --timeline (or "named" list), so view_audit cannot tell which '
                                 'signs that page says: every must-read sign is judged as needed there.')
            run.run_tool(f'letters, loud signs, heads and landmarks for {view} (view_audit.py)', 'calculators/view_audit.py', arguments,
                         where=f'{place} {view}')
    else:
        arguments = ['audit', '--place-facts', place_facts]
        for view in listed:
            arguments += ['--view', view]
        if timeline and item.get('page'):
            arguments += ['--timeline', timeline, '--page', str(item['page'])]
        else:
            run.notes.append('view_audit was not told which page each view serves (a plan\'s shots item "views": {"w3": {"page": 9, "named": '
                             '[...]}} with --timeline): every must-read sign counts as needed in every view, and loud unnamed signs are not '
                             'compared.')
        run.run_tool('letters, loud signs, heads and landmarks (view_audit.py)', 'calculators/view_audit.py', arguments, where=place)
    smoky = [e for e in facts.get('emitters', []) if 'chimney' in str(e.get('kind', '')) or e.get('kind') == 'fire']
    if smoky:
        # the page's own word cards per view when the plan gives them; the house's rule cards (looks only) for the rest
        arguments = ['wind', '--place-facts', place_facts, '--default-cards']
        if item.get('smoke') and run.need(item, 'smoke', 'plan_effects.py wind', required=False):
            arguments += ['--smoke', item['smoke']]
        for view, d in details.items():
            for name, box in (d.get('cards') or {}).items():
                arguments += ['--card', f'{view}:{name}=' + ','.join(str(v) for v in box)]
        run.run_tool('wind and chimney smoke in every view (plan_effects.py wind)', 'calculators/plan_effects.py', arguments, where=place)
    else:
        run.notes.append('Wind and smoke (plan_effects.py wind): skipped, the place has no chimney or fire.')
    if facts.get('lights'):
        for view in chosen:
            run.run_tool(f'lights for {view} (plan_lights.py plan)', 'calculators/plan_lights.py',
                         ['plan', '--place-facts', place_facts, '--view', view], where=f'{place} {view}')
    else:
        run.notes.append('Lights (plan_lights.py plan): skipped, the place facts list no lights.')
    if item.get('state_plan'):
        if run.need(item, 'state_plan', 'plan_states.py', required=False):
            run.run_tool('held-shot plates, cuts and blends (plan_states.py plan)', 'calculators/plan_states.py',
                         ['plan', '--plan', item['state_plan'], '--out-folder', os.path.join(run.work, 'state-plan')], where=place)
    else:
        run.need(item, 'state_plan', 'plan_states.py', required=False,
                 why='states not checked: without it the held-shot state plates, cuts and blends are not planned (a place with no state change needs none)')
    run.show_known(f'{os.path.basename(place_facts)} (place facts)', facts.get('accepted', []))
    check_files = item.get('check_files') or {}
    findings = []
    for view in chosen:
        path = check_files.get(view)
        if not path:
            findings.append({'verdict': 'info', 'check': 'check file', 'where': f'{place} {view}',
                             'text': f'no check file given for {view}: make it after the assemble script with paper-film/blender/make_check_file.py '
                                     f'(give it here as --check-files {view}=FILE to check its keys)'})
            continue
        if not os.path.exists(path):
            run.need({'check_files': path}, 'check_files', f'the check file of {view}', required=False)
            continue
        run.register(path)
        findings += check_file_findings(run, path, view, place, facts)
    run.add_check('each view\'s check file carries its kinds, figures and accepted list', findings, where=place)


def check_file_findings(run, path, view, place, facts):
    check = run.read_json('check_files', path, f'the check file of {view}')
    if not isinstance(check, dict):
        return []
    found = []
    view_facts = next((v for v in facts.get('views', []) if isinstance(v, dict) and v.get('name') == view), {})
    kinds = check.get('kind_of_shot')
    if not kinds:
        found.append({'verdict': 'warn', 'check': 'kind_of_shot', 'where': f'{place} {view}',
                      'text': f'{os.path.basename(path)} names no "kind_of_shot": the shot checker judges it as a still life'
                              + (f' (the place facts say {" + ".join(view_facts.get("kind_of_shot", []))})' if view_facts.get('kind_of_shot') else ''),
                      'fix': 'add "kind_of_shot": [...] (still_life, crowd, overview, interior, dark_subject)'})
    elif view_facts.get('kind_of_shot') and sorted(kinds) != sorted(view_facts['kind_of_shot']):
        found.append({'verdict': 'warn', 'check': 'kind_of_shot', 'where': f'{place} {view}',
                      'text': f'{os.path.basename(path)} says {" + ".join(kinds)}, the place facts say {" + ".join(view_facts["kind_of_shot"])}',
                      'fix': 'make them the same'})
    if kinds and 'crowd' in kinds and not check.get('figures'):
        found.append({'verdict': 'warn', 'check': 'figures', 'where': f'{place} {view}',
                      'text': 'a crowd view with no "figures" list: the heads-apart test cannot run', 'fix': 'list the groups that are people under "figures"'})
    for entry in check.get('accepted', []) or []:
        if not entry_is_signed(entry):
            found.append({'verdict': 'fail', 'check': 'accepted', 'where': f'{place} {view}',
                          'text': f'an accepted entry for "{entry.get("rule")}" has no who, or no real date (YYYY-MM-DD, not after today): the shot '
                                  'checker does not use it, so its problem counts as new',
                          'fix': 'add who accepted it and when, or take the entry out'})
    run.show_known(f'{os.path.basename(path)} (check file)', check.get('accepted', []), where=f'{place} {view}')
    if not found:
        found.append({'verdict': 'pass', 'check': 'check file', 'where': f'{place} {view}',
                      'text': f'{os.path.basename(path)}: kinds {" + ".join(kinds)}, {len(check.get("figures", []))} figure group(s), '
                              f'{len(check.get("accepted", []) or [])} accepted problem(s)'})
    return found


SHOT_REPORT_TITLE = '# Shot check: '
SHOT_REPORT_VERSION = re.compile(r'^Made by check_shot\.py version \S+', re.M)


def shot_report_findings(report_path, run=None):
    """The shot checker's report: its numbered problems (new) and its "Known and allowed" list. A file the shot checker did
    not write (no "# Shot check:" title and version line, nor a known.json of check_shot.py beside it) is a failure: a paid
    repaint needs the checker's light rules passed (decision 37), and an empty or made-up file proves nothing. An accepted
    item without who and when counts as new."""
    folder = os.path.dirname(report_path) if os.path.isfile(report_path) else report_path
    report_file = report_path if os.path.isfile(report_path) else os.path.join(folder, 'report.md')
    found = []
    known_file = os.path.join(folder, 'known.json')
    not_checker = {'verdict': 'fail', 'check': 'shot checker\'s report', 'where': '',
                   'fix': 'run the shot checker on this plate: BLEND=SCENE.blend paper-film/tools/check-shot.sh SHOT_SCRIPT CHECK_FILE OUT_FOLDER PLATE, '
                          'and give its OUT_FOLDER (or OUT_FOLDER/report.md)'}
    if os.path.exists(known_file):
        try:
            known = load_json(known_file)
        except (ValueError, OSError) as error:
            return [dict(not_checker, text=f'{known_file} is not valid JSON ({short(error, 120)})')]
        if not (isinstance(known, dict) and known.get('version') and isinstance(known.get('problems'), list)
                and str(known.get('about', '')).startswith('check_shot.py')):
            return [dict(not_checker, text=f'{known_file} was not written by check_shot.py (it has no "about", "version" and "problems" of the checker)')]
        for item in known.get('problems', []):
            found.append({'verdict': 'fail', 'check': f'shot checker: {item.get("rule", "")}', 'where': '', 'text': short(item.get('what', '')),
                          'fix': short(item.get('fix') or '', 400)})
        for item in known.get('known', []):
            how = item.get('known') or {}
            entry = how.get('entry') or {}
            if how.get('how') == 'accepted' and not entry_is_signed(entry):
                found.append({'verdict': 'fail', 'check': f'shot checker: {item.get("rule", "")}', 'where': '',
                              'text': short(item.get('what', '')) + ' (accepted in the check file without who and when, so it counts as new)',
                              'fix': 'add "who" and "date" to the check file\'s accepted entry (or fix the problem), then run the shot checker again'})
                continue
            found.append({'verdict': 'known', 'check': f'shot checker: {item.get("rule", "")}', 'where': '', 'text': short(item.get('what', '')),
                          'accepted': {'reason': how.get('words', ''), 'who': entry.get('who', ''),
                                       'date': entry.get('date', ''), 'source': 'the check file (shot checker)'}})
        if not found:
            found.append({'verdict': 'pass', 'check': 'shot checker', 'where': '', 'text': f'check_shot.py version {known["version"]} lists no problems'})
        return found
    if not os.path.isfile(report_file):
        return [dict(not_checker, text=f'no report.md or known.json in {folder}')]
    text = open(report_file, errors='replace').read()
    if not (text.startswith(SHOT_REPORT_TITLE) and SHOT_REPORT_VERSION.search(text)):
        return [dict(not_checker, text=f'{os.path.basename(report_file)} is not the shot checker\'s report (it has no "{SHOT_REPORT_TITLE.strip()}" title and '
                                       '"Made by check_shot.py version" line)')]
    section = ''
    for line in text.splitlines():
        if line.startswith('## '):
            section = line[3:].strip().lower()
            continue
        match = re.match(r'^(\d+)\. \*\*(.+?)\.\*\* (.*)$', line)
        if section == 'problems' and match:
            found.append({'verdict': 'fail', 'check': f'shot checker: {match.group(2)}', 'where': '', 'text': short(match.group(3)), 'fix': ''})
        elif section == 'problems' and line.strip().startswith('- Fix:') and found:
            found[-1]['fix'] = short(line.strip()[6:], 400)
        elif section == 'known and allowed' and line.startswith('- **'):
            m = re.match(r'^- \*\*(.+?)\.\*\* (.*)$', line)
            if m:
                found.append({'verdict': 'known', 'check': f'shot checker: {m.group(1)}', 'where': '', 'text': short(m.group(2)),
                              'accepted': {'reason': 'listed under "Known and allowed" by the shot checker', 'who': '', 'date': '', 'source': 'shot checker'}})
        elif section == 'known and allowed' and line.strip().startswith('- Accepted:') and found and found[-1]['verdict'] == 'known':
            signed = re.search(r'\(([^()]*), (\d{4}-\d{2}-\d{2})\)\s*$', line.strip())
            if not signed or signed.group(1).strip() in ('', 'None'):
                found[-1].update({'verdict': 'fail', 'text': found[-1]['text'] + ' (accepted in the check file without who and when, so it counts as new)',
                                  'fix': 'add "who" and "date" to the check file\'s accepted entry (or fix the problem), then run the shot checker again'})
                found[-1].pop('accepted', None)
            else:
                found[-1]['accepted'].update({'who': signed.group(1).strip(), 'date': signed.group(2)})
    if not found:
        found.append({'verdict': 'pass', 'check': 'shot checker', 'where': '', 'text': 'the report lists no problems'})
    return found


def picture_size(path):
    """(width, height) of a PNG or JPEG picture, or None (PIL when it is there, else the PNG header)."""
    try:
        from PIL import Image
        with Image.open(path) as picture:
            return picture.size
    except Exception:   # noqa: BLE001 - fall back to reading a PNG's header
        pass
    try:
        with open(path, 'rb') as handle:
            head = handle.read(24)
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            return int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')
    except OSError:
        pass
    return None


PICTURE_EXTENSIONS = ('.png', '.jpg', '.jpeg')


def picture_files(folder):
    if not folder or not os.path.isdir(folder):
        return []
    return sorted(os.path.join(folder, name) for name in os.listdir(folder) if name.lower().endswith(PICTURE_EXTENSIONS))


def audit_freshness(run, audit_path, audit_data, blend, where):
    """The audit must describe THIS scene file: its scene_sha1 against the sha1 of the scene file (the one given, else the one the audit names
    beside itself). Without a scene file it is a look (not checked); a changed file fails (a stale audit)."""
    if not blend and isinstance(audit_data, dict) and audit_data.get('scene_file'):
        beside = os.path.join(os.path.dirname(os.path.abspath(audit_path)), audit_data['scene_file'])
        if os.path.exists(beside):
            blend = beside
            run.register(beside)
            run.notes.append(f'The scene file was not given (--blend); {beside}, the one the audit names beside itself, was used for the freshness check.')
    if not blend:
        return [{'verdict': 'warn', 'check': 'place: stale audit', 'where': where, 'text': 'not checked: the scene file was not given (--blend FILE.blend), so a changed scene would not be noticed.',
                 'fix': 'give --blend with the finished scene file.'}]
    recorded = audit_data.get('scene_sha1') if isinstance(audit_data, dict) else None
    now = sha1_of(blend)
    if not recorded:
        return [{'verdict': 'fail', 'check': 'place: stale audit', 'where': where, 'text': f'the audit records no scene_sha1, so it cannot be tied to {os.path.basename(blend)}.',
                 'fix': 'make the audit again: explainer-film-place audit --scene SCENE.blend'}]
    if now != recorded:
        return [{'verdict': 'fail', 'check': 'place: stale audit', 'where': where,
                 'text': f'the scene file changed after the audit was made (audit {recorded[:8]}, file {str(now)[:8]}): the audit says nothing about this file.',
                 'fix': 'run explainer-film-place audit on the saved file again, then this stage.'}]
    return [{'verdict': 'pass', 'check': 'place: stale audit', 'where': where, 'text': f'the audit was made from this exact scene file ({os.path.basename(blend)})', 'fix': ''}]


def run_place_audit(run, item, where, blend, why):
    """The place audit's checks for a stage: the judge, and the freshness of the audit. Returns True when an audit was read."""
    audit = run.need(item, 'place_audit', why)
    if not audit:
        return False
    facts = item.get('real_world_facts') if item.get('real_world_facts') and run.need(item, 'real_world_facts', 'place_audit_check.py check', required=False) else None
    settings_path = item.get('place_settings') if item.get('place_settings') and run.need(item, 'place_settings', 'place_audit_check.py check', required=False) else None
    arguments = ['check', audit] + (['--facts', facts] if facts else []) + (['--place-settings', settings_path] if settings_path else []) + (['--allow-quick'] if item.get('allow_quick') else []) + ['--skip-freshness']
    run.run_tool('the place audit: surfaces, wear and construction (place_audit_check.py)', 'calculators/place_audit_check.py', arguments, where=where)
    data = run.read_json('place_audit', audit, why)
    run.add_check('the audit is about this scene file (freshness)', audit_freshness(run, audit, data, blend, where), where=where, tool='preflight.py place')
    return True


def stage_place(run, item, where):
    blend = item.get('blend') if item.get('blend') and run.need(item, 'blend', 'the freshness check of the audit', required=False) else None
    if not item.get('blend'):
        run.need(item, 'blend', 'the freshness check of the audit', required=False, why='without it a scene changed after the audit would not be noticed (the audit\'s own scene_file is used when it is beside the audit)')
    audited = run_place_audit(run, item, where, blend, 'place_audit_check.py check')
    pictures = picture_files(item.get('place_pictures'))
    if item.get('place_pictures'):
        run.need(item, 'place_pictures', 'picture_measures.py check', required=False)
    guard = item.get('style_guard') if item.get('style_guard') and run.need(item, 'style_guard', 'picture_measures.py check', required=False) else None
    if pictures and guard:
        previous = picture_files(item.get('previous_pictures')) if item.get('previous_pictures') else []
        arguments = ['check'] + pictures + ['--guard', guard] + (['--previous', previous[0]] if previous else [])
        run.run_tool('the place pictures against the style guard (picture_measures.py)', 'calculators/picture_measures.py', arguments, where=where)
        data = run.read_json('style_guard', guard, 'picture_measures.py check')
        if isinstance(data, dict) and data.get('provisional'):
            run.add_check('the style guard is provisional', [{'verdict': 'warn', 'check': 'place pictures: guard', 'where': where,
                          'text': 'the guard was made from the first honest picture and has not been accepted by a person yet, so it locks in whatever that picture looked like.',
                          'fix': 'have a person accept it (remove "provisional": true and write who and when), or measure against absolute floors.'}], where=where, tool='preflight.py place')
    elif pictures:
        run.add_check('the place pictures against the style guard', [{'verdict': 'warn', 'check': 'place pictures: not checked', 'where': where,
                      'text': 'not checked: there are pictures but no style guard (--style-guard).', 'fix': 'make one from the first honest picture: explainer-film-place measure PICTURE --make-guard --out style-guard.json'}], where=where, tool='preflight.py place')
    fresh = item.get('fresh_check') if item.get('fresh_check') and run.need(item, 'fresh_check', 'place_audit_check.py fresh', required=False) else None
    if fresh:
        arguments = ['fresh', fresh] + (['--audit', item['place_audit']] if item.get('place_audit') and os.path.exists(item['place_audit']) else [])
        run.run_tool('a fresh checker\'s result (place_audit_check.py fresh)', 'calculators/place_audit_check.py', arguments, where=where)
    else:
        run.add_check('a fresh checker has looked', [{'verdict': 'warn', 'check': 'place: fresh checker', 'where': where, 'text': 'not checked: no fresh checker has looked at this place (--fresh-check).',
                      'fix': 'run the workflow build-a-place (phase Check), or ask a helper who did not build the place to recompute its claims.'}], where=where, tool='preflight.py place')
    run.notes.append('The order of the stages: shots (before building), build the place, place (this stage), then plates (before paying for paintings). '
                     'A place that passes here has not been judged by eye: the fresh checkers and the person still look.')
    return audited


def plate_engine(item, plate):
    """The engine a plate was drawn with, from the place kit's render record (PLATE.json beside the picture, or the plan's render_record);
    (engine, record path, scene) or (None, None, None)."""
    record = item.get('render_record') or (os.path.splitext(plate)[0] + '.json' if plate else None)
    if not record or not os.path.exists(record):
        return None, None, None
    try:
        data = load_json(record)
    except (ValueError, OSError):
        return None, None, None
    engine = str(data.get('engine') or '').upper() if isinstance(data, dict) else ''
    return (engine or None), record, (data.get('scene') if isinstance(data, dict) else None)


def plate_engines_check(run, items):
    """After every plate: a LOOK when plates of one place were drawn with different engines (EEVEE streets came out cold blue and Cycles
    streets warm gold, mostly because EEVEE's light cut-off stops lamp light reaching the road; the painter follows the plate)."""
    places = {}
    for item, (engine, record, scene) in getattr(run, 'plate_engines', []):
        if engine:
            key = item.get('place') or scene or item.get('blend') or 'the plates of this run'
            places.setdefault(key, {}).setdefault(engine, []).append(item.get('name') or item.get('view') or os.path.basename(record))
    findings = []
    for place, engines in places.items():
        if len(engines) > 1:
            findings.append({'verdict': 'warn', 'check': 'one engine per place', 'where': str(place),
                             'text': 'plates of one place were drawn with different engines (' + '; '.join(f'{e}: {", ".join(v)}' for e, v in sorted(engines.items()))
                                     + '). The renderer sets the mood the painter follows: EEVEE streets came out cold blue and Cycles streets warm gold.',
                             'fix': 'draw every plate of one place with the same renderer (if any plate needs Cycles, draw them all with Cycles: "renderer": "cycles" in place-settings.json), then paint'})
        else:
            findings.append({'verdict': 'pass', 'check': 'one engine per place', 'where': str(place), 'text': f'every plate drawn with {next(iter(engines))}'})
    if findings:
        run.add_check('the plates of one place drawn with one engine', findings, tool='preflight.py plates')


def stage_plates(run, item, where):
    check = run.need(item, 'check', 'paint_request.py preflight')
    plate = run.need(item, 'plate', 'paint_request.py preflight')
    engine, record, scene = plate_engine(item, plate)
    if record:
        run.register(record)
    if not hasattr(run, 'plate_engines'):
        run.plate_engines = []
    run.plate_engines.append((item, (engine, record, scene)))
    if engine == 'CYCLES':
        run.add_check('the plate\'s engine against the painting checks', [{'verdict': 'warn', 'check': 'cycles plate', 'where': where,
                      'text': 'this plate was drawn with Cycles: the painting checks (paint_request.py, after_painting.py) were tuned on EEVEE plates and are untested on '
                              'Cycles plates, and Cycles has effects of its own (a fire drum lit orange, a speck at a roof corner, a sky dome that darkened). Not tried '
                              'either: Cycles in a moving shot (its noise clean-up could flicker).',
                      'fix': 'look at the plate and the painting yourself as well as reading the checks'}], where=where, tool='preflight.py plates')
    plate_facts = run.need(item, 'plate_facts', 'paint_request.py preflight')
    render_log = run.need(item, 'render_log', 'plan_lights.py render-log and paint_request.py (a paid repaint needs a clean render)')
    shot_report = run.need(item, 'shot_report', 'paint_request.py (a paid repaint needs the shot checker\'s light rules passed)')
    if render_log:
        # the log must be Blender's, and must save this plate: an empty or unrelated log proves nothing (decision 37)
        run.run_tool('the plate rendered cleanly (plan_lights.py render-log)', 'calculators/plan_lights.py',
                     ['render-log', render_log] + (['--plate', plate] if plate else []), where=where)
    if shot_report:
        report_findings = shot_report_findings(shot_report)
        run.add_check('the shot checker\'s report: new problems only', report_findings, where=where, tool='check_shot.py report')
    blend = item.get('blend')
    if check:
        data = run.read_json('check', check, 'paint_request.py preflight')
        if isinstance(data, dict):
            run.show_known(f'{os.path.basename(check)} (check file)', data.get('accepted', []), where=where)
            stamped = data.get('scene_file')
            if stamped and not blend:
                beside = stamped if os.path.isabs(stamped) else os.path.join(os.path.dirname(os.path.abspath(check)), stamped)
                if os.path.exists(beside):
                    blend = beside
                    item['blend'] = beside
                    run.register(beside)
                    run.notes.append(f'The check file names the scene it was made from ({stamped}), so the place audit is required before paying for a painting of it.')
        else:
            check = None
    if blend:
        run_place_audit(run, item, where, blend, 'place_audit_check.py check (a place built in Blender must pass its audit before a paid painting)')
    else:
        run.add_check('the place audit (when the plate comes from a place built in Blender)', [{'verdict': 'warn', 'check': 'place: not audited', 'where': where,
                      'text': 'not checked: no scene file was named (--blend FILE.blend with --place-audit, or scene_file in the check file), so nothing here says the place passed the surface, wear and construction audit before this paid painting.',
                      'fix': 'if the plate comes from a place built in Blender, give --blend and --place-audit (explainer-film-place finish writes the audit); if it does not, this look can stay.'}], where=where, tool='preflight.py plates')
    if check and plate and plate_facts:
        arguments = ['preflight', '--check', check, '--facts', plate_facts, '--plate', plate, '--work-folder', os.path.join(run.work, 'paint-work')]
        for key, option in (('render_log', '--render-log'), ('shot_report', '--shot-report'), ('helper_plate', '--helper-plate'),
                            ('real_names', '--real-names'), ('brief', '--brief')):
            if item.get(key) and os.path.exists(item[key]):
                path = item[key]
                if key == 'shot_report' and os.path.isdir(path):
                    path = os.path.join(path, 'report.md')
                arguments += [option, path]
                run.register(item[key])
        if item.get('place_facts') and item.get('view') and run.need(item, 'place_facts', 'paint_request.py', required=False):
            arguments += ['--place-facts', item['place_facts'], '--view', item['view']]
        if item.get('exposure') is not None:
            arguments += ['--exposure', str(item['exposure'])]
        if item.get('hollow'):
            arguments += ['--hollow'] + list(item['hollow'])
        if not item.get('helper_plate'):
            run.need(item, 'helper_plate', 'paint_request.py preflight', required=False,
                     why='without it the long-shadow check (lesson 135) cannot run')
        run.run_tool('the plate is ready to paint (paint_request.py preflight)', 'calculators/paint_request.py', arguments, where=where)
    # the price, from the pictures really sent: the plate as given and the style picture (the place's master painting)
    behind = bool(item.get('with_behind'))
    arguments = ['price'] + (['--behind'] if behind else [])
    sent, how = [], []
    plate_size = picture_size(plate) if plate else None
    style = item.get('style_picture') if item.get('style_picture') and run.need(item, 'style_picture', 'paint_request.py price', required=False) else None
    style_size = picture_size(style) if style else None
    if plate_size:
        sent.append(f'{plate_size[0]}x{plate_size[1]}')
        how.append(f'the plate {plate_size[0]} x {plate_size[1]}')
    if plate_size and style_size:
        sent.append(f'{style_size[0]}x{style_size[1]}')
        how.append(f'the style picture {style_size[0]} x {style_size[1]}')
    elif plate_size:
        default_style = run.house_number('painting.style_picture_size_pixels', [768, 1368])
        sent.append(f'{default_style[0]}x{default_style[1]}')
        how.append(f'the house\'s style-picture size {default_style[0]} x {default_style[1]} (give --style-picture for its real size)')
    if sent:
        arguments += ['--send'] + sent
    if not behind and item.get('helper_plate'):
        run.notes.append('Priced without a behind painting: say --with-behind (or "with_behind": true in the plan) if this view gets one.')
    priced = run.run_tool('the painting\'s price (paint_request.py price)', 'calculators/paint_request.py', arguments, where=where)
    result = priced['result'] or {}
    if result.get('total_cents') is not None:
        main = result.get('main_painting', {})
        run.cost(f'painting {where or "the plate"}' + (' and its behind painting' if behind else ''), result['total_cents'] / 100,
                 f'an estimate: {main.get("rate_cents_per_megapixel")} c a megapixel (read {main.get("rate_read_on")}) x the megapixels returned and sent'
                 + (f' ({", ".join(how)})' if how else ' (the house\'s plate and style sizes)'))
    if item.get('models'):
        if run.need(item, 'models', 'model_lint.py', required=False):
            files = sorted({p for pattern in item['models'] for p in (glob.glob(pattern) or [pattern])})
            # one dressed set (their places are shared) only when the plan says so; separate prop files each sit at their own origin
            as_set = bool(item.get('models_as_set'))
            run.run_tool('models: stripes, same-plane faces, floors, names, glass (model_lint.py)', 'paper-film/blender/model_lint.py',
                         files + (['--as-set'] if as_set and len(files) > 1 else []), where=where)


def stage_paint(run, item, where):
    painting = run.need(item, 'painting', 'after_painting.py check')
    plate = run.need(item, 'plate', 'after_painting.py check')
    check = run.need(item, 'check', 'after_painting.py check')
    plate_facts = run.need(item, 'plate_facts', 'after_painting.py check')
    if not (painting and plate and check and plate_facts):
        return
    data = run.read_json('check', check, 'after_painting.py check')
    if not isinstance(data, dict):
        return
    run.show_known(f'{os.path.basename(check)} (check file)', data.get('accepted', []), where=where)
    out_folder = os.path.join(run.work, f'painting-{slug(where or os.path.basename(painting))}')
    arguments = ['check', '--painting', painting, '--plate', plate, '--check', check, '--facts', plate_facts, '--out-folder', out_folder]
    for key, option in (('behind', '--behind'), ('near_list', '--near-list'), ('helper_plate', '--helper-plate'), ('standard', '--standard')):
        if item.get(key) and run.need(item, key, 'after_painting.py check', required=False):
            arguments += [option, item[key]]
    if item.get('figures'):
        arguments += ['--figures'] + list(item['figures'])
    if item.get('toe') is not None:
        arguments += ['--toe', str(int(item['toe']))]
    run.run_tool('the painting as it arrived (after_painting.py check)', 'calculators/after_painting.py', arguments, where=where)
    run.notes.append(f'The lined-up painting (PNG) is in {out_folder}: use that file, not the one the painter returned.')


def stage_pages(run, item, where):
    events = item.get('events')
    if not events and item.get('scene') and (item.get('make_events') or run.args.make_events) and not node_modules_ready(run):
        return
    if not events and item.get('scene') and (item.get('make_events') or run.args.make_events):
        events = os.path.join(run.work, 'page-events.json')
        arguments = [item['scene'], events] + (['--pages', str(item['pages_list'] if isinstance(item.get('pages_list'), str) else
                                                             ','.join(str(p) for p in item['pages_list']))] if item.get('pages_list') else [])
        run.run_tool('what every page does (page_events.mjs)', 'paper-film/tools/page_events.mjs', arguments, kind='node', where=where,
                     json_out=False, settings=False)
        if os.path.exists(events):
            item = dict(item, events=events)
    events = run.need(item, 'events', 'plan_page_timing.py check, check_page_layout.mjs')
    if events:
        accepted_file = timing_accepted_file(run, item)
        arguments = ['check', events]
        if item.get('numbers_ledger') and run.need(item, 'numbers_ledger', 'plan_page_timing.py check', required=False):
            arguments += ['--ledger', item['numbers_ledger']]
        if accepted_file:
            arguments += ['--accepted', accepted_file]
        run.run_tool('timing and words on screen (plan_page_timing.py check)', 'calculators/plan_page_timing.py', arguments, where=where)
        run.run_tool('pops, effects, held shots and overlaps (check_page_layout.mjs)', 'paper-film/tools/check_page_layout.mjs', [events],
                     kind='node', where=where)
    if item.get('camera_log'):
        if run.need(item, 'camera_log', 'camera_audit.py', required=False):
            arguments = [item['camera_log']]
            if item.get('timeline') and item.get('page') and run.need(item, 'timeline', 'camera_audit.py', required=False):
                arguments += ['--timeline', item['timeline'], '--page', str(item['page'])]
            if item.get('place_facts') and item.get('view') and run.need(item, 'place_facts', 'camera_audit.py --built-set', required=False):
                arguments += ['--built-set', '--place-facts', item['place_facts'], '--view', item['view']]
            run.run_tool('the camera rule and the built-set slide (camera_audit.py)', 'paper-film/tools/camera_audit.py', arguments, where=where)
    else:
        run.need(item, 'camera_log', 'camera_audit.py', required=False, why='without it the camera rule (at most 3 moves a shot, no turn in a slide) is not measured')
    if item.get('paper_pages') and run.need(item, 'paper_pages', 'plan_effects.py lint', required=False):
        files = sorted({p for pattern in item['paper_pages'] for p in (glob.glob(pattern) or [pattern])})
        run.run_tool('paper pages make their effects through kit.effect (plan_effects.py lint)', 'calculators/plan_effects.py', ['lint'] + files, where=where)


def node_modules_ready(run):
    """page_events.mjs runs the pages in a browser (playwright): the kit needs its node modules. Without them the stage
    stops with the command that installs them, not with a raw Node error."""
    found = os.path.join(run.kit, 'paper-film', 'node_modules')
    named = os.environ.get('PAPER_FILM_PLAYWRIGHT')
    if (named and os.path.exists(named)) or os.path.isdir(os.path.join(found, 'playwright-core')):
        return True
    run.missing.append({'input': 'events', 'option': '--events', 'what': INPUTS['events'][0], 'needed_by': 'page_events.mjs (--make-events)',
                        'make': 'install the drawing tools first: run explainer-film-setup /path/to/work/film-kit (it copies the kit and installs '
                                'paper-film/node_modules), then give that kit here with --kit; or set PAPER_FILM_PLAYWRIGHT to a playwright-core '
                                'index.mjs; or make the events yourself: ' + INPUTS['events'][1],
                        'required': True, 'why': '', 'given_but_absent': [],
                        'unusable': f'{found}: no playwright there, so page_events.mjs cannot run the pages'})
    return False


def timing_accepted_file(run, item):
    """The timing problems accepted on purpose, for plan_page_timing.py: the given file plus the plan's entries for this stage."""
    entries = []
    if item.get('timing_accepted') and run.need(item, 'timing_accepted', 'plan_page_timing.py check', required=False):
        data = run.read_json('timing_accepted', item['timing_accepted'], 'plan_page_timing.py check')
        listed = data.get('accepted', []) if isinstance(data, dict) else data
        if data is not None and not isinstance(listed, list):
            run.unusable('timing_accepted', item['timing_accepted'], 'it is not a list of entries (nor {"accepted": [...]})', 'plan_page_timing.py check')
            listed = []
        entries += listed or []
    entries += [{k: v for k, v in e.items() if k in ('check', 'page', 'text', 'reason', 'who', 'date')} for e in run.accepted
                if e.get('stage') in (None, '', 'pages') and e.get('check') and e.get('text')]
    if not entries:
        return None
    os.makedirs(run.work, exist_ok=True)
    path = os.path.join(run.work, 'timing-accepted.json')
    with open(path, 'w') as handle:
        json.dump(entries, handle, indent=1)
    return path


def page_file_list(values):
    files = []
    for value in values or []:
        if os.path.isdir(value):
            files += [os.path.join(folder, n) for folder, _, names in os.walk(value) for n in names if n.endswith(('.js', '.mjs'))]
        else:
            files += glob.glob(value) or ([value] if os.path.exists(value) else [])
    return sorted(set(files))


SEVERITY_VERDICT = {'must fix': 'fail', 'should fix': 'warn', 'nice to have': 'info'}


def critique_list(data):
    """The critique-film workflow's confirmed findings: {"critics": [...], "verdict": {"confirmed": [...], "rejected": [...],
    "summary": ...}} (or only its "verdict" object). None when the file is not such a result. An empty "confirmed" list
    means the skeptic confirmed nothing: the critics' raw findings (some of them rejected) are never read instead."""
    if not isinstance(data, dict):
        return None
    verdict = data.get('verdict')
    if isinstance(verdict, dict) and isinstance(verdict.get('confirmed'), list):
        return verdict['confirmed']
    if isinstance(data.get('confirmed'), list):
        return data['confirmed']
    return None


def severity_of(finding):
    """The finding's severity as the workflow writes it ("must fix", "should fix", "nice to have"); "-" and "_" count as
    spaces and case does not matter. An unknown or missing severity counts as must fix."""
    words = plain_name(finding.get('severity', ''))
    return words if words in SEVERITY_VERDICT else 'must fix'


def history_critic_finding(data):
    """Period accuracy needs its own critic: the critique's "critics" list must hold one whose area starts with "history" (it looks at every
    still and every word written on a prop and asks: was this in that place and that year?). A FAIL without one (an accepted entry, stage
    film, check "history critic", can waive it); only a LOOK when the file has no "critics" list at all (an older shape)."""
    critics = data.get('critics') if isinstance(data, dict) else None
    if not isinstance(critics, list):
        return {'verdict': 'warn', 'check': 'history critic', 'where': '',
                'text': 'the critique has no "critics" list (an older shape), so whether a critic judged period accuracy is not known',
                'fix': 'run the critique-film workflow again: it has a history critic (wrong-era objects, too much of a thing, words on props)'}
    areas = [str((c.get('area') or c.get('key') or '') if isinstance(c, dict) else c) for c in critics]
    if any(area.strip().lower().startswith('history') for area in areas):
        return {'verdict': 'pass', 'check': 'history critic', 'where': '', 'text': f'a history critic looked (areas: {", ".join(a for a in areas if a)})'}
    return {'verdict': 'fail', 'check': 'history critic', 'where': '',
            'text': f'no critic\'s area starts with "history" (areas: {", ".join(a for a in areas if a) or "none named"}): nobody judged whether what the viewer '
                    'sees was in that place and that year (wrong-era vehicles, a symbol that reads wrongly today, too much of a thing that was scarce)',
            'fix': 'run the critique-film workflow again (it has a history critic), or accept this in the plan\'s "accepted" (stage film, check history critic, '
                   'with a reason, who and date)'}


def critique_findings(run, path, newest, newest_file):
    found = []
    age = os.path.getmtime(path)
    when = datetime.fromtimestamp(age).strftime('%Y-%m-%d %H:%M')
    if age <= newest:
        found.append({'verdict': 'fail', 'check': 'critique newer than the pages', 'where': '',
                      'text': f'the critique ({when}) is older than {os.path.basename(newest_file)} '
                              f'({datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M")}): the pages changed after it',
                      'fix': 'run the critique-film workflow again on fresh stills of the changed pages, then mark each finding fixed or accepted'})
    else:
        found.append({'verdict': 'pass', 'check': 'critique newer than the pages', 'where': '',
                      'text': f'the critique ({when}) is newer than every page file (newest: {os.path.basename(newest_file)})'})
    if not path.endswith(('.json', '.json.gz')):
        run.unusable('critique', path, 'it is not JSON, so its findings cannot be counted: save the critique-film workflow\'s result as JSON',
                     'the critique gate')
        return found
    data = run.read_json('critique', path, 'the critique gate')
    if data is None:
        return found
    findings = critique_list(data)
    if findings is None:
        run.unusable('critique', path, 'not a critique-film result: it holds no "verdict": {"confirmed": [...]} (the workflow\'s list of confirmed '
                     'findings, empty when there is nothing to fix)', 'the critique gate')
        return found
    found.append(history_critic_finding(data))
    if not findings:
        found.append({'verdict': 'pass', 'check': 'critique findings', 'where': '',
                      'text': 'the critique confirmed no findings' + (f' ({len(data["verdict"].get("rejected", []))} rejected by its skeptic)'
                                                                       if isinstance(data.get('verdict'), dict) and data['verdict'].get('rejected') else '')})
    open_count = 0
    for f in findings:
        if not isinstance(f, dict):
            continue
        status = plain_name(f.get('status', ''))
        severity = severity_of(f)
        where = f'page {f.get("page")}' + (f' at {f.get("time")}' if f.get('time') else '')
        text = short(f.get('what', ''), 300)
        if status in ('fixed', 'rejected', 'not a fault'):
            found.append({'verdict': 'pass', 'check': f'critique finding ({severity})', 'where': where, 'text': f'{status}: {text}'})
        elif status == 'accepted' and entry_is_signed(f):
            found.append({'verdict': 'known', 'check': f'critique finding ({severity})', 'where': where, 'text': text,
                          'accepted': {'reason': f.get('reason', ''), 'who': f['who'], 'date': f['date'], 'source': 'the critique'}})
        else:
            open_count += 1
            raw = str(f.get('severity', '')).strip()
            found.append({'verdict': SEVERITY_VERDICT[severity], 'check': f'critique finding ({severity})', 'where': where,
                          'text': text + (f' (severity "{raw}" is not one the workflow uses: counted as must fix)' if raw and plain_name(raw) not in SEVERITY_VERDICT else '')
                          + (' (marked accepted without who and a real date: still open)' if status == 'accepted' else ''),
                          'fix': short(f.get('fix', ''), 300)})
    if open_count:
        found.append({'verdict': 'info', 'check': 'critique findings', 'where': '',
                      'text': f'{open_count} finding(s) not yet marked "status": "fixed" or "accepted" (with "who" and "date") in the critique file'})
    return found


def newest_report(reports, stage):
    files = sorted(glob.glob(os.path.join(reports, f'preflight-{stage}-*.json')))
    return files[-1] if files else None


def pages_report_for(reports, events_path, events_sha):
    """The newest pages report made on these very events (an input with the same sha1), with how many pages reports there
    are in all; (None, count) when none was made on them."""
    files = sorted(glob.glob(os.path.join(reports, 'preflight-pages-*.json')))
    for path in reversed(files):
        try:
            data = load_json(path)
        except (ValueError, OSError):
            continue
        inputs = data.get('inputs', {}) or {}
        if inputs.get(os.path.abspath(events_path)) == events_sha or events_sha in inputs.values():
            return path, data, len(files)
    return None, None, len(files)


def stage_film(run, item, where):
    page_files = run.need(item, 'page_files', 'the critique and pages-report age checks')
    files = page_file_list(page_files) if page_files else []
    for path in files:
        run.register(path)
    newest = max((os.path.getmtime(p) for p in files), default=None)
    newest_file = max(files, key=os.path.getmtime) if files else ''
    events = run.need(item, 'events', 'the pages-report check and plan_budget.py filming')
    if not item.get('scene'):
        run.missing.append({'input': 'scene', 'option': '--scene', 'what': INPUTS['scene'][0], 'make': INPUTS['scene'][1],
                            'needed_by': 'plan_budget.py filming', 'required': True, 'why': '', 'given_but_absent': []})
    critique = run.need(item, 'critique', 'the critique gate (fresh critics before filming)')
    if critique and newest is not None:
        run.add_check('a critique newer than every page file, each finding fixed or accepted', critique_findings(run, critique, newest, newest_file), where=where)
    if newest is not None and events:
        # the pages report must be about THESE events, and the events must be newer than every page file (made after the
        # last page edit): another chapter's or an older run's passing report proves nothing about these pages
        events_sha = sha1_of(events)
        findings = []
        if os.path.getmtime(events) <= newest:
            findings.append({'verdict': 'fail', 'check': 'events newer than the pages', 'where': '',
                             'text': f'the events file {os.path.basename(events)} ({datetime.fromtimestamp(os.path.getmtime(events)).strftime("%Y-%m-%d %H:%M")}) '
                                     f'is older than {os.path.basename(newest_file)}: the pages changed after the events were made',
                             'fix': 'make the events again (node paper-film/tools/page_events.mjs SCENE OUT.json, or the pages stage with --make-events), '
                                    'then run the pages stage on them'})
        report, data, count = pages_report_for(run.reports, events, events_sha)
        if not report:
            findings.append({'verdict': 'fail', 'check': 'pages report on these events', 'where': '',
                             'text': f'no pages report in {run.reports} was made on {os.path.basename(events)} (sha1 {events_sha[:8]}; '
                                     f'{count} pages report(s) there, all on other events)',
                             'fix': f'run: explainer-film-preflight pages --events {events} (with the same plan and reports folder)'})
        else:
            made = datetime.strptime(data['started'], '%Y-%m-%d %H:%M:%S').timestamp()
            if made <= newest:
                findings.append({'verdict': 'fail', 'check': 'pages report newer than the pages', 'where': '',
                                 'text': f'the newest pages report on these events ({data["started"]}) is older than {os.path.basename(newest_file)}',
                                 'fix': 'run: explainer-film-preflight pages again'})
            if data.get('verdict') not in ('pass', 'warn'):
                findings.append({'verdict': 'fail', 'check': 'pages report passed', 'where': '',
                                 'text': f'the newest pages report on these events says {data.get("verdict", "?").upper()} ({os.path.basename(report)})',
                                 'fix': 'fix what it lists (or accept it, with who and when), then run the pages stage again'})
            changed = [p for p, h in (data.get('inputs') or {}).items() if sha1_of(p) != h]
            if changed:
                findings.append({'verdict': 'fail', 'check': 'pages report inputs unchanged', 'where': '',
                                 'text': f'{len(changed)} input(s) of that pages report changed since: ' + ', '.join(os.path.basename(p) for p in changed[:6]),
                                 'fix': 'run: explainer-film-preflight pages again'})
            if not any(f['verdict'] == 'fail' for f in findings):
                findings.append({'verdict': 'pass', 'check': 'pages report', 'where': '',
                                 'text': f'the pages report {os.path.basename(report)} ({data["started"]}) was made on these events, passed, and is newer '
                                         'than every page file'})
        run.add_check('a passed pages report on these events, newer than every page file', findings, where=where)
    if events and item.get('scene'):
        arguments = ['filming', events, '--scene', item['scene']]
        if item.get('rates') and run.need(item, 'rates', 'plan_budget.py filming', required=False):
            arguments += ['--rates', item['rates']]
        else:
            run.need(item, 'rates', 'plan_budget.py filming', required=False,
                     why='without this film\'s own measured rates the plan uses the table (round 4), which missed round 5 by 52%')
        for key, option in (('processors', '--processors'), ('free_memory_gb', '--free-memory-gb'), ('free_disk_gb', '--free-disk-gb'), ('from_frame', '--from-frame'),
                            ('to_frame', '--to-frame'), ('blender_running', '--blender-running')):
            if item.get(key) is not None:
                arguments += [option, str(item[key])]
        record = run.run_tool('filming time, workers, pieces, memory and disk (plan_budget.py filming)', 'calculators/plan_budget.py', arguments, where=where)
        result = record['result'] or {}
        if result.get('predicted_seconds'):
            run.step_time('filming', result['predicted_seconds'], f'{result.get("workers")} worker(s), {len(result.get("stretches", []))} stretch(es) under 2 hours; '
                          f'rates from {"this film" if item.get("rates") else "the table (a fallback)"}')


def clip_critique_findings(run, path, film):
    """A fresh helper's critique of the FILMED clip in motion (faults stills cannot show: a shadow that fades in when a move starts, a barrel
    that floats, a one-frame colour change, a pale outline once the camera moves). It must be newer than the film and about this film, say
    what it looked at, and every "must fix" finding must be fixed or accepted (with who and date), as for the critique before filming."""
    found = []
    data = run.read_json('clip_critique', path, 'the clip critique gate')
    if data is None:
        return found
    if not isinstance(data, dict) or not isinstance(data.get('findings'), list):
        run.unusable('clip_critique', path, 'not a clip critique: it needs {"film": PATH, "looked_at": [...], "findings": [{"time", "what", "severity", '
                     '"status", "who", "date"}]} (an empty findings list when there is nothing to fix)', 'the clip critique gate')
        return found
    when = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
    if film and os.path.getmtime(path) <= os.path.getmtime(film):
        found.append({'verdict': 'fail', 'check': 'clip critique newer than the film', 'where': '',
                      'text': f'the clip critique ({when}) is older than the film {os.path.basename(film)}: the film changed after it was judged',
                      'fix': 'have a fresh helper judge the new film in motion (the film-critic agent\'s clip mode) and save its clip critique'})
    elif film:
        found.append({'verdict': 'pass', 'check': 'clip critique newer than the film', 'where': '', 'text': f'the clip critique ({when}) is newer than the film'})
    named = data.get('film')
    if film and named and os.path.basename(str(named)) != os.path.basename(film):
        found.append({'verdict': 'fail', 'check': 'clip critique of this film', 'where': '',
                      'text': f'the clip critique judged {os.path.basename(str(named))}, not {os.path.basename(film)}', 'fix': 'judge this film in motion'})
    if not data.get('looked_at'):
        found.append({'verdict': 'warn', 'check': 'clip critique looked at', 'where': '', 'text': 'the clip critique does not say what it looked at (the clip, contact sheets, times)',
                      'fix': 'ask the helper to list what it watched'})
    open_count = 0
    for f in data['findings']:
        if not isinstance(f, dict):
            continue
        status, severity = plain_name(f.get('status', '')), severity_of(f)
        where = f'at {f.get("time")}' if f.get('time') is not None else ''
        text = short(f.get('what', ''), 300)
        if status in ('fixed', 'rejected', 'not a fault'):
            found.append({'verdict': 'pass', 'check': f'clip critique finding ({severity})', 'where': where, 'text': f'{status}: {text}'})
        elif status == 'accepted' and entry_is_signed(f):
            found.append({'verdict': 'known', 'check': f'clip critique finding ({severity})', 'where': where, 'text': text,
                          'accepted': {'reason': f.get('reason', ''), 'who': f['who'], 'date': f['date'], 'source': 'the clip critique'}})
        else:
            open_count += 1
            found.append({'verdict': SEVERITY_VERDICT[severity], 'check': f'clip critique finding ({severity})', 'where': where,
                          'text': text + (' (marked accepted without who and a real date: still open)' if status == 'accepted' else ''), 'fix': short(f.get('fix', ''), 300)})
    if not data['findings']:
        found.append({'verdict': 'pass', 'check': 'clip critique findings', 'where': '', 'text': 'the clip critique found nothing to fix in motion'})
    if open_count:
        found.append({'verdict': 'info', 'check': 'clip critique findings', 'where': '', 'text': f'{open_count} finding(s) not yet marked "status": "fixed" or "accepted" (with "who" and "date")'})
    return found


def stage_finish(run, item, where):
    film = run.need(item, 'film', 'sound_gates.py loudness, length and alignment')
    mix = run.need(item, 'mix', 'sound_gates.py alignment')
    timeline = run.need(item, 'timeline', 'sound_gates.py length and alignment')
    clip = run.need(item, 'clip_critique', 'the clip critique gate (a fresh helper judged the filmed clip in motion)')
    if clip:
        run.add_check('a fresh critique of the filmed clip in motion, newer than the film, each must-fix finding fixed or accepted',
                      clip_critique_findings(run, clip, film), where=where, tool='preflight.py finish')
    if film:
        run.run_tool('loudness and true peak of the film (sound_gates.py loudness)', 'narration-tools/sound_gates.py', ['loudness', film], where=where)
    if film and timeline:
        data = run.read_json('timeline', timeline, 'sound_gates.py length')
        seconds = data.get('chapter_seconds') if isinstance(data, dict) else None
        if data is not None and not seconds:
            run.unusable('timeline', timeline, 'it has no "chapter_seconds" (a timeline from assemble_chapter_narration.py has one)', 'sound_gates.py length')
        if seconds:
            run.run_tool('the film is as long as the timeline (sound_gates.py length)', 'narration-tools/sound_gates.py',
                         ['length', film, '--expected', f'{seconds:.4f}', '--step', 'finishing'], where=where)
    if film and mix and timeline:
        run.run_tool('the film\'s sound against the mix at every page (sound_gates.py alignment)', 'narration-tools/sound_gates.py',
                     ['alignment', film, mix, timeline], where=where)
    if item.get('send') and run.need(item, 'send', 'sound_gates.py loudness', required=False):
        run.run_tool('loudness of the sendable copy (sound_gates.py loudness)', 'narration-tools/sound_gates.py', ['loudness', item['send']], where=where)
        size = os.path.getsize(item['send']) / 1e6
        limit = sendable_limit(run)
        run.add_check('the sendable copy fits a chat message', [{'verdict': 'pass' if limit is None or size <= limit else 'fail', 'check': 'sendable size',
                                                               'where': '', 'text': f'{size:.1f} MB' + (f' (at most {limit} MB)' if limit else ''),
                                                               'fix': 'encode it again at a lower bitrate (finish_film.sh SIZE_MB)'}], where=where)
    needed, free = jump_finder_memory_gb(film) if film else (None, None)
    fits = needed is not None and free is not None and needed + 2 <= free
    if film and not (item.get('jumps') or run.args.jumps or fits):
        # (a jump the finder lists outside the planned cuts is a LOOK for a person on its sheet, never a block: the delivered,
        # accepted chapter 2 shows 46 of them that are the pages' own moves and fades)
        run.notes.append('find_jumps.py was not run: it holds the whole film in memory (about '
                         + (f'{needed:.1f} GB for this film, with {free:.1f} GB free' if needed is not None and free is not None else
                            '10 GB for a 4.5-minute film') + '). Run it on a machine with the memory, or add --jumps to try anyway.')
    elif film:
        cuts = planned_cuts(run, item)
        sheet = os.path.join(run.work, 'jumps-sheet.jpg')
        os.makedirs(run.work, exist_ok=True)
        run.run_tool('jumps between frames, outside the planned cuts (find_jumps.py)', 'paper-film/tools/find_jumps.py',
                     [film, sheet, '4'] + [f'{c:.3f}' for c in cuts], where=where, json_out=False, settings=False)
    paths = list(item.get('deliver') or []) + ([item['send']] if item.get('send') else [])
    if paths:
        run.run_tool('files safe to push or send (plan_budget.py push)', 'calculators/plan_budget.py', ['push'] + paths, where=where)


def jump_finder_memory_gb(film):
    """(GB find_jumps.py needs for this film, GB of memory free now): it keeps every frame at 270 x 480 as bytes and as
    floats, and their differences (about 10 bytes a pixel). Either is None when it cannot be found out."""
    needed = free = None
    try:
        probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames,r_frame_rate,duration',
                                '-of', 'json', film], capture_output=True, text=True, timeout=60)
        stream = json.loads(probe.stdout)['streams'][0]
        frames = int(stream.get('nb_frames') or 0)
        if not frames:
            num, den = (int(v) for v in stream['r_frame_rate'].split('/'))
            frames = int(float(stream['duration']) * num / den)
        needed = frames * 270 * 480 * 10 / 1e9
    except (OSError, ValueError, KeyError, IndexError, subprocess.TimeoutExpired):
        pass
    try:
        for line in open('/proc/meminfo'):
            if line.startswith('MemAvailable:'):
                free = int(line.split()[1]) / 1e6
    except OSError:
        pass
    return needed, free


def sendable_limit(run):
    try:
        from settings import load_settings
        value = load_settings(run.args.settings).value('delivery.sendable_megabytes')
        return value.get('chat_message') if isinstance(value, dict) else value
    except Exception:   # noqa: BLE001 - only a size label
        return None


def planned_cuts(run, item):
    source = item.get('planned_cuts')
    if not source:
        report = newest_report(run.reports, 'pages')
        data = None
        if report:
            try:
                data = load_json(report)
            except (ValueError, OSError):
                data = None
        if data:
            source = next((c.get('output_json') for c in data.get('checks', []) if c.get('tool', '').endswith('plan_page_timing.py')), None)
            if source:
                run.notes.append(f'Planned cuts read from the newest pages report ({os.path.basename(report)}).')
    if not source or not os.path.exists(source):
        run.need(item, 'planned_cuts', 'find_jumps.py', required=False, why='without them every planned cut is listed as a jump to look at')
        return []
    run.register(source)
    data = run.read_json('planned_cuts', source, 'find_jumps.py')
    if data is None:
        return []
    cuts = (data.get('planned_cuts') or {}).get('cuts', []) if isinstance(data, dict) else data
    try:
        return [float(c['film_seconds'] if isinstance(c, dict) else c) for c in cuts]
    except (KeyError, TypeError, ValueError):
        run.unusable('planned_cuts', source, 'its cuts are not numbers of seconds (plan_page_timing.py check\'s "planned_cuts": {"cuts": [{"film_seconds"}]})',
                     'find_jumps.py')
        return []


STAGE_RUNNERS = {'script': stage_script, 'record': stage_record, 'shots': stage_shots, 'place': stage_place, 'plates': stage_plates, 'paint': stage_paint,
                 'pages': stage_pages, 'film': stage_film, 'finish': stage_finish}


# ------------------------------------------------------------------------------------------------ the report
def summarise(run, hashes_before, hashes_after):
    findings = [f for c in run.checks for f in c['findings']]
    count = {v: sum(1 for f in findings if f['verdict'] == v) for v in ('fail', 'warn', 'known', 'info', 'pass')}
    required_missing = [m for m in run.missing if m['required']]
    changed = sorted(p for p in hashes_after if hashes_before.get(p) != hashes_after.get(p))
    if changed:
        verdict = 'stale'
    elif required_missing:
        verdict = 'inputs missing'
    elif count['fail']:
        verdict = 'fail'
    elif count['warn']:
        verdict = 'warn'
    else:
        verdict = 'pass'
    step, kind = GUARDED[run.stage]
    blocked = verdict in ('fail', 'inputs missing', 'stale')
    cost = round(sum(c['dollars'] for c in run.costs), 2)
    return {'stage': run.stage, 'stage_means': STAGE_WORDS[run.stage], 'verdict': verdict, 'counts': count, 'guarded_step': step, 'step_kind': kind,
            'blocked': blocked, 'cost_dollars': cost if run.costs else None, 'costs': run.costs, 'times': run.times,
            'allowance': run.allowance, 'preflight_seconds': round(time.time() - run.started, 1), 'changed_inputs': changed}


def first_lines(run, summary):
    counts = summary['counts']
    verdict = summary['verdict']
    unusable = any(m.get('unusable') for m in run.missing)
    word = {'pass': 'PASS', 'warn': 'PASS, with things to look at', 'fail': 'FAIL',
            'inputs missing': 'INPUTS MISSING OR UNUSABLE' if unusable else 'INPUTS MISSING', 'stale': 'STALE'}[verdict]
    lines = [f'Preflight {run.stage} ({STAGE_WORDS[run.stage]}): {word}. {counts["fail"]} to fix, {counts["warn"]} to look at, '
             f'{counts["known"]} known and accepted, {len([m for m in run.missing if m["required"]])} input(s) missing; '
             f'{len(run.checks)} check(s) in {summary["preflight_seconds"]:.1f} s.']
    cost = ''
    if summary['cost_dollars'] is not None:
        parts = [f'{c["note"]}' for c in run.costs if c['note']] if len(run.costs) == 1 else \
            [f'{c["what"]} {dollars_text(c["dollars"])}' for c in run.costs]
        if run.allowance:
            parts.append(f'{dollars_text(run.allowance["left_dollars"])} left of the allowance "{run.allowance["name"]}"'
                         + ('' if run.allowance['fits'] else ', NOT ENOUGH'))
        cost = f' (about {dollars_text(summary["cost_dollars"])}' + (': ' + '; '.join(parts) if parts else '') + ')'
    elif run.times:
        cost = ' (' + '; '.join(f'{t["what"]}: about {minutes_text(t["seconds"])}' for t in run.times) + ')'
    step, kind = summary['guarded_step'], summary['step_kind']
    what = {'paid': 'Paid step', 'long': 'Long step', None: 'Next step'}[kind]
    if summary['blocked']:
        why = {'fail': 'fix the failures below (or accept them, with who and when)',
               'inputs missing': 'make (or mend) the inputs listed below' if unusable else 'make the missing inputs listed below',
               'stale': 'its inputs changed while it ran; run it again'}[verdict]
        lines.append(f'{what} BLOCKED: {step}{cost}. First {why}, then run this stage again.')
    else:
        lines.append(f'{what} ready: {step}{cost}.' + (' It still needs the user\'s yes before anything is paid.' if kind == 'paid' else ''))
    if run.times and summary['cost_dollars'] is not None:
        lines.append('Time: ' + '; '.join(f'{t["what"]}: about {minutes_text(t["seconds"])}' for t in run.times) + '.')
    return lines


def plain_report(run, summary, hashes_after, report_json):
    lines = first_lines(run, summary)
    lines += ['', f'Made {run.started_text} by preflight.py version {version_of(os.path.abspath(__file__))}; kit {run.kit}; '
              f'every tool\'s own output is in {run.work}.', '']
    fails = [(c, f) for c in run.checks for f in c['findings'] if f['verdict'] == 'fail']
    warns = [(c, f) for c in run.checks for f in c['findings'] if f['verdict'] == 'warn']
    knowns = [(c, f) for c in run.checks for f in c['findings'] if f['verdict'] == 'known']
    required = [m for m in run.missing if m['required']]
    optional = [m for m in run.missing if not m['required']]

    def finding_line(check, f):
        where = f' [{f["where"]}]' if f.get('where') else ''
        text = f'- {f["check"]}{where}: {f["text"]}' if f.get('check') else f'- {f["text"]}{where}'
        out = [text + f' ({os.path.basename(check["tool"])})']
        if f.get('fix'):
            out.append(f'  Fix: {f["fix"]}')
        return out

    if required:
        lines += ['## Inputs missing or unusable (the stage cannot pass without them; exit 2)', '']
        for m in required:
            lines.append(f'- {m["option"]} {m["input"].upper()}: {m["what"]}. Needed by {m["needed_by"]}.'
                         + (f' Given but not found: {", ".join(m["given_but_absent"])}.' if m['given_but_absent'] else '')
                         + (f' Given but it cannot be used: {m["unusable"]}.' if m.get('unusable') else ''))
            if m.get('make'):
                lines.append(f'  Make it: {m["make"]}')
        lines.append('')
    if fails:
        lines += ['## To fix (these block the next step)', '']
        for check, f in fails:
            lines += finding_line(check, f)
        lines.append('')
    if warns:
        lines += ['## To look at (they do not block; a person decides)', '']
        for check, f in warns:
            lines += finding_line(check, f)
        lines.append('')
    if knowns or run.known_lists:
        lines += ['## Known and accepted (kept on purpose; they do not block)', '']
        for check, f in knowns:
            how = f.get('accepted') or {}
            lines += finding_line(check, f)
            lines.append(f'  Accepted: {how.get("reason", "")}' + (f' ({how.get("who")}, {how.get("date")}; {how.get("source")})' if how.get('who') else
                                                                     f' ({how.get("source", "")})'))
        if run.known_lists:
            lines.append('')
            lines.append('Accepted lists read from the check files and place facts:')
            for k in run.known_lists:
                lines.append(f'- {k["source"]}{" [" + k["where"] + "]" if k["where"] else ""}: {k["rule"]}'
                             + (f' ({", ".join(k["things"])})' if k['things'] else '') + (f', accepted at {k["measured"]}' if k['measured'] is not None else '')
                             + f': {short(k["reason"], 300)} ({short(k["who"], 120) or "WHO MISSING"}, {k["date"] or "DATE MISSING"})')
        lines.append('')
    if optional:
        lines += ['## Inputs not given (the stage runs without them, but checks less)', '']
        for m in optional:
            lines.append(f'- {m["option"]} {m["input"].upper()}: {m["what"]}' + (f'; {m["why"]}' if m['why'] else '') + '.')
            lines.append(f'  Make it: {m["make"]}')
        lines.append('')
    if run.costs or run.times:
        lines += ['## Cost and time', '']
        lines += [f'- {c["what"]}: {dollars_text(c["dollars"])}' + (f' ({c["note"]})' if c['note'] else '') for c in run.costs]
        lines += [f'- {t["what"]}: about {minutes_text(t["seconds"])}' + (f' ({t["note"]})' if t['note'] else '') for t in run.times]
        if run.allowance:
            a = run.allowance
            lines.append(f'- the allowance "{a["name"]}": {dollars_text(a["left_dollars"])} left; this step ({dollars_text(a["next_cost_dollars"])}) '
                         + ('fits.' if a['fits'] else 'does NOT fit (plan_budget.py refuses it).'))
        lines.append(f'- this preflight: {summary["preflight_seconds"]:.1f} s')
        lines.append('')
    if run.notes:
        lines += ['## Notes', ''] + [f'- {n}' for n in run.notes] + ['']
    lines += ['## Checks run', '']
    if not run.checks:
        lines.append('- none (make the missing inputs first)')
    for check in run.checks:
        c = {v: sum(1 for f in check['findings'] if f['verdict'] == v) for v in ('fail', 'warn', 'known', 'pass', 'info')}
        lines.append(f'- {check["verdict"].upper():4s}  {check["title"]}{" [" + check["where"] + "]" if check["where"] else ""}: '
                     f'{c["fail"]} fail, {c["warn"]} look, {c["known"]} known, {c["pass"]} pass, {c["info"]} info; exit {check["exit"]}, '
                     f'{check["seconds"]:.1f} s; {check["tool"]} version {check["version"]}')
        lines.append(f'  {check["command"]}')
    lines.append('')
    if summary['changed_inputs']:
        lines += ['## STALE: these inputs changed while the preflight ran', ''] + [f'- {p}' for p in summary['changed_inputs']] + ['']
    lines += ['## Inputs (sha1 when the run ended)', '']
    lines += [f'- {h or "missing"}  {p}' for p, h in hashes_after.items()] or ['- none']
    lines += ['', f'The same report as JSON: {report_json}']
    return '\n'.join(lines) + '\n'


def strip_for_json(run):
    checks = []
    for check in run.checks:
        c = {k: v for k, v in check.items() if k != 'result'}
        checks.append(c)
    return checks


# ------------------------------------------------------------------------------------------------ gate, list, example
def register_item_inputs(run, item):
    """The inputs a stage's item names (files, folders, globs, page folders, check files), hashed before any tool reads
    them. A real run and --gate both use this, so the gate compares the same list."""
    for key, value in item.items():
        if key in PATH_KEYS and key not in LIST_KEYS and isinstance(value, str) and os.path.exists(value):
            run.register(value)
        elif key == 'page_files' and isinstance(value, list):
            for path in page_file_list(value):
                run.register(path)
        elif key in ('models', 'paper_pages', 'deliver') and isinstance(value, list):
            for pattern in value:
                for path in (glob.glob(pattern) or ([pattern] if os.path.exists(pattern) else [])):
                    run.register(path)
        elif key == 'check_files' and isinstance(value, dict):
            for path in value.values():
                if isinstance(path, str) and os.path.exists(path):
                    run.register(path)


def gate(run, stage):
    """Opens only when the newest report of the stage passed, was made on the inputs this command names (path for path, sha1
    for sha1: the plan's, the command line's, the accepted file and the settings), and when every input that report read,
    and every tool it ran, is unchanged since. Names the first difference otherwise."""
    reports = run.reports
    report = newest_report(reports, stage)
    if not report:
        print(f'GATE {stage}: CLOSED. No report in {reports}. Run: explainer-film-preflight {stage}')
        return 1
    try:
        data = load_json(report)
    except (ValueError, OSError) as error:
        print(f'GATE {stage}: CLOSED. The newest report {os.path.basename(report)} cannot be read ({short(error, 120)}). Run the stage again.')
        return 1
    if data.get('verdict') not in ('pass', 'warn'):
        print(f'GATE {stage}: CLOSED. The newest report ({os.path.basename(report)}, {data.get("started")}) says {data.get("verdict", "?").upper()}.')
        return 1
    recorded = data.get('inputs', {}) or {}
    for item in run.items():
        register_item_inputs(run, item)
    named = run.hash_inputs()
    for path, sha in named.items():
        if path not in recorded:
            print(f'GATE {stage}: CLOSED. The newest report ({data.get("started")}) was not made on {path}: run the stage on these inputs.')
            return 1
        if recorded[path] != sha:
            print(f'GATE {stage}: CLOSED. {os.path.basename(path)} changed since the newest report ({data.get("started")}). Run the stage again.')
            return 1
    changed = [p for p, h in recorded.items() if sha1_of(p) != h]
    if changed:
        print(f'GATE {stage}: CLOSED. {len(changed)} input(s) changed since the newest report ({data.get("started")}): '
              + ', '.join(os.path.basename(p) for p in changed[:6]) + '. Run the stage again.')
        return 1
    tools = {c['tool']: c['version'] for c in data.get('checks', []) if c.get('command') != '(inside the preflight)' and c.get('version')}
    tools['calculators/preflight.py'] = data.get('preflight_version')
    for tool, version in tools.items():
        now = version_of(os.path.abspath(__file__)) if tool == 'calculators/preflight.py' else version_of(os.path.join(run.kit, tool))
        if version and now != version:
            print(f'GATE {stage}: CLOSED. {tool} changed since the newest report (version {version}, now {now}). Run the stage again.')
            return 1
    print(f'GATE {stage}: OPEN. The newest report ({data.get("started")}) passed; it was made on the {len(named)} input(s) named here, and all '
          f'{len(recorded)} of its inputs and its {len(tools)} tool(s) are unchanged.')
    return 0


def list_inputs():
    lines = ['The preflight\'s stages, and their inputs (r = required, o = optional). Give an input as --option PATH, or in a preflight plan.', '']
    for stage in STAGES:
        lines.append(f'{stage}: {STAGE_WORDS[stage]}. Guards: {GUARDED[stage][0]}.')
        for key, need in STAGE_INPUTS[stage].items():
            what, make = INPUTS[key]
            lines.append(f'  ({need}) --{key.replace("_", "-")}: {what}')
            lines.append(f'        made by: {make}')
        lines.append('')
    return '\n'.join(lines)


EXAMPLE_PLAN = {
    'about': 'A preflight plan: the film\'s files, named once for every stage. Paths are read from this file\'s folder. Each stage holds one '
             'item, or a list of items (one per place, view, painting or chapter).',
    'kit': 'film-kit',
    'reports': 'preflight-reports',
    'script': {'script': 'narration/narration-script.json', 'word_times': 'film-kit/examples/inflation-chapter-2/word-times.json',
               'research_ledger': 'research/claims.json', 'spend_ledger': 'spend-ledger.json'},
    'record': {'script': 'narration/narration-script.json', 'transcripts': 'narration/transcripts', 'recordings': 'narration/recordings',
               'word_times': 'narration/word-times.json'},
    'shots': [{'place_facts': 'places/works-place-facts.json', 'shot_list': 'places/works-shots.json',
               'check_files': {'w1': 'places/works-w1-shot-check.json', 'w3': 'places/works-w3-shot-check.json'}}],
    'place': [{'name': 'place one', 'place_audit': 'places/place-one-place-audit.json', 'blend': 'places/place-one-finished.blend', 'place_settings': 'places/place-settings.json',
               'place_pictures': 'places/previews', 'style_guard': 'places/style-guard.json', 'fresh_check': 'places/fresh-check.json'}],
    'plates': [{'name': 'w1', 'view': 'w1', 'check': 'places/works-w1-shot-check.json', 'plate': 'plates/works-w1-plate.png',
                'plate_facts': 'plates/w1-plate-facts', 'render_log': 'plates/plates.log', 'shot_report': 'checks/w1/report.md',
                'helper_plate': 'plates/works-w1-behind-plate.png', 'place_facts': 'places/works-place-facts.json', 'brief': 'places/works-brief.json',
                'spend_ledger': 'spend-ledger.json'}],
    'paint': [{'name': 'w1', 'painting': 'paintings/w1-returned.png', 'plate': 'plates/works-w1-plate.png', 'check': 'places/works-w1-shot-check.json',
               'plate_facts': 'plates/w1-plate-facts', 'near_list': 'requests/w1/near-list.json'}],
    'pages': {'events': 'checks/page-events-3-5.json', 'scene': 'my-chapter', 'numbers_ledger': 'research/numbers.json',
              'camera_log': 'checks/camera.json'},
    'film': {'events': 'checks/page-events-3-5.json', 'scene': 'my-chapter', 'critique': 'checks/critique.json',
             'page_files': ['film-kit/paper-film/scenes/my-chapter'], 'rates': 'checks/rates.json'},
    'finish': {'film': 'deliver/chapter.mp4', 'mix': 'mix/chapter-mix.flac', 'timeline': 'narration/timeline.json', 'clip_critique': 'checks/clip-critique.json',
               'send': 'deliver/chapter-send.mp4'},
    'accepted': [{'stage': 'pages', 'check': 'lookups', 'text': 'workers', 'page': 3, 'reason': 'takes the first time, which is the one meant',
                  'who': 'the director', 'date': '2026-10-16'}],
}


# ------------------------------------------------------------------------------------------------ main
def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('stage', nargs='?', choices=STAGES, help='script, record, shots, place, plates, paint, pages, film or finish')
    general = parser.add_argument_group('general')
    general.add_argument('--project', help='the film\'s folder (default: the plan\'s folder, else the current folder)')
    general.add_argument('--plan', help='a preflight plan (default: PROJECT/preflight-plan.json when there is one)')
    general.add_argument('--reports', help='where reports go (default: PROJECT/preflight-reports)')
    general.add_argument('--kit', help='the kit whose tools run (default: the kit this file is in)')
    general.add_argument('--settings', help='the settings file (default: kit/film-settings.json, or FILM_SETTINGS)')
    general.add_argument('--accepted', help='a JSON list of problems accepted on purpose (each with who and date)')
    general.add_argument('--gate', action='store_true', help='only answer whether the newest report of the stage passed and its inputs are unchanged')
    general.add_argument('--list', action='store_true', help='list every stage\'s inputs and which tool makes each')
    general.add_argument('--example-plan', action='store_true', help='print an example preflight plan')
    general.add_argument('--json', action='store_true', help='print the report as JSON instead of plain words')
    general.add_argument('--timeout', type=float, default=1800, help='seconds before one tool is stopped (default 1800)')
    general.add_argument('--name', help='a name for this item in the report (a place, view or painting)')
    words = parser.add_argument_group('script and record')
    words.add_argument('--script')
    words.add_argument('--word-times', dest='word_times')
    words.add_argument('--timeline')
    words.add_argument('--research-ledger', dest='research_ledger')
    words.add_argument('--today', help='the date the research ledger is judged on (default: today)')
    words.add_argument('--spend-ledger', dest='spend_ledger')
    words.add_argument('--allowance', help='the allowance\'s name in the spend ledger')
    words.add_argument('--transcripts')
    words.add_argument('--recordings')
    words.add_argument('--heard')
    words.add_argument('--narration')
    places = parser.add_argument_group('shots, plates and paint')
    places.add_argument('--place-facts', dest='place_facts')
    places.add_argument('--shot-list', dest='shot_list')
    places.add_argument('--shot', dest='shot_names', nargs='+', help='only these shots of the shot list')
    places.add_argument('--view', help='a view of the place facts (plates: the view of this plate)')
    places.add_argument('--views', nargs='+', help='shots: only these views')
    places.add_argument('--check-files', dest='check_files', nargs='+', help='shots: VIEW=FILE for each view\'s check file')
    places.add_argument('--state-plan', dest='state_plan')
    places.add_argument('--smoke')
    places.add_argument('--page', help='the page (view_audit.py\'s narration, camera_audit.py\'s window)')
    places.add_argument('--check', help='the view\'s shot-check file')
    places.add_argument('--plate')
    places.add_argument('--plate-facts', dest='plate_facts')
    places.add_argument('--render-log', dest='render_log')
    places.add_argument('--shot-report', dest='shot_report')
    places.add_argument('--helper-plate', dest='helper_plate')
    places.add_argument('--brief')
    places.add_argument('--real-names', dest='real_names')
    places.add_argument('--exposure', type=float)
    places.add_argument('--hollow', nargs='+')
    places.add_argument('--models', nargs='+')
    places.add_argument('--with-behind', dest='with_behind', action='store_true', default=None, help='plates: price a behind painting too')
    places.add_argument('--style-picture', dest='style_picture', help='plates: the style picture sent with the plate (its real size sets the price)')
    places.add_argument('--models-as-set', dest='models_as_set', action='store_true', default=None,
                        help='plates: the --models files are one dressed set sharing one origin (model_lint.py --as-set)')
    places.add_argument('--painting')
    places.add_argument('--behind')
    places.add_argument('--near-list', dest='near_list')
    places.add_argument('--figures', nargs='+')
    places.add_argument('--standard')
    places.add_argument('--toe', type=int, choices=(0, 1), help='paint: the page\'s look.toe (1 for a dark, dusk or wet page), passed to after_painting.py --toe')
    places.add_argument('--render-record', dest='render_record', help='plates: the place kit\'s render record of the plate (default: PLATE.json beside the picture)')
    place = parser.add_argument_group('place (and plates: --blend, --place-audit)')
    place.add_argument('--place-audit', dest='place_audit', help='the place audit (place-audit.json from explainer-film-place audit)')
    place.add_argument('--blend', help='the finished scene file the audit was made from (the audit goes stale when it changes)')
    place.add_argument('--place-settings', dest='place_settings', help='the place settings (place-settings.json)')
    place.add_argument('--place-pictures', dest='place_pictures', help='a folder of the place\'s preview pictures')
    place.add_argument('--previous-pictures', dest='previous_pictures', help='a folder of the previous round\'s pictures (for the squint test)')
    place.add_argument('--style-guard', dest='style_guard', help='the style guard (style-guard.json)')
    place.add_argument('--real-world-facts', '--facts', dest='real_world_facts', help='the place\'s own real-world facts (the same file `explainer-film-place audit --facts` and `finish --facts` take)')
    place.add_argument('--fresh-check', dest='fresh_check', help='a fresh checker\'s result')
    place.add_argument('--allow-quick', dest='allow_quick', action='store_true', default=None, help='accept an audit made with --quick (a trial) as a look')
    pages = parser.add_argument_group('pages, film and finish')
    pages.add_argument('--events')
    pages.add_argument('--scene')
    pages.add_argument('--pages', dest='pages_list', help='pages: the pages page_events.mjs runs (3,4,5)')
    pages.add_argument('--make-events', dest='make_events', action='store_true', help='pages: run page_events.mjs first (about a minute a page)')
    pages.add_argument('--numbers-ledger', dest='numbers_ledger')
    pages.add_argument('--timing-accepted', dest='timing_accepted')
    pages.add_argument('--camera-log', dest='camera_log')
    pages.add_argument('--page-files', dest='page_files', nargs='+')
    pages.add_argument('--paper-pages', dest='paper_pages', nargs='+')
    pages.add_argument('--critique')
    pages.add_argument('--rates')
    pages.add_argument('--processors', type=int)
    pages.add_argument('--free-memory-gb', dest='free_memory_gb', type=float)
    pages.add_argument('--free-disk-gb', dest='free_disk_gb', type=float, help='the free disk space in gigabytes (the film stage measures it when this is not given)')
    pages.add_argument('--from-frame', dest='from_frame', type=int)
    pages.add_argument('--to-frame', dest='to_frame', type=int)
    pages.add_argument('--blender-running', dest='blender_running', choices=['yes', 'no', 'auto'])
    pages.add_argument('--film')
    pages.add_argument('--clip-critique', dest='clip_critique', help='finish: a fresh helper\'s critique of the filmed clip in motion (the film-critic agent\'s clip mode)')
    pages.add_argument('--mix')
    pages.add_argument('--send')
    pages.add_argument('--deliver', nargs='+')
    pages.add_argument('--planned-cuts', dest='planned_cuts')
    pages.add_argument('--jumps', action='store_true', help='finish: run find_jumps.py even when the memory looks too small for it')
    return parser


def main(argv=None):
    if hasattr(signal, 'SIGPIPE'):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # a report piped into head stops quietly
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list:
        print(list_inputs())
        return 0
    if args.example_plan:
        print(json.dumps(EXAMPLE_PLAN, indent=1))
        return 0
    if not args.stage:
        parser.error('name a stage: ' + ', '.join(STAGES))
    plan_path = args.plan or (os.path.join(args.project, 'preflight-plan.json') if args.project else None)
    plan, plan_folder = {}, os.getcwd()
    if plan_path:
        if not os.path.exists(plan_path):
            if args.plan:
                print(f'Preflight {args.stage}: INPUTS MISSING. The preflight plan {plan_path} is not there (print an example with --example-plan).')
                return 2
        else:
            try:
                plan = load_json(plan_path)
            except ValueError as error:
                print(f'Preflight {args.stage}: INPUTS MISSING. The preflight plan {plan_path} is not valid JSON: {error}')
                return 2
            plan_folder = os.path.dirname(os.path.abspath(plan_path))
    kit = os.path.abspath(args.kit or (plan.get('kit') and Run.resolve(plan['kit'], plan_folder)) or DEFAULT_KIT)
    if not os.path.isdir(os.path.join(kit, 'calculators')):
        print(f'Preflight {args.stage}: INPUTS MISSING OR UNUSABLE. The kit {kit} is not a kit folder (it has no calculators/): give --kit, '
              'or EXPLAINER_FILM_KIT, the folder holding calculators/, narration-tools/ and paper-film/ (the plugin\'s own kit, or '
              'explainer-film-setup\'s copy).')
        return 2
    run = Run(args.stage, args, plan, plan_folder)
    run.register_fixed_inputs(plan_path if plan else None)
    if args.gate:
        return gate(run, args.stage)
    run.started_text = now_text()
    items = run.items()
    accepted_broken = any(m.get('unusable') and m['input'] == 'accepted' for m in run.missing)
    for index, item in enumerate(items):
        if args.name and len(items) == 1:
            item['name'] = args.name
        where = run.label(item, index, len(items))
        register_item_inputs(run, item)
        if not accepted_broken:      # with a broken accepted file nothing is judged until it is mended
            STAGE_RUNNERS[args.stage](run, item, where)
    if args.stage in ('script', 'plates') and not accepted_broken:
        spend_ledger_check(run, items)
    if args.stage == 'plates' and not accepted_broken:
        plate_engines_check(run, items)
    run.check_accepted_breadth()
    hashes_before = dict(run.input_paths)   # each input's hash from when it was first seen, before a tool read it
    hashes_after = run.hash_inputs()
    summary = summarise(run, hashes_before, hashes_after)
    os.makedirs(run.reports, exist_ok=True)
    report_json = os.path.join(run.reports, run.name + '.json')
    report_text = os.path.join(run.reports, run.name + '.md')
    text = plain_report(run, summary, hashes_after, report_json)
    data = dict(summary, started=run.started_text, first_lines=first_lines(run, summary), kit=run.kit,
                preflight_version=version_of(os.path.abspath(__file__)), plan=os.path.abspath(plan_path) if plan_path and plan else None,
                work_folder=run.work, inputs=hashes_after, missing=run.missing, checks=strip_for_json(run), known_lists=run.known_lists,
                notes=run.notes, accepted_entries=run.accepted, report_text=report_text)
    with open(report_json, 'w') as handle:
        json.dump(data, handle, indent=1, default=str)
    with open(report_text, 'w') as handle:
        handle.write(text)
    print(json.dumps(data, indent=1, default=str) if args.json else text, end='' if not args.json else '\n')
    if summary['verdict'] == 'inputs missing':
        return 2
    return 1 if summary['blocked'] else 0


if __name__ == '__main__':
    sys.exit(main())
