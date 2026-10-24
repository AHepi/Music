# Blender's camera for Euler XYZ (90, roll, yaw): R = Rz(yaw) @ Ry(roll) @ Rx(90); camera right = R @ x, up = R @ y, looks along R @ -z.
# shot_facts.py reports roll_degrees = matrix_world.to_euler('XYZ').y = roll. check_shot.camera_axes(turn, tilt, roll) should give the same axes.
import sys, math
import numpy as np
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
import check_shot as cs
def Rx(a): c, s = math.cos(a), math.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def Ry(a): c, s = math.cos(a), math.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def Rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
yaw, roll = 6.87, 5.0
R = Rz(math.radians(yaw)) @ Ry(math.radians(roll)) @ Rx(math.radians(90))
print('blender  ahead', (R @ [0,0,-1]).round(4), 'right', (R @ [1,0,0]).round(4), 'up', (R @ [0,1,0]).round(4))
a, r, u = cs.camera_axes(yaw, 0, roll)
print('checker  ahead', a.round(4), 'right', r.round(4), 'up', u.round(4))
a, r, u = cs.camera_axes(yaw, 0, -roll)
print('checker with roll negated: right', r.round(4), 'up', u.round(4))
# where a point 4 m ahead and 1 m right lands, Blender vs checker
eye = np.array([2.96, 17.85, 3.1882]); W, H, fov = 1080, 1920, 60.4
f = (H/2)/math.tan(math.radians(fov)/2)
pt = eye + (R @ [0,0,-1]) * 4 + np.array([1.0, 0, 0])
v = pt - eye; d = v @ (R @ [0,0,-1])
blender_px = np.array([W/2 + f * (v @ (R @ [1,0,0]))/d, H/2 - f * (v @ (R @ [0,1,0]))/d])
ours, _ = cs.project((*eye, yaw, fov), pt, (W, H), 0, roll)
print('point: Blender pixel', blender_px.round(1), 'checker pixel', ours.round(1))
