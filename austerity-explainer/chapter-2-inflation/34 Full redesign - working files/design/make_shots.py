# What this does: writes shots.json (every shot of chapter 2 for newcomers in the redesign) from the
# lists below, and prints the frame counts by kind, which the plan's filming time comes from.
# Times are from the estimated timeline (film-kit/examples/inflation-chapter-2-newcomers/timeline-estimated.json).
import json, os, sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shots.json')
FPS = 30

CAM = {
 'W3': "Upstairs window of the end house across the cross street at the lane's mouth, on the lane's centre line, about 30 m from the works wall; eye about 4.6 m up (the shot checker picks between 4.5 and 7 m), level, facing straight up the lane, never turning. The lane's lines meet on the wall between the two gates.",
 'W1': "On the lane's left pavement, standing in line with the left pier of No. 1's gate (where the brazier is), 13 m from the gate at the plate's spot and 11.8 m at the composed frame; standing eye height (about 1.7 m), level, facing straight up the lane. The lines meet at the pier's edge, beside the gate.",
 'W2': "Mirror of W1: on the lane's right pavement, in line with the right pier of No. 2's gate, 13 m from the gate at the plate's spot and 11.8 m at the composed frame; eye height, level, facing straight up the lane. The lines meet at the pier's edge, beside the gate.",
 'W4': "Inside No. 2's yard, where a worker on his break would stand, in line with the gate's hinge post; 7.2 m from the gate at the plate's spot, 6.0 m at the composed frame; eye height, level, facing straight out through the gate and down the lane.",
 'C1': "Where the next shopper in the line stands, in line with the edge of the newspaper bill; 3.1 m from the basket at the plate's spot, 2.4 m at the composed frame; eye height 1.6 m, level, looking along the belt.",
 'J1': "Where the next customer stands, about 2.4 m from the basket on the counter; eye height 1.6 m, level.",
 'S1a': "On the footpath at the site's open gate, in line with the edge of the digger's cab, about 6 m from the digger; eye height, level, looking straight up the driveway into the section. The driveway's edges, the neighbours' side walls and the scaffold planks meet at the cab's edge.",
 'S1b': "The same spot as S1a, outside the now shut gate; eye height, level, looking straight up the driveway.",
 'K1': "Seated in the chair across the table from the pushed-back one (eye about 1.2 m), in line with the letter's edge; 1.85 m from the letter at the plate's spot, 1.42 m at the composed frame; level.",
 'G1': "On the right-hand pavement, an arm's length in from the kerb, in line with the munitions works' gate at the street's far end (about 120 m); eye height, level, facing straight down the street. The grocer's splayed corner window, across the next side street, stands just right of where the lines meet, 8 m away at the plate's spot.",
 'G2': "On the left pavement of a short side street that ends at a tenement facing us; standing in line with the close arch's right edge, 8.0 m from the close at the plate's spot and 6.5 m at the composed frame; eye height, level, facing straight up the street.",
}
PLACE = {'W1': 'A. The Works', 'W2': 'A. The Works', 'W3': 'A. The Works', 'W4': 'A. The Works',
         'C1': 'B. The checkout (New Zealand, 2025-26)', 'J1': 'C. The corner shop (Japan, 2013)',
         'S1a': 'D. The building site (New Zealand), busy', 'S1b': 'D. The building site (New Zealand), stopped in 2026',
         'K1': 'E. The kitchen (New Zealand, 2022-23)', 'G1': 'F. Glasgow, 1915: the street to the works', 'G2': 'F. Glasgow, 1915: the close mouth'}
