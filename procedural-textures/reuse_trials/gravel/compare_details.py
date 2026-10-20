# What this does (plain words): shows, for hand tuning, WHERE a picture differs from the gravel reference on the measures that score worst:
# the sharpness of edges (how big the step between neighbouring dots is, in percentiles), and how much picture detail sits at each feature size
# (the radial spectrum, as the difference candidate minus reference per size band, in log steps), plus the brightness distribution.
# It only reads the two pictures; it changes nothing. Use: python3 -I compare_details.py CANDIDATE_FOLDER   (a folder with colour.png and height.png)
import os
import sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import numpy as np
import texture_compare as tc

reference = tc.summarise(os.path.join(tc.REFERENCE_FOLDER, 'gravel'))
candidate = tc.summarise(sys.argv[1])
percent = [10, 25, 50, 75, 90, 99]
print('colour edge step (percentiles %s)' % percent)
print('  reference', np.round(np.percentile(reference['gradient'], percent), 4))
print('  candidate', np.round(np.percentile(candidate['gradient'], percent), 4))
print('height edge step')
print('  reference', np.round(np.percentile(reference['height_gradient'], percent), 4))
print('  candidate', np.round(np.percentile(candidate['height_gradient'], percent), 4))
edges = np.geomspace(3.0, 1254 / 2.0 - 1, 31)
print('spectrum candidate minus reference, by feature size (dots across = 1254 / frequency); positive = candidate has MORE detail there')
for name, key in (('colour', 'spectrum'), ('height', 'height_spectrum')):
    difference = candidate[key] - reference[key]
    row = ' '.join('%4.0f:%+.2f' % (1254.0 / ((edges[i] + edges[i + 1]) / 2), difference[i]) for i in range(0, 30, 3))
    print('  ', name, row)
print('lightness (L*) percentiles 5/25/50/75/95  reference', np.round(np.percentile(reference['lightness'], [5, 25, 50, 75, 95]), 1), ' candidate', np.round(np.percentile(candidate['lightness'], [5, 25, 50, 75, 95]), 1))
