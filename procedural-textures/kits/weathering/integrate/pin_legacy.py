# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Makes PINNED COPIES of the three earlier layers' code (WETNESS, JOINTS, RUBBISH, with the pictures they read), so the baseline cannot drift if the originals change
# (the second painter round is fixing the rubbish pieces in the originals). The copies keep the originals' folder layout under legacy_pinned/street_wet/ so every relative
# path in them still works. The ONLY edit: apply_wetness_to_set.py reads its photo pictures from the original set_copy folder (an absolute path, same on the rented machine).
# legacy_pinned.json holds, for every file, the hash of the original and of the pinned copy, and the edit. Run again only to re-pin on purpose.
# Run: python3 -I pin_legacy.py
import hashlib
import json
import os
import shutil

SRC = 'proc-work/street_wet'
HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, 'legacy_pinned', 'earlier')
FILES = [
    'tools/wetness_layer.py', 'tools/apply_wetness_to_set.py', 'tools/22_render_eevee.py',
    'relief_and_rubbish/setts/tools/joint_layer.py', 'relief_and_rubbish/setts/tools/apply_joints_to_set.py',
    'relief_and_rubbish/setts/maps/sett_joints_clean.png', 'relief_and_rubbish/setts/maps/sett_groove_normal_16bit.png',
    'relief_and_rubbish/rubbish/tools/rubbish_layer.py', 'relief_and_rubbish/rubbish/tools/rubbish_pieces.py', 'relief_and_rubbish/rubbish/tools/apply_rubbish_to_set.py',
    'relief_and_rubbish/rubbish/tools/rubbish_runner.py', 'relief_and_rubbish/rubbish/tools/make_places_pictures.py',
    'relief_and_rubbish/rubbish/maps/places_street_a.png', 'relief_and_rubbish/rubbish/maps/places_street_b.png',
    'relief_and_rubbish/rubbish/maps/places_lockout_a.png', 'relief_and_rubbish/rubbish/maps/places_lockout_b.png',
    'relief_and_rubbish/rubbish/work/objects_street.txt',
    'relief_and_rubbish/study/tools/b02_lighting_and_variants.py', 'relief_and_rubbish/study/tools/b09_lighting_test_set.py', 'relief_and_rubbish/study/tools/b04_measure_joints.py',
    'relief_and_rubbish/setts/tools/measure_grid_visibility.py', 'relief_and_rubbish/study/work/joint_cores.png',
]
EDITS = {
    'tools/apply_wetness_to_set.py': [("TEX = os.path.join(ROOT, 'set_copy', 'polyhaven_maps') + os.sep", "TEX = os.path.join('%s', 'set_copy', 'polyhaven_maps') + os.sep" % SRC)],
}


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    record = {'schema': 'legacy-pinned/1', 'source_root': SRC, 'files': {}}
    for rel in FILES:
        src = os.path.join(SRC, rel)
        dst = os.path.join(DST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        data = open(src, 'rb').read()
        edits = EDITS.get(rel, [])
        if edits:
            text = data.decode()
            for old, new in edits:
                assert old in text, (rel, old)
                text = text.replace(old, new)
            data = text.encode()
        open(dst, 'wb').write(data)
        record['files'][rel] = dict(original_sha256=sha(src), pinned_sha256=sha(dst), edited=bool(edits), edits=[e[1] for e in edits], bytes=len(data))
    json.dump(record, open(os.path.join(HERE, 'legacy_pinned.json'), 'w'), indent=1)
    print('pinned', len(FILES), 'files,', sum(v['bytes'] for v in record['files'].values()), 'bytes')


if __name__ == '__main__':
    main()
