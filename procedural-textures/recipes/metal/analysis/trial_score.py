# What this does (plain words): runs both comparison tools on a wear trial folder (outputs/trial_NAME) and prints the scores and every texture measure. Use: python3 -I trial_score.py NAME ...
import sys
sys.path.insert(0,'proc-work/recipes/metal/generator')
import preview_tools as pt
for n in sys.argv[1:]:
    pixel,tex=pt.compare('proc-work/recipes/metal/outputs/trial_'+n,sheet=False)
    print(n,pt.summary_line(pixel,tex),tex['groups']); print('   ',{k:round(v,2) for k,v in tex['scores'].items()})
