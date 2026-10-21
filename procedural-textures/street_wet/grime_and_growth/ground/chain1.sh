#!/bin/bash
cd proc-work/street_wet/grime_and_growth/ground
python3 -I - <<'PY'
import sys
sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
import rr
rr.plan('plan_r2', ['class','dirt:film','dirt:polish','dirt:marks','dirt:halo','dirt:drum','dirt:tar','dirt:splash','dirt:scrub','groundcracks:flag_fine','groundcracks:flag_broken','groundcracks:flag_tilt','groundcracks:flag_chip','groundcracks:kerb_chips','groundcracks:kerb_joints','groundcracks:kerb_scuffs','groundcracks:sett_disturbed','groundcracks:sett_joints','groundcracks:flag_fine_cells','groundcracks:flag_broken_cells','groundcracks:sett_joint_all','groundmoss:joint_moss','groundmoss:joint_all','groundmoss:patch_moss','groundmoss:algae','groundmoss:liverwort','groundmoss:far_band'])
PY
python3 -I proc-work/kits/weathering/ground/feature_report.py proc-work/street_wet/grime_and_growth/ground/runs/plan_r2/out proc-work/street_wet/grime_and_growth/ground/ 12
python3 -I proc-work/kits/weathering/ground/run_round.py pit_village_street kit:dirt,groundcracks,groundmoss,iron proc-work/street_wet/grime_and_growth/ground/rounds r2 --layers dirt,groundcracks,groundmoss,iron
python3 -I proc-work/street_wet/grime_and_growth/ground/pics_jobs.py pics_r2
echo CHAIN1 DONE
