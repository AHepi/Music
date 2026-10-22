# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE JOB WRITER: turns a set's test set into job files (one per scene file) that the runner draws. A job file is
#   {"set": set id, "scene": scene id, "pack": true, "feature_dirs": [...], "jobs": [job, ...]}.
# write(settings, look, out_dir, parts=...) writes jobs_<scene>_<look>.json and returns {scene id: path}. Several looks are written as several files (one Blender run each,
# 'today' first). run_all() does write + send + draw + bring back + measure in one go.
import json
import os

from apply import settings as settings_module

from . import testset


def feature_dirs(settings):
    """Where builders write feature_report.json (the set file's feature_report_dirs)."""
    return list(settings.get('feature_report_dirs', []))


def write(settings, looks, out_dir, parts=('t22', 'close', 'plates', 'masks'), scenes=None, extra_jobs=None, kit_root=None, layer_keys=()):
    os.makedirs(out_dir, exist_ok=True)
    result = {}
    for scene in settings.scenes:
        if scenes and scene['id'] not in scenes:
            continue
        for look in looks:
            jobs = testset.make_jobs(settings, look, scene['id'], parts, layer_keys=layer_keys)
            jobs += [j for j in (extra_jobs or []) if j.get('scene') in (None, scene['id'])]
            if not jobs:
                continue
            tag = look.replace(':', '_').replace(',', '+')
            path = os.path.join(out_dir, f'jobs_{scene["id"]}_{tag}.json')
            spec = dict(set=settings.id, scene=scene['id'], pack=True, feature_dirs=feature_dirs(settings), jobs=jobs)
            json.dump(spec, open(path, 'w'), indent=1)
            result[(scene['id'], look)] = path
    return result
