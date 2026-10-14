"""What this does: measures why a picture's composition works, without judging taste.
It draws the thirds grid and the picture's main converging lines, finds where those lines meet,
makes a "squint" view (only big light and dark areas), a warm-light map, a mirror image, and
counts where the picture's visual weight sits.

Use: python3 measure_composition.py PICTURE OUTPUT_FOLDER [OBJECT_BOXES.json]
OBJECT_BOXES.json (optional) names the objects to report, each as [left, top, right, bottom] in
fractions of the picture's width and height (0 = left or top, 1 = right or bottom), for example
{"notice paper": [0.744, 0.4525, 0.914, 0.645]}. Output: five pictures and "06 measurements.json".
Needs Python with OpenCV (cv2) and NumPy. If fewer than about 15 slanted lines are found, the
"where the lines meet" figure is unreliable (soft frames give few lines): trace the kerbs and
gutters by hand instead. The rules these numbers check are in "07 Composing a shot.md" (in the film kit)."""
import sys, json, math
import cv2
import numpy as np

if len(sys.argv) < 3:
    sys.exit('Use: python3 measure_composition.py PICTURE OUTPUT_FOLDER [OBJECT_BOXES.json]')
picture_path, output_folder = sys.argv[1], sys.argv[2]
object_boxes_path = sys.argv[3] if len(sys.argv) > 3 else None
picture = cv2.imread(picture_path)
height, width = picture.shape[:2]
elements = json.load(open(object_boxes_path)) if object_boxes_path else {}
def box_in_pixels(box):
    left, top, right, bottom = box
    return int(left * width), int(top * height), int(right * width), int(bottom * height)

grey = cv2.cvtColor(picture, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
numbers = {'size': [width, height]}

# 1. Brightness of each element against the whole picture
numbers['average brightness of whole picture'] = round(float(grey.mean()), 3)
element_numbers = {}
for name, box in elements.items():
    left, top, right, bottom = box_in_pixels(box)
    patch = grey[top:bottom, left:right]
    centre_x = (left + right) / 2 / width
    centre_y = (top + bottom) / 2 / height
    element_numbers[name] = {
        'centre across (0 left, 1 right)': round(centre_x, 3),
        'centre down (0 top, 1 bottom)': round(centre_y, 3),
        'average brightness': round(float(patch.mean()), 3),
        'share of picture area %': round(100 * (right - left) * (bottom - top) / (width * height), 2),
    }
numbers['elements'] = element_numbers

# 2. Converging lines: find long slanted straight lines and where they meet
detector = cv2.createLineSegmentDetector()
found_lines = detector.detect((grey * 255).astype(np.uint8))[0]
slanted = []
for line in found_lines.reshape(-1, 4):
    x1, y1, x2, y2 = map(float, line)
    length = math.hypot(x2 - x1, y2 - y1)
    if length < 0.06 * height:
        continue
    angle = abs(math.degrees(math.atan2(y2 - y1, x2 - x1))) % 180
    if angle < 8 or angle > 172 or 80 < angle < 100:
        continue   # skip flat and upright lines; keep the ones that run into the distance
    slanted.append((x1, y1, x2, y2, length))
meeting_points = []
for i in range(len(slanted)):
    for j in range(i + 1, len(slanted)):
        a, b = slanted[i], slanted[j]
        x1, y1, x2, y2 = a[:4]; x3, y3, x4, y4 = b[:4]
        denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denominator) < 1e-6:
            continue
        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator
        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator
        if 0 <= px < width and 0 <= py < height:
            meeting_points.append((px, py, min(a[4], b[4])))
if meeting_points:
    points = np.array(meeting_points)
    # find the densest meeting place with a coarse vote
    votes = np.zeros((40, 24))
    for px, py, weight in points:
        votes[min(39, int(py / height * 40)), min(23, int(px / width * 24))] += weight
    row, column = np.unravel_index(votes.argmax(), votes.shape)
    near = points[(np.abs(points[:, 1] / height * 40 - row - 0.5) < 1.5) & (np.abs(points[:, 0] / width * 24 - column - 0.5) < 1.5)]
    vanishing_x = float(np.average(near[:, 0], weights=near[:, 2]))
    vanishing_y = float(np.average(near[:, 1], weights=near[:, 2]))
    numbers['where the lines meet (0-1 across, 0-1 down)'] = [round(vanishing_x / width, 3), round(vanishing_y / height, 3)]
numbers['slanted lines found'] = len(slanted)

