# What this does: checks the shot plan's camera spots with simple pinhole geometry, using the film's lens
# (60.4 degrees top to bottom of a 1080 x 1920 frame, level camera), as in assemble_notice_corner.py.
import math
V = math.radians(60.4); W_PX, H_PX = 1080, 1920
tv = math.tan(V/2); th = tv*W_PX/H_PX
print("half-angle across: %.1f deg" % math.degrees(math.atan(th)))
def across(side_offset, forward):   # 0..1 across the frame, camera facing +forward, level, no yaw
    return 0.5 + 0.5*(side_offset/forward)/th
def down(height_below_eye, forward):  # 0..1 down the frame
    return 0.5 + 0.5*(height_below_eye/forward)/tv
def px_tall(size, forward): return size/(2*forward*tv)*H_PX
print("\n-- W1: camera 1 m out from the wall, looking along it to No. 1's gate --")
for d in (13.0, 11.8):
    print("gate face seen at %.1f deg to the line of sight (board foreshortened to %.0f%% of its width)" % (math.degrees(math.atan(1/d)), 100*math.sin(math.atan(1/d))))
for name, along, behind in (("No.1 chimney, 12 m behind the wall", 12, 12), ("No.1 windows, 5 m behind the wall", 12, 5), ("No.2 chimneys, 7 m further, 12 m behind", 19, 12)):
    a = math.degrees(math.atan((behind+1)/along))
    print("%s: %.0f deg off the line of sight; frame edge is at %.1f deg -> %s" % (name, a, math.degrees(math.atan(th)), "IN" if a < math.degrees(math.atan(th)) else "OUT of frame"))
print("\n-- W3: camera on the right-hand pavement, 30 m from the wall --")
for cam_x in (3.0, 3.6):
    gap = cam_x/30
    print("camera %.1f m right of the lane's middle: lines meet %.2f of the frame width right of the shared pier (No. 2's gate centre is 3.5 m right of the pier)" % (cam_x, 0.5*gap/th))
print("gate 4 m tall at 30 m: top %.2f, foot %.2f down the frame; man 1.75 m: %.0f px; board letters 0.3 m: %.0f px" % (down(1.7-4, 30), down(1.7, 30), px_tall(1.75, 30), px_tall(0.3, 30)))
# the bank on the left: house fronts at -5.15 (7 m lane + 1.65 m pavements), camera at +3.6, best case turned left to centre the pier
yaw = math.atan(3.6/30); edge = math.atan(th)+yaw
for d in (15, 19, 22):
    print("bank front %2d m ahead: left frame edge reaches x = %.1f m (fronts at -5.15) -> %s" % (d, 3.6 - d*math.tan(edge), "visible" if 3.6 - d*math.tan(edge) < -5.15 else "OUT of frame"))
print("bank window 1.2 m wide at 20 m, front seen from 8.75 m to the side: about %.0f px wide; NEW MONEY letters 0.15 m: %.0f px tall" % (8.75*1.2/400/(2*th)*W_PX, px_tall(0.15, 20)))
print("\n-- K1: eye 1.6 m, table top 0.75 m, level camera --")
for d in (1.4, 1.8, 2.6, 2.9):
    print("letter %.1f m away sits %.2f down the frame%s" % (d, down(0.85, d), "  (below the frame)" if down(0.85, d) > 1 else ""))
print("seated eye 1.2 m, letter 1.4 m away: %.2f down" % down(0.45, 1.4))
print("\n-- C1/J1: eye 1.6 m, basket on a 0.9 m belt or counter --")
for d in (1.0, 1.5, 2.4):
    print("basket %.1f m away sits %.2f down the frame" % (d, down(0.7, d)))
print("headline letters 4 cm at 2.5 m: %.0f px; 6 cm: %.0f px (plan's test: 40 px)" % (px_tall(0.04, 2.5), px_tall(0.06, 2.5)))
print("\n-- W4: man 1.75 m at 6.5 m: %.0f px tall, head about %.0f px --" % (px_tall(1.75, 6.5), px_tall(0.23, 6.5)))
print("-- W1 board letters 0.3 m at 12 m, seen face-on: %.0f px --" % px_tall(0.3, 12))
print("\n-- G2: camera near the kerb, 7 m down the street from the close, facing along the street --")
for side in (1.8, 2.5):
    print("notice on the facade %.1f m to the side at 7 m: %.2f across; facade seen at %.0f deg (foreshortened to %.0f%%)" % (side, across(side, 7), math.degrees(math.atan(side/7)), 100*math.sin(math.atan(side/7))))
print("placard letters 0.10 m in a window 15 m away: %.0f px; 5 m away: %.0f px" % (px_tall(0.10, 15), px_tall(0.10, 5)))
print("\n-- G1: works gate 4 m tall at 120 m: %.0f px; walker at 25 m: %.0f px, at 50 m: %.0f px --" % (px_tall(4, 120), px_tall(1.7, 25), px_tall(1.7, 50)))