PAINTINGS = {'W3': 1, 'W1': 2, 'W2': 3, 'W4': 2, 'C1': 2, 'J1': 1, 'S1a': 2, 'S1b': 1, 'K1': 2, 'G1': 2, 'G2': 2}
STORY = {
 'W3': "No. 1 (left column): the round chimney, cold; the shut, chained gate; the brazier and lit lantern; a queue of 7 whose tail reaches the lane's last third. No. 2 (right column): two square chimneys smoking and the water tank; the open, lit gateway; crates; a handcart of crates coming up the right pavement. Between them, the shared wall with a high dividing wall rising behind it. On the left in the lane's last third: the bank, its hanging sign BANK square to the lane, window dark until page 9. PETROL and DIESEL drums by both gates.",
 'W1': "The shut No. 1 gate with chain and padlock (own-surface leaves); the brazier against the left pier, its rim clearly overlapping the pier's base; the front man beside it, one hand on a gate bar; six more in single file behind him along the pavement, each overlapping the one in front; a lit lantern and a lunch tin on the wall's coping above the third man; the No. 1 board over the gate; two drums stencilled PETROL and DIESEL against the pier. Above: No. 1's mill windows (dark) and its round chimney in the same column; small, upper right, No. 2's two square chimneys.",
 'W2': "The open No. 2 gate, its leaf pinned back (own surface); crates stencilled THIS WAY UP stacked inside the gateway beside the leaf, a handcart's shafts over them; the gate lamp on the pier; the warm patch of the gateway's light on the empty pavement where a queue would be; the No. 2 board; two drums stencilled PETROL and DIESEL against the pier. Above: the blazing mill windows and two smoking square chimneys; small, upper left, No. 1's round chimney.",
 'W4': "The half-shut gate leaf; a jacket and cap on a nail on the inside post; an upturned crate against the post's foot with a tin mug and a pay envelope lettered WAGES; through the bars, the lamp-lit lane and a queue of 8 men as dark silhouettes (own surfaces), the nearest just outside the bars at about 6.5 m.",
 'C1': "A full grey wire basket on the belt (bread in a paper bag, milk in a plastic bottle, butter, cheese, kiwifruit, apples, bananas hanging over the rim); the divider bar against its front; the newspaper bill in a wire stand at the counter's end, its edge overlapping the basket's far side, reading NEW MONEY: PRICES WILL GO UP; the card terminal beyond with its keypad turned away; reusable bags on the rack. Near ceiling lights off for closing time; a warm lamp over the belt.",
 'J1': "A basket on the counter (rice balls, a bottle of tea, a carton of milk) touching the till's edge; a change tray in front of it; the glowing hot-food cabinet against the till's other side; through the window, across the night street, a bank with its shutter down and its small cash-machine corner lit.",
 'S1a': "Just inside the open gate, all touching: a faded-orange mini digger with its bucket on the ground, a strapped packet of fresh timber against its track, an orange hi-vis vest hanging on the digger's door, a white hard hat on the timber. Behind: the pine house frame with building wrap and scaffolding, against a low late-afternoon sun. FOR RENT board on the neighbour's fence (hidden until page 11); PLEASE SANITISE YOUR HANDS sign on the gate (page 10 only).",
 'S1b': "The gate shut with a chain and padlock; the hi-vis vest hung over the fence rail on our side; gumboots by the post; a flattened patch where the digger stood; the timber gone grey under a torn cover; the frame no further on; grass along the fence; a grey overcast late afternoon.",
 'K1': "The letter from the bank propped against a mug, facing us (own surface: an invented bank's name, Your home loan, Your new interest rate; no figures); its torn envelope under it; reading glasses folded on it; a phone face down; across the table the chair pushed back at an angle with a cardigan over it; the dark window behind (garden, a neighbour's lit window). The pendant lamp is above the frame, its light pooled on the letter.",
 'G1': "The grocer's splayed corner window, its tiered display thinning out (gaps between stocked stands, a half-empty tier, labelled tins TEA, COCOA, SYRUP), an empty wicker basket at the stand's foot, a slumped flour sack by the door frame, the brass till in the gas light; a text-only recruiting poster on the pilaster beside the window, overlapping its frame, a gas lamp above it. Up the street, about 14 small walkers far off (40 to 80 m) heading for the munitions works' lit, smoking gate.",
 'G2': "The factor's notice on the pilaster at the close's edge, face-on (own surface); directly below it on the step a suitcase with a blanket bundle tied on top; the close's gas bracket just inside the arch, lighting the notice from the side and below; the facing tenement's windows (own glass, so they can light and take placards); on the quiet side, the half-built tenement with scaffold poles.",
}

# frame kinds: 'plain' = held, nothing live; 'fx' = held with live smoke, flames or flicker
shots = []
def shot(page, sid, view, start, end, subject, beats, cards, effects, kind, move='none', move_secs=0.0, first_paint=0):
    shots.append(dict(page=page, shot=sid, place=PLACE[view], view=view, camera=CAM[view], subject=subject,
                      story_props=STORY[view], move=move, beats=[dict(word=w, event=e) for w, e in beats],
                      cards=[dict(text=t, where=p) for t, p in cards], effects=effects,
                      paintings=PAINTINGS[view], paintings_first_needed_here=first_paint,
                      start=round(start, 2), end=round(end, 2), seconds=round(end - start, 1),
                      _kind=kind, _move=move_secs))

TOP = "top band (about 0.05 to 0.22 down), left-aligned from 0.06 across, kept left of 0.90"
TOP2 = "top band, second line under the first"
SMALL = "small line under the card above"
CREDIT = "small credit, left, about 0.75 down (above the strip where phone apps show captions)"
PANEL = "100-dot panel in the top band, left, 0.06 to 0.45 across"

# ---------------------------------------------------------------- page 1
shot(1, '1a', 'C1', 0.0, 28.08, "The basket at the checkout, with the newspaper bill's warning beside it",
 [("felt (1.4 s)", "the picture fades up from dark"),
  ("same (3.4 s)", "the slide starts: 0.7 m toward the basket"),
  ("inflation (7.3 s)", "the slide stops on the composed frame; INFLATION"),
  ("general (8.9 s)", "PRICES IN GENERAL, GOING UP under it"),
  ("whole (10.8 s)", "small up-arrow tags spring up beside every item at once (arrows only, no prices)"),
  ("warning (12.8 s)", "the tags fold away; the label THE WARNING with a thin line to the newspaper bill, whose own lettering reads NEW MONEY: PRICES WILL GO UP"),
  ("always (17.7 s)", "IS THAT ALWAYS TRUE?"),
  ("cure (22.4 s)", "THE USUAL CURE"),
  ("loans (23.3 s)", "→ MANY LOANS COST MORE"),
  ("out (25.9 s)", "→ OUT OF WORK"),
  ("(27.2 s)", "page peel")],
 [("INFLATION", TOP), ("PRICES IN GENERAL, GOING UP", SMALL),
  ("THE WARNING", "label with a thin line to the newspaper bill"),
  ("IS THAT ALWAYS TRUE?", TOP),
  ("THE USUAL CURE → MANY LOANS COST MORE → OUT OF WORK", TOP + "; builds word by word")],
 [], 'plain', move="one slide of 0.7 m toward the basket (3.1 m to 2.4 m), from 'same' to 'inflation'. Why: we step up to our own basket.", move_secs=3.9, first_paint=2)

