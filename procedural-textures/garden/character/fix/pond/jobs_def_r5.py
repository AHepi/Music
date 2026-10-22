BASE = {"maple_windows": False, "maple_thick_scale": 0.82}
def V(**kw):
    d = dict(BASE); d.update(kw); return d
VARIANTS = [
 ("G", V(maple_hue_noise=0.05, maple_old_noise=0.05, maple_tone_sd=0.08)),
 ("H", V(maple_hue_noise=0.05, maple_old_noise=0.05, maple_tone_sd=0.08, maple_wr_scale=0.6)),
 ("I", V(maple_hue_noise=0.04, maple_old_noise=0.04, maple_tone_sd=0.06, maple_wr_scale=0.45, maple_bump=1.3)),
 ("J", V(maple_hue_noise=0.05, maple_old_noise=0.05, maple_tone_sd=0.08, maple_wr_scale=0.6, maple_sun_bias=0.3)),
]
