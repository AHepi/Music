"""What this does: the camera sums every other calculator rests on, done once and tested, so nobody has to rewrite them
in scratch files again (helpers re-derived them at least five times in logs 30-34). Without rendering anything it says:
where a 3D point lands on the film frame (or on the plate), how big a thing comes out in pixels, how many metres one
pixel covers, where the street's straight lines meet, how far away a camera may stand for a thing to reach a given
height on the frame ("down"), how high the eye must be, how far a turn or a sideways slide moves things on screen, how
much a near thing slides against what is behind it, and how much a slide magnifies the painting at the nearest painted
surface (which must stay under what the painting's own sharpness allows).

Places are Blender metres: x across, y forward (up the street), z up; three.js is (x, z, -y). On the frame, "across"
runs 0 (left edge) to 1 (right edge) and "down" 0 (top) to 1 (bottom); pixels count from the top-left corner.
Turn is + to the left of straight up +y (as shot_facts.py and Blender's Z rotation); tilt is + looking up.
The same sums for page files (three.js): kit/paper-film/scenes/frame-geometry.js (tests/test_frame_geometry_parity.py
proves the two give the same numbers).

Use (each command prints plain lines; --json prints JSON; --out FILE writes it; every command names the
film-settings.json values it used):
  python3 frame_geometry.py project --camera works-camera-w1.json --lens film NAME=x,y,z ...
        where points land (a camera file: a projector JSON such as works-camera-w1.json, a shot_facts facts.json, or a
        place facts file with --view and --spot; or give --at x,y,z --turn DEG [--tilt DEG] [--fov DEG] instead)
  python3 frame_geometry.py boxes --camera FILE --must-read notice NAME=cx,cy,cz,w,d,h ...   whole things (8 corners):
        inside the frame? clear of the phone buttons? (the safe-area numbers in film-settings.json; frame_check.py's
        one point and 140/380 px margins are older)
  python3 frame_geometry.py meeting-point --turn 6.87 --slope 0.069927      where a straight street's lines meet
        (or --camera FILE --direction 0,1,0.069927 for any camera)
  python3 frame_geometry.py size --depth 6 --metres 0.23        a 0.23 m head at 6 m, in pixels (or --pixels 25: metres needed)
  python3 frame_geometry.py reach --eye 1.7 --down 0.70 [--meeting-down 0.5] [--depth 7.42]
        the deepest a thing's front foot may stand to reach 0.70 down (and where a foot at --depth lands)
  python3 frame_geometry.py eye --depth 24.2 --down 0.70 --surface-height 0.14   the camera height needed
  python3 frame_geometry.py turn --across 0.684        the turn that puts the meeting point there; what one degree moves
  python3 frame_geometry.py slide --start-camera A --end-camera B NAME=x,y,z ...  magnification of each named painted
        thing, the limit from the painting's returned height, and the longest slide (or --place-facts F --view V)
  python3 frame_geometry.py parallax --slide 0.14 --near 3.3 --behind 4.9 [--forward --offset-pixels 300]
  python3 frame_geometry.py allowance            how far the film camera may turn, tilt or step sideways inside the plate
Run any command with --help for its options.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings, MissingSetting  # noqa: E402
from calculator_output import add_output_options, finish  # noqa: E402


# ------------------------------------------------------------------------------------------------ small vector sums
def add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def subtract(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def scale(a, k):
    return [a[0] * k, a[1] * k, a[2] * k]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def length(a):
    return math.sqrt(dot(a, a))


def normalise(a):
    n = length(a)
    if n == 0:
        raise ValueError('a direction of length 0 has no direction')
    return [a[0] / n, a[1] / n, a[2] / n]


def to_three(point):
    """Blender (x, y, z) -> three.js (x, z, -y)."""
    return [point[0], point[2], -point[1]]


def from_three(point):
    """three.js (x, y, z) -> Blender (x, -z, y)."""
    return [point[0], -point[2], point[1]]


# ------------------------------------------------------------------------------------------------ lenses
def focal_length_pixels(vertical_fov_degrees, frame_height):
    """f = (H / 2) / tan(V / 2): 1649.4 px for the film lens (60.4 degrees on 1920 rows), 2168 px for the plate."""
    return (frame_height / 2) / math.tan(math.radians(vertical_fov_degrees) / 2)


def horizontal_fov_degrees(vertical_fov_degrees, frame_width, frame_height):
    return math.degrees(2 * math.atan(math.tan(math.radians(vertical_fov_degrees) / 2) * frame_width / frame_height))


# ------------------------------------------------------------------------------------------------ cameras
def make_camera(position, forward, up, vertical_fov_degrees, frame_width, frame_height, name=''):
    """A camera as a plain dict: where it stands, its three axes (Blender world), its lens and frame."""
    forward = normalise(forward)
    right = normalise(cross(forward, up))
    true_up = cross(right, forward)
    return {'name': name, 'position': [float(v) for v in position], 'forward': forward, 'right': right, 'up': true_up,
            'vertical_fov_degrees': float(vertical_fov_degrees), 'frame': [int(frame_width), int(frame_height)],
            'focal': focal_length_pixels(vertical_fov_degrees, frame_height)}


def blender_euler_matrix(x_degrees, y_degrees, z_degrees):
    """Blender's XYZ Euler rotation as rows of a 3 x 3 matrix: R = Rz @ Ry @ Rx."""
    cx, sx = math.cos(math.radians(x_degrees)), math.sin(math.radians(x_degrees))
    cy, sy = math.cos(math.radians(y_degrees)), math.sin(math.radians(y_degrees))
    cz, sz = math.cos(math.radians(z_degrees)), math.sin(math.radians(z_degrees))
    rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return multiply(rz, multiply(ry, rx))


def multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def apply(matrix, v):
    return [sum(matrix[i][k] * v[k] for k in range(3)) for i in range(3)]


