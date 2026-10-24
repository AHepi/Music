"""Strict, Blender-independent semantic contract. JSON is data, never executable.
Units are source-local metres. An object's positive uniform scale scales the result.
Authored fields are art direction; no erosion, ecological or structural simulation.
"""
import copy
import hashlib
import json
import math
import random

VERSION = '0.2.1'
SCHEMA = 'astra.landscape/1'


def number(value, label, lo, hi):
    if type(value) not in (int, float) or not lo <= value <= hi or not math.isfinite(value):
        raise ValueError(f'{label} must be finite in [{lo}, {hi}]')
    return float(value)


def integer(value, label, lo=0, hi=1048576):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{label} must be an integer in [{lo}, {hi}]')
    return value


def fields(value, required, optional=(), label='object'):
    if type(value) is not dict or any(type(k) is not str for k in value):
        raise ValueError(label + ' must be an object with string keys')
    extra = set(value) - set(required) - set(optional)
    missing = set(required) - set(value)
    if extra or missing:
        raise ValueError(f'{label}: unknown fields {sorted(extra)}; missing {sorted(missing)}')


def vec(value, count, label, lo=-10000, hi=10000):
    if type(value) not in (tuple, list) or len(value) != count:
        raise ValueError(f'{label} must contain {count} numbers')
    return [number(v, label, lo, hi) for v in value]


def stable_rng(seed, identity):
    # No Python hash(), object-name hashes, global random state, or wall-clock seeds.
    digest = hashlib.sha256(f'{seed}|{identity}'.encode('utf8')).digest()
    return random.Random(int.from_bytes(digest[:16], 'big'))


def validate(spec):
    fields(spec, ['schema', 'seed', 'detail_scale', 'relief', 'paths', 'protected',
                  'water', 'contacts', 'shelter', 'pebbles', 'moss'])
    if spec['schema'] != SCHEMA:
        raise ValueError('Unsupported landscape schema; expected ' + SCHEMA)
    integer(spec['seed'], 'seed'); number(spec['detail_scale'], 'detail_scale', .25, 3)
    fields(spec['relief'], ['height', 'banks'], label='relief')
    number(spec['relief']['height'], 'relief.height', 0, 1.5)
    all_ids = set()
    def zones(rows, label, weights=False):
        if type(rows) is not list or len(rows) > 64:
            raise ValueError(label + ' must be a list with at most 64 zones')
        for row in rows:
            fields(row, ['id', 'center', 'radius'] + (['weight'] if weights else []), label=label)
            uid = row['id']
            if type(uid) is not str or not 1 <= len(uid) <= 64 or uid in all_ids:
                raise ValueError('Zone IDs must be nonempty, unique stable strings, at most 64 characters')
            all_ids.add(uid); vec(row['center'], 2, label+'.center')
            vec(row['radius'], 2, label+'.radius', .05, 100)
            if weights: number(row['weight'], label+'.weight', 0, 1)
    zones(spec['relief']['banks'], 'relief.banks', True)
    zones(spec['contacts'], 'contacts', True); zones(spec['shelter'], 'shelter', True)
    if type(spec['paths']) is not list or len(spec['paths']) > 32:
        raise ValueError('paths must be a list with at most 32 polylines')
    for path in spec['paths']:
        fields(path, ['points', 'width', 'feather'], label='path')
        if type(path['points']) is not list or not 2 <= len(path['points']) <= 128:
            raise ValueError('Path requires 2..128 distinct consecutive points')
        for p in path['points']: vec(p, 2, 'path point')
        if any(math.dist(a,b) < 1e-8 for a,b in zip(path['points'],path['points'][1:])):
            raise ValueError('Consecutive path points must differ')
        number(path['width'], 'path.width', .05, 20)
        number(path['feather'], 'path.feather', .01, 10)
    if type(spec['protected']) is not list or len(spec['protected']) > 64:
        raise ValueError('protected must contain at most 64 rectangles')
    for r in spec['protected']:
        fields(r, ['min', 'max', 'feather'], label='protected')
        a=vec(r['min'],2,'protected.min');b=vec(r['max'],2,'protected.max')
        if any(x>=y for x,y in zip(a,b)): raise ValueError('Protected min must be less than max')
        number(r['feather'],'protected.feather',.01,10)
    fields(spec['water'], ['level', 'shore_reach'], label='water')
    if spec['water']['level'] is not None: number(spec['water']['level'], 'water.level', -10000,10000)
    number(spec['water']['shore_reach'],'water.shore_reach',.05,10)
    fields(spec['pebbles'], ['density', 'radius', 'patches'], label='pebbles')
    number(spec['pebbles']['density'],'pebbles.density',0,50)
    number(spec['pebbles']['radius'],'pebbles.radius',.015,.25)
    zones(spec['pebbles']['patches'],'pebbles.patches',True)
    fields(spec['moss'], ['density','radius','body_height','contact_influence','shelter_influence','patches'],label='moss')
    number(spec['moss']['density'],'moss.density',0,50)
    number(spec['moss']['radius'],'moss.radius',.03,.4)
    number(spec['moss']['body_height'],'moss.body_height',.012,.15)
    for key in ['contact_influence','shelter_influence']:number(spec['moss'][key],'moss.'+key,0,1)
    zones(spec['moss']['patches'],'moss.patches',True)
    # A footprint-based cap rejects explosive requests before any Blender IDs exist.
    expected = sum(min(6000, math.ceil(math.pi*r['radius'][0]*r['radius'][1]*spec[k]['density']))
                   for k in ['pebbles','moss'] for r in spec[k]['patches'])
    if expected>12000: raise ValueError('Candidate budget exceeds 12000; lower density or patch area')
    return copy.deepcopy(spec)


