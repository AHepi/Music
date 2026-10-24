import json, math
def st(lx, ly):
    a = math.radians(-4.0); c, s = math.cos(a), math.sin(a)
    return [round(8.0 + lx * c - ly * s, 3), round(31.5 + lx * s + ly * c, 3)]
E, H = 0.5, 0.15
spec = [
 dict(name="c06h", eye=[-4.6, 22.6], eye_h=1.65, tgt=[-10.0, 28.7], tgt_h=1.75, lens=26, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c07j", eye=[-1.0, 24.9], eye_h=1.3, tgt=[4.6, 27.6], tgt_h=0.4, lens=24, dof=[4.0, 8.0], exposure=E, haze=H),
 dict(name="c07k", eye=[0.0, 25.3], eye_h=1.35, tgt=[5.5, 27.8], tgt_h=0.45, lens=24, dof=[3.5, 8.0], exposure=E, haze=H),
 dict(name="c08j", eye=st(-1.15, -6.4), eye_h=1.62, tgt=st(-1.3, 2.0), tgt_z=1.35, lens=30, dof="tgt", fstop=5.6, exposure=E, haze=H),
]
json.dump(spec, open('spec_r4.json', 'w'), indent=1)
