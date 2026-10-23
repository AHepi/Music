"""What this does: defines, in one place, the verbs of the `explainer-film-place` command and the options each one takes, so the plain-Python
launcher (place_command.py), the code that runs inside Blender (blender_run.py) and the tests all read the same list. It is plain Python
with no Blender in it, so `--verbs` and `VERB --help` work on any machine.

A concrete example: build_parser().parse_args(['finish', '--scene', 'place.blend', '--save-as', 'out.blend', '--look', 'neglected']).
Each verb says whether it runs inside Blender ("blender": True) or in plain Python.
"""
import argparse
import os
import sys

from . import settings_file

THREADS_VARIABLE = 'EXPLAINER_FILM_BLENDER_THREADS'


def blender_thread_arguments(environment=None):
    """['-t', 'N'] when the environment variable EXPLAINER_FILM_BLENDER_THREADS=N is set to a whole number of 1 or more: every Blender run the kit
    starts then uses at most N processor threads, so several helpers on one computer do not starve each other (an earlier project's six builders each
    ran blender -t 2). Unset or empty: [] and Blender chooses as before. Anything else is ignored with a LOOK line on the error stream.
    A concrete example: with EXPLAINER_FILM_BLENDER_THREADS=2 the launcher runs blender -b -t 2 --disable-autoexec ..."""
    text = str((environment if environment is not None else os.environ).get(THREADS_VARIABLE, '')).strip()
    if not text:
        return []
    if text.isdigit() and int(text) >= 1:
        return ['-t', str(int(text))]
    print(f'LOOK {THREADS_VARIABLE}="{text}" is not a whole number of 1 or more, so it is ignored (Blender chooses its own thread count).', file=sys.stderr)
    return []

VERBS = {
    'new-settings': {'blender': True, 'help': 'draft place-settings.json from the scene\'s names, collections and materials; lists what it could not classify'},
    'roles': {'blender': True, 'help': 'give every object one role (exit 1 when one is unknown); --write stores place_role on each object'},
    'surfaces': {'blender': True, 'help': 'UVs, real normal maps, roughness and colour variation, bevels and displacement by role'},
    'roads': {'blender': True, 'help': 'grade the ground and shape ruts, banks, optional hoof prints, a grass crown and puddle hollows from the settings'},
    'damage': {'blender': True, 'help': 'damage as shape: bent boards, chipped corners, leaning posts, sag; no two parts alike'},
    'age': {'blender': True, 'help': 'the nine wear layers in their fixed order (dirt, grime, weathering, wetness, cracks and chips, edge wear, moss, rust, rubbish)'},
    'grow': {'blender': True, 'help': 'weeds, tufts, ferns, nettles, moss cushions and litter pieces, with exact keep-out gates'},
    'light': {'blender': True, 'help': 'add a sun, a sky and a lamp in every glowing thing when the scene has none (a scene with no light renders black); no fill: add a soft area lamp or raise the sky yourself, never a second sun lamp'},
    'finish': {'blender': True, 'help': 'the whole pass in order (curves, text and instances become meshes, then roles, roads, surfaces, damage, wear, growth, light), then save, reopen and audit; idempotent; say where to save with --save-as'},
    'finish-part': {'blender': True, 'help': 'a part builder\'s share: only that owner\'s objects, masks from that part alone; always a quick trial, and its audit accepts that (the integrator runs the full finish)'},
    'construction': {'blender': True, 'help': 'the construction check alone: every part carried from the ground up, sizes of doorways, spans'},
    'normals-test': {'blender': True, 'help': 'prove every normal map points the right way (against its own height, and a test light with a flipped control)'},
    'audit': {'blender': True, 'help': 'gather the facts into place-audit.json, then judge them (PASS, LOOK or FAIL lines)'},
    'undo': {'blender': True, 'help': 'remove everything the kit added and restore the material slots'},
    'combine': {'blender': True, 'help': 'run several builders\' stage files in order, check what each changed against who owns what'},
    'fingerprint': {'blender': True, 'help': 'a fingerprint of the whole scene (objects, materials, collections, frozen state)'},
    'ownership-diff': {'blender': False, 'help': 'compare two fingerprints with ownership.json and name who changed what they do not own'},
    'renderer-for': {'blender': True, 'help': 'which renderer the film owner\'s rule picks (Cycles where lights are lit, EEVEE when off) and why'},
    'render': {'blender': True, 'help': 'draw the pictures of a job file with the renderer rule (local, or on a rented card)'},
    'rent': {'blender': False, 'help': 'the rented-card client: status, upload, run, job, wait, download, balance'},
    'measure': {'blender': False, 'help': 'measure pictures (value range, detail energy, flat windows, palette, squint) and make or check a style guard'},
    'crops': {'blender': False, 'help': 'cut 100 percent crops of a picture (with before and after strips)'},
    'variations': {'blender': False, 'help': 'a batch of about 10 measurably different variations of one change, drawn small and quick in up to 3 card jobs at once, measured, on ONE labelled contact sheet (actions: make, scout, plan, run, collect, refine, sheet, keys)'},
    'variations-worker': {'blender': True, 'help': 'internal: one job of a variations batch, inside Blender (`variations run` starts it, here or on a card)'},
    'card-time': {'blender': False, 'help': 'the card-time ledger and each helper\'s allowance: show, check, add, start'},
    'check-presets': {'blender': False, 'help': 'check the kit\'s own data and code (kinds and sources, agreement, required treatments are made and tested, no place words, nothing private)'},
}
SCREEN_VERBS = ('render', 'normals-test', 'variations-worker')           # verbs that may draw with EEVEE and so want a virtual screen when there is no real one
NEEDS_SCENE = tuple(v for v, spec in VERBS.items() if spec['blender'] and v not in ('new-settings', 'combine')) + ('new-settings', 'combine')