# ---------------------------------------------------------------- page 2
shot(2, '2a', 'S1a', 28.08, 47.72, "Workers, materials and machines: the three things touching just inside the open gate",
 [("Reserve (31.6 s)", "THE RESERVE BANK (typed, no logo)"),
  ("can (2) (32.3 s)", "CAN CREATE NEW MONEY under it"),
  ("economists (36.5 s)", "the Reserve Bank card clears; ECONOMISTS WHO STUDY HOW MODERN MONEY WORKS"),
  ("argue (39.6 s)", "ARGUE: is added"),
  ("money (3) (42.2 s)", "OUR GOVERNMENT CAN'T RUN OUT OF ITS OWN MONEY"),
  ("But (43.0 s)", "BUT IT CAN RUN OUT OF..."),
  ("workers (44.2 s)", "label WORKERS with a thin line to the vest and hard hat"),
  ("materials (45.0 s)", "label MATERIALS to the timber"),
  ("machines (45.7 s)", "label MACHINES to the digger")],
 [("THE RESERVE BANK", TOP), ("CAN CREATE NEW MONEY", SMALL),
  ("ECONOMISTS WHO STUDY HOW MODERN MONEY WORKS ARGUE:", TOP + " (smaller heading)"),
  ("OUR GOVERNMENT CAN'T RUN OUT OF ITS OWN MONEY", TOP2),
  ("BUT IT CAN RUN OUT OF...", TOP2 + ", replacing the line above"),
  ("WORKERS", "label → the vest and hard hat"), ("MATERIALS", "label → the timber"), ("MACHINES", "label → the digger")],
 [], 'plain', first_paint=2)

# ---------------------------------------------------------------- page 3
shot(3, '3a', 'W3', 47.72, 55.1, "The two factories side by side, each its own column",
 [("Picture (48.1 s)", "PICTURE TWO FACTORIES"),
  ("country (51.3 s)", "EACH ONE = A WHOLE COUNTRY (held to the cut)"),
  ("workers (1) (52.7 s)", "label WORKERS → No. 1's queue"),
  ("materials (53.4 s)", "label MATERIALS → the crates at No. 2's gate"),
  ("machines (1) (54.1 s)", "label MACHINES → No. 2's lit sheds")],
 [("PICTURE TWO FACTORIES", TOP), ("EACH ONE = A WHOLE COUNTRY", TOP2),
  ("WORKERS", "label → No. 1's queue"), ("MATERIALS", "label → the crates at No. 2's gate"), ("MACHINES", "label → No. 2's lit sheds")],
 ["No. 2's smoke from both chimneys", "No. 2's window flicker", "No. 1's brazier flames and glow", "the lantern's flicker"], 'fx', first_paint=1)
shot(3, '3b', 'W1', 55.1, 75.13, "The shut No. 1 gate at the head of the queue",
 [("In (55.1 s)", "cut in: windows dark, chimney cold, gate shut and chained, 7 men waiting, the brazier burning"),
  ("Workers (2) (57.9 s)", "the slide starts: 1.2 m along the queue toward the gate"),
  ("Call (61.0 s)", "the slide stops on the composed frame"),
  ("quiet (61.6 s)", "THE QUIET FACTORY"),
  ("spends (63.9 s)", "NEW MONEY SPENT, with a small arrow into the gate"),
  ("go (67.2 s)", "a cut within the held shot: the gate stands open, the men are gone, the brazier still burns by the empty pier, the lunch tin stays on the coping (fallback: the gate swings open in 0.8 s and the men fade in 1.2 s inside the swing)"),
  ("start (68.7 s)", "No. 1's windows light (a 0.8 s blend to the lit picture) and its chimney starts to smoke"),
  ("More (1) (69.5 s)", "MORE MONEY"),
  ("things (71.2 s)", "+ MORE THINGS TO BUY, as crates stencilled THIS WAY UP pop up stacked inside the open gateway"),
  ("barely (72.9 s)", "a price arrow over No. 1 that stays level: → PRICES BARELY MOVE"),
  ("(74.3 s)", "page peel")],
 [("THE QUIET FACTORY", TOP + "; stays as the page's tag"), ("NEW MONEY SPENT", TOP2 + ", with a small arrow into the gate"),
  ("MORE MONEY + MORE THINGS TO BUY → PRICES BARELY MOVE", TOP2 + "; builds in three steps, the arrow level over No. 1's column")],
 ["the brazier's flames, glow and a little smoke", "the lantern's flicker", "after 'start': chimney smoke at the top of the frame and a faint window flicker"],
 'fx', move="one slide of 1.2 m along the queue toward the gate, from 'Workers' (2) to 'Call'. Why: we join the line.", move_secs=3.1, first_paint=2)

# ---------------------------------------------------------------- page 4
shot(4, '4a', 'W2', 75.13, 95.70, "The open No. 2 gate with nobody waiting",
 [("In (75.5 s)", "flat out: the gate wide open, windows blazing, both chimneys smoking hard, the empty pavement lit by the gateway"),
  ("busy (79.2 s)", "the windows flicker brighter"),
  ("No (82.0 s)", "the slide starts: 1.2 m toward the gate, with nobody in the way"),
  ("flat-out (84.5 s)", "THE FLAT-OUT FACTORY, with a small line under it: FLAT OUT = WORKING AS HARD AS THEY CAN"),
  ("factory (2) (84.9 s)", "the slide stops on the composed frame"),
  ("spent (87.0 s)", "NEW MONEY SPENT (the same words as page 3)"),
  ("prices (90.0 s)", "WHAT HAPPENS TO PRICES?"),
  ("guess (91.0 s)", "HAVE A GUESS, with a ring that fills over 4 seconds"),
  ("(91.8 to 95.7 s)", "the 4-second guess hold on the still frame, music up; page 5 runs on with no join")],
 [("THE FLAT-OUT FACTORY", TOP), ("FLAT OUT = WORKING AS HARD AS THEY CAN", SMALL),
  ("NEW MONEY SPENT", TOP2), ("WHAT HAPPENS TO PRICES?", TOP), ("HAVE A GUESS", SMALL + ", with the ring")],
 ["heavy smoke from both chimneys", "window flicker", "the gate lamp's glow"],
 'fx', move="one slide of 1.2 m toward the gate, from 'No' to 'factory' (2). Why: we walk up to the gate with nobody in the way, from where W1's camera stood, mirrored.", move_secs=2.9, first_paint=3)