def camera_from_turn(position, turn_degrees=0.0, tilt_degrees=0.0, roll_degrees=0.0, vertical_fov_degrees=60.4,
                     frame_width=1080, frame_height=1920, name=''):
    """The way the project's scripts set a camera: Blender rotation (90 + tilt, roll, turn) in XYZ order
    (assemble_people_test.py, shot_facts.py --yaw). A level camera turned 0 looks straight up +y."""
    matrix = blender_euler_matrix(90.0 + tilt_degrees, roll_degrees, turn_degrees)
    return make_camera(position, apply(matrix, [0, 0, -1]), apply(matrix, [0, 1, 0]), vertical_fov_degrees, frame_width, frame_height, name)


def camera_looking_at(position, target, vertical_fov_degrees=60.4, frame_width=1080, frame_height=1920, name=''):
    """A camera aimed at a point, kept level (no lean), as frame_check.py and kit.stillShot aim."""
    return make_camera(position, subtract(target, position), [0, 0, 1], vertical_fov_degrees, frame_width, frame_height, name)


def quaternion_matrix(w, x, y, z):
    n = math.sqrt(w * w + x * x + y * y + z * z)
    w, x, y, z = w / n, x / n, y / n, z / n
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def camera_from_blender_quaternion(position, quaternion_wxyz, vertical_fov_degrees, frame_width=1080, frame_height=1920, name=''):
    """A camera from a Blender location and rotation_quaternion (w, x, y, z), as the camera files store it."""
    matrix = quaternion_matrix(*quaternion_wxyz)
    return make_camera(position, apply(matrix, [0, 0, -1]), apply(matrix, [0, 1, 0]), vertical_fov_degrees, frame_width, frame_height, name)


def camera_from_three(position_three, quaternion_xyzw_three, vertical_fov_degrees, frame_width=1080, frame_height=1920, name=''):
    """A three.js camera (position, quaternion x, y, z, w, vertical fov) turned into Blender space."""
    x, y, z, w = quaternion_xyzw_three
    matrix = quaternion_matrix(w, x, y, z)
    forward, up = from_three(apply(matrix, [0, 0, -1])), from_three(apply(matrix, [0, 1, 0]))
    return make_camera(from_three(position_three), forward, up, vertical_fov_degrees, frame_width, frame_height, name)


def camera_angles(camera):
    """Turn (+ left of +y), tilt (+ up) and roll (lean) in degrees, as shot_facts.py reports them."""
    f, r = camera['forward'], camera['right']
    return {'turn_degrees': math.degrees(math.atan2(-f[0], f[1])),
            'tilt_degrees': math.degrees(math.asin(max(-1.0, min(1.0, f[2])))),
            'roll_degrees': math.degrees(math.asin(max(-1.0, min(1.0, -r[2]))))}


def with_lens(camera, vertical_fov_degrees, frame_width=None, frame_height=None):
    """The same camera with another lens (film or plate) or frame."""
    width, height = frame_width or camera['frame'][0], frame_height or camera['frame'][1]
    return make_camera(camera['position'], camera['forward'], camera['up'], vertical_fov_degrees, width, height, camera.get('name', ''))


def moved_to(camera, position):
    """The same camera (same turn and lens) standing somewhere else: a slide never turns."""
    return make_camera(position, camera['forward'], camera['up'], camera['vertical_fov_degrees'], camera['frame'][0], camera['frame'][1],
                       camera.get('name', ''))


# ------------------------------------------------------------------------------------------------ projection
def project_point(camera, point):
    """Where a point lands: across and down (shares of the frame), pixels, and its depth along the view (metres).
    A point behind the camera (depth <= 0) is reported with in_front False."""
    d = subtract(point, camera['position'])
    depth = dot(d, camera['forward'])
    width, height = camera['frame']
    f = camera['focal']
    if abs(depth) < 1e-12:
        return {'across': None, 'down': None, 'x_pixels': None, 'y_pixels': None, 'depth': depth, 'in_front': False}
    across = 0.5 + f * dot(d, camera['right']) / (depth * width)
    down = 0.5 - f * dot(d, camera['up']) / (depth * height)
    return {'across': across, 'down': down, 'x_pixels': across * width, 'y_pixels': down * height, 'depth': depth, 'in_front': depth > 0}


def project_direction(camera, direction):
    """Where lines running along a direction meet on the frame (their vanishing point); None if they meet behind."""
    if dot(direction, camera['forward']) <= 0:
        return None
    width, height = camera['frame']
    f = camera['focal']
    depth = dot(direction, camera['forward'])
    return {'across': 0.5 + f * dot(direction, camera['right']) / (depth * width),
            'down': 0.5 - f * dot(direction, camera['up']) / (depth * height)}


def box_corners(low, high):
    """The 8 corners of an upright box from its lowest and highest corners."""
    return [[x, y, z] for x in (low[0], high[0]) for y in (low[1], high[1]) for z in (low[2], high[2])]


def box_from_centre(centre, size):
    """(low, high) of an upright box from its centre and [width x, depth y, height z]."""
    half = [s / 2 for s in size]
    return subtract(centre, half), add(centre, half)


def project_box(camera, points):
    """The frame box [left, top, right, bottom] (shares) of a set of points (for example a box's 8 corners), its nearest
    depth, and whether all of it is in front of the camera."""
    landed = [project_point(camera, p) for p in points]
    front = [p for p in landed if p['in_front']]
    if not front:
        return {'box': None, 'nearest_depth': None, 'all_in_front': False}
    return {'box': [min(p['across'] for p in front), min(p['down'] for p in front), max(p['across'] for p in front), max(p['down'] for p in front)],
            'nearest_depth': min(p['depth'] for p in front), 'all_in_front': len(front) == len(landed)}


