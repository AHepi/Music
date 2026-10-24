# What this does: inserts the two new house-number sections (place_card_time, place_variations) into kit/film-settings.json before "place_light",
# keeping the file's own layout (one space per level). Run once.
import json, sys
path = '/home/user/Music/plugins/explainer-film/kit/film-settings.json'
text = open(path, encoding='utf-8').read()
if '"place_card_time"' in text:
    sys.exit('already there')

def entry(value, unit, kind, source, **more):
    out = {'value': value, 'unit': unit, 'kind': kind, 'source': source}
    out.update(more)
    return out

PERSON = "the person's rules of 22 October 2026 (a card-time allowance for each helper; small quick test pictures; full-size pictures once at the end)"
card_time = {
    'about': "Card time: how many seconds of a rented card each helper may use, and how they are counted. Every rented-card job is written into the card-time ledger with its billed seconds "
             "(explainer-film-place card-time show). Seconds are counted cautiously (work + wake-up + the idle tail); a price made from seconds is an estimate, never a bill.",
    'allowance_minutes': {
        'builder': entry(10, 'minutes of card time', 'judged', PERSON + '; a builder may draw about two batches of ten variations (3 to 4 minutes each when no card is warm) and a few single pictures'),
        'fixer': entry(5, 'minutes of card time', 'judged', PERSON + '; a fixer draws one batch to choose the repair and one check'),
        'integrator': entry(10, 'minutes of card time', 'judged', PERSON + '; the integrator checks the combined place and may draw one batch of looks'),
        'renderer': entry(10, 'minutes of card time', 'judged', PERSON + '; the renderer draws the full-size pictures once at the end (about 45 s for each on a 4090, plus wake-up)'),
        'checker': entry(3, 'minutes of card time', 'judged', PERSON + '; a checker needs one or two close-ups'),
        'planner': entry(0, 'minutes of card time', 'judged', PERSON + '; a planner draws nothing'),
        'default': entry(5, 'minutes of card time', 'judged', PERSON + '; a helper that gives no role gets this'),
    },
    'team_total_minutes': entry(60, 'minutes of card time for one whole job', 'judged', 'about US$1.10 at the price shown on the day; the person sets the real cap for a job with `card-time start --team-minutes N` (the 22 October rule: a total cap for a test)'),
    'warn_share': entry(0.8, 'share of the allowance', 'judged', 'a plain warning when a helper has used this share of the allowance'),
    'override_extra_share': entry(0.5, 'share of the allowance', 'judged', 'with a written reason a helper may go over by at most this share; past it the tool refuses and the person decides'),
    'override_reason_letters_min': entry(15, 'letters', 'judged', 'the same rule as an off entry in the place settings: a reason of at least 15 letters'),
    'idle_tail_seconds': entry(5, 'seconds', 'judged', 'the rented-card guide: a worker stops about 5 seconds after its last job, and billing runs while a worker is up'),
    'batches_per_change_max': entry(2, 'batches', 'judged', "the person's rule: draw one batch, look at the sheet, at most one more batch for the same change"),
}
variations = {
    'about': "Batched variation rounds (explainer-film-place variations): about 10 measurably different versions of one change, drawn small and quick in up to 3 rented-card jobs at the same time, "
             "measured, and shown on one labelled contact sheet. The numbers that say 'measurably different' are starting points: nobody has yet shown by experiment how far apart settings must be for a picture to change enough to see.",
    'picture_size_pixels': entry([600, 400], 'pixels', 'judged', "the person: 'small quick test pictures'; about 600 x 400"),
    'eevee_samples': entry(16, 'samples', 'invented', 'a quick look; the full-size pictures use place_render.eevee_samples'),
    'cycles_samples': entry(24, 'samples', 'invented', 'a quick look with denoising; the full-size pictures use place_render.final_samples'),
    'jpeg_quality': entry(85, 'percent', 'judged', 'small files that still show fine detail'),
    'batch_size': entry(10, 'variations', 'judged', "the person: 'maybe 10 variations that are measurably different for each asset change'"),
    'batch_size_min': entry(3, 'variations', 'judged', 'fewer than this is not a batch: draw single pictures instead'),
    'batch_size_max': entry(16, 'variations', 'judged', 'more than this is a sign of wandering: pick fewer, wider apart'),
    'min_variations_per_job': entry(3, 'variations', 'judged', 'each wake-up of a card (20 to 25 s) should be shared by at least this many variations; the number of jobs is at most place_render.workers_max'),
    'settings_difference_min_share': entry(0.15, 'share of the setting\'s range', 'invented', 'two variations whose every setting is closer than this are near-duplicates (the later one is dropped before drawing and the sheet says so)'),
    'number_without_range_difference_min_share': entry(0.25, 'share of the larger value', 'invented', 'for a number in a script hook that has no written range: the smallest relative difference that counts'),
    'picture_mean_difference_min': entry(0.6, 'of 255, mean absolute difference', 'invented', 'two pictures that differ by less than this on average AND in fewer than picture_changed_share_min of their pixels came out nearly the same'),
    'picture_changed_share_min': entry(0.004, 'share of pixels', 'invented', 'share of pixels that differ by more than picture_pixel_step; a change on a small part of the picture still counts'),
    'picture_pixel_step': entry(8, 'of 255', 'judged', 'a pixel whose largest colour channel moved more than this counts as changed (JPEG noise stays under it)'),
    'estimated_seconds_open_scene': entry(6, 'seconds', 'invented', 'planning only, to estimate card seconds before drawing; replaced by what the first real batch measured when there is one'),
    'estimated_seconds_first_picture': entry(12, 'seconds', 'invented', 'planning only: the first picture of a job builds the shaders and the light tree'),
    'estimated_seconds_per_picture': entry(4, 'seconds', 'invented', 'planning only: one small picture after the first'),
    'sheet_thumbnail_width_pixels': entry(300, 'pixels', 'judged', 'width of one picture on the contact sheet; the sheet stays under place_render.preview_download_kilobytes_max'),
}
block = ''
for key, section in (('place_card_time', card_time), ('place_variations', variations)):
    body = json.dumps(section, indent=1, ensure_ascii=False).replace('\n', '\n ')
    block += f' "{key}": {body},\n'
marker = ' "place_light": {'
assert text.count(marker) == 1
new = text.replace(marker, block + marker)
json.loads(new)
open(path, 'w', encoding='utf-8').write(new)
print('inserted')