# 3. Where the visual weight sits: local contrast (busy detail) plus distance from mid grey
edges = cv2.Laplacian(cv2.GaussianBlur(grey, (0, 0), 2), cv2.CV_32F)
detail = cv2.GaussianBlur(np.abs(edges), (0, 0), 25)
light_dark = np.abs(grey - grey.mean())
weight = detail / detail.mean() + light_dark / light_dark.mean()
ys, xs = np.mgrid[0:height, 0:width]
numbers['centre of visual weight (0-1 across, 0-1 down)'] = [round(float((weight * xs).sum() / weight.sum() / width), 3), round(float((weight * ys).sum() / weight.sum() / height), 3)]
numbers['weight left half vs right half %'] = [round(100 * float(weight[:, :width // 2].sum() / weight.sum()), 1), round(100 * float(weight[:, width // 2:].sum() / weight.sum()), 1)]
numbers['weight in thirds, top/middle/bottom %'] = [round(100 * float(weight[h0:h1].sum() / weight.sum()), 1) for h0, h1 in ((0, height // 3), (height // 3, 2 * height // 3), (2 * height // 3, height))]

# 3b. Where the brightest 3% sits (after a light blur), and how bright the top third is
blurred_for_brightest = cv2.GaussianBlur(grey, (0, 0), width * 0.01)
brightest = blurred_for_brightest >= np.percentile(blurred_for_brightest, 97)
brightest_ys, brightest_xs = np.nonzero(brightest)
numbers['brightest 3% centre (0-1 across, 0-1 down)'] = [round(float(brightest_xs.mean() / width), 3), round(float(brightest_ys.mean() / height), 3)]
numbers['brightest 3% share in top third %'] = round(100 * float((brightest_ys < height / 3).mean()), 1)
numbers['brightest 3% share inside each object %'] = {}
for name, box in elements.items():
    left, top, right, bottom = box_in_pixels(box)
    numbers['brightest 3% share inside each object %'][name] = round(100 * float(brightest[top:bottom, left:right].sum() / brightest.sum()), 1)
numbers['top row brightness, left/middle/right'] = [round(float(grey[:height // 3, a:b].mean()), 3) for a, b in ((0, width // 3), (width // 3, 2 * width // 3), (2 * width // 3, width))]

# 4. Warm light: where the picture is clearly orange or yellow and bright
blue, green, red = [channel.astype(np.float32) for channel in cv2.split(picture)]
warmth = np.clip((red - blue) / 255.0, 0, 1) * grey
warm_mask = warmth > 0.18
numbers['warm light share of picture %'] = round(100 * float(warm_mask.mean()), 2)
numbers['warm light share by thirds across (left/middle/right) %'] = [round(100 * float(warm_mask[:, a:b].sum() / max(1, warm_mask.sum())), 1) for a, b in ((0, width // 3), (width // 3, 2 * width // 3), (2 * width // 3, width))]

# Pictures --------------------------------------------------------------------------
def save(name, image):
    cv2.imwrite(f'{output_folder}/{name}', image, [cv2.IMWRITE_JPEG_QUALITY, 88])

thick = max(2, width // 400)
guide = picture.copy()
for fraction in (1 / 3, 2 / 3):
    cv2.line(guide, (int(width * fraction), 0), (int(width * fraction), height), (255, 255, 255), thick)
    cv2.line(guide, (0, int(height * fraction)), (width, int(height * fraction)), (255, 255, 255), thick)
for x1, y1, x2, y2, length in sorted(slanted, key=lambda line: -line[4])[:60]:
    cv2.line(guide, (int(x1), int(y1)), (int(x2), int(y2)), (0, 220, 255), thick)
if meeting_points:
    cv2.circle(guide, (int(vanishing_x), int(vanishing_y)), width // 40, (0, 0, 255), thick * 2)
for name in elements:
    left, top, right, bottom = box_in_pixels(elements[name])
    cv2.rectangle(guide, (left, top), (right, bottom), (255, 120, 0), thick)
save('01 thirds grid and where the lines meet.jpg', guide)

squint = cv2.GaussianBlur(grey, (0, 0), width / 60)
levels = np.floor(squint * 5) / 5 + 0.1
save('02 squint view - big light and dark areas.jpg', (np.clip(levels, 0, 1) * 255).astype(np.uint8))

warm_view = (grey[..., None] * 0.35 * 255).astype(np.uint8).repeat(3, axis=2)
warm_view[warm_mask] = (0, 150, 255)
save('03 warm light only.jpg', warm_view)

save('04 mirror image.jpg', cv2.flip(picture, 1))

weight_view = cv2.applyColorMap((np.clip(weight / np.percentile(weight, 99), 0, 1) * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
centre = numbers['centre of visual weight (0-1 across, 0-1 down)']
cv2.drawMarker(weight_view, (int(centre[0] * width), int(centre[1] * height)), (255, 255, 255), cv2.MARKER_CROSS, width // 15, thick * 2)
cv2.line(weight_view, (width // 2, 0), (width // 2, height), (255, 255, 255), thick)
save('05 where the visual weight sits.jpg', weight_view)

json.dump(numbers, open(f'{output_folder}/06 measurements.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in numbers.items() if k != 'elements'}, indent=1))
for name, values in element_numbers.items():
    print(name, values)