def in_frame(landed, margin=0.0):
    return bool(landed['in_front'] and margin <= landed['across'] <= 1 - margin and margin <= landed['down'] <= 1 - margin)


# ------------------------------------------------------------------------------------------------ sizes
def metres_per_pixel(camera, depth):
    return depth / camera['focal']


def size_in_pixels(camera, size_metres, depth):
    """On-screen size of something size_metres across or tall, square to the view, at depth: size x f / depth."""
    return size_metres * camera['focal'] / depth


def size_needed(camera, pixels, depth):
    """How big (metres) a thing must be at depth to come out `pixels` tall."""
    return pixels * depth / camera['focal']


def distance_for_size(camera, size_metres, pixels):
    """The depth at which something size_metres tall comes out `pixels` tall."""
    return size_metres * camera['focal'] / pixels


def frame_share(camera, area_square_metres, depth):
    """Share of the frame covered by a flat area square to the view: area x (f/d)^2 / (W x H)."""
    width, height = camera['frame']
    return area_square_metres * (camera['focal'] / depth) ** 2 / (width * height)


def distance_for_width_share(camera, width_metres, share):
    """The depth at which something width_metres wide fills `share` of the frame's width."""
    return width_metres * camera['focal'] / (share * camera['frame'][0])


# ------------------------------------------------------------------------------------------------ closed forms for planning
def meeting_point_level(turn_degrees, slope, vertical_fov_degrees, frame_width, frame_height):
    """Where a straight street (direction (0, 1, slope)) meets for a level camera turned `turn_degrees` left:
    across = 0.5 + f tan(turn) / W, down = 0.5 - f slope / (H cos(turn))."""
    f = focal_length_pixels(vertical_fov_degrees, frame_height)
    psi = math.radians(turn_degrees)
    return {'across': 0.5 + f * math.tan(psi) / frame_width, 'down': 0.5 - f * slope / (frame_height * math.cos(psi))}


def turn_for_meeting_point(across, vertical_fov_degrees, frame_width, frame_height):
    """The turn (degrees, + left) that puts the street's meeting point at `across`: atan((u - 0.5) W / f)."""
    f = focal_length_pixels(vertical_fov_degrees, frame_height)
    return math.degrees(math.atan((across - 0.5) * frame_width / f))


def turn_moves_per_degree(vertical_fov_degrees, frame_width, frame_height):
    """Share of the width one degree of turn moves things near the middle: f (pi / 180) / W (0.0267 for the film)."""
    return focal_length_pixels(vertical_fov_degrees, frame_height) * math.pi / 180 / frame_width


def ground_point_down(depth, eye_above_surface, meeting_down, vertical_fov_degrees, frame_height):
    """Where a point on a surface (ground, counter) at `depth` lands for a level camera: down = v_meet + f eye / (d H),
    eye = the camera's height above that surface, v_meet = where the surface's lines meet (0.5 on a level surface)."""
    f = focal_length_pixels(vertical_fov_degrees, frame_height)
    return meeting_down + f * eye_above_surface / (depth * frame_height)


def reach_distance(reach_down, eye_above_surface, meeting_down, vertical_fov_degrees, frame_height):
    """The deepest a thing's front foot may stand on a surface to reach `reach_down` on the frame:
    d_max = f eye / ((r - v_meet) H). None when the surface never comes that low (r at or above v_meet)."""
    if reach_down <= meeting_down:
        return None
    f = focal_length_pixels(vertical_fov_degrees, frame_height)
    return f * eye_above_surface / ((reach_down - meeting_down) * frame_height)


def eye_needed(depth, reach_down, meeting_down, surface_height, vertical_fov_degrees, frame_height):
    """The camera height (z) at which a point on a surface at `depth` lands at `reach_down`:
    eye = surface + (r - v_meet) H d / f (for an overview from a window, raise the eye; never tilt)."""
    f = focal_length_pixels(vertical_fov_degrees, frame_height)
    return surface_height + (reach_down - meeting_down) * frame_height * depth / f


def slide_for_screen_shift(shift_share_of_width, depth, vertical_fov_degrees, frame_width, frame_height):
    """How far to slide sideways (metres) to move a thing at `depth` by `shift_share_of_width` on screen; the meeting
    point stays put (a turn would move everything together instead)."""
    f = focal_length_pixels(vertical_fov_degrees, frame_height)
    return shift_share_of_width * frame_width * depth / f


def parallax_sideways_pixels(slide_metres, near_depth, behind_depth, vertical_fov_degrees, frame_height):
    """How many pixels a near thing slides against the surface behind it when the camera steps sideways:
    f s |1/d - 1/d_behind|."""
    f = focal_length_pixels(vertical_fov_degrees, frame_height)
    return f * slide_metres * abs(1 / near_depth - 1 / behind_depth)


def parallax_forward_pixels(offset_pixels_from_centre, slide_metres, near_depth, behind_depth):
    """How many pixels a near thing slides against what is behind it (lined up at first) when the camera moves
    forward by slide_metres: p L (d_behind - d) / ((d - L)(d_behind - L)), p its pixels from the frame's centre."""
    return offset_pixels_from_centre * slide_metres * (behind_depth - near_depth) / ((near_depth - slide_metres) * (behind_depth - slide_metres))


def slide_limit(painting_height_pixels, film_height_pixels, film_vertical_fov_degrees, plate_vertical_fov_degrees):
    """How many times nearer a painted surface may come before the painting runs out of detail: the painting's rows per
    film row at the plate's spot, (painting H / film H) x tan(film V / 2) / tan(plate V / 2). With the painting Flux
    returns (2672 rows) this is 1.29; with the plate's 2730 rows it would be 1.314 (the skeptic's correction, log 35)."""
    return (painting_height_pixels / film_height_pixels) * math.tan(math.radians(film_vertical_fov_degrees) / 2) / \
        math.tan(math.radians(plate_vertical_fov_degrees) / 2)


