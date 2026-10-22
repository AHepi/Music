# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE ACCEPTANCE CHECKS of the where-pictures: numbers measured on what the reader made, compared with the set's `expect` block (facts measured earlier from the real
# geometry) and with the plan's rules (the "check" column of section 6.2). Each check returns {pass: True/False/None, value, wanted, note}; None = not applicable (the set has
# no such thing). Only generic comparisons live here; every number to compare against is in the set file.
import re

import numpy as np


def _c(passed, value, wanted, note=''):
    return dict(passed=passed, value=value, wanted=wanted, note=note)


def run_geometry_checks(settings, role_map, geo, grid, a, fine, fine_grid, sheets, entrances):
    expect = settings.get('expect') or {}
    out = {}
    has = a['has_ground']
    names = a['_role_names']
    # ---- ground facts
    if 'ground_slope_deg' in expect:
        roles = settings.expand_roles((settings.geometry.get('crown') or {}).get('roles', [])) or settings.expand_roles(settings.geometry['ground']['roles'])[:1]
        if roles and roles[0] in names:
            mask = (a['ground_role'] == names.index(roles[0]) + 1)
            if mask.any():
                ys, xs = np.nonzero(mask)
                A = np.stack([grid.xs[xs], grid.ys[ys], np.ones(len(xs))], axis=1)
                coef, *_ = np.linalg.lstsq(A, a['ground_height'][ys, xs].astype(np.float64), rcond=None)
                deg = float(np.degrees(np.arctan(np.hypot(coef[0], coef[1]))))
                out['slope_degrees'] = _c(abs(deg - expect['ground_slope_deg']) <= 0.3, deg, expect['ground_slope_deg'], 'plane fitted through the crown role (the overall lean)')
    crown_spec = settings.geometry.get('crown')
    if crown_spec and 'crown_m' in expect:
        role = settings.expand_roles(crown_spec['roles'])[0]
        mask = a['ground_role'] == names.index(role) + 1
        crown = a['crown']
        # the middle of the crown role across x: take the dots whose crown is highest per row, report the height of the crown above the lowest dot of the role at the same y
        h = a['ground_height']
        ys = np.nonzero(mask.any(axis=1))[0]
        diffs = []
        for j in ys[::20]:
            row = np.nonzero(mask[j])[0]
            if len(row) > 10:
                diffs.append(float(h[j, row].max() - h[j, row].min()))
        value = float(np.median(diffs)) if diffs else None
        out['crown_height_m'] = _c(abs(value - expect['crown_m']) <= 0.01 if value is not None else None, value, expect['crown_m'], 'highest minus lowest road dot in a row')
        # crown mask near the middle line and beyond 1.8 m of it (x is across)
        cx = 0.5 * (grid.X[mask].max() + grid.X[mask].min()) if mask.any() else 0.0
        near = mask & (np.abs(grid.X - cx) < 1.0)
        far = mask & (np.abs(grid.X - cx) > 1.8)
        if near.any():
            out['crown_near_middle'] = _c(float((crown[near] >= 0.6).mean()) >= 0.9, float((crown[near] >= 0.6).mean()), '>= 0.9 of dots at >= 0.6', 'within 1 m of the middle line')
        if far.any():
            out['crown_far'] = _c(float((crown[far] == 0).mean()) >= 0.95, float((crown[far] == 0).mean()), '>= 0.95 of dots at 0.0', 'farther than 1.8 m from the middle line')
        other = has & ~mask
        out['crown_off_role'] = _c(float(crown[other].max()) == 0.0 if other.any() else None, float(crown[other].max()) if other.any() else None, 0.0, 'no crown on other ground roles')
    for role_key, label in (('ground.channel', 'gutter'),):
        if role_key in names and has.any():
            mask = a['ground_role'] == names.index(role_key) + 1
            if mask.any():
                low = a['lowness'][mask]
                out['lowness_gutter'] = _c(float((low >= 0.7).mean()) >= 0.95, float((low >= 0.7).mean()), '>= 0.95 of dots at >= 0.7', f'{role_key} dots')
    if crown_spec:
        role = settings.expand_roles(crown_spec['roles'])[0]
        mask = a['ground_role'] == names.index(role) + 1
        mid = mask & (np.abs(grid.X - (0.5 * (grid.X[mask].max() + grid.X[mask].min()))) < 0.5)
        if mid.any():
            out['lowness_road_middle'] = _c(float(np.percentile(a['lowness'][mid], 95)) <= 0.2, float(np.percentile(a['lowness'][mid], 95)), '<= 0.2', '95th percentile of the middle of the crown role')
    # ---- entrances, steps
    if 'doorways' in expect:
        out['entrances_found'] = _c(len(entrances) == expect['doorways'], len(entrances), expect['doorways'])
    if 'ledges_sample' in expect and sheets:
        out.update(_ledge_checks(expect['ledges_sample'], sheets, role_map))
    if 'stone_pieces' in expect:
        out['stone_pieces_wanted'] = _c(None, None, expect['stone_pieces'], 'compare with stats.fine.pieces of the pack')
    # ---- the earlier places pictures (regression)
    reg = expect.get('places_regression')
    return out


