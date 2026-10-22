# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# DAMPNESS and the four HABITAT FIELDS (moss_site, weed_site, algae_site, lichen_site) on the ground plan: where may each thing live. Made ONCE here and read by every layer
# that paints moss or algae and by the 3D weed and moss pieces, so painted and 3D growth land in the same places and the exclusion rules live in the field itself:
#     no growth where footfall is 0.6 or more, where the crown is 0.7 or more, where keepclear is 0.5 or more: those places are EXACTLY 0 (the gates reach 1 at those limits).
# Weights come from the set's `habitat` and `dampness` blocks. In words (plan section 6.3):
#   dampness   = weights x (closeness to a wall foot, drip zone, water, lowness, shelter, shade)
#   edge_affinity = the largest of "close to a wall foot", "close to a seam where two ground roles meet", "close to the foot of standing iron"
#   moss_site  = (w_damp x dampness + w_shade x shade + w_edge x edge_affinity) x (1 - footfall_gate) x (1 - keep_gate) x (1 - smother)
#   weed_site  = (w_edge x edge_affinity + w_seam x seam_closeness + w_light x (1 - shade)) x (1 - footfall_gate) x (1 - crown_gate) x (1 - keep_gate) x (1 - heap_gate)
#   algae_site = (w_damp x dampness + w_shade x shade + w_outlet x outlet) x (1 - keep_gate)
#   lichen_site = 0 unless habitat.lichen.enabled: (w_north x shade + (1 - w_north) x (1 - dampness)) x (1 - footfall_gate) x (1 - keep_gate)
import numpy as np

from .grid import smoothstep


def _g(a, lo, hi):
    return smoothstep(a, lo, hi).astype(np.float32)


def dampness(settings, a):
    """a: dict of ground-plan arrays (wall_dist in 0..1 of the reach, drip, water_dist, lowness, sheltered, shade). Returns 0..1."""
    spec = settings.get('dampness') or {}
    w = spec.get('weights', {})
    reach = settings.geometry.get('wall_reach_m', 1.275)
    foot_reach = spec.get('wall_foot_reach_m', 0.5)
    foot = np.clip(1.0 - a['wall_dist'] * reach / foot_reach, 0.0, 1.0)
    water = 1.0 - a['water_dist']
    terms = dict(wall_foot=foot, drip=a.get('drip', np.zeros_like(foot)), water=water, lowness=a['lowness'], shelter=a.get('sheltered', np.zeros_like(foot)), shade=a['shade'],
                 standing_foot=a.get('vertical_foot', np.zeros_like(foot)))
    total = np.zeros_like(foot)
    for key, array in terms.items():
        total = total + float(w.get(key, 0.0)) * array
    out = np.clip(total, 0.0, 1.0).astype(np.float32)
    out[~a['has_ground']] = 0.3
    return out


def fields(settings, a):
    """The four habitat fields on the ground grid. a: ground-plan arrays incl. dampness, shade, wall_dist, seam_dist, vertical_foot, footfall, crown, keepclear, rubbish_heap."""
    h = settings.get('habitat') or {}
    reach = settings.geometry.get('wall_reach_m', 1.275)
    moss, weed, algae, lichen = h.get('moss', {}), h.get('weed', {}), h.get('algae', {}), h.get('lichen', {})
    edge_reach = moss.get('edge_reach_m', 0.5)
    wall_close = np.clip(1.0 - a['wall_dist'] * reach / edge_reach, 0.0, 1.0)
    seam_close = np.clip(1.0 - a['seam_dist'] * 0.5 / (edge_reach / 2.0), 0.0, 1.0)
    foot_close = np.clip(1.0 - (1.0 - a['vertical_foot']) , 0.0, 1.0)
    edge_affinity = np.maximum.reduce([wall_close, seam_close, foot_close * 0.0 + a['vertical_foot']])
    foot_gate = _g(a['footfall'], 0.3, 0.6)
    crown_gate = _g(a['crown'], 0.4, 0.7)
    keep_gate = _g(a['keepclear'], 0.2, 0.5)
    heap = a.get('rubbish_heap', np.zeros_like(wall_close))
    smother = _g(heap, moss.get('rubbish_smother_from', 0.30), moss.get('rubbish_smother_to', 0.60))
    heap_gate = _g(heap, weed.get('rubbish_thin_max', 0.45), weed.get('rubbish_heap_min', 0.75))
    out = {}
    out['moss_site'] = (moss.get('dampness', 0.45) * a['dampness'] + moss.get('shade', 0.30) * a['shade'] + moss.get('edge', 0.25) * edge_affinity) \
        * (1 - foot_gate) * (1 - keep_gate) * (1 - smother)
    out['weed_site'] = (weed.get('edge', 0.55) * edge_affinity + weed.get('cracks_and_seams', 0.25) * seam_close + weed.get('light', 0.20) * (1.0 - a['shade'])) \
        * (1 - foot_gate) * (1 - crown_gate) * (1 - keep_gate) * (1 - heap_gate)
    out['algae_site'] = (algae.get('dampness', 0.5) * a['dampness'] + algae.get('shade', 0.2) * a['shade'] + algae.get('pipe_outlets', 0.3) * a['vertical_foot']) * (1 - keep_gate)
    if lichen.get('enabled'):
        north = lichen.get('north_bias', 0.6)
        out['lichen_site'] = (north * a['shade'] + (1 - north) * (1.0 - a['dampness'])) * (1 - foot_gate) * (1 - keep_gate)
    else:
        out['lichen_site'] = np.zeros_like(wall_close)
    for key in out:
        out[key] = np.clip(out[key], 0.0, 1.0).astype(np.float32)
        out[key][~a['has_ground']] = 0.0
    return out
