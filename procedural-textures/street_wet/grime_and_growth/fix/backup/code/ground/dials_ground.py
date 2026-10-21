# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The EXTRA dials of the four ground layers (dirt, groundcracks, groundmoss, iron). The dials of the plan's Appendix A are already in apply/dial_table.json; this file adds a few
# finer ones in the same style (the plan allows it: "you may add finer ones, you may not rename or remove the Appendix A ones") and a debug dial `show_part`.
#   * show_part: 0 = the layer's whole Mask output; 1, 2, 3 ... = one named part of the layer (PARTS below). The checking views (`layer:<key>` through the runner or
#     apply_ground.show_part) use it, and so do the measures that count one element (tar, cracks ...). It changes only the Mask output, never the picture.
#   * Every extra dial has a kit default that suits any set; a look can change it two ways: a file ground/looks_ground/<look id>.json ({layer: {dial: value}}) read by
#     apply_ground.register(), or (when the integrator wants) the same rows in presets/<look>.json.
# A dial is one number; sizes are in metres unless the unit says plate dots; shares are 0..1.
from apply import dials


def row(name, lo, hi, default, doc, unit=''):
    return dict(name=name, lo=lo, hi=hi, unit=unit, default=default, doc=doc)


EXTRA = {
    'dirt': [
        row('show_part', 0, 9, 0, 'Checking view only: 0 = the whole Mask output; 1 film, 2 polish, 3 water marks, 4 rust halo, 5 drum ring, 6 tar patches, 7 tar splash, 8 scrub strip.'),
        row('film_octaves', 1, 6, 3, 'How broken-up the film patches are (noise detail).'),
        row('dust', 0.0, 0.15, 0.04, 'A thin even dust on all ground that dulls its tone a little at every distance (the film is patchy and gives way to its average far away; this is the part that stays).'),
        row('ring_m', 0.03, 0.4, 0.1, 'Width of the dried puddle ring.', 'm'),
        row('pool_scale_m', 0.5, 3.0, 1.3, 'Size of the shallow dips the dried puddle rings sit in.', 'm'),
        row('drum_ring_m', 0.03, 0.4, 0.12, 'Width of the rust bleed ring round the fire drum.', 'm'),
        row('tar_spacing_m', 2.0, 15.0, 6.0, 'Tar patch sites lie on a loose grid of this size.', 'm'),
        row('tar_patch_m', 0.3, 1.6, 0.75, 'Longest half-size of a tar patch (shrunk so that tar_max_share is never passed).', 'm'),
        row('tar_weathered', 0.0, 1.0, 0.6, 'Share of tar patches that are old, grey and matt (the rest are new, black and glossy).'),
        row('tar_chippings', 0.0, 1.0, 0.5, 'Strength of the pale chippings speckle on a tar patch.'),
        row('splash_m', 0.1, 0.6, 0.25, 'Size of a tar splash at the kerb foot.', 'm'),
        row('scrub_whitened_share', 0.0, 1.0, 0.5, 'Same number as the doorstep layer\'s whitened_share (copied from the look when the layer is registered).'),
        row('scrub_scrubbed_share', 0.0, 1.0, 0.3, 'Same number as the doorstep layer\'s scrubbed_share (copied from the look when the layer is registered).'),
        row('scrub_lift', 0.0, 1.0, 0.45, 'How much paler the scrubbed strip on the flags is than the dirty flags round it.'),
        row('mark_dots', 4, 40, 14, 'Smallest width in plate dots of a stain edge or a ring (they are widened with distance up to Inflate Limit).'),
    ],
    'groundcracks': [
        row('show_part', 0, 12, 0, 'Checking view only: 0 = whole Mask; 1 flag fine cracks, 2 flag broken, 3 flag tilted, 4 flag chipped corners, 5 kerb chips, 6 kerb open joints and cracks, 7 kerb scuffs, 8 setts disturbed, 9 sett open joints; 10 and 11 the flags that were chosen for fine and for broken cracks (whole flag), 12 all sett joints (the length the open-joint share is counted against).'),
        row('crack_scale_m', 0.4, 2.0, 0.85, 'Size of the pieces the crack lines run between (about one flag).', 'm'),
        row('crack_real_mm', 1, 8, 3, 'Real width of a fine crack, before it is drawn wider for the picture.', 'mm'),
        row('broken_gap_mm', 2, 12, 5, 'Real width of the gap of a broken flag.', 'mm'),
        row('site_bias', 0.0, 1.0, 0.6, 'How much cracks gather near the kerb, seams and covers rather than anywhere.'),
        row('chip_m', 0.02, 0.15, 0.05, 'Size of one kerb or flag edge chip.', 'm'),
        row('chip_depth_mm', 5, 40, 15, 'Depth of a kerb chip.', 'mm'),
        row('sunk_depth_mm', 2, 25, 8, 'How far a sunken sett patch lies below its neighbours.', 'mm'),
        row('missing_depth_mm', 10, 60, 30, 'Depth of a missing sett.', 'mm'),
        row('lip_dark', 0.0, 1.0, 0.35, 'Darkness of the shadow line along the raised edge of a tilted flag.'),
        row('relief', 0.0, 1.0, 1.0, 'Strength of the slopes (the Bump): lips of tilted stones, chip notches, crack grooves. 0 = colour and dullness only.'),
        row('ref_brightness', 0.1, 0.5, 0.2, 'Plate brightness of the surface the cracks sit on (a crack_contrast of 0.11 on 0.2 takes the plate down to 0.09).'),
        row('open_dark', 0.0, 0.6, 0.22, 'How much darker an open joint is than the joint round it (the joint layer already makes joints dark).'),
    ],
    'groundmoss': [
        row('show_part', 0, 9, 0, 'Checking view only: 0 = whole Mask; 1 joint moss, 2 patch moss, 3 algae fans, 4 liverwort, 5 far band, 6 all joints where moss could grow (the length the moss share is counted against).'),
        row('patch_moss', 0.0, 1.0, 0.6, 'Moss as soft patches on open ground (for sets with no joints, e.g. earth, gravel, stones). A set that wants moss only in joints gives the role a multiplier of 0.'),
        row('patch_scale_m', 0.2, 2.0, 0.7, 'Size of a moss patch on open ground.', 'm'),
        row('moss_lift', 1.0, 6.0, 2.2, 'How much lighter than the stone beneath the dry moss is (in scene light; the painter weakens colour, so moss is made stronger than wanted).'),
        row('moss_rim', 0.0, 1.0, 0.5, 'A paler rim on the moss edge (a painted look).'),
        row('liverwort_m', 0.1, 0.6, 0.25, 'Size of a liverwort patch.', 'm'),
        row('algae_dark', 0.0, 1.0, 0.55, 'How dark the algae film is (1 = near black-green).'),
        row('outlet_reach', 0.05, 1.0, 0.7, 'How close to a wall (0 touching, 1 = the set\'s wall reach) a standing foot must be to count as a downpipe outlet; posts stand farther out.'),
    ],
    'iron': [
        row('show_part', 0, 9, 0, 'Checking view only: 0 = whole Mask; 1 foot rust, 2 collar rings, 3 shoe streak, 4 base ring, 5 drum rust, 6 heat scale, 7 soot.'),
        row('streak_m', 0.01, 0.08, 2.5e-2, 'Width of a vertical rust or wet streak.', 'm'),
        row('rust_bright', 1.0, 3.5, 1.7, 'Brightness of rust against the iron paint it lies on (1 = as dark as the paint).'),
        row('grime_dark', 0.0, 0.2, 0.06, 'A thin even coat of soot on all iron: it darkens the paint a little at every distance.'),
        row('shoe_streak', 0.0, 1.0, 0.6, 'Dark wet streak at the foot (shoe) of a downpipe.'),
        row('shoe_height', 0.1, 1.0, 0.45, 'How high the dark wet streak at the pipe shoe reaches.', 'm'),
        row('base_ring', 0.0, 1.0, 0.7, 'Rust ring at the base flange of a post.'),
        row('base_ring_m', 0.05, 0.3, 0.12, 'Height of the base-flange ring.', 'm'),
        row('collar_m', 0.02, 0.15, 0.06, 'Height of a rust ring at a collar.', 'm'),
        row('drum_rust', 0.0, 1.0, 0.7, 'Share of a drum covered by rust and old paint (60 to 80 percent).'),
        row('rim_soot_m', 0.03, 0.3, 0.12, 'Height of the black soot rim at the top of a drum.', 'm'),
    ],
}

_done = []


def ensure():
    """Adds the extra rows to the kit's dial table (once)."""
    if _done:
        return
    for layer, rows in EXTRA.items():
        existing = dials.TABLE.layers.get(layer)
        present = set(existing.names()) if existing else set()
        new = [r for r in rows if r['name'] not in present]
        if new:
            dials.register_layer(layer, new)
    _done.append(True)


def set_defaults(layer, values):
    """Changes the kit default of some dials of a layer (a look's extras). Unknown names raise."""
    table = dials.TABLE.layers[layer]
    for name, value in values.items():
        table.rows[name]['default'] = value
