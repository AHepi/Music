import sys, os
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from harness import remote
G='proc-work/street_wet/grime_and_growth/growth/gallery'
blend='proc-work/street_wet/set_copy/street.blend'
print(remote.run_script(blend, KIT+'/growth/gallery_growth.py', ['{out}','1800','1100','48'], '/workspace/wk_out/growth_gallery', G))
