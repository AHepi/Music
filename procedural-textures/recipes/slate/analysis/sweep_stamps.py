# What this does (plain words): tries several settings of the stamp paint (how random the tones are, how strong the smooth tone drift is, how many tiny
# patches) with the quick preview painter and prints how each one scores against the reference (same-kind score and its parts). Plain Python.
import itertools, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import preview_tools as pt
import build_s_description as bs
base_rates = [0.608, 0.671, 0.676, 0.78, 1.141, 4.089]
rows = []
grid = [dict(noise_scale=n, field_amp=f, small=s) for n, f, s in itertools.product((0.25, 0.4, 0.55), (9.0, 14.0, 20.0), (1.0,))]
for g in grid:
    rates = list(base_rates)
    rates[0] *= g['small']; rates[1] *= g['small'] ** 0.5
    path = bs.build('tmp_sweep', rate_scale=rates, noise_scale=g['noise_scale'], field_amp=g['field_amp'])
    d = json.load(open(path))
    t = time.time()
    folder = os.path.join(HERE, 'prev_sweep')
    pt.write_preview(d, folder)
    sc = pt.score(folder)
    tx, px = sc['texture_compare'], sc['pixel_compare']
    row = dict(g, overall=tx['overall'], colour=tx['groups']['colour'], height=tx['groups']['height'], normal=tx['groups']['normal'], spectrum=tx['scores']['colour_spectrum'],
               scale=tx['scores']['colour_scale'], corr=tx['facts']['correlation_length_px_candidate'], de=px['colour_mean_delta_e'], hmae=px['height_mae_best_fit_levels'])
    print(row, flush=True)
    rows.append(row)
json.dump(rows, open(os.path.join(HERE, 'sweep_stamps.json'), 'w'), indent=1)