def slide_magnifications(start_camera, end_camera, named_points):
    """For each named painted point: its depth from the slide's start and end cameras and how many times nearer it
    comes (start depth / end depth). The nearest painted surface magnifies most."""
    found = []
    for name, point in named_points:
        start = project_point(start_camera, point)['depth']
        end = project_point(end_camera, point)['depth']
        found.append({'name': name, 'point': point, 'depth_start': start, 'depth_end': end,
                      'magnification': start / end if end > 0 and start > 0 else None})
    return found


def longest_slide(nearest_depth_at_end, limit):
    """The longest straight push (metres) for the nearest painted surface at the end: d_end x (limit - 1)."""
    return nearest_depth_at_end * (limit - 1)


def turn_allowance_degrees(film_vertical_fov_degrees, plate_vertical_fov_degrees, frame_width, frame_height):
    """How far the film camera may turn sideways or tilt (each way) and stay inside the plate's view."""
    sideways = (horizontal_fov_degrees(plate_vertical_fov_degrees, frame_width, frame_height) -
                horizontal_fov_degrees(film_vertical_fov_degrees, frame_width, frame_height)) / 2
    return {'turn_each_way_degrees': sideways, 'tilt_each_way_degrees': (plate_vertical_fov_degrees - film_vertical_fov_degrees) / 2}


def sideways_allowance_metres(nearest_depth, film_vertical_fov_degrees, plate_vertical_fov_degrees, frame_width, frame_height):
    """How far the film camera may step sideways before the frame's edge leaves the plate at the nearest surface."""
    aspect = frame_width / frame_height
    tan_plate = math.tan(math.radians(plate_vertical_fov_degrees) / 2) * aspect
    tan_film = math.tan(math.radians(film_vertical_fov_degrees) / 2) * aspect
    return nearest_depth * (tan_plate - tan_film)


# ------------------------------------------------------------------------------------------------ reading camera files
class frame_and_lenses:
    """The frame size and lenses from film-settings.json, read only when asked for (so a report lists only what it used)."""
    KEYS = {'width': 'frame.width_pixels', 'height': 'frame.height_pixels', 'film_fov': 'frame.film_vertical_fov_degrees',
            'plate_fov': 'frame.plate_vertical_fov_degrees'}

    def __init__(self, settings):
        self.settings = settings

    def __getitem__(self, name):
        return self.settings.value(self.KEYS[name])


def load_camera(path, settings, lens='film', view=None, spot=None):
    """Reads a camera from a file. Understands: a projector JSON (works-camera-w1.json, notice-corner-camera.json:
    the plate camera; lens 'film' keeps its place and turn with the film lens), a shot_facts facts.json, and a place
    facts file (with view and spot 'composed' or 'plate'). lens: 'film', 'plate' or a number of degrees."""
    with open(path) as handle:
        data = json.load(handle)
    frame = frame_and_lenses(settings)
    fov = frame['film_fov'] if lens == 'film' else frame['plate_fov'] if lens == 'plate' else float(lens)
    if 'blender' in data and 'rotation_quaternion_wxyz' in data['blender']:
        camera = camera_from_blender_quaternion(data['blender']['location'], data['blender']['rotation_quaternion_wxyz'], fov,
                                                frame['width'], frame['height'], os.path.basename(path))
    elif 'camera' in data and 'at' in data['camera']:
        cam = data['camera']
        width, height = data.get('size', [frame['width'], frame['height']])
        fov = cam['vertical_fov_degrees'] if lens == 'film' and 'vertical_fov_degrees' in cam else fov
        camera = camera_from_turn(cam['at'], cam.get('turn_degrees', 0), cam.get('tilt_degrees', 0), cam.get('roll_degrees', 0), fov,
                                  width, height, os.path.basename(path))
    elif 'views' in data and 'place' in data:
        camera = camera_from_place_facts(data, settings, view, spot or ('composed' if lens == 'film' else 'plate'), lens)
    else:
        raise SystemExit(f'frame_geometry: {path} is not a camera file this tool knows (a projector JSON with "blender", '
                         f'a shot_facts facts.json with "camera", or a place facts file with "views")')
    return camera


def camera_from_place_facts(facts, settings, view=None, spot='composed', lens=None):
    """The camera of one view of a place facts file, at its composed or plate spot."""
    views = {v['name']: v for v in facts['views']}
    if view is None:
        if len(views) != 1:
            raise SystemExit(f'frame_geometry: say which view (--view): {", ".join(views)}')
        view = next(iter(views))
    if view not in views:
        raise SystemExit(f'frame_geometry: no view "{view}" in the place facts (views: {", ".join(views)})')
    v = views[view]
    camera = v['camera']
    place = camera.get(spot) or camera.get('composed') or camera.get('plate')
    if place is None:
        raise SystemExit(f'frame_geometry: view "{view}" has no {spot} spot')
    frame = frame_and_lenses(settings)
    width, height = facts.get('frame', {}).get('width', frame['width']), facts.get('frame', {}).get('height', frame['height'])
    if lens in (None, 'film', 'plate'):
        which = lens or ('film' if spot == 'composed' else 'plate')
        fov = camera.get(f'{which}_vertical_fov_degrees') or frame[f'{which}_fov']
    else:
        fov = float(lens)
    return camera_from_turn(place, camera.get('turn_degrees', 0.0), camera.get('tilt_degrees', 0.0), camera.get('roll_degrees', 0.0), fov,
                            width, height, f'{facts.get("place", "")} {view} {spot}')


