# What this does (plain words): assembles a stamp-paint description (class S) from the fitted layout, the fitted paint model and the palette of the traced
# description; options let the stamp shape, the noise scale and the coherent field strength be changed so that settings can be compared.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SLATE = os.path.abspath(os.path.join(HERE, '..'))

def build(name, rate_scale=None, shape='streak', noise_scale=1.0, field_amp=6.0, seed=1, with_paint=True, contrast=1.0):
    base = json.load(open(os.path.join(SLATE, 'description', 'S0_layout_only.json')))
    m = json.load(open(os.path.join(HERE, 'paint_model.json')))
    model = {k: v for k, v in m.items() if k != 'slates'}
    model['field'] = {'amp': field_amp, 'scale_x': 70.0, 'scale_y': 90.0}
    # rebuild the layout block with the newest fit (clipped leans)
    sys.path.insert(0, HERE)
    import describe_tools as dt
    import make_descriptions as md
    trace = json.load(open(os.path.join(HERE, 'trace_full.json')))
    d = md.layout_only_description(trace)
    md.finish(d)
    if with_paint:
        d['paint'] = {'model': model, 'slates': m['slates'], 'seed': seed, 'shape': shape, 'noise_scale': noise_scale, 'contrast': contrast}
        if rate_scale:
            d['paint']['rate_scale'] = rate_scale
    path = os.path.join(SLATE, 'description', name + '.json')
    json.dump(d, open(path, 'w'), separators=(',', ':'))
    return path

if __name__ == '__main__':
    print(build(sys.argv[1]))
