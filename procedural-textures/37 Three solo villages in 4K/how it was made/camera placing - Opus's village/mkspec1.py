import json, math
def st(lx, ly):  # stable local -> world (centre 8, 31.5, rot -4 deg)
    a = math.radians(-4.0); c, s = math.cos(a), math.sin(a)
    return [round(8.0 + lx * c - ly * s, 3), round(31.5 + lx * s + ly * c, 3)]
E, H = 0.5, 0.15
spec = [
 # Cam06 cottage B (stone, thatch) three-quarter from the north-east
 dict(name="c06a", eye=[-26.0, -15.5], eye_h=1.65, tgt=[-36.0, -21.0], tgt_h=2.3, lens=26, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c06b", eye=[-28.5, -12.8], eye_h=1.65, tgt=[-36.0, -20.5], tgt_h=2.3, lens=24, dof="tgt", fstop=5.6, exposure=E, haze=H),
 # Cam07 props by cottage C
 dict(name="c07a", eye=[22.0, -4.6], eye_h=1.35, tgt=[22.0, -8.8], tgt_h=0.45, lens=24, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c07b", eye=[28.8, -5.4], eye_h=1.35, tgt=[21.5, -8.9], tgt_h=0.5, lens=30, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c07c", eye=[16.6, -5.6], eye_h=1.35, tgt=[20.0, -9.6], tgt_h=0.45, lens=26, dof="tgt", fstop=5.6, exposure=E, haze=H),
 # Cam08 stable stalls through the open middle door
 dict(name="c08a", eye=st(-0.9, -5.4), eye_h=1.65, tgt=st(-1.5, 2.2), tgt_z=1.25, lens=24, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="c08b", eye=st(-3.3, -5.6), eye_h=1.65, tgt=st(0.2, 2.0), tgt_z=1.2, lens=24, dof="tgt", fstop=5.6, exposure=E, haze=H),
 # Cam09 puddle ground level
 dict(name="c09a", eye=[4.35, 2.6], eye_h=0.4, tgt=[6.6, 16.0], tgt_h=0.6, lens=28, dof=[5.0, 5.6], exposure=E, haze=H),
 dict(name="c09b", eye=[-31.6, -9.9], eye_h=0.4, tgt=[-18.0, -6.6], tgt_h=0.5, lens=28, dof=[4.5, 5.6], exposure=E, haze=H),
 # Cam10 road into the forest
 dict(name="c10a", eye=[-38.0, -11.4], eye_h=1.65, tgt=[-62.0, -17.6], tgt_h=1.8, lens=26, exposure=E, haze=H),
 dict(name="c10b", eye=[-10.2, -30.5], eye_h=1.65, tgt=[-2.5, -50.0], tgt_h=1.8, lens=26, exposure=E, haze=H),
 # Cam11 low drone
 dict(name="c11a", eye=[-40.0, -16.0], eye_h=10.0, tgt=[-12.0, 10.0], tgt_h=0.0, lens=24, exposure=E, haze=H),
]
json.dump(spec, open('spec_r1.json', 'w'), indent=1)
json.dump([dict(name=s['name'], eye=s['eye'], tgt=s['tgt']) for s in spec], open('marks_r1.json', 'w'))
print(len(spec))