def _ledge_checks(exp, sheets, role_map):
    """Compares the ledge finder's sources on the sheet that holds the sample object (exp['object']) with the expected heights (within 5 cm)."""
    out = {}
    target = None
    for sh in sheets:
        if any(o.startswith(exp['object']) for o in sh.objects):
            target = sh
    if target is None:
        # the sheet that serves the first house of the expectation: any sheet whose object list matches the pattern
        return out
    heights = sorted(s.z for s in target.sources if s.kind in ('ledge', 'eave'))

    def has(z, tol=0.05):
        return any(abs(h - z) <= tol for h in heights)
    for key, label in (('sills_m', 'sills'), ('lintels_m', 'lintels')):
        wanted = exp.get(key, [])
        found = [has(z) for z in wanted]
        out[f'ledge_{label}'] = _c(all(found) if wanted else None, [round(h, 3) for h in heights], wanted, f'within 5 cm: {found}')
    for key in ('string_course_m', 'eaves_course_m'):
        if key in exp:
            out[f'ledge_{key}'] = _c(has(exp[key]), [round(h, 3) for h in heights], exp[key], '')
    if 'steps_out_m' in exp:
        outs = sorted({round(0.5 * (s.out0 + s.out1), 2) for s in target.sources if s.z < 0.0 and s.out1 > 0.1})
        out['ledge_steps_out'] = _c(all(any(abs(o - w) <= 0.05 for o in outs) for w in exp['steps_out_m']), outs, exp['steps_out_m'], 'middle of each step tread (m out from the wall face)')
    pipe = target.pipe_info
    if pipe and 'pipe_run_across_m' in exp:
        out['pipe_across'] = _c(abs(abs(pipe['u']) - exp['pipe_run_across_m']) <= 0.05, pipe['u'], exp['pipe_run_across_m'], 'pipe column across the front (sign depends on the frame)')
        out['pipe_proud'] = _c(abs(pipe['proud'] - exp['pipe_proud_m']) <= 0.05, pipe['proud'], exp['pipe_proud_m'])
    return out


def habitat_checks(gp):
    """The exclusion rules inside the habitat fields (plan P6, first half): exactly 0.0 where footfall >= 0.6, crown >= 0.7 or keepclear >= 0.5 (moss, weeds, lichen; algae is not
    kept off the crown or the lanes by the plan's rule, only off keep-clear places)."""
    out = {}
    zones = {'footfall_0.6': gp['footfall'] >= 0.6, 'crown_0.7': gp['crown'] >= 0.7, 'keepclear_0.5': gp['keepclear'] >= 0.5}
    for field in ('moss_site', 'weed_site', 'lichen_site'):
        worst, count = 0.0, 0
        for name, zone in zones.items():
            if zone.any():
                worst = max(worst, float(gp[field][zone].max()))
                count += int(zone.sum())
        out[f'{field}_zero_in_zones'] = _c(worst == 0.0, worst, 0.0, f'{count} dots in the three zones')
    zone = gp['keepclear'] >= 0.5
    if zone.any():
        out['algae_site_zero_in_keepclear'] = _c(float(gp['algae_site'][zone].max()) == 0.0, float(gp['algae_site'][zone].max()), 0.0, f'{int(zone.sum())} dots')
    return out


def resolve_stone_pieces(manifest):
    """The one check the reader cannot make before the pack's statistics exist: the set's expected count of separate stones of a role (stone_pieces) against what the fine pictures found.
    Call it after manifest['stats'] is set. A count of at least the wanted number passes (a mesh may split a stone in two, never merge two)."""
    check = (manifest.get('checks') or {}).get('stone_pieces_wanted')
    if not check or check.get('passed') is not None:
        return
    want = check['wanted']
    found = ((manifest.get('stats') or {}).get('fine') or {}).get('pieces', {}).get(want['role'])
    check['value'] = found
    check['passed'] = found is not None and found >= want['count']
    check['note'] = f"{found} separate pieces of {want['role']} found, {want['count']} wanted (at least)"
