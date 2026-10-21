import sys
sys.path.insert(0, '.')
from fixrun import job, run
jobs = []
S = (960, 720, 24)
jobs.append(job('close_road_wet_now', 'close_road', 'A', 'wet', size=(1920, 1440, 32), plate_height=1440))
jobs.append(job('close_road_dry_now', 'close_road', 'A', 'dry', size=(1920, 1440, 32), plate_height=1440))
for k in range(0, 13):
    jobs.append(job(f'gc_part{k:02d}_close', 'close_road', 'A', 'wet', view='layer:groundcracks', size=(960, 720, 1), plate_height=1440, dials={'groundcracks': {'show_part': k}}, jpg=True))
jobs.append(job('gc_part00_back', 'close_road', 'A', 'wet', view='layer:groundcracks', size=(960, 720, 1), plate_height=1440, dials={'groundcracks': {'show_part': 0}}, jpg=True))
for k in range(1, 9):
    jobs.append(job(f'dirt_part{k:02d}_close', 'close_road', 'A', 'wet', view='layer:dirt', size=(960, 720, 1), plate_height=1440, dials={'dirt': {'show_part': k}}, jpg=True))
jobs.append(job('dirt_part00_back', 'close_road', 'A', 'wet', view='layer:dirt', size=(960, 720, 1), plate_height=1440, dials={'dirt': {'show_part': 0}}, jpg=True))
run('street', jobs, 'diag1')
