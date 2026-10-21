# What this does: reads an audit JSON and prints counts per kind of message and the first examples. Changes nothing.
import json, re, sys, collections
r = json.load(open(sys.argv[1]))
print('profile', r['profile'], 'pass', r['pass'], 'eps', r['eps'], 'tol', r['tol'], 'gap', r['gap'])
print('errors', len(r['errors']), 'warnings', len(r['warnings']), 'objects', len(r['per_object']))
def kind(t):
    t2 = t.split(': ', 1)[1] if ': ' in t else t
    t2 = re.sub(r'[\d\.]+e?-?\d*', 'N', t2)
    t2 = re.sub(r'\[.*?\]', '[..]', t2)
    return t2
for key in ('errors', 'warnings'):
    c = collections.Counter(kind(t) for t in r[key])
    print('==', key)
    for k, n in c.most_common(): print(f'  {n:4d}  {k}')
print('== first 12 errors'); [print('  ', t) for t in r['errors'][:12]]
print('== first 12 warnings'); [print('  ', t) for t in r['warnings'][:12]]
print('total tris (welded)', sum(v['tris'] for v in r['per_object'].values()), 'parts', sum(v['parts'] for v in r['per_object'].values()))
print('objects with errors', sum(1 for v in r['per_object'].values() if v['errors']), 'with warnings', sum(1 for v in r['per_object'].values() if v['warnings']), 'clean', sum(1 for v in r['per_object'].values() if not v['errors'] and not v['warnings']))
