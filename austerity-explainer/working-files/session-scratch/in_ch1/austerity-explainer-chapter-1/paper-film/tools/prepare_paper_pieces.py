"""What this does: turns the painted pictures from fal into paper pieces for the paper animation.

It reads a cut list (a JSON file, for example paper-film/scene-data/chapter-1-cut-list.json) that
names every page painting and every cut-out piece, and for each figure or object (painted on a
plain grey background, with a cut-out mask from the background-removal step) it:
  1. keeps only the main shape (drops stray specks the mask picked up) and fills tiny holes;
  2. cuts it out with a narrow paper margin, with smooth scissor-like edges;
  3. nudges the colours toward the page paintings (cooler shadows, slightly less saturated), so the
     pieces sit in the same light as the backgrounds;
  4. trims to the shape and scales it down so its longest side fits the cut list's size;
  5. writes a PNG with see-through surroundings, and records each piece's size in pieces.json.

Page paintings are copied at full size, unchanged.

Extra treatments, each switched on in the cut list for the pieces that need it:
  - leave_out_boxes / add_polygons: take bits out of the mask, or put back bits it missed;
  - mask_threshold: how solid the mask must be to count as part of the piece (default 128 of 255);
  - jaw: splits a speaking figure into three layers for its paper mouth: the face with the jaw cut
    out, the jaw on its own (it slides down and up), and a dark mouth that shows through the gap;
  - labels: prints words onto an object (a report's title, a book's title, TAX on a price tag);
  - split_shapes: every separate shape becomes its own piece (name-1, name-2 ... left to right);
  - map_card: prints the picture on a small rounded paper card instead of cutting round it.

Use: python3 -I prepare_paper_pieces.py CUT_LIST.json PROJECT_FOLDER [NAME ...]
(naming pieces at the end remakes only those, keeping the rest of pieces.json)
"""

import json
import math
import os
import sys

import cv2
import numpy
from PIL import Image, ImageDraw, ImageFont

PAPER_MARGIN_COLOUR = numpy.array([214, 226, 233], dtype=numpy.float32)  # warm off-white, in BGR
MOUTH_COLOUR = (24, 18, 38)  # very dark warm red-brown, BGR
LABEL_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DEFAULT_LONGEST_SIDE = 2048
DEFAULT_GRADE = 0.35
DEFAULT_MARGIN = 0.008


def solid_mask(mask, threshold):
    """0/1 mask: 1 where the background remover is at least `threshold` sure it is the piece."""
    return (mask >= threshold).astype(numpy.uint8)


def keep_main_shape(binary):
    """Binary mask with stray specks removed and pin-holes filled."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if count > 1:
        largest = stats[1:, cv2.CC_STAT_AREA].max()
        keep = numpy.zeros(count, dtype=bool)
        keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= largest * 0.02
        binary = keep[labels].astype(numpy.uint8)
    return fill_small_holes(binary)


def fill_small_holes(binary):
    holes = 1 - binary
    count, labels, stats, _ = cv2.connectedComponentsWithStats(holes, connectivity=4)
    small_hole_area = binary.size * 0.0004
    for label in range(1, count):
        x, y, w, h, area = stats[label]
        touches_edge = x == 0 or y == 0 or x + w == binary.shape[1] or y + h == binary.shape[0]
        if not touches_edge and area < small_hole_area:
            binary[labels == label] = 1
    return binary


def separate_shapes(binary):
    """List of 0/1 masks, one per sizeable separate shape, ordered left to right."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    largest = stats[1:, cv2.CC_STAT_AREA].max()
    shapes = [(stats[label, cv2.CC_STAT_LEFT], label) for label in range(1, count)
              if stats[label, cv2.CC_STAT_AREA] >= largest * 0.2]
    return [fill_small_holes((labels == label).astype(numpy.uint8)) for _, label in sorted(shapes)]


def paper_cut(binary, margin_pixels):
    """Soft-edged alpha (0..1) for the shape grown by a paper margin, with rounded scissor-cut edges."""
    radius = max(2, int(round(margin_pixels)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius + 1, 2 * radius + 1))
    grown = cv2.dilate(binary, kernel)
    smoothed = cv2.GaussianBlur(grown.astype(numpy.float32), (0, 0), radius * 0.9)
    cut = (smoothed > 0.5).astype(numpy.float32)
    return cv2.GaussianBlur(cut, (0, 0), 1.0)