# ---------------------------------------------------------------- page 5
shot(5, '5a', 'W2', 95.70, 107.1, "The flat-out gate, the composed frame",
 [("spare (1) (95.9 s)", "the question and ring clear; NO SPARE"),
  ("More (100.7 s)", "MORE MONEY"),
  ("same (102.2 s)", "+ SAME THINGS TO BUY (the crates in the gateway stay as they are)"),
  ("up (1) (106.5 s)", "a price arrow over No. 2 climbs: → PRICES UP")],
 [("NO SPARE", TOP), ("MORE MONEY + SAME THINGS TO BUY → PRICES UP", TOP2 + "; same layout as page 3's line")],
 ["as page 4"], 'fx')
shot(5, '5b', 'W3', 107.1, 123.46, "Both factories, with the rule over them",
 [("Most (107.1 s)", "cut; the small name tags QUIET and FLAT OUT appear over the two columns (they come back on every return to W3)"),
  ("agree (108.0 s)", "MOST ECONOMISTS AGREE"),
  ("spent (110.4 s)", "upper rule card: NEW MONEY SPENT"),
  ("spare (2) (112.1 s)", "+ SPARE"),
  ("made (2) (116.3 s)", "→ MOSTLY MORE THINGS MADE, with a thin line down to No. 1's chimney"),
  ("nothing (117.3 s)", "lower rule card: NOTHING SPARE"),
  ("up (2) (120.0 s)", "→ MOSTLY PRICES UP, with a thin line down to No. 2's chimneys"),
  ("(120.6 to 122.6 s)", "the 2-second rule hold, music up; then the page peel")],
 [("QUIET", "small tag over No. 1's column"), ("FLAT OUT", "small tag over No. 2's column"),
  ("MOST ECONOMISTS AGREE", "small, top band, above the rule cards"),
  ("NEW MONEY SPENT + SPARE → MOSTLY MORE THINGS MADE", "upper rule card, 0.06 to 0.90 across, about 0.07 to 0.15 down, over a soft dark band; thin line to No. 1's chimney"),
  ("NOTHING SPARE → MOSTLY PRICES UP", "lower rule card, 0.06 to 0.90 across, about 0.16 to 0.24 down; thin line to No. 2's chimneys")],
 ["No. 2's smoke", "No. 2's window flicker", "No. 1's brazier and lantern"], 'fx')

# ---------------------------------------------------------------- page 6
shot(6, '6a', 'G1', 123.46, 146.4, "The grocer's thinning window and the recruiting poster, with the munitions works' gate where the lines meet",
 [("real (124.4 s)", "A REAL CASE"),
  ("Britain (1) (125.5 s)", "BRITAIN, FIRST WORLD WAR"),
  ("fewer (1) (130.4 s)", "the 100-dot panel, every dot lit but the last, which is nearly empty: FEWER THAN 1 IN 100 OUT OF WORK"),
  ("More (140.1 s)", "MORE MONEY"),
  ("fewer (2) (141.4 s)", "+ FEWER THINGS TO BUY; the slide starts: 1.2 m toward the grocer's window"),
  ("doubled (145.5 s)", "the slide stops; two bars, BEFORE THE WAR and END OF THE WAR: ROUGHLY ×2")],
 [("A REAL CASE", TOP), ("BRITAIN, FIRST WORLD WAR", TOP2 + " (place title)"),
  ("FEWER THAN 1 IN 100 OUT OF WORK", PANEL),
  ("MORE MONEY + FEWER THINGS TO BUY", TOP2 + "; same layout as pages 3 and 5"),
  ("PRICES: BEFORE THE WAR / END OF THE WAR: ROUGHLY ×2", "two bars in the top band, left")],
 ["the works' smoke far off", "the gas lamps' faint flicker"],
 'fx', move="one slide of 1.2 m toward the grocer's window, from 'fewer' (2) to 'doubled'. Why: we step up to the thinning shelves on 'fewer things to buy'.", move_secs=4.1, first_paint=2)
shot(6, '6b', 'W2', 146.4, 150.50, "The flat-out gate, the composed frame",
 [("Britain (2) (146.4 s)", "cut to W2, flat out; the tag FLAT OUT"),
  ("close (147.4 s)", "CLOSE TO THE FLAT-OUT FACTORY")],
 [("FLAT OUT", "small tag over the gate's column"), ("CLOSE TO THE FLAT-OUT FACTORY", TOP)],
 ["as page 4"], 'fx')

# ---------------------------------------------------------------- page 7
shot(7, '7a', 'G1', 150.50, 154.9, "The street to the works, from the plate's spot",
 [("fifteen (151.5 s)", "GLASGOW 1915"),
  ("crowds (152.2 s)", "label CROWDS OF WAR WORKERS with a thin line to the walkers (or to the works' gate, if the walkers are dropped)")],
 [("GLASGOW 1915", TOP + " (place title)"), ("CROWDS OF WAR WORKERS", "label → the walkers")],
 ["the works' smoke", "the gas lamps' faint flicker"], 'fx')
