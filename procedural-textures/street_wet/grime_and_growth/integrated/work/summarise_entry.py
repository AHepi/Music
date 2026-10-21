import json, sys, os
W = os.path.dirname(os.path.abspath(__file__))
for which in sys.argv[1:]:
    p = os.path.join(W, 'entry_tests', which, 'entry_test.json')
    if not os.path.exists(p): print(which, 'missing'); continue
    d = json.load(open(p))
    print('=====', which, 'errors:', len(d['errors']))
    for e in d['errors']: print(e[-1500:])
    t = d['tests']
    for k, v in t.items(): print(' ', k, json.dumps(v)[:300])
    print('  applied', d.get('applied'), 'problems', d.get('problems'), 'verify', d.get('verify_problems'))
    print('  seconds', d.get('seconds'))