def grade(bgr, strength):
    """Cooler shadows, a touch less saturation and brightness: closer to the page paintings."""
    image = bgr.astype(numpy.float32) / 255.0
    luminance = (0.114 * image[..., 0] + 0.587 * image[..., 1] + 0.299 * image[..., 2])[..., None]
    shadow_weight = numpy.clip(1.0 - luminance, 0, 1) ** 1.5
    cool = image * numpy.array([1.06, 0.98, 0.86], dtype=numpy.float32)  # B up, R down
    image = image + (cool - image) * shadow_weight * strength
    grey = (0.114 * image[..., 0] + 0.587 * image[..., 1] + 0.299 * image[..., 2])[..., None]
    image = grey + (image - grey) * (1.0 - 0.12 * strength)
    image = image * (1.0 - 0.06 * strength)
    return numpy.clip(image * 255.0, 0, 255)


def over_paper(bgr, shape_alpha):
    """The painting laid over off-white paper (the paper shows wherever the shape is not)."""
    margin = PAPER_MARGIN_COLOUR[None, None, :]
    return bgr * shape_alpha[..., None] + margin * (1 - shape_alpha[..., None])


def trim_box(alpha, pad=4):
    ys, xs = numpy.where(alpha > 0.02)
    y0, y1 = max(0, ys.min() - pad), min(alpha.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(alpha.shape[1], xs.max() + pad + 1)
    return x0, y0, x1, y1


def save_rgba(rgba_float, path, scale):
    rgba = numpy.clip(rgba_float, 0, 255).astype(numpy.uint8)
    if scale != 1.0:
        rgba = cv2.resize(rgba, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    image = Image.fromarray(cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA))
    image.save(path, optimize=True)
    return image.size


def print_labels(rgba_path, labels):
    """Prints each block of words onto the finished piece (sizes are shares of the piece's width)."""
    image = Image.open(rgba_path).convert("RGBA")
    width, height = image.size
    for label in labels:
        font = ImageFont.truetype(LABEL_FONT, int(width * label["font_share"]))
        colour = tuple(label.get("colour", [28, 34, 42, 235]))
        if label.get("along_long_side"):
            print_along_long_side(image, label["lines"][0], font, colour)
            continue
        draw = ImageDraw.Draw(image)
        y = height * label["top_y"]
        for line in label["lines"]:
            box = draw.textbbox((0, 0), line, font=font)
            x = width * label["centre_x"] - (box[2] - box[0]) / 2
            draw.text((x, y), line, font=font, fill=colour)
            y += (box[3] - box[1]) * label.get("line_gap", 1.45)
    image.save(rgba_path, optimize=True)


def print_along_long_side(image, text, font, colour):
    """Prints one word at the middle of the piece, turned to run along the piece's longest direction.
    Thin parts (a tag's string) are worn away first, so they do not pull the word off the middle."""
    alpha = (numpy.asarray(image)[..., 3] > 128).astype(numpy.uint8)
    wear = max(3, int(max(alpha.shape) * 0.04))
    body = cv2.erode(alpha, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * wear + 1, 2 * wear + 1)))
    ys, xs = numpy.nonzero(body if body.any() else alpha)
    centre_x, centre_y = xs.mean(), ys.mean()
    covariance = numpy.cov(numpy.vstack([xs - centre_x, ys - centre_y]))
    values, vectors = numpy.linalg.eigh(covariance)
    long_x, long_y = vectors[:, numpy.argmax(values)]
    angle = math.degrees(math.atan2(-long_y, long_x))  # counter-clockwise, as PIL rotates
    if angle > 90:
        angle -= 180
    if angle < -90:
        angle += 180
    box = font.getbbox(text)
    text_image = Image.new("RGBA", (box[2] - box[0] + 20, box[3] - box[1] + 20), (0, 0, 0, 0))
    ImageDraw.Draw(text_image).text((10 - box[0], 10 - box[1]), text, font=font, fill=colour)
    turned = text_image.rotate(angle, resample=Image.BICUBIC, expand=True)
    image.alpha_composite(turned, (int(centre_x - turned.width / 2), int(centre_y - turned.height / 2)))


