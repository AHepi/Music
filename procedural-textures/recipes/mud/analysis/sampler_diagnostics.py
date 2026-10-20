# What this does (plain words): compares simple "how much of the picture is what" numbers between the reference mud picture and sampled mud tiles (drawn with the quick numpy painter):
# share of grey/blue (stones and water), share of dark dots, average colour, share of bright dots. Used to calibrate the sampler's counts. Analysis only (reads the reference).
import sys, cv2, numpy as np
sys.path.insert(0, '../generator'); sys.path.insert(0, '.')
import sampler, mud_layers as ml, element_tools as et
ref = cv2.imread('../../../reference/mud/colour.png')
def facts(img):
    lab = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    nonearth = (lab[..., 2] < 7.0)
    water = (lab[..., 2] < -3.5) & (lab[..., 0] > 30)
    dark = lab[..., 0] < 18
    return dict(nonearth=round(float(nonearth.mean()), 3), water=round(float(water.mean()), 3), stone_like=round(float((nonearth & ~water).mean()), 3), dark=round(float(dark.mean()), 3),
                light_mean=round(float(lab[..., 0].mean()), 1), b_mean=round(float(lab[..., 2].mean()), 1), light_sd=round(float(lab[..., 0].std()), 1))
print('reference', facts(ref))
for seed in (11, 12, 13, 14):
    d = sampler.sample_description(seed)
    print('sample', seed, facts(ml.draw_preview(d)))