def add_global_options(parser):
    parser.add_argument('--scene', help='the Blender scene file (.blend)')
    parser.add_argument('--settings', help='the place settings (default: place-settings.json beside the scene; a missing file is drafted)')
    parser.add_argument('--out', help='also write the result as JSON to this file')
    parser.add_argument('--json', action='store_true', help='print the result as JSON')
    parser.add_argument('--report', help='also write the plain report to this file')
    parser.add_argument('--kit', help='the kit folder (default: the plugin\'s own kit, or EXPLAINER_FILM_KIT)')
    parser.add_argument('--blender', help='the Blender program (default: BLENDER, then machine-settings.env, then the PATH)')
    parser.add_argument('--quick', action='store_true', help='trial sizes (maps 256 px, plan masks 0.5 m): for trials only, the audit refuses it as a final')
    parser.add_argument('--owner', help='only this owner\'s objects (the part builders\' share)')
    parser.add_argument('--save-as', dest='save_as', help='for verbs that change the scene: the file to save to (the input is never overwritten without --overwrite)')
    parser.add_argument('--overwrite', action='store_true', help='allow --save-as to overwrite the input scene')
    return parser


def add_card_options(parser):
    """The options every command that can use a rented card takes: who you are (for the card-time ledger) and how to go over the allowance."""
    parser.add_argument('--helper', help='your name, for the card-time ledger (default: PLACE_HELPER, else unnamed-helper)')
    parser.add_argument('--role', choices=['builder', 'fixer', 'integrator', 'renderer', 'checker', 'planner', 'default'], help='your role: it sets your card-time allowance (default: PLACE_HELPER_ROLE, else default)')
    parser.add_argument('--ledger', help='the card-time ledger file (default: PLACE_CARD_LEDGER, else card-time-ledger.jsonl in the folder you run in)')
    parser.add_argument('--over-allowance', dest='over_allowance', help='a reason of at least 15 letters to go over your allowance by at most half again; it is written into the ledger and the person reads it')
    return parser


