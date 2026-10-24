import json, math
def st(lx, ly):
    a = math.radians(-4.0); c, s = math.cos(a), math.sin(a)
    return [round(8.0 + lx * c - ly * s, 3), round(31.5 + lx * s + ly * c, 3)]
E, H = 0.5, 0.15
spec = [
 dict(name="c06c", eye=[-16.5, 21.0], eye_h=1.65, tgt=[-10.0, 28.6], tgt_h=1.9, lens=26, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c06d", eye=[-3.6, 21.6], eye_h=1.65, tgt=[-10.0, 28.6], tgt_h=1.9, lens=26, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c06e", eye=[-29.5, -31.5], eye_h=1.65, tgt=[-36.0, -21.0], tgt_h=2.3, lens=26, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c07d", eye=[-1.5, 25.5], eye_h=1.35, tgt=[5.0, 27.3], tgt_h=0.5, lens=26, dof=[4.5, 5.6], exposure=E, haze=H),
 dict(name="c07e", eye=[0.2, 24.0], eye_h=1.35, tgt=[3.2, 27.7], tgt_h=0.45, lens=26, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c07f", eye=[9.0, 21.6], eye_h=1.4, tgt=[11.8, 25.4], tgt_h=0.6, lens=24, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c08c", eye=st(-1.35, -4.7), eye_h=1.72, tgt=st(-1.35, 2.6), tgt_z=1.35, lens=20, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c08d", eye=st(-0.55, -4.9), eye_h=1.72, tgt=st(-2.3, 2.4), tgt_z=1.35, lens=22, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c08e", eye=st(-2.15, -4.7), eye_h=1.72, tgt=st(-0.3, 2.4), tgt_z=1.35, lens=22, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c10c", eye=[-35.5, -10.7], eye_h=1.65, tgt=[-62.0, -17.6], tgt_h=2.0, lens=28, exposure=E, haze=H),
 dict(name="c11b", eye=[-41.0, -14.0], eye_h=11.0, tgt=[-14.0, 14.0], tgt_h=0.0, lens=26, exposure=E, haze=H),
]
json.dump(spec, open('spec_r2.json', 'w'), indent=1)
print(len(spec))
