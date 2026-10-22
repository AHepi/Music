BASE = {"maple_windows": False, "maple_thick_scale": 0.82, "maple_old_nn": True, "maple_old_noise": 0.02}
def V(**kw):
    d = dict(BASE); d.update(kw); return d
VARIANTS = [
 ("K", V()),
 ("L", V(maple_old_tone_blend=1.0)),
 ("M", V(maple_old_tone_blend=1.0, maple_old_normal_blend=0.5)),
 ("N", V(maple_old_tone_blend=1.0, maple_old_normal_blend=1.0)),
]