def build_parser():
    parser = argparse.ArgumentParser(prog='explainer-film-place', description='One command per job for places built in Blender: roles, surfaces, wear, growth, construction, audit, rendering. '
                                     'Run `explainer-film-place --verbs` for the list and `explainer-film-place VERB --help` for a verb\'s options. Exit: 0 pass (read the LOOK lines), 1 fail, 2 an input is missing or unusable.')
    parser.add_argument('--verbs', action='store_true', help='print the verbs, one per line')
    sub = parser.add_subparsers(dest='verb')

    def verb(name):
        p = sub.add_parser(name, help=VERBS[name]['help'], description=VERBS[name]['help'])
        return add_global_options(p)

    p = verb('new-settings')
    p.add_argument('--place', default='place', help='the place\'s name')
    p.add_argument('--type', dest='place_type', default='generic', help='the place type (a file in data/place_types: ' + ', '.join(settings_file.place_type_ids()) + ')')
    p = verb('roles')
    p.add_argument('--write', action='store_true', help='store each object\'s role as its place_role property (needs --save-as)')
    p.add_argument('--list', action='store_true', help='print every role id with one plain line saying what it is for (needs no scene)')
    p = verb('surfaces')
    p.add_argument('--map-size', dest='map_size', type=int, help='normal-map size in pixels (default 1024; 256 with --quick)')
    p.add_argument('--maps-folder', dest='maps_folder', help='also save the maps as PNG files here')
    verb('roads')
    p = verb('damage')
    p.add_argument('--amount', type=float, help='how strong (0 to 1; default from the look)')
    p = verb('age')
    p.add_argument('--look', choices=['kept', 'lived_in', 'neglected', 'derelict'], help='the look (default: the settings\')')
    p.add_argument('--state', choices=['dry', 'damp', 'wet'], help='how wet the place is')
    p.add_argument('--master', type=float, help='one number that scales every layer (1 = the look as written; 0 = exactly nothing)')
    p.add_argument('--layers', help='only these layers, comma separated')
    p.add_argument('--layers-off', dest='layers_off', help='leave these layers out, comma separated')
    p.add_argument('--mask-cell-metres', dest='mask_cell', type=float, help='plan-mask cell size in metres')
    p = verb('grow')
    p.add_argument('--density', type=float, help='multiplier on the plant and litter density (default 1)')
    p = verb('light')
    p.add_argument('--sun-only', dest='sun_only', action='store_true', help='add only a sun')
    p = verb('finish')
    p.add_argument('--look', choices=['kept', 'lived_in', 'neglected', 'derelict'])
    p.add_argument('--state', choices=['dry', 'damp', 'wet'])
    p.add_argument('--map-size', dest='map_size', type=int)
    p.add_argument('--no-audit', dest='no_audit', action='store_true', help='skip the audit at the end (the place is then not proved)')
    p.add_argument('--type', dest='place_type', help='when there is no settings file: the place type the draft starts from (a file in data/place_types: ' + ', '.join(settings_file.place_type_ids()) + '; default generic)')
    p.add_argument('--place', help='when there is no settings file: the place\'s name')
    p.add_argument('--facts', help='the place\'s own real-world facts file (the same file `audit --facts` and `explainer-film-preflight place --real-world-facts` take)')
    p = verb('finish-part')
    p.add_argument('--look', choices=['kept', 'lived_in', 'neglected', 'derelict'])
    p.add_argument('--state', choices=['dry', 'damp', 'wet'])
    p.add_argument('--facts', help='the place\'s own real-world facts file')
    p = verb('construction')
    p = verb('normals-test')
    p.add_argument('--size', type=int, default=96, help='size of the test pictures in pixels')
    p.add_argument('--samples', type=int, default=24, help='Cycles samples for the test pictures')
    p = verb('audit')
    p.add_argument('--no-judge', dest='no_judge', action='store_true', help='only gather the facts; do not run the judge')
    p.add_argument('--allow-quick', dest='allow_quick', action='store_true', help='accept a quick trial as a look')
    p.add_argument('--facts', help='the place\'s own real-world facts file')
    verb('undo')
    p = verb('combine')
    p.add_argument('--stages', nargs='+', required=False, help='the stage files (stage_<owner>.py), in order')
    p.add_argument('--order', choices=['plain', 'reverse', 'both'], default='plain', help='plain order, reverse order, or both (each from the same saved start, compared)')
    p.add_argument('--options', help='a JSON object passed to every stage\'s apply(options)')
    p.add_argument('--owners', help='ownership.json')
    verb('fingerprint')
    p = verb('ownership-diff')
    p.add_argument('--start', required=False, help='the fingerprint before')
    p.add_argument('--end', required=False, help='the fingerprint after')
    p.add_argument('--owners', required=False, help='ownership.json')
    p.add_argument('--actor', help='the owner whose stage just ran (changes to other owners\' things are violations)')
    verb('renderer-for')
    p = verb('render')
    p.add_argument('--job', required=False, help='the job file (scene, out_folder, views)')
    p.add_argument('--where', choices=['rented', 'local', 'auto', 'on-card'], default='auto', help='local (this computer, tiny), rented (a rented card), auto (a card when one is set up and the renderer is Cycles or finals are asked, else tiny local previews), on-card (used by the client: already on the card; to ask for a card say rented)')
    p.add_argument('--engine', choices=['auto', 'cycles', 'eevee'], default='auto')
    p.add_argument('--finals', action='store_true', help='draw final-size pictures too (default: previews only)')
    add_card_options(p)
    p = verb('rent')
    p.add_argument('action', nargs='?', choices=['status', 'upload', 'run', 'job', 'wait', 'download', 'balance'], help='what to do on the rented card')
    p.add_argument('target', nargs='*', help='the file, folder, command or job id the action needs')
    p.add_argument('--remote', help='upload: the remote path')
    p.add_argument('--cwd', help='run: the folder to run in')
    p.add_argument('--timeout', type=float, help='run: seconds before the job is given up')
    p.add_argument('--limit', type=float, help='wait: seconds to wait at most')
    p.add_argument('--local', help='download: the local path')
    add_card_options(p)
    p = verb('measure')
    p.add_argument('pictures', nargs='*', help='the pictures to measure')
    p.add_argument('--guard', help='a style guard JSON to check against')
    p.add_argument('--make-guard', dest='make_guard', action='store_true', help='make a style guard from the first picture (provisional until a person accepts it)')
    p.add_argument('--view', help='with --make-guard: the view this guard is for (a name inside its pictures\' file names); several views can share one --out guard file')
    p.add_argument('--regions', help='a regions JSON')
    p.add_argument('--id-map', dest='id_map', help='a flat-colour picture of role classes')
    p.add_argument('--id-colours', dest='id_colours', help='the colours of the id map')
    p.add_argument('--previous', help='the previous round\'s picture (for the squint test)')
    p = verb('crops')
    p.add_argument('--picture', help='the picture')
    p.add_argument('--boxes', nargs='+', help='boxes as x,y,w,h')
    p.add_argument('--previous', help='the earlier picture (for before and after strips)')
    p.add_argument('--out-folder', dest='out_folder', help='where the crops go')
    p = verb('variations')
    p.add_argument('action', choices=['make', 'scout', 'plan', 'run', 'collect', 'refine', 'sheet', 'keys'], help='make: write a variations file that spreads settings across their ranges; '
                   'scout: draw the same file HERE, tiny, for free, and say which variations would not show (not a batch); plan: check and plan, draw nothing; run: draw the batch and make the sheet; '
                   'collect: finish a batch whose command was cut off after its jobs were sent; refine: write the second batch around the variations you picked; sheet: make the sheet again from '
                   'pictures already drawn; keys: list the settings a variation may change')
    p.add_argument('spec', nargs='?', help='scout, plan and run: the variations file; collect: the run folder; refine and sheet: the variations-result.json (or its folder) of a finished run')
    p.add_argument('--cameras', nargs='+', help='the cameras to look through (default: the file\'s, else the scene\'s own camera)')
    p.add_argument('--where', choices=['local', 'rented', 'auto'], default='auto', help='local: draw here (tiny scenes, tests); rented: on rented cards; auto: a card when one is set up (--card-client, PLACE_CARD_CLIENT, or the plugin client\'s settings), else here')
    p.add_argument('--card-client', dest='card_client', help='the command that starts a card client with the actions upload, run, job and download, for example "python3 -I /path/render_client_serverless.py" (or PLACE_CARD_CLIENT)')
    p.add_argument('--store-folder', dest='store_folder', help='with --card-client: the folder on the card\'s store for jobs (default /workspace)')
    p.add_argument('--jobs', type=int, help='how many card jobs at the same time (default: enough that each holds at least 3 variations, at most 3)')
    p.add_argument('--engine', choices=['auto', 'cycles', 'eevee'], default='auto', help='auto: the renderer rule (Cycles where lit or water is in view, EEVEE when not)')
    p.add_argument('--size', help='picture size such as 600x400 (default: place_variations.picture_size_pixels)')
    p.add_argument('--samples', type=int, help='samples for each picture (default: low, from the house numbers)')
    p.add_argument('--run-folder', dest='run_folder', help='where the job files, pictures, result and sheet go (default: beside the variations file)')
    p.add_argument('--check-reset', dest='check_reset', action='store_true', help='draw the baseline again after all the variations in its job, to prove the reset put everything back (one more small picture)')
    p.add_argument('--max-kilobytes', dest='max_kilobytes', type=int, help='the sheet stays under this size (default 400)')
    p.add_argument('--keys', nargs='+', help='make: the settings to spread, for example amount.moss_and_algae dials.moss_and_algae.cover')
    p.add_argument('--range', nargs=3, action='append', metavar=('KEY', 'LOW', 'HIGH'), help='make: spread KEY only from LOW to HIGH (the part of its range that shows, from a scout); give it once for each setting to limit')
    p.add_argument('--scout', help='plan and run: the scout to use (its folder or its variations-result.json; default: the FILE-scout folder beside the variations file)')
    p.add_argument('--no-scout', dest='no_scout', action='store_true', help='plan and run: do not use a scout even when there is one')
    p.add_argument('--count', type=int, help='make: how many variations (default 10); refine: how many (default 6)')
    p.add_argument('--seed', type=int, default=1, help='make and refine: the seed of the spread (the same seed gives the same file)')
    p.add_argument('--change', help='make: the one change this batch tries, in plain words')
    p.add_argument('--pick', nargs='+', help='refine: the names of the variation(s) you picked (several are blended)')
    p.add_argument('--radius', type=float, default=0.3, help='refine: how far around the pick to spread, as a share of each setting\'s range (default 0.3)')
    add_card_options(p)
    p = verb('variations-worker')
    p.add_argument('--job', required=False, help='the job file the runner wrote')
    p.add_argument('--where', choices=['local', 'on-card'], default='local')
    p = verb('card-time')
    p.add_argument('action', nargs='?', choices=['show', 'check', 'add', 'start'], help='show: the ledger and every helper\'s allowance; check: would a paid step of --estimate-seconds fit; add: log a job you ran by hand; start: the person\'s total cap for the whole job')
    p.add_argument('--estimate-seconds', dest='estimate_seconds', type=float, help='check: the card seconds the step would use')
    p.add_argument('--work-seconds', dest='work_seconds', type=float, help='add: the billed work seconds of the job')
    p.add_argument('--wake-up-seconds', dest='wake_up_seconds', type=float, help='add: its wake-up seconds')
    p.add_argument('--job-id', dest='job_id', help='add: the job id (a job already in the ledger is not added twice)')
    p.add_argument('--what', help='add and start: a plain note')
    p.add_argument('--team-minutes', dest='team_minutes', type=float, help='start: the most card minutes the whole job may use')
    add_card_options(p)
    verb('check-presets')
    return parser
