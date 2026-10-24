import json, math
def st(lx, ly):
    a = math.radians(-4.0); c, s = math.cos(a), math.sin(a)
    return [round(8.0 + lx * c - ly * s, 3), round(31.5 + lx * s + ly * c, 3)]
E, H = 0.5, 0.15
spec = [
 dict(name="Cam06_second_cottage", eye=[-4.1, 22.0], eye_h=1.65, tgt=[-10.0, 28.7], tgt_h=1.85, lens=26, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="Cam07_props_close", eye=[-1.4, 24.4], eye_h=1.3, tgt=[3.6, 27.7], tgt_h=0.4, lens=24, dof=[4.5, 8.0], exposure=E, haze=H),
 dict(name="Cam07_alt", eye=[-2.0, 24.0], eye_h=1.3, tgt=[3.3, 26.75], tgt_h=0.4, lens=24, dof=[5.0, 8.0], exposure=E, haze=H),
 dict(name="Cam08_stable_stalls", eye=st(-1.15, -6.4), eye_h=1.62, tgt=st(-1.3, 2.0), tgt_z=1.35, lens=30, dof="tgt", fstop=5.6, exposure=E, haze=H),
 dict(name="Cam09_puddle_ground_level", eye=[4.35, 2.6], eye_h=0.4, tgt=[6.6, 16.0], tgt_h=0.6, lens=28, dof=[5.0, 5.6], exposure=E, haze=H),
 dict(name="Cam10_road_into_forest", eye=[-35.5, -10.7], eye_h=1.65, tgt=[-62.0, -17.6], tgt_h=2.0, lens=28, exposure=E, haze=H),
 dict(name="Cam11_village_low_drone", eye=[-40.0, -16.0], eye_h=10.0, tgt=[-12.0, 10.0], tgt_h=0.0, lens=24, exposure=E, haze=H),
]
json.dump(spec, open('spec_final_p2.json', 'w'), indent=1)
