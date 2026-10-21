# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Makes the SECOND set of pinned copies of the earlier layers: the ones the second painter round fixed (rubbish: flatter coal lumps, more gutter density, curved straw, pieces that gather
# at kerb and wall foot, new defaults amount 1.4 / patchiness 0.7 / wall foot 0.6; joints: new joint pictures and a joint relief that fades earlier). The first set (integrate/legacy_pinned/,
# made by pin_legacy.py) stays as it was, so the frozen baseline in harness/baseline/ can still be understood; the integrator's pictures use THIS set, because the second round's plate
# step is finished (its numbers are in painter_round_2/plate/plate_round2_numbers.json).
# The copies keep the folder layout of street_wet (tools/, relief_and_rubbish/...) so every relative path in them works. The only edits: the lines that pointed at the original folder by
# absolute path (the second round's files had them) are put back to the relative form the first set uses, so the pinned folder holds together on its own, and the wetness script
# reads its photo pictures from the original set_copy folder (as in the first set). legacy_round2.json holds the hash of every original and of every copy and the edit.
# Run: python3 -I pin_round2.py     (only to re-pin on purpose; it never writes outside integrate/legacy_round2/)
import hashlib
import json
import os
import re

SRC = 'proc-work/street_wet'
R2 = os.path.join(SRC, 'painter_round_2', 'plate')
HERE = os.path.dirname(os.path.abspath(__file__))
FIRST = os.path.join(HERE, 'legacy_pinned', 'earlier')
DST = os.path.join(HERE, 'legacy_round2', 'earlier')
# (relative path inside the pinned layout, where the original lives)
FILES = {
    'tools/wetness_layer.py': os.path.join(SRC, 'tools/wetness_layer.py'),
    'tools/apply_wetness_to_set.py': os.path.join(SRC, 'tools/apply_wetness_to_set.py'),
    'tools/22_render_eevee.py': os.path.join(SRC, 'tools/22_render_eevee.py'),
    'relief_and_rubbish/setts/tools/joint_layer.py': os.path.join(R2, 'setts/tools/joint_layer.py'),
    'relief_and_rubbish/setts/tools/apply_joints_to_set.py': os.path.join(R2, 'setts/tools/apply_joints_to_set.py'),
    'relief_and_rubbish/setts/tools/measure_grid_visibility.py': os.path.join(R2, 'setts/tools/measure_grid_visibility.py'),
    'relief_and_rubbish/setts/maps/sett_joints_clean.png': os.path.join(R2, 'setts/maps/sett_joints_clean.png'),
    'relief_and_rubbish/setts/maps/sett_groove_normal_16bit.png': os.path.join(R2, 'setts/maps/sett_groove_normal_16bit.png'),
    'relief_and_rubbish/rubbish/tools/rubbish_layer.py': os.path.join(R2, 'rubbish/tools/rubbish_layer.py'),
    'relief_and_rubbish/rubbish/tools/rubbish_pieces.py': os.path.join(R2, 'rubbish/tools/rubbish_pieces.py'),
    'relief_and_rubbish/rubbish/tools/apply_rubbish_to_set.py': os.path.join(R2, 'rubbish/tools/apply_rubbish_to_set.py'),
    'relief_and_rubbish/rubbish/tools/rubbish_runner.py': os.path.join(R2, 'rubbish/tools/rubbish_runner.py'),
    'relief_and_rubbish/rubbish/tools/make_places_pictures.py': os.path.join(R2, 'rubbish/tools/make_places_pictures.py'),
    'relief_and_rubbish/rubbish/maps/places_street_a.png': os.path.join(R2, 'rubbish/maps/places_street_a.png'),
    'relief_and_rubbish/rubbish/maps/places_street_b.png': os.path.join(R2, 'rubbish/maps/places_street_b.png'),
    'relief_and_rubbish/rubbish/maps/places_lockout_a.png': os.path.join(R2, 'rubbish/maps/places_lockout_a.png'),
    'relief_and_rubbish/rubbish/maps/places_lockout_b.png': os.path.join(R2, 'rubbish/maps/places_lockout_b.png'),
    'relief_and_rubbish/rubbish/work/objects_street.txt': os.path.join(R2, 'rubbish/work/objects_street.txt'),
    'relief_and_rubbish/study/tools/b02_lighting_and_variants.py': os.path.join(R2, 'study/tools/b02_lighting_and_variants.py'),
    'relief_and_rubbish/study/tools/b04_measure_joints.py': os.path.join(R2, 'study/tools/b04_measure_joints.py'),
    'relief_and_rubbish/study/tools/b09_lighting_test_set.py': os.path.join(R2, 'study/tools/b09_lighting_test_set.py'),
    'relief_and_rubbish/study/work/joint_cores.png': os.path.join(SRC, 'relief_and_rubbish/study/work/joint_cores.png'),
}
ABS = re.compile(r"os\.path\.abspath\('" + re.escape(SRC) + r"'\)")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def first_set_line(rel, pattern):
    """The relative form the first pinned set uses for the same line (found by pattern)."""
    text = open(os.path.join(FIRST, rel)).read()
    match = re.search(pattern, text, re.M)
    return match.group(0) if match else None


def main():
    record = {'schema': 'legacy-pinned/1', 'what': 'second painter round (rubbish and joints fixed); source_root is street_wet, the second round files are in painter_round_2/plate', 'source_root': SRC, 'files': {}}
    for rel, src in FILES.items():
        dst = os.path.join(DST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        data = open(src, 'rb').read()
        edits = []
        if rel == 'tools/apply_wetness_to_set.py':
            data = open(os.path.join(FIRST, rel), 'rb').read()      # the first set's copy carries the one allowed edit (the photo folder), the original is unchanged
            edits.append('same file as the first set (photo folder path)')
        elif rel.endswith('.py') and ABS.search(data.decode()):
            text = data.decode()
            out = []
            for line in text.split('\n'):
                if ABS.search(line):
                    key = line.split('=')[0].strip() if line.lstrip().startswith(('ROOT', 'RUBBISH')) else None
                    old = first_set_line(rel, r'^ROOT = .*$') if key == 'ROOT' else None
                    if key == 'ROOT' and old:
                        edits.append(f'ROOT line put back to the relative form: {old.strip()}')
                        line = old
                    elif 'sys.path.insert' in line:
                        old = first_set_line(rel, r'^sys\.path\.insert\(0, os\.path\.join\(HERE, .*$')
                        if old is None:
                            raise SystemExit(f'{rel}: no relative form for {line.strip()}')
                        edits.append('sys.path line put back to the relative form')
                        line = old
                    else:
                        raise SystemExit(f'{rel}: an absolute path line I do not know: {line.strip()}')
                out.append(line)
            data = '\n'.join(out).encode()
        open(dst, 'wb').write(data)
        record['files'][rel] = dict(original=src, original_sha256=sha(open(src, 'rb').read()), pinned_sha256=sha(data), edited=bool(edits), edits=edits, bytes=len(data))
    json.dump(record, open(os.path.join(HERE, 'legacy_round2.json'), 'w'), indent=1)
    print('pinned', len(FILES), 'files,', sum(v['bytes'] for v in record['files'].values()), 'bytes')


if __name__ == '__main__':
    main()
