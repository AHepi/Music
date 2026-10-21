#!/bin/bash
cd proc-work/street_wet/grime_and_growth/ground
python3 -I - <<'PY'
import sys
sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
import rr
rr.plan('plan_r4', ['class','dirt:tar','groundcracks:flag_fine','groundcracks:flag_broken','groundcracks:flag_tilt','groundcracks:flag_chip','groundcracks:kerb_chips','groundcracks:sett_disturbed','groundcracks:sett_joints','groundcracks:flag_fine_cells','groundcracks:flag_broken_cells','groundcracks:sett_joint_all','groundmoss:joint_moss','groundmoss:joint_all','groundmoss:algae','groundmoss:liverwort','bus:vertical_foot','bus:wall_dist','bus:keepclear','bus:footfall'])
PY
python3 -I proc-work/kits/weathering/ground/measure_period_ground.py pit_village_street proc-work/street_wet/grime_and_growth/ground/runs/plan_r4/out --out proc-work/street_wet/grime_and_growth/ground/period_r4.json
echo PLAN4 DONE