def camera_from_options(args, settings):
    """A camera from --camera FILE (with --lens, --view, --spot) or from --at x,y,z --turn D [--tilt D] [--fov D]."""
    frame = frame_and_lenses(settings)
    if getattr(args, 'camera', None):
        return load_camera(args.camera, settings, args.lens, getattr(args, 'view', None), getattr(args, 'spot', None))
    if getattr(args, 'at', None):
        fov = args.fov if args.fov is not None else frame['film_fov']
        return camera_from_turn(parse_point(args.at), args.turn or 0.0, args.tilt or 0.0, 0.0, fov, frame['width'], frame['height'], 'given')
    raise SystemExit('frame_geometry: give a camera: --camera FILE, or --at x,y,z --turn DEGREES [--tilt DEGREES] [--fov DEGREES]')


def parse_point(text):
    values = [float(v) for v in text.split(',')]
    if len(values) != 3:
        raise SystemExit(f'frame_geometry: "{text}" is not a point x,y,z')
    return values


def parse_named_points(items):
    named = []
    for k, item in enumerate(items or []):
        name, _, value = item.rpartition('=')
        named.append((name or f'point {k + 1}', parse_point(value)))
    return named


# ------------------------------------------------------------------------------------------------ command line
def round_all(value, digits=4):
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, list):
        return [round_all(v, digits) for v in value]
    if isinstance(value, dict):
        return {k: round_all(v, digits) for k, v in value.items()}
    return value


def describe_camera(camera):
    angles = camera_angles(camera)
    p = camera['position']
    return (f'Camera {camera.get("name") or ""} at Blender ({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f}), turned {angles["turn_degrees"]:.2f} degrees '
            f'(+ left), tilted {angles["tilt_degrees"]:.2f}, lens {camera["vertical_fov_degrees"]:.1f} degrees top to bottom on '
            f'{camera["frame"][0]} x {camera["frame"][1]} (focal length {camera["focal"]:.1f} px).')


def command_project(args, settings):
    camera = camera_from_options(args, settings)
    lines, rows = [describe_camera(camera)], []
    for name, point in parse_named_points(args.points):
        landed = project_point(camera, point)
        row = {'name': name, 'point': point, **landed}
        if landed['in_front']:
            row['metres_per_pixel'] = metres_per_pixel(camera, landed['depth'])
            row['in_frame'] = in_frame(landed)
            lines.append(f'{name}: {landed["across"]:.3f} across, {landed["down"]:.3f} down ({landed["x_pixels"]:.0f}, {landed["y_pixels"]:.0f} px), '
                         f'{landed["depth"]:.2f} m away, {row["metres_per_pixel"] * 1000:.2f} mm a pixel, '
                         f'{"inside the frame" if row["in_frame"] else "OUTSIDE the frame"}')
        else:
            lines.append(f'{name}: behind the camera (depth {landed["depth"]:.2f} m)')
        rows.append(row)
    if args.size:
        size = float(args.size)
        for row in rows:
            if row['in_front']:
                row['size_pixels'] = size_in_pixels(camera, size, row['depth'])
                lines.append(f'  {row["name"]}: {size} m comes out {row["size_pixels"]:.1f} px')
    return {'camera': round_all(camera), 'points': round_all(rows)}, lines


def command_meeting_point(args, settings):
    frame = frame_and_lenses(settings)
    if args.camera or args.at:
        camera = camera_from_options(args, settings)
        direction = parse_point(args.direction or '0,1,0')
        met = project_direction(camera, direction)
        lines = [describe_camera(camera)]
        lines.append(f'Lines along {direction} meet at {met["across"]:.4f} across, {met["down"]:.4f} down.' if met else
                     f'Lines along {direction} meet behind the camera.')
        return {'camera': round_all(camera), 'direction': direction, 'meeting_point': round_all(met)}, lines
    fov = args.fov if args.fov is not None else frame['film_fov']
    met = meeting_point_level(args.turn or 0.0, args.slope or 0.0, fov, frame['width'], frame['height'])
    lines = [f'A level camera turned {args.turn or 0.0} degrees left, lens {fov} degrees, street rising {args.slope or 0.0} m a metre: '
             f'its lines meet at {met["across"]:.4f} across, {met["down"]:.4f} down.']
    return {'turn_degrees': args.turn or 0.0, 'slope': args.slope or 0.0, 'vertical_fov_degrees': fov, 'meeting_point': round_all(met)}, lines


def lens_camera(args, settings):
    frame = frame_and_lenses(settings)
    fov = args.fov if getattr(args, 'fov', None) is not None else frame['film_fov']
    return camera_from_turn([0, 0, 0], 0, 0, 0, fov, frame['width'], frame['height'], 'lens only')


def command_size(args, settings):
    camera = lens_camera(args, settings)
    if args.depth is None:
        raise SystemExit('frame_geometry size: give --depth (metres)')
    result = {'depth': args.depth, 'vertical_fov_degrees': camera['vertical_fov_degrees'], 'metres_per_pixel': metres_per_pixel(camera, args.depth)}
    lines = [f'At {args.depth} m with a {camera["vertical_fov_degrees"]} degree lens one pixel covers {result["metres_per_pixel"] * 1000:.2f} mm.']
    if args.metres is not None:
        result['pixels'] = size_in_pixels(camera, args.metres, args.depth)
        lines.append(f'{args.metres} m comes out {result["pixels"]:.1f} px ({result["pixels"] / camera["frame"][1]:.3f} of the height).')
    if args.pixels is not None:
        result['metres_needed'] = size_needed(camera, args.pixels, args.depth)
        lines.append(f'To come out {args.pixels} px it must be {result["metres_needed"]:.4f} m.')
    return round_all(result), lines


def meeting_down_from(args, settings):
    if args.meeting_down is not None:
        return args.meeting_down
    if getattr(args, 'camera', None) or getattr(args, 'at', None):
        met = project_direction(camera_from_options(args, settings), parse_point(args.direction or '0,1,0'))
        return met['down']
    return 0.5


