# What this does (plain words): writes description/sampler_model.json: the numbers sample_description.py draws from. Each number has a note saying where
# it comes from in the reference (measured by the analysis scripts in this folder). Style parts (rivet picture, shared edge profiles, wear layers) are
# copied from the fitted description so new tiles look like the same kind of steel. Run: python3 -I make_sampler_model.py
import json, os
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..')); D=PROC+'/recipes/metal/description/'
S=json.load(open(D+'S.json'))
shared=json.load(open(D+'profiles_shared.json'))
model={
 'note':'Numbers measured on the reference metal tile (1254 dots). See analysis_findings.md for how each was measured.',
 'maps':S['maps'],
 'plate':[56,57,58],                       # median colour of the bare plate panels: 56,57,58 (analysis/make_layout.py)
 'face':[59,58,58],                        # median colour of the strap faces away from rust: 57..61 (analysis/make_layout.py)
 'vertical_count_choices':[2,2,2,2,2,2,2,3],       # the reference has 2 vertical straps in one tile
 'horizontal_count_choices':[2,2,2,2,2,2,2,3],     # and 2 horizontal ones (one wraps round the tile edge)
 'vertical_half_width':[68.0,5.0],         # crease to centre: 67.5 and 68.5 dots (mean, spread)
 'horizontal_half_width_range':[48.0,84.0],# 50 and 81.5 dots
 'brace_half_width':[50.0,2.5],            # 51 and 49.5 dots
 'brace_probability':0.5,                  # 2 of the 4 panels have a diagonal brace
 'brace_down_right_share':0.85,            # both braces run from upper left to lower right
 'seam_probability':0.6,                   # seam lines in 3 of the 4 panels
 'strap_rivet_spacing':[170.0,290.0],      # gaps between rivets along a strap: 172..287 dots (88 next to a crossing)
 'brace_rivet_spacing':[190.0,260.0],      # 220 dots between the two rivets on a brace
 'shared_profiles':shared,
 'seam_profiles':{k:S['profiles'][k] for k in ('seam_lit','seam_soft')} if 'seam_lit' in S['profiles'] else {},
 'rivet':S['rivet'],
 'procedural':S['procedural'],
}
json.dump(model,open(D+'sampler_model.json','w'),separators=(',',':'))
print('sampler model bytes',os.path.getsize(D+'sampler_model.json'),'seam profiles',list(model['seam_profiles']))
