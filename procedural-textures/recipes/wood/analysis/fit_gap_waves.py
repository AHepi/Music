# What this does (plain words): ANALYSIS. Writes each gap line and each gap width (from layout_fit.json) as a mean plus a few WAVES (whole numbers of waves per
# tile, amplitude, phase), found with a Fourier transform and keeping the strongest ones. This is the compact form the generator's "plank_rows" layer reads, and a
# line described this way repeats exactly across the tile edge. Output: gap_waves.json. Plain Python.
import json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
fit = json.load(open(os.path.join(HERE, 'layout_fit.json')))
gl = fit['gap_lines']
xs = np.linspace(gl['x_from'], gl['x_to'], gl['samples'])
grid = np.arange(1254)
def waves_of(values, keep, kmax=30):
    v = np.interp(grid, xs, values)                        # the samples cover a little more than one tile: take x = 0 .. 1253
    f = np.fft.rfft(v) / len(v)
    mean = float(f[0].real)
    order = np.argsort(-np.abs(f[1:kmax + 1])) + 1
    out = []
    for k in sorted(order[:keep].tolist()):
        out.append([int(k), round(float(2 * np.abs(f[k])), 2), round(float(np.angle(f[k]) / (2 * np.pi)), 3)])   # a cos(2 pi (k x / T + phase))
    return mean, out
result = []
for line, width in zip(gl['lines'], fit['gap_widths']):
    y, wave = waves_of(np.array(line, float), 10)
    w, wwave = waves_of(np.array(width, float), 5)
    result.append({'y': round(y, 1), 'wave': wave, 'width': round(w, 2), 'width_wave': wwave})
    # check: error of the wave form against the samples
    rec = y + sum(a * np.cos(2 * np.pi * (k * grid / 1254 + p)) for k, a, p in wave)
    print('gap at', round(y), ': 10 waves, max error', round(float(np.abs(rec - np.interp(grid, xs, line)).max()), 1), 'dots')
json.dump(result, open(os.path.join(HERE, 'gap_waves.json'), 'w'))
