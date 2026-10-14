"""What this does: finds where a camera would have to stand in our 3D pit village street to see it the
way the picture the user liked (log 30, Nano Banana Pro's own camera) draws it. It compares the
picture's landmarks (the winding wheels, the chimney top, the colliery gate, the left roofline and both
kerbs) with the same landmarks of our street seen from a trial camera, and moves the trial camera
until they line up as well as they can. Output: the best camera, and how far off each landmark is."""
import math
import numpy as np

W, H = 1536, 2752                         # the liked picture's size in pixels
RISE = math.tan(math.radians(4.0))        # the street climbs 4 degrees

# landmarks read off the liked picture (pixels), and the same things in our street (Blender metres)
POINTS = {
    'left wheel hub': ((878, 600), (-2.275, 86.0, 24.31)),
    'right wheel hub': ((1038, 595), (2.275, 86.0, 24.31)),
    'chimney top': ((695, 330), (-9.5, 108.0, 47.1)),
    'gate bottom left': ((795, 1290), (-2.975, 71.5, 71.5 * RISE)),
    'gate top left': ((795, 1170), (-2.975, 71.5, 71.5 * RISE + 2.93)),
}
# lines along the street: two points on each in the picture; in the street, x and the height rule
LINES = {
    'left roofline': (((100, 560), (700, 940)), (-4.3, lambda y: y * RISE + 6.44)),
    'left kerb': (((0, 1650), (800, 1295)), (-2.5, lambda y: y * RISE + 0.13)),
    'right kerb': (((1030, 1300), (890, 1700)), (2.5, lambda y: y * RISE + 0.13)),
}


def project(camera, point):
    x, y, z, yaw_degrees, fov_degrees = camera
    yaw = math.radians(yaw_degrees)
    ahead = np.array([-math.sin(yaw), math.cos(yaw), 0.0])
    right = np.array([math.cos(yaw), math.sin(yaw), 0.0])
    up = np.array([0.0, 0.0, 1.0])
    v = np.array(point) - np.array([x, y, z])
    depth = v @ ahead
    focal = (H / 2) / math.tan(math.radians(fov_degrees) / 2)
    return np.array([W / 2 + focal * (v @ right) / depth, H / 2 - focal * (v @ up) / depth]), depth


def errors(camera):
    found = {}
    for name, (seen, where) in POINTS.items():
        drawn, depth = project(camera, where)
        found[name] = np.hypot(*(drawn - np.array(seen))) if depth > 0 else 1e5
    for name, (seen, (line_x, height)) in LINES.items():
        a, depth_a = project(camera, (line_x, camera[1] + 4.0, height(camera[1] + 4.0)))
        b, depth_b = project(camera, (line_x, camera[1] + 60.0, height(camera[1] + 60.0)))
        along = (b - a) / np.linalg.norm(b - a)
        across = np.array([-along[1], along[0]])
        found[name] = math.sqrt(sum(((np.array(p) - a) @ across) ** 2 for p in seen) / 2) if min(depth_a, depth_b) > 0 else 1e5
    return found


def cost(camera):
    return sum(e * e for e in errors(camera).values())


def nelder_mead(f, start, steps, rounds=4000):
    points = [np.array(start, float)] + [np.array(start, float) + np.eye(len(start))[i] * steps[i] for i in range(len(start))]
    values = [f(p) for p in points]
    for _ in range(rounds):
        order = np.argsort(values)
        points, values = [points[i] for i in order], [values[i] for i in order]
        centre = np.mean(points[:-1], axis=0)
        reflected = centre + (centre - points[-1]); fr = f(reflected)
        if fr < values[0]:
            expanded = centre + 2 * (centre - points[-1]); fe = f(expanded)
            points[-1], values[-1] = (expanded, fe) if fe < fr else (reflected, fr)
        elif fr < values[-2]:
            points[-1], values[-1] = reflected, fr
        else:
            contracted = centre + 0.5 * (points[-1] - centre); fc = f(contracted)
            if fc < values[-1]:
                points[-1], values[-1] = contracted, fc
            else:
                points = [points[0] + 0.5 * (p - points[0]) for p in points]
                values = [f(p) for p in points]
    best = int(np.argmin(values))
    return points[best], values[best]


if __name__ == '__main__':
    current = (3.25, 16.6, 3.52, 5.9, 60.0)
    print('our test camera  x, y, height, turn, lens:', current)
    for name, e in errors(current).items():
        print(f'   {name:18s} off by {e:6.0f} px')
    results = []
    for start_y in (4.0, 10.0, 16.0, 22.0):
        for start_fov in (45.0, 60.0, 75.0):
            best, value = nelder_mead(cost, (3.0, start_y, start_y * RISE + 2.0, 6.0, start_fov), (0.5, 3.0, 0.5, 2.0, 5.0))
            results.append((value, tuple(round(float(v), 3) for v in best)))
    results.sort()
    for value, camera in results[:4]:
        print('matched camera   x, y, height, turn, lens:', camera, ' total error', round(value ** 0.5), 'px')
    best = results[0][1]
    for name, e in errors(best).items():
        print(f'   {name:18s} off by {e:6.0f} px')
    x, y, z, yaw, fov = best
    print('eye above the pavement under the camera:', round(z - (y * RISE + 0.13), 2), 'm')