shot(7, '7b', 'G2', 154.9, 183.48, "The factor's notice at the close mouth, the suitcase on the step below it",
 [("There (154.9 s)", "cut to the close mouth; the tenement windows dark"),
  ("homes (1) (156.4 s)", "the windows light in a quick ripple from the close outward, in 12 steps over 1.5 s: every home full; TOO FEW HOMES ALREADY"),
  ("built (160.8 s)", "label FEW NEW HOMES BUILT → the half-built tenement"),
  ("factory (166.8 s)", "FOR HOMES: LIKE THE FLAT-OUT FACTORY (the lit windows rhyme with No. 2's)"),
  ("Landlords (167.7 s)", "the slide starts: 1.5 m toward the notice"),
  ("rent (168.8 s)", "RENT RAISED"),
  ("quarter (170.8 s)", "the slide stops; UP TO A QUARTER MORE, IN PLACES"),
  ("twenty (172.9 s)", "ABOUT 20,000 FAMILIES REFUSING THE EXTRA lands whole"),
  ("refusing (174.5 s)", "placards appear in the lit windows one by one over 3 s (own surfaces, in steps)"),
  ("back (179.9 s)", "a typed stamp RENTS ON SMALL HOMES BACK TO BEFORE THE WAR, landing on 'war' (3) (181.7 s)"),
  ("(182.6 s)", "page peel")],
 [("TOO FEW HOMES ALREADY", TOP), ("FEW NEW HOMES BUILT", "label → the half-built tenement"),
  ("FOR HOMES: LIKE THE FLAT-OUT FACTORY", TOP), ("RENT RAISED: UP TO A QUARTER MORE, IN PLACES", TOP2),
  ("ABOUT 20,000 FAMILIES REFUSING THE EXTRA", TOP + ", replacing the cards above"),
  ("RENTS ON SMALL HOMES BACK TO BEFORE THE WAR", "a typed stamp across the middle of the top band")],
 ["the gas lamps' and the close bracket's faint flicker"],
 'fx', move="one slide of 1.5 m toward the notice, from 'Landlords' to 'quarter'. Why: we step up to the notice that turns too few homes into higher rent.", move_secs=3.1, first_paint=2)

# ---------------------------------------------------------------- page 8
shot(8, '8a', 'J1', 183.48, 201.82, "Another country's basket at another checkout",
 [("thirteen (184.8 s)", "JAPAN 2013"),
  ("version (186.2 s)", "a small heading, JAPAN'S VERSION OF OUR RESERVE BANK, ends in a colon"),
  ("double (188.2 s)", "×2 MONEY"),
  ("years (190.8 s)", "IN TWO YEARS"),
  ("warning (192.0 s)", "a small chart: a dashed line climbs steeply, IF THE WARNING IS RIGHT"),
  ("happened (196.0 s)", "WHAT HAPPENED?"),
  ("guess (197.1 s)", "HAVE A GUESS and its ring"),
  ("(197.9 to 201.8 s)", "the 4-second guess hold; page 9 runs on with no join")],
 [("JAPAN 2013", TOP + " (place title)"), ("JAPAN'S VERSION OF OUR RESERVE BANK: ×2 MONEY IN TWO YEARS", TOP2),
  ("IF THE WARNING IS RIGHT", "on the dashed line of a small chart in the top band"),
  ("WHAT HAPPENED?", TOP), ("HAVE A GUESS", SMALL + ", with the ring")],
 [], 'plain', first_paint=1)

# ---------------------------------------------------------------- page 9
shot(9, '9a', 'J1', 201.82, 214.0, "The same frame; the answer lands on the chart",
 [("barely (202.2 s)", "a real line runs almost level beside the dashed one: PRICES BARELY MOVED"),
  ("eight (204.0 s)", "FOR ABOUT 8 YEARS, along the chart's span"),
  ("half (207.1 s)", "ABOUT ½% A YEAR, ON AVERAGE, on the line"),
  ("banks (213.2 s)", "label ONE REASON: MOST SAT IN THE BANKS, with a thin line to the bank across the street (fallback: cut to 9b on 'most' (1), 211.2 s)")],
 [("PRICES BARELY MOVED", "chart title in the top band"), ("FOR ABOUT 8 YEARS", "along the chart's span"),
  ("ABOUT ½% A YEAR, ON AVERAGE", "on the chart's line"),
  ("ONE REASON: MOST SAT IN THE BANKS", "label → the bank across the street")],
 [], 'plain')
shot(9, '9b', 'W3', 214.0, 230.23, "Both factories, untouched; the lit bank in the lane",
 [("In (214.0 s)", "cut to W3; tags QUIET and FLAT OUT"),
  ("picture (214.4 s)", "IN OUR PICTURE"),
  ("most (2) (215.1 s)", "the bank's window lights from inside (1 s, its own glass) with a soft pool of light on the pavement; a tag NEW MONEY lands on the window"),
  ("never (215.7 s)", "a dotted line runs from the bank up the lane toward the gates and stops halfway: NEVER REACHED THE FACTORY. Both gates stay as they are, so the picture doesn't say which factory Japan was like"),
  ("much (218.7 s)", "NOT JUST HOW MUCH"),
  ("whether (220.7 s)", "→ WHETHER IT'S SPENT, AND ON WHAT"),
  ("spare (223.8 s)", "SPARE WORKERS, MATERIALS, MACHINES TO MAKE WHAT IT BUYS? replaces the cards"),
  ("(227.4 to 229.4 s)", "that card held 2 seconds, then the page peel")],
 [("IN OUR PICTURE", TOP + " (small)"), ("NEW MONEY", "tag on the bank's lit window"),
  ("NEVER REACHED THE FACTORY", "at the dotted line's end, halfway up the lane"),
  ("NOT JUST HOW MUCH → WHETHER IT'S SPENT, AND ON WHAT", TOP2),
  ("SPARE WORKERS, MATERIALS, MACHINES TO MAKE WHAT IT BUYS?", TOP + ", replacing the cards above")],
 ["No. 2's smoke and window flicker", "No. 1's brazier and lantern", "the bank window's own light"], 'fx')

