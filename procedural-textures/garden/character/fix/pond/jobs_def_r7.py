BASE = {"maple_windows": False, "maple_thick_scale": 0.82}
def V(**kw):
    d = dict(BASE); d.update(kw); return d
VARIANTS = [
 ("X1", V(maple_hue_noise=0.02, maple_old_noise=0.02, maple_tone_sd=0.04, maple_wr_scale=0.3)),
 ("X2", V(maple_hue_noise=0.01, maple_old_noise=0.01, maple_tone_sd=0.02, maple_wr_scale=0.1, maple_old_cell=0.3)),
]
