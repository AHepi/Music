"""What this does: draws one explainer picture comparing the picture the user liked with our clip.
On each it marks where the street's lines meet (yellow lines, red ring), the brightest parts
(white outlines) and the biggest thing near the camera (blue box), so you can see whether they
agree on one place. Input: the two pictures and an output path."""
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

liked_path, clip_path, output_path = sys.argv[1:4]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def brightest_outlines(picture):
    grey = cv2.cvtColor(picture, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    blurred = cv2.GaussianBlur(grey, (0, 0), picture.shape[1] * 0.01)
    mask = (blurred >= np.percentile(blurred, 97)).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def mark(picture, lines, meeting_point, ring_radius, near_box, notice_box):
    picture = picture.copy()
    thick = max(3, picture.shape[1] // 300)
    for start, end in lines:
        cv2.line(picture, start, end, (0, 230, 255), thick, cv2.LINE_AA)
    cv2.drawContours(picture, brightest_outlines(picture), -1, (255, 255, 255), thick, cv2.LINE_AA)
    cv2.circle(picture, meeting_point, ring_radius, (40, 40, 255), thick * 2, cv2.LINE_AA)
    cv2.rectangle(picture, near_box[:2], near_box[2:], (255, 140, 30), thick * 2)
    cv2.rectangle(picture, notice_box[:2], notice_box[2:], (120, 255, 120), thick)
    return Image.fromarray(cv2.cvtColor(picture, cv2.COLOR_BGR2RGB))

liked = cv2.imread(liked_path)          # 1536 x 2752
clip = cv2.imread(clip_path)            # 1080 x 1920
liked_meeting = (1085, 1167)
liked_marked = mark(liked,
    lines=[((890, 1700), liked_meeting), ((0, 1655), liked_meeting), ((0, 497), liked_meeting)],
    meeting_point=liked_meeting, ring_radius=80,
    near_box=(1080, 1658, 1486, 2312), notice_box=(1142, 1245, 1404, 1775))
clip_meeting = (230, 1175)
clip_marked = mark(clip,
    lines=[((1001, 367), clip_meeting), ((1079, 1590), clip_meeting)],
    meeting_point=clip_meeting, ring_radius=90,
    near_box=(105, 1565, 665, 1835), notice_box=(848, 1080, 972, 1250))

panel_width, panel_height, gap, header, footer = 720, 1290, 40, 150, 330
sheet = Image.new('RGB', (panel_width * 2 + gap * 3, header + panel_height + footer), (24, 24, 30))
draw = ImageDraw.Draw(sheet)
title_font, label_font, small_font = ImageFont.truetype(BOLD, 40), ImageFont.truetype(BOLD, 32), ImageFont.truetype(FONT, 27)
draw.text((gap, 30), 'Do the strongest things in the picture agree on one place?', fill=(240, 240, 240), font=title_font)
for index, (image, label, verdict) in enumerate([
        (liked_marked, 'The picture you liked', 'Yes: lines, brightness and the big near\nthings all land on the notice corner.'),
        (clip_marked, 'Our clip, 4 seconds in', 'No: lines meet at the colliery door, the\nbrightest parts are scattered (sky, fire,\nlamps) and the biggest near thing is the sacks.')]):
    x = gap + index * (panel_width + gap)
    draw.text((x, 95), label, fill=(255, 215, 120), font=label_font)
    sheet.paste(image.resize((panel_width, panel_height)), (x, header))
    draw.multiline_text((x, header + panel_height + 18), verdict, fill=(235, 235, 235), font=small_font, spacing=8)
legend_y = header + panel_height + 150
for row, (colour, words) in enumerate([
        ((255, 230, 0), 'Yellow lines: the street\'s straight lines.  Red ring: where they meet.'),
        ((255, 255, 255), 'White outlines: the brightest 3 per cent of the picture.'),
        ((30, 140, 255), 'Blue box: the biggest thing near the camera.   Green box: the notice.')]):
    draw.rectangle((gap, legend_y + row * 52 + 8, gap + 30, legend_y + row * 52 + 34), fill=colour)
    draw.text((gap + 48, legend_y + row * 52), words, fill=(225, 225, 225), font=small_font)
sheet.save(output_path, quality=90)