def command_reach(args, settings):
    frame = frame_and_lenses(settings)
    fov = args.fov if args.fov is not None else frame['film_fov']
    meeting_down = meeting_down_from(args, settings)
    target = args.down if args.down is not None else settings.value('shot_kind_profiles.still_life.rules.rule7_story_reaches_down')
    d_max = reach_distance(target, args.eye, meeting_down, fov, frame['height'])
    result = {'eye_above_surface': args.eye, 'meeting_down': meeting_down, 'reach_down': target, 'deepest_metres': d_max}
    lines = [f'Eye {args.eye} m above the surface, lines meeting {meeting_down:.4f} down, lens {fov} degrees:',
             (f'a thing\'s front foot must stand within {d_max:.2f} m (depth along the view) to reach {target} down.' if d_max else
              f'nothing on that surface can reach {target} down (the surface\'s lines meet lower).')]
    for depth in args.depth or []:
        down = ground_point_down(depth, args.eye, meeting_down, fov, frame['height'])
        result.setdefault('feet', []).append({'depth': depth, 'down': down})
        lines.append(f'A foot {depth} m away lands {down:.3f} down.')
    return round_all(result), lines


def command_eye(args, settings):
    frame = frame_and_lenses(settings)
    fov = args.fov if args.fov is not None else frame['film_fov']
    target = args.down if args.down is not None else settings.value('shot_kind_profiles.still_life.rules.rule7_story_reaches_down')
    height = eye_needed(args.depth, target, args.meeting_down, args.surface_height, fov, frame['height'])
    lines = [f'For a thing on a surface at height {args.surface_height} m, {args.depth} m away, to land {target} down (lines meeting '
             f'{args.meeting_down} down), the camera must stand {height:.2f} m high ({height - args.surface_height:.2f} m above that surface).']
    return round_all({'depth': args.depth, 'reach_down': target, 'surface_height': args.surface_height, 'camera_height': height}), lines


def command_turn(args, settings):
    frame = frame_and_lenses(settings)
    fov = args.fov if args.fov is not None else frame['film_fov']
    per_degree = turn_moves_per_degree(fov, frame['width'], frame['height'])
    result = {'vertical_fov_degrees': fov, 'share_of_width_per_degree': per_degree}
    lines = [f'One degree of turn moves things near the middle {per_degree:.4f} of the frame\'s width ({per_degree * frame["width"]:.1f} px).']
    if args.across is not None:
        result['turn_degrees'] = turn_for_meeting_point(args.across, fov, frame['width'], frame['height'])
        lines.append(f'To put the street\'s meeting point {args.across} across, turn {result["turn_degrees"]:.2f} degrees '
                     f'({"left" if result["turn_degrees"] >= 0 else "right"}). Then close any gap to the subject by sliding, never by turning.')
    if args.shift is not None and args.depth is not None:
        result['slide_metres'] = slide_for_screen_shift(args.shift, args.depth, fov, frame['width'], frame['height'])
        lines.append(f'To move a thing {args.depth} m away by {args.shift} of the width, slide {result["slide_metres"]:.3f} m sideways '
                     f'(the meeting point stays where it is).')
    return round_all(result), lines


def command_slide(args, settings):
    frame = frame_and_lenses(settings)
    painting_height = args.painting_height
    points = parse_named_points(args.points)
    if args.place_facts:
        with open(args.place_facts) as handle:
            facts = json.load(handle)
        view = next((v for v in facts['views'] if v['name'] == args.view), None) if args.view else (facts['views'][0] if len(facts['views']) == 1 else None)
        if view is None:
            raise SystemExit(f'frame_geometry slide: say which view (--view): {", ".join(v["name"] for v in facts["views"])}')
        slide = view.get('slide')
        if not slide:
            raise SystemExit(f'frame_geometry slide: view {view["name"]} has no slide')
        cam = view['camera']
        end = camera_from_turn(slide['end'], cam.get('turn_degrees', 0), cam.get('tilt_degrees', 0), 0, frame['film_fov'], frame['width'], frame['height'], 'end')
        start = moved_to(end, slide['start'])
        painting = facts.get('painting') or {}
        if not painting_height and painting.get('returned_size'):
            painting_height = painting['returned_size'][1]
        if not points:
            points = [(p.get('name'), p['point']) for p in view.get('painted_points', [])]
    else:
        if not (args.start_camera and args.end_camera):
            raise SystemExit('frame_geometry slide: give --start-camera and --end-camera, or --place-facts with --view')
        end = load_camera(args.end_camera, settings, 'film')
        start = moved_to(end, load_camera(args.start_camera, settings, 'film')['position'])
    if not points:
        raise SystemExit('frame_geometry slide: name the painted things to judge: NAME=x,y,z ... (the nearest painted surface decides)')
    painting_height = painting_height or settings.value('frame.painting_returned_size_pixels')[1]   # the table only when nothing else says
    limit = slide_limit(painting_height, frame['height'], frame['film_fov'], frame['plate_fov'])
    borderline = settings.value('camera.slide_magnification_borderline_share')
    found = slide_magnifications(start, end, points)
    ground = [f for f in found if '(derived)' in f['name'] or 'ground at' in f['name']]
    judged = [f for f in found if f not in ground or args.count_ground] or found
    nearest = min((f for f in judged if f['depth_end'] > 0), key=lambda f: f['depth_end'])
    worst = max((f for f in judged if f['magnification']), key=lambda f: f['magnification'])
    over = worst['magnification'] / limit - 1
    verdict = 'pass' if over <= 0 else ('on the limit: judge it' if over <= borderline else 'too far: the painting will look soft')
    slide_length = length(subtract(end['position'], start['position']))
    lines = [f'Slide {slide_length:.2f} m. Limit: {limit:.3f} times nearer (painting {painting_height} rows over the plate\'s '
             f'{frame["plate_fov"]} degrees, film {frame["height"]} rows at {frame["film_fov"]} degrees).']
    for f in sorted(found, key=lambda f: f['depth_end']):
        counted = '' if f in judged else '  (not counted: see below)'
        lines.append(f'  {f["name"]}: {f["depth_start"]:.2f} m -> {f["depth_end"]:.2f} m, {f["magnification"]:.3f} times nearer{counted}')
    lines.append(f'Worst: {worst["name"]} {worst["magnification"]:.3f} against {limit:.3f}: {verdict}'
                 + (f' ({over * 100:.1f}% over).' if over > 0 else '.'))
    lines.append(f'Longest slide for the nearest painted thing ({nearest["name"]}, {nearest["depth_end"]:.2f} m at the end): '
                 f'{longest_slide(nearest["depth_end"], limit):.2f} m.')
    if ground and not args.count_ground:
        lines.append('The painted ground at the frame\'s bottom edge comes nearer still, but is not counted: nobody has judged whether its '
                     'softness shows (the notice corner\'s ground came about 1.53 times nearer and the user kept the film). --count-ground counts it.')
    return round_all({'slide_metres': slide_length, 'limit': limit, 'painting_height_pixels': painting_height, 'points': found,
                      'worst': worst['name'], 'worst_magnification': worst['magnification'], 'verdict': verdict,
                      'ground_counted': bool(args.count_ground), 'longest_slide_metres': longest_slide(nearest['depth_end'], limit)}), lines


