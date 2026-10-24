import sys, os
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from harness import remote
G='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/growth/gallery'
blend='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/set_copy/street.blend'
print(remote.run_script(blend, KIT+'/growth/gallery_growth.py', ['{out}','1800','1100','48'], '/workspace/wk_out/growth_gallery', G))
