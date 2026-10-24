# What this does: reads a finished proof scene and says how many plan cells count as standing water and how deep the hollows are (to find why no puddle was laid).
import sys, json
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import numpy as np
import bpy
from place_kit.wear import masks
from place_kit.growth import sites, scatter, puddles
plan = masks.load_plan_masks()
low = sites.grid(plan.grids, 'lowness')
wet = sites.grid(plan.grids, 'above_water') < 0.5
print('PUDDLE cells', int(wet.sum()), 'lowness max', float(low.max()), 'lowness>=0.55', int((low >= 0.55).sum()), 'cell', plan.cell)
pieces = puddles.blobs(wet)
print('blobs', len(pieces), [len(r) for r, c in pieces[:10]])