def parse_named_boxes(items):
    """NAME=cx,cy,cz,width,depth,height (an upright box: its centre and its size along x, y and z, Blender metres)."""
    boxes = []
    for k, item in enumerate(items or []):
        name, _, value = item.rpartition('=')
        numbers = [float(v) for v in value.split(',')]
        if len(numbers) != 6:
            raise SystemExit(f'frame_geometry boxes: "{item}" should be NAME=cx,cy,cz,width,depth,height')
        boxes.append((name or f'box {k + 1}', numbers[:3], numbers[3:]))
    return boxes


def command_boxes(args, settings):
    """Where whole things land (all 8 corners of each box, not one point), and whether each stays inside the frame and
    clear of the phone buttons: words to read left of the must-read edge, story things left of the story edge within
    the button strip, and nothing to read below the bottom band (all from film-settings.json safe_area)."""
    camera = camera_from_options(args, settings)
    must_read_edge = settings.value('safe_area.must_read_right_edge_share')
    story_edge = settings.value('safe_area.story_right_edge_share')
    strip = settings.value('safe_area.button_strip_down')
    lowest_words = settings.value('safe_area.nothing_to_read_below_down')
    must_read = {n.strip() for n in args.must_read.split(',') if n.strip()}
    lines, rows = [describe_camera(camera)], []
    for name, centre, size in parse_named_boxes(args.boxes):
        low, high = box_from_centre(centre, size)
        landed = project_box(camera, box_corners(low, high))
        row = {'name': name, 'centre': centre, 'size': size, **landed, 'problems': []}
        box = landed['box']
        if box is None:
            row['problems'].append('behind the camera')
        else:
            left, top, right, bottom = box
            if not landed['all_in_front'] or left < 0 or top < 0 or right > 1 or bottom > 1:
                row['problems'].append('cut by the frame\'s edge')
            if name in must_read:
                if right > must_read_edge:
                    row['problems'].append(f'words reach {right:.3f} across, past {must_read_edge} (phone buttons)')
                if bottom > lowest_words:
                    row['problems'].append(f'words reach {bottom:.3f} down, below {lowest_words} (buttons and captions)')
            elif right > story_edge and bottom > strip[0] and top < strip[1]:
                row['problems'].append(f'reaches {right:.3f} across in the button strip ({strip[0]}-{strip[1]} down), past {story_edge}')
            row['metres_per_pixel'] = metres_per_pixel(camera, landed['nearest_depth'])
        rows.append(row)
        verdict = 'clear' if not row['problems'] else '; '.join(row['problems'])
        lines.append(f'{name}{" (to read)" if name in must_read else ""}: ' +
                     (f'{box[0]:.3f} to {box[2]:.3f} across, {box[1]:.3f} to {box[3]:.3f} down, nearest {landed["nearest_depth"]:.2f} m: {verdict}'
                      if box else verdict))
    return {'camera': round_all(camera), 'boxes': round_all(rows), 'problems': sum(len(r['problems']) for r in rows)}, lines


def command_parallax(args, settings):
    frame = frame_and_lenses(settings)
    fov = args.fov if args.fov is not None else frame['film_fov']
    if args.forward:
        if args.offset_pixels is None:
            raise SystemExit('frame_geometry parallax --forward: give --offset-pixels (the near thing\'s pixels from the frame\'s centre)')
        moved = parallax_forward_pixels(args.offset_pixels, args.slide, args.near, args.behind)
        lines = [f'Moving {args.slide} m forward, a thing {args.near} m away and {args.offset_pixels} px from the centre slides '
                 f'{moved:.1f} px against the surface {args.behind} m away.']
    else:
        moved = parallax_sideways_pixels(args.slide, args.near, args.behind, fov, frame['height'])
        lines = [f'Stepping {args.slide} m sideways, a thing {args.near} m away slides {moved:.1f} px against the surface {args.behind} m away.']
    return round_all({'slide_metres': args.slide, 'near_depth': args.near, 'behind_depth': args.behind, 'forward': bool(args.forward),
                      'pixels': moved}), lines


def command_allowance(args, settings):
    frame = frame_and_lenses(settings)
    turns = turn_allowance_degrees(frame['film_fov'], frame['plate_fov'], frame['width'], frame['height'])
    lines = [f'Film lens {frame["film_fov"]} inside a plate lens {frame["plate_fov"]} (degrees top to bottom): the camera may turn '
             f'{turns["turn_each_way_degrees"]:.2f} degrees each way and tilt {turns["tilt_each_way_degrees"]:.1f} before the frame leaves the plate.']
    result = dict(turns)
    if args.nearest is not None:
        result['sideways_metres'] = sideways_allowance_metres(args.nearest, frame['film_fov'], frame['plate_fov'], frame['width'], frame['height'])
        lines.append(f'With the nearest surface {args.nearest} m away it may step {result["sideways_metres"]:.3f} m sideways.')
    return round_all(result), lines