# ---------------------------------------------------------------- page 10
shot(10, '10a', 'S1a', 230.23, 248.5, "The busy site in 2020, the sanitise sign on the gate",
 [("here (231.4 s)", "NEW ZEALAND"),
  ("twenty (2) (233.5 s)", "2020 joins it"),
  ("money (235.7 s)", "NEW MONEY"),
  ("government (237.0 s)", "+ GOVERNMENT SPENT MORE"),
  ("twenty-one (241.8 s)", "the 100-dot panel appears, headed END OF 2021"),
  ("three (246.1 s)", "three dots empty: ABOUT 3 IN 100 OUT OF WORK, with the small credit STATS NZ")],
 [("NEW ZEALAND 2020", TOP + " (place title)"), ("NEW MONEY + GOVERNMENT SPENT MORE", TOP2),
  ("END OF 2021: ABOUT 3 IN 100 OUT OF WORK", PANEL), ("STATS NZ", CREDIT)],
 [], 'plain')
shot(10, '10b', 'W3', 248.5, 255.96, "Both factories: which one?",
 [("Which (248.5 s)", "cut to W3: WHICH ONE? with a small arrow to each gate; tags QUIET and FLAT OUT; the dot panel carried over, small, beside the question"),
  ("guess (251.2 s)", "HAVE A GUESS and its ring"),
  ("(252.0 to 255.9 s)", "the 4-second guess hold; a plain cut to page 11 on 'Close'")],
 [("WHICH ONE?", TOP + ", with a small arrow to each gate"), ("ABOUT 3 IN 100 OUT OF WORK", "the dot panel, small, top band right of the question, left of 0.90"),
  ("HAVE A GUESS", SMALL + ", with the ring")],
 ["as 3a"], 'fx')

# ---------------------------------------------------------------- page 11
shot(11, '11a', 'W2', 255.96, 268.3, "The flat-out gate: the answer",
 [("Close (256.0 s)", "plain cut from the guess; CLOSE TO THE FLAT-OUT FACTORY; tag FLAT OUT"),
  ("prices (1) (260.7 s)", "PRICES WENT UP FAST, a price arrow climbing over No. 2"),
  ("Partly (262.5 s)", "PARTLY: MORE SPENT"),
  ("partly (2) (265.2 s)", "PARTLY: PRICES OVERSEAS, LIKE OIL, with a thin line to the PETROL and DIESEL drums by the gate")],
 [("CLOSE TO THE FLAT-OUT FACTORY", TOP), ("PRICES WENT UP FAST:", TOP + ", replacing it"),
  ("PARTLY: MORE SPENT", TOP2), ("PARTLY: PRICES OVERSEAS, LIKE OIL", TOP2 + "; thin line to the drums")],
 ["as page 4"], 'fx')
shot(11, '11b', 'S1a', 268.3, 275.00, "The house frame going up",
 [("At (268.3 s)", "cut to the busy site"),
  ("peak (268.6 s)", "the slide starts: 1.2 m through the gate toward the house frame; AT THE PEAK, ending in a colon"),
  ("building (271.4 s)", "THE PRICE OF BUILDING NEW HOMES"),
  ("homes (272.0 s)", "the slide stops"),
  ("rents (273.1 s)", "AND RENTS, as the FOR RENT board appears on the neighbour's fence (the camera has stopped)"),
  ("(274.2 s)", "page peel")],
 [("AT THE PEAK: THE PRICE OF BUILDING NEW HOMES... AND RENTS", TOP + "; builds in three steps, never BUILDING NEW HOMES on its own")],
 [], 'plain', move="one slide of 1.2 m through the gate toward the house frame, from 'peak' to 'homes'. Why: it lands on the price of building new homes, the homes the viewer saw going up on page 2.", move_secs=3.4)

# ---------------------------------------------------------------- page 12
shot(12, '12a', 'K1', 275.00, 294.8, "The letter about the home loan",
 [("cure (276.4 s)", "THE USUAL CURE"),
  ("raises (277.8 s)", "a dial in the dark window under it, INTEREST RATE, its needle rising (no figures)"),
  ("Interest (2) (279.6 s)", "INTEREST = THE EXTRA YOU PAY BACK WHEN YOU BORROW"),
  ("Many (282.8 s)", "the slide starts: 0.43 m toward the letter"),
  ("loans (283.0 s)", "MANY LOANS COST MORE"),
  ("spend (285.7 s)", "the slide stops; → LESS TO SPEND"),
  ("sell (287.0 s)", "→ SELL FEWER THINGS"),
  ("hire (288.5 s)", "→ HIRE FEWER PEOPLE"),
  ("slowly (1) (291.1 s)", "the chain clears: PRICES GO UP MORE SLOWLY"),
  ("down (292.6 s)", "USUALLY NOT DOWN")],
 [("THE USUAL CURE", TOP), ("INTEREST RATE", "label on the dial drawn in the dark window"),
  ("INTEREST = THE EXTRA YOU PAY BACK WHEN YOU BORROW", TOP2),
  ("MANY LOANS COST MORE → LESS TO SPEND → SELL FEWER THINGS → HIRE FEWER PEOPLE", TOP + "; builds as a chain"),
  ("PRICES GO UP MORE SLOWLY. USUALLY NOT DOWN", TOP + ", replacing the chain")],
 [], 'plain', move="one slide of 0.43 m toward the letter (1.85 m to 1.42 m), from 'Many' to 'spend'. Why: we lean in to the letter on 'Many loans cost more'.", move_secs=2.9, first_paint=2)
