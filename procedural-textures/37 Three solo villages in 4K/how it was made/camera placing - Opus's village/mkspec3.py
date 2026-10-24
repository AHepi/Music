import json, math
def st(lx, ly):
    a = math.radians(-4.0); c, s = math.cos(a), math.sin(a)
    return [round(8.0 + lx * c - ly * s, 3), round(31.5 + lx * s + ly * c, 3)]
E, H = 0.5, 0.15
spec = [
 dict(name="c06f", eye=[-27.0, -28.8], eye_h=1.65, tgt=[-36.2, -21.2], tgt_h=2.2, lens=28, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c06g", eye=[-30.8, -33.0], eye_h=1.65, tgt=[-35.6, -21.0], tgt_h=2.2, lens=28, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c07g", eye=[-3.0, 24.6], eye_h=1.35, tgt=[4.5, 27.4], tgt_h=0.5, lens=26, dof=[5.5, 5.6], exposure=E, haze=H),
 dict(name="c08f", eye=st(-1.35, -6.6), eye_h=1.62, tgt=st(-1.35, 2.0), tgt_z=1.45, lens=32, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c08g", eye=st(0.6, -6.4), eye_h=1.62, tgt=st(-1.9, 1.8), tgt_z=1.4, lens=30, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c08h", eye=st(-3.3, -6.4), eye_h=1.62, tgt=st(-0.9, 1.8), tgt_z=1.4, lens=30, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c08i", eye=st(-1.35, -6.6), eye_h=1.62, tgt=st(-1.35, 2.0), tgt_z=1.45, lens=32, dof="tgt", fstop=5.6, exposure=1.3, haze=H),
 dict(name="c09c", eye=[4.75, 3.2], eye_h=0.35, tgt=[6.4, 16.0], tgt_h=0.55, lens=28, dof=[4.5, 5.6], exposure=E, haze=H),
]
json.dump(spec, open('spec_r3.json', 'w'), indent=1)