def load_json(text):
    def reject_constant(s): raise ValueError('Non-finite JSON constant ' + s)
    def duplicate_guard(rows):
        out={}
        for key,value in rows:
            if key in out:raise ValueError('Duplicate JSON key: '+key)
            out[key]=value
        return out
    try:return json.loads(text, parse_constant=reject_constant, object_pairs_hook=duplicate_guard)
    except (TypeError,json.JSONDecodeError) as exc:raise ValueError('Invalid landscape JSON: '+str(exc)) from exc


def parse(text):return validate(load_json(text))


def clamp(v):return max(0.,min(1.,v))
def smooth(t):t=clamp(t);return t*t*(3-2*t)
def segment_distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=clamp(((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy))
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)


def path_distance(x,y,spec):
    return min((segment_distance((x,y),a,b)-path['width']/2
                for path in spec['paths'] for a,b in zip(path['points'],path['points'][1:])), default=1e6)


def clearance(x,y,spec):
    """Signed distance outside a protected/traffic footprint (negative inside)."""
    d=path_distance(x,y,spec)
    for r in spec['protected']:
        a,b=r['min'],r['max']
        dx=max(a[0]-x,0,x-b[0]);dy=max(a[1]-y,0,y-b[1])
        rd=math.hypot(dx,dy) if dx or dy else -min(x-a[0],b[0]-x,y-a[1],b[1]-y)
        d=min(d,rd)
    return d


def protection(x,y,spec):
    weight=1.
    for path in spec['paths']:
        d=min(segment_distance((x,y),a,b) for a,b in zip(path['points'],path['points'][1:]))
        weight*=smooth((d-path['width']/2)/path['feather'])
    for r in spec['protected']:
        dx=max(r['min'][0]-x,0,x-r['max'][0]);dy=max(r['min'][1]-y,0,y-r['max'][1])
        weight*=smooth(math.hypot(dx,dy)/r['feather'])
    return weight


def zone_field(x,y,rows):
    return max((r['weight']*math.exp(-2*((x-r['center'][0])/r['radius'][0])**2-2*((y-r['center'][1])/r['radius'][1])**2) for r in rows), default=0.)


def relief(x,y,z,spec):
    banks=sum(r['weight']*math.exp(-2*((x-r['center'][0])/r['radius'][0])**2-2*((y-r['center'][1])/r['radius'][1])**2) for r in spec['relief']['banks'])
    level=spec['water']['level']
    wet=1 if level is None else smooth((z-level)/(.12*spec['detail_scale']))
    return spec['relief']['height']*min(banks,1.4)*protection(x,y,spec)*wet


def default_spec(bounds=(-4,-3,4,3), seed=137):
    a,b,c,d=bounds;w=c-a;h=d-b;cx=(a+c)/2;cy=(b+d)/2
    def zone(uid,x,y,rx,ry,weight=1):return dict(id=uid,center=[x,y],radius=[rx,ry],weight=weight)
    return validate(dict(schema=SCHEMA,seed=seed,detail_scale=1.,
      relief=dict(height=.35,banks=[zone('bank-west',a+.22*w,cy,.22*w,.35*h),zone('bank-east',c-.18*w,cy+.2*h,.18*w,.25*h,.65)]),
      paths=[dict(points=[[cx,b],[cx,d]],width=1.25,feather=.45)],protected=[],
      water=dict(level=None,shore_reach=.5),
      contacts=[zone('contact-west',a+.2*w,cy,.2*w,.4*h,.75)],
      shelter=[zone('shelter-west',a+.23*w,cy,.25*w,.45*h,.8)],
      pebbles=dict(density=20.,radius=.065,patches=[zone('gravel-west',a+.25*w,cy-.15*h,.17*w,.28*h),zone('gravel-east',c-.22*w,cy+.2*h,.17*w,.2*h,.7)]),
      moss=dict(density=13.,radius=.19,body_height=.055,contact_influence=.65,shelter_influence=.7,
                patches=[zone('moss-west',a+.2*w,cy+.1*h,.19*w,.30*h,.95),zone('moss-east',c-.17*w,cy+.28*h,.13*w,.21*h,.6)])))