shot(12, '12b', 'W2', 294.8, 301.25, "The flat-out factory slows and the queue returns",
 [("In (294.8 s)", "cut to W2, flat out; tag FLAT OUT"),
  ("picture (295.2 s)", "IN OUR PICTURE"),
  ("slows (297.0 s)", "the tag becomes THE FLAT-OUT FACTORY SLOWS; two thirds of the windows dim (a 1.5 s blend to the slowed picture), the smoke thins to one chimney, the gate leaf swings half shut (own surface)"),
  ("workers (298.4 s)", "a cut within the held shot: 8 men wait along the pavement (fallback: a 1.2 s fade)"),
  ("gate (299.4 s)", "MORE WORKERS AT THE GATE"),
  ("(300.4 s)", "page peel")],
 [("IN OUR PICTURE", TOP + " (small)"), ("THE FLAT-OUT FACTORY SLOWS", "the tag over the gate's column, replacing FLAT OUT"),
  ("MORE WORKERS AT THE GATE", TOP2)],
 ["smoke (thinning on 'slows')", "window flicker (dimming)"], 'fx')

# ---------------------------------------------------------------- page 13
shot(13, '13a', 'K1', 301.25, 311.2, "The letter, the composed frame",
 [("pays (1) (301.8 s)", "WHO PAYS FOR THE CURE?"),
  ("From (303.0 s)", "the dial returns in the window, its needle stepping up again and again"),
  ("twenty-one (303.9 s)", "LATE 2021 under the dial"),
  ("twenty-three (305.1 s)", "→ 2023")],
 [("WHO PAYS FOR THE CURE?", TOP), ("LATE 2021 → 2023", "caption under the dial in the window")],
 [], 'plain')
shot(13, '13b', 'S1b', 311.2, 324.2, "The same site, stopped",
 [("jobs (311.2 s)", "cut to the stopped site"),
  ("middle (313.4 s)", "the dot panel returns, headed MIDDLE OF 2026"),
  ("six (315.7 s)", "nearly six dots empty: NEARLY 6 IN 100 OUT OF WORK, with the credit STATS NZ"),
  ("three (318.7 s)", "three dots outlined faintly: UP FROM ABOUT 3"),
  ("only (321.0 s)", "small NOT THE ONLY REASON (it stays on through 13d)"),
  ("pays (2) (323.0 s)", "WHO PAYS?")],
 [("MIDDLE OF 2026: NEARLY 6 IN 100 OUT OF WORK", PANEL), ("UP FROM ABOUT 3", "faint, on the panel"),
  ("STATS NZ", CREDIT), ("NOT THE ONLY REASON", "small, under the panel"), ("WHO PAYS?", TOP)],
 [], 'plain', first_paint=1)
shot(13, '13c', 'K1', 324.2, 325.9, "The letter",
 [("Many (2) (324.2 s)", "cut to the letter"), ("loans (2) (325.1 s)", "MANY PEOPLE WITH LOANS under WHO PAYS?")],
 [("MANY PEOPLE WITH LOANS", TOP2)], [], 'plain')
shot(13, '13d', 'S1b', 325.9, 328.95, "The stopped site",
 [("and (3) (325.9 s)", "cut to the stopped site; NOT THE ONLY REASON stays"),
  ("put (326.5 s)", "...AND PEOPLE PUT OUT OF WORK"), ("(328.1 s)", "page peel")],
 [("AND PEOPLE PUT OUT OF WORK", "under MANY PEOPLE WITH LOANS"), ("NOT THE ONLY REASON", "small, stays")],
 [], 'plain')

# ---------------------------------------------------------------- page 14
shot(14, '14a', 'W4', 328.95, 352.93, "Someone with a job, and the men waiting outside the gate",
 [("America's (329.3 s)", "heading AMERICA'S VERSION OF OUR RESERVE BANK:, with the small credit US FEDERAL RESERVE"),
  ("jobs (1) (333.5 s)", "PROBABLY FEWER JOBS"),
  ("unfortunate (335.2 s)", "UNFORTUNATE, appears under it"),
  ("goal (1) (337.0 s)", "BUT NOT THE GOAL (no quotation marks)"),
  ("Clara (337.7 s)", "the typed name card CLARA E. MATTEI comes in below the American block, with the small credit THE CAPITAL ORDER (no portrait, no book cover, no year)"),
  ("Mattei (338.7 s)", "the American block (heading and its two cards) clears at about 339.5 s; the name card stays"),
  ("argues (342.2 s)", "MATTEI ARGUES: heads her block"),
  ("goal (2) (344.5 s)", "FEWER JOBS ARE THE MAIN GOAL"),
  ("With (345.2 s)", "the slide starts: 1.2 m toward the gate and the queue"),
  ("says (347.8 s)", "the slide stops"),
  ("power (349.8 s)", "LESS POWER TO ASK FOR HIGHER WAGES, under MATTEI ARGUES, which stays to the page's end"),
  ("(352.1 s)", "page peel")],
 [("AMERICA'S VERSION OF OUR RESERVE BANK:", TOP + " (heading)"), ("US FEDERAL RESERVE", CREDIT),
  ("PROBABLY FEWER JOBS", TOP2), ("UNFORTUNATE, BUT NOT THE GOAL", "under PROBABLY FEWER JOBS"),
  ("CLARA E. MATTEI", "typed name card below the American block, about 0.25 down"), ("THE CAPITAL ORDER", CREDIT),
  ("MATTEI ARGUES:", TOP + " (heading, replacing the American one)"), ("FEWER JOBS ARE THE MAIN GOAL", TOP2),
  ("LESS POWER TO ASK FOR HIGHER WAGES", "under FEWER JOBS ARE THE MAIN GOAL")],
 ["the lane's gas lamps glowing, a faint flicker"],
 'fx', move="one slide of 1.2 m toward the gate, from 'With' to 'says'. Why: we move closer to the queue on 'with more workers waiting at the gate'.", move_secs=2.6, first_paint=2)