def map_card(bgr, mask, settings, grade_strength):
    """The picture printed on a rounded paper card: returns the card as float RGBA (BGR order)."""
    border = numpy.concatenate([bgr[:12].reshape(-1, 3), bgr[-12:].reshape(-1, 3), bgr[:, :12].reshape(-1, 3), bgr[:, -12:].reshape(-1, 3)])
    background = numpy.median(border, axis=0)
    difference = numpy.abs(bgr - background[None, None, :]).max(axis=2)
    land = ((difference > settings["background_tolerance"]) | (mask >= 128)).astype(numpy.uint8)
    land = cv2.morphologyEx(land, cv2.MORPH_OPEN, numpy.ones((3, 3), numpy.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(land, connectivity=8)
    keep = numpy.zeros(count, dtype=bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= 30
    land = fill_small_holes(keep[labels].astype(numpy.uint8))
    land_alpha = cv2.GaussianBlur(land.astype(numpy.float32), (0, 0), 0.8)

    x0, y0, x1, y1 = trim_box(land.astype(numpy.float32), pad=0)
    side = max(x1 - x0, y1 - y0)
    pad = int(side * settings["padding_share"])
    corner = int(side * settings["corner_share"])
    height, width = mask.shape
    canvas_x0, canvas_y0 = x0 - pad, y0 - pad
    canvas_w, canvas_h = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    # a larger canvas, in case the card reaches past the picture's edges
    big = numpy.zeros((canvas_h, canvas_w, 4), dtype=numpy.float32)
    card = numpy.zeros((canvas_h, canvas_w), dtype=numpy.uint8)
    cv2.rectangle(card, (corner, 0), (canvas_w - 1 - corner, canvas_h - 1), 1, -1)
    cv2.rectangle(card, (0, corner), (canvas_w - 1, canvas_h - 1 - corner), 1, -1)
    for cx, cy in ((corner, corner), (canvas_w - 1 - corner, corner), (corner, canvas_h - 1 - corner), (canvas_w - 1 - corner, canvas_h - 1 - corner)):
        cv2.circle(card, (cx, cy), corner, 1, -1)
    card_alpha = cv2.GaussianBlur(card.astype(numpy.float32), (0, 0), 1.0)

    painted = numpy.zeros((canvas_h, canvas_w, 3), dtype=numpy.float32)
    painted[:] = PAPER_MARGIN_COLOUR
    land_big = numpy.zeros((canvas_h, canvas_w), dtype=numpy.float32)
    sx0, sy0 = max(0, canvas_x0), max(0, canvas_y0)
    sx1, sy1 = min(width, canvas_x0 + canvas_w), min(height, canvas_y0 + canvas_h)
    graded = grade(bgr, grade_strength)
    painted[sy0 - canvas_y0:sy1 - canvas_y0, sx0 - canvas_x0:sx1 - canvas_x0] = graded[sy0:sy1, sx0:sx1]
    land_big[sy0 - canvas_y0:sy1 - canvas_y0, sx0 - canvas_x0:sx1 - canvas_x0] = land_alpha[sy0:sy1, sx0:sx1]
    big[..., :3] = over_paper(painted, land_big)
    big[..., 3] = card_alpha * 255.0
    return big


def mouth_layers(rgba, jaw_settings):
    """Face (jaw cut out), jaw, and dark mouth layers on the same canvas, so they line up exactly."""
    shape = rgba.shape[:2]
    jaw = numpy.zeros(shape, dtype=numpy.uint8)
    cv2.fillPoly(jaw, [numpy.array(jaw_settings["jaw_polygon"], dtype=numpy.int32)], 1)
    jaw_alpha = cv2.GaussianBlur(jaw.astype(numpy.float32), (0, 0), 0.7)
    face = rgba.copy()
    face[..., 3] = face[..., 3] * (1 - jaw_alpha)
    jaw_layer = rgba.copy()
    jaw_layer[..., 3] = 255.0 * jaw_alpha
    mouth = numpy.zeros(shape, dtype=numpy.uint8)
    cv2.fillPoly(mouth, [numpy.array(jaw_settings["mouth_polygon"], dtype=numpy.int32)], 1)
    mouth_layer = numpy.zeros_like(rgba)
    mouth_layer[..., :3] = numpy.array(jaw_settings.get("mouth_colour", MOUTH_COLOUR), dtype=numpy.float32)
    mouth_layer[..., 3] = 255.0 * cv2.GaussianBlur(mouth.astype(numpy.float32), (0, 0), 1.5)
    return face, jaw_layer, mouth_layer


def record(pieces, name, size, kind="piece", **extra):
    pieces[name] = {"file": f"{name}.png" if kind == "piece" else f"{name}.jpg", "width_px": size[0], "height_px": size[1], "kind": kind, **extra}


def make_piece(name, settings, project, output_folder, pieces):
    bgr = cv2.imread(os.path.join(project, settings["image"]), cv2.IMREAD_COLOR).astype(numpy.float32)
    mask = cv2.imread(os.path.join(project, settings["mask"]), cv2.IMREAD_GRAYSCALE)
    if mask.shape != bgr.shape[:2]:
        mask = cv2.resize(mask, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_LINEAR)
    longest_side = settings.get("longest_side", DEFAULT_LONGEST_SIDE)
    grade_strength = settings.get("grade", DEFAULT_GRADE)

    if "map_card" in settings:
        card = map_card(bgr, mask, settings["map_card"], grade_strength)
        scale = min(1.0, longest_side / max(card.shape[:2]))
        size = save_rgba(card, os.path.join(output_folder, f"{name}.png"), scale)
        record(pieces, name, size)
        return

    for x0, y0, x1, y1 in settings.get("leave_out_boxes", []):
        mask[y0:y1, x0:x1] = 0
    for polygon in settings.get("add_polygons", []):
        cv2.fillPoly(mask, [numpy.array(polygon, dtype=numpy.int32)], 255)
    binary = solid_mask(mask, settings.get("mask_threshold", 128))
    margin_pixels = settings.get("margin", DEFAULT_MARGIN) * max(binary.shape)
    graded = grade(bgr, grade_strength)

    shapes = separate_shapes(binary) if settings.get("split_shapes") else [keep_main_shape(binary)]
    for number, shape in enumerate(shapes, start=1):
        piece_name = f"{name}-{number}" if settings.get("split_shapes") else name
        alpha_cut = paper_cut(shape, margin_pixels)
        shape_alpha = cv2.GaussianBlur(shape.astype(numpy.float32), (0, 0), 0.8)
        rgba = numpy.dstack([over_paper(graded, shape_alpha), alpha_cut * 255.0])
        x0, y0, x1, y1 = trim_box(alpha_cut)
        scale = min(1.0, longest_side / max(x1 - x0, y1 - y0))

        if "jaw" in settings:
            face, jaw_layer, mouth_layer = mouth_layers(rgba, settings["jaw"])
            for layer_name, layer in ((f"{name}-face", face), (f"{name}-jaw", jaw_layer), (f"{name}-mouth", mouth_layer)):
                size = save_rgba(layer[y0:y1, x0:x1], os.path.join(output_folder, f"{layer_name}.png"), scale)
                record(pieces, layer_name, size)
            jaw_points = settings["jaw"]["jaw_polygon"]
            jaw_top = min(y for _, y in jaw_points)
            jaw_bottom = max(y for _, y in jaw_points)
            # where the jaw's top edge sits (share of the piece height, from the bottom), and how far the
            # jaw may drop: a fifth of its own height, as a share of the piece height (for the film)
            pieces[f"{name}-face"]["jaw_top_from_bottom"] = round((y1 - jaw_points[0][1]) / (y1 - y0), 4)
            pieces[f"{name}-face"]["jaw_drop_share"] = round(0.2 * (jaw_bottom - jaw_top) / (y1 - y0), 4)
            continue

        size = save_rgba(rgba[y0:y1, x0:x1], os.path.join(output_folder, f"{piece_name}.png"), scale)
        record(pieces, piece_name, size)
        if "labels" in settings:
            print_labels(os.path.join(output_folder, f"{piece_name}.png"), settings["labels"])


def main():
    cut_list_path, project = sys.argv[1], sys.argv[2]
    with open(cut_list_path, encoding="utf-8") as handle:
        cut_list = json.load(handle)
    output_folder = os.path.join(project, cut_list["output_folder"])
    os.makedirs(output_folder, exist_ok=True)
    pieces = {}

    for name, file_name in cut_list["backgrounds"].items():
        image = Image.open(os.path.join(project, file_name)).convert("RGB")
        image.save(os.path.join(output_folder, f"{name}.jpg"), quality=95)
        record(pieces, name, image.size, kind="page")

    only = set(sys.argv[3:])
    for name, settings in cut_list["pieces"].items():
        if only and name not in only:
            continue
        make_piece(name, settings, project, output_folder, pieces)

    pieces_path = os.path.join(output_folder, "pieces.json")
    if only and os.path.exists(pieces_path):
        with open(pieces_path, encoding="utf-8") as handle:
            pieces = {**json.load(handle), **pieces}
    with open(pieces_path, "w", encoding="utf-8") as handle:
        json.dump(pieces, handle, indent=1)
    for name, info in pieces.items():
        print(f"{name:20s} {info['width_px']:5d} x {info['height_px']:5d}  {info['kind']}")


if __name__ == "__main__":
    main()