def camera_options(parser):
    parser.add_argument('--camera', help='a camera file: projector JSON, shot_facts facts.json, or place facts (with --view, --spot)')
    parser.add_argument('--lens', default='film', help='film, plate or degrees (default film)')
    parser.add_argument('--view', help='the view, in a place facts file')
    parser.add_argument('--spot', choices=['composed', 'plate'], help='the camera spot, in a place facts file')
    parser.add_argument('--at', help='or: the camera\'s place x,y,z (Blender metres)')
    parser.add_argument('--turn', type=float, help='turn in degrees, + to the left of +y')
    parser.add_argument('--tilt', type=float, help='tilt in degrees, + up')
    parser.add_argument('--fov', type=float, help='vertical lens angle in degrees (default: the film lens)')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Camera sums for the film frame and the plate (see the note at the top of this file).')
    commands = parser.add_subparsers(dest='command', required=True)
    p = add_output_options(commands.add_parser('project', help='where points land on the frame'))
    camera_options(p)
    p.add_argument('points', nargs='+', help='NAME=x,y,z (Blender metres)')
    p.add_argument('--size', help='also give the pixels of a thing this many metres tall at each point')
    p = add_output_options(commands.add_parser('boxes', help='where whole things land (8 corners) and whether they clear the frame\'s edges and phone buttons'))
    camera_options(p)
    p.add_argument('boxes', nargs='+', help='NAME=cx,cy,cz,width,depth,height (Blender metres)')
    p.add_argument('--must-read', default='', help='the names that carry words to read, separated by commas (notice,board)')
    p = add_output_options(commands.add_parser('meeting-point', aliases=['vp'], help='where a street\'s lines meet'))
    camera_options(p)
    p.add_argument('--direction', help='with a camera: the lines\' direction x,y,z (default 0,1,0)')
    p.add_argument('--slope', type=float, help='without a camera: the street\'s rise in metres a metre')
    p = add_output_options(commands.add_parser('size', help='pixels for metres at a depth, or metres for pixels'))
    p.add_argument('--depth', type=float)
    p.add_argument('--metres', type=float)
    p.add_argument('--pixels', type=float)
    p.add_argument('--fov', type=float)
    p = add_output_options(commands.add_parser('reach', help='how far a camera may stand for a thing to reach a given down'))
    camera_options(p)
    p.add_argument('--eye', type=float, required=True, help='the camera\'s height above the surface the thing stands on (metres)')
    p.add_argument('--down', type=float, help='the down to reach (default: the rule 7 reach in film-settings.json)')
    p.add_argument('--meeting-down', type=float, help='where the surface\'s lines meet, down (default 0.5, or from --camera)')
    p.add_argument('--direction', help='with a camera: the surface\'s direction for its meeting point')
    p.add_argument('--depth', type=float, nargs='*', help='also say where a foot at each of these depths lands')
    p = add_output_options(commands.add_parser('eye', help='the camera height needed for a thing at a depth to reach a down'))
    p.add_argument('--depth', type=float, required=True)
    p.add_argument('--down', type=float)
    p.add_argument('--meeting-down', type=float, default=0.5)
    p.add_argument('--surface-height', type=float, default=0.0)
    p.add_argument('--fov', type=float)
    p = add_output_options(commands.add_parser('turn', help='the turn for a meeting point; what one degree moves; a sideways slide'))
    p.add_argument('--across', type=float, help='where the meeting point should be, across')
    p.add_argument('--shift', type=float, help='with --depth: a wanted screen shift (share of width) of a thing')
    p.add_argument('--depth', type=float)
    p.add_argument('--fov', type=float)
    p = add_output_options(commands.add_parser('slide', help='slide magnification at the nearest painted surface, the limit and the longest slide'))
    p.add_argument('--start-camera')
    p.add_argument('--end-camera')
    p.add_argument('--place-facts')
    p.add_argument('--view')
    p.add_argument('--painting-height', type=float, help='rows the painter returns (default: the place facts\' painting, else film-settings.json)')
    p.add_argument('points', nargs='*', help='NAME=x,y,z: painted things to judge (the nearest decides)')
    p.add_argument('--count-ground', action='store_true', help='also count the painted ground at the frame\'s bottom edge (a judgement: see the report)')
    p = add_output_options(commands.add_parser('parallax', help='how far a near thing slides against what is behind it'))
    p.add_argument('--slide', type=float, required=True)
    p.add_argument('--near', type=float, required=True)
    p.add_argument('--behind', type=float, required=True)
    p.add_argument('--forward', action='store_true', help='a forward move (default: sideways)')
    p.add_argument('--offset-pixels', type=float)
    p.add_argument('--fov', type=float)
    p = add_output_options(commands.add_parser('allowance', help='how far the film camera may turn, tilt or step inside the plate'))
    p.add_argument('--nearest', type=float, help='the nearest surface\'s distance, for the sideways step')
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    runner = {'project': command_project, 'boxes': command_boxes, 'meeting-point': command_meeting_point, 'vp': command_meeting_point, 'size': command_size,
              'reach': command_reach, 'eye': command_eye, 'turn': command_turn, 'slide': command_slide, 'parallax': command_parallax,
              'allowance': command_allowance}[args.command]
    try:
        result, lines = runner(args, settings)
    except MissingSetting as problem:
        raise SystemExit(f'frame_geometry: {problem}')
    return finish(f'frame_geometry {args.command}', result, lines, settings, args)


if __name__ == '__main__':
    main()