# ---------------------------------------------------------------- page 15
shot(15, '15a', 'C1', 352.93, 367.4, "The basket again: a hundred dollars",
 [("dollars (356.2 s)", "a tag beside the basket: $100"),
  ("twenty-five (357.4 s)", ", JUNE 2025 joins it"),
  ("later (358.9 s)", "it flips to ABOUT $104, A YEAR LATER"),
  ("three (366.6 s)", "a ghost tag beside it: ABOUT $103 IF PETROL AND DIESEL PRICES HADN'T CHANGED, with the credit STATS NZ")],
 [("$100, JUNE 2025 → ABOUT $104, A YEAR LATER", "price tag beside the basket"),
  ("ABOUT $103 IF PETROL AND DIESEL PRICES HADN'T CHANGED", "ghost tag beside the first"), ("STATS NZ", CREDIT)],
 [], 'plain')
shot(15, '15b', 'W3', 367.4, 374.3, "Both factories, petrol and diesel at both gates",
 [("When (367.4 s)", "cut to W3; tags QUIET and FLAT OUT"),
  ("petrol (2) (367.7 s)", "labels with thin lines to the drums at both gates: PETROL AND DIESEL"),
  ("both (373.0 s)", "a price arrow climbs over each factory: IN BOTH FACTORIES")],
 [("PETROL AND DIESEL", "labels → the drums at both gates"), ("IN BOTH FACTORIES", TOP + ", with an arrow climbing over each column")],
 ["as 3a"], 'fx')
shot(15, '15c', 'C1', 374.3, 379.49, "The basket",
 [("So (374.3 s)", "cut back to the basket"), ("part (374.4 s)", "PART OF IT: PETROL AND DIESEL (never 'mostly')"), ("(378.6 s)", "page peel")],
 [("PART OF IT: PETROL AND DIESEL", TOP)], [], 'plain')

# ---------------------------------------------------------------- page 16
shot(16, '16a', 'W3', 379.49, 393.9, "Both factories, the rule again",
 [("always (380.6 s)", "DOES NEW MONEY ALWAYS PUSH PRICES UP?"),
  ("No (382.1 s)", "NO."),
  ("spent (1) (383.7 s)", "page 5's upper rule card, the same words in the same place: NEW MONEY SPENT"),
  ("spare (1) (385.3 s)", "+ SPARE"),
  ("made (389.5 s)", "→ MOSTLY MORE THINGS MADE"),
  ("nothing (390.6 s)", "lower card: NOTHING SPARE"),
  ("up (2) (393.3 s)", "→ MOSTLY PRICES UP")],
 [("DOES NEW MONEY ALWAYS PUSH PRICES UP? NO.", TOP + ", cleared at 'spent' for the rule cards"),
  ("NEW MONEY SPENT + SPARE → MOSTLY MORE THINGS MADE", "upper rule card, exactly as page 5"),
  ("NOTHING SPARE → MOSTLY PRICES UP", "lower rule card, exactly as page 5")],
 ["as 3a"], 'fx')
shot(16, '16b', 'C1', 393.9, 406.94, "The basket and the warning, stepping back",
 [("So (393.9 s)", "cut to the basket at the composed frame"),
  ("next (394.1 s)", "the slide starts: 0.7 m back from the basket to the plate's spot, the reverse of page 1 (stops about 397.3 s)"),
  ("warning (395.3 s)", "the label THE WARNING to the newspaper bill again, as on page 1"),
  ("Spent (2) (397.7 s)", "SPENT ON WHAT?"),
  ("anything (399.2 s)", "ANYTHING SPARE TO MAKE WHAT IT BUYS? in a small line under it"),
  ("pays (401.8 s)", "WHO PAYS FOR THE CURE?"),
  ("(402.9 to 406.9 s)", "both held; the 4-second fade to dark")],
 [("THE WARNING", "label → the newspaper bill"), ("SPENT ON WHAT?", TOP), ("ANYTHING SPARE TO MAKE WHAT IT BUYS?", SMALL),
  ("WHO PAYS FOR THE CURE?", TOP2)],
 [], 'plain', move="one slide of 0.7 m back from the basket to the plate's spot, from 'next' to about 397.3 s. Why: stepping back as the two questions land; the bill stays in frame.", move_secs=3.2)

# -------------------------------------------------------------- numbers
joins = 12 * 0.85            # page peels: both pages drawn
frames = {'plain': 0, 'fx': 0, 'moving': 0}
for s in shots:
    held = (s['end'] - s['start']) - s['_move']
    frames[s['_kind']] += held * FPS
    frames['moving'] += s['_move'] * FPS
turn_frames = joins * FPS
total = sum(frames.values())
print('shots', len(shots), 'slides', sum(1 for s in shots if s['move'] != 'none'))
print({k: round(v) for k, v in frames.items()}, 'page-turn frames (inside the above, drawn twice):', round(turn_frames), 'total', round(total))
print('paintings first needed (sum):', sum(s['paintings_first_needed_here'] for s in shots))
# filming time: held stretches two at a time, moving stretches one at a time (measured, critic-feasibility)
low = (frames['plain'] * 0.57 + frames['fx'] * 1.05 + frames['moving'] * 5.6 + turn_frames * 1.05) / 3600
high = (frames['plain'] * 0.8 + frames['fx'] * 1.5 + frames['moving'] * 7.0 + turn_frames * 1.5) / 3600
print('filming hours (12,208 frames): %.1f to %.1f, plus loading' % (low, high))
scale = 13000 / total
print('at 13,000 frames: %.1f to %.1f' % (low * scale, high * scale))
for s in shots:
    s.pop('_kind'); s.pop('_move')
json.dump(shots, open(OUT, 'w'), indent=1, ensure_ascii=False)
print('wrote', os.path.abspath(OUT))
