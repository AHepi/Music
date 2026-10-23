# Painting prompts

**What this is:** how the paintings for the paper pop-up look were asked for, word for word, so a new series
matches. Model: fal `blackforestlabs/flux-3/text-to-image`, `output_format` png. Every prompt is one
subject sentence followed by the same style words. The full prompt of every painting, with its request id,
is in `assets/paintings/austerity-chapter-1/paintings.json`.

## A concrete example first

The cut-out of the iron weight that squashes the pay packet on page 1 was asked for as one sentence about
the object, then the object style words below, at aspect 1:1 and resolution 1k (about 2.5 US cents).
Its exact prompt is the `prompt` of `303-iron-weight.jpg` in `paintings.json`.

## The style words (use them exactly)

**Backgrounds** (aspect 9:16, resolution 2k = 1536 x 2736, about 10 US cents). Subject sentence: the place, the year,
"seen at standing eye level", what is in it, then "The lower quarter of the picture is the empty floor/street. No people." Then:

> Painterly 2D digital illustration, the look of a modern animated history documentary: semi-realistic with slightly stylised, expressive proportions, visible confident brush strokes, rich detail, cinematic lighting. Restrained palette: deep teal-blue shadows, cold blue-grey midtones, warm amber lamplight, with only small touches of dull brick red. Tense, uneasy mood. Absolutely no text, letters, numbers, logos, emblems or symbols anywhere.

The empty lower quarter is for the paper route only: cut-out pieces stand in it. A place built in Blender and painted
over is never asked for an empty lower part: its nearest story thing reaches about 0.70 down the frame and the bottom
third is not bare floor (`07 Composing a shot.md`, rule 7). Measured on chapter 2: in about 70 percent of frames the
bottom fifth was over 30 percent darker than the middle, and the review traced it to this sentence. The painter's
prompt for a built place comes from `calculators/paint_request.py`, not from this page.

**Figures and groups** (aspect 21:9 = 3136 x 1344 for groups, 4:5 = 1824 x 2288 for one figure; 2k; about 10 US cents).
Subject sentence: who, how many, the year, seen from the front, waist up or full length, what they wear and do. Then:

> Painterly 2D digital illustration, the look of a modern animated history documentary: semi-realistic with slightly stylised, expressive proportions, visible confident brush strokes, rich detail, cinematic lighting. Restrained palette: deep teal-blue shadows, cold blue-grey midtones, warm amber lamplight, with only small touches of dull brick red. Absolutely no text, letters, numbers, logos, emblems or symbols anywhere. Isolated subject on a perfectly plain, flat, light grey background (#cfcfcf) with no floor, no cast shadow, no scenery, nothing else in the image.

and, for groups, "Every figure fully inside the picture, not cropped at the sides."

**Objects** (1:1, 4:5 or 3:2 at resolution 1k, about 2.5 US cents). One sentence about the object; the words below
are the iron weight's exact ending (other objects used the same words with the highlight colour and the last sentence
adjusted to the object):

> Painterly 2D digital illustration, the look of a modern animated history documentary: visible confident brush strokes, rich detail, cinematic lighting. Restrained palette: deep teal-blue shadows, cold blue-grey midtones, warm amber highlights. Absolutely no text, letters, numbers, logos, emblems or symbols anywhere. Isolated subject on a perfectly plain, flat, light grey background (#cfcfcf) with no floor, no cast shadow, no scenery, nothing else in the image. The whole subject inside the picture with a margin.

## What worked

- Say what must not be there: "No people", "no cartridge cases", "NO turret on top", "completely blank, plain cardboard placards", "a plain blank cover with no writing at all".
- Describe the shape of anything historical exactly (the tank: a rhomboid hull with tracks running all the way round, a gun in a box-shaped side sponson, no turret). Models default to modern shapes.
- Ask for the whole subject inside the picture with a margin, on plain light grey (#cfcfcf); the background remover then cuts cleanly.
- For a figure that will speak, ask for a symmetrical front view with the lips closed in a straight line (the miner); the jaw is cut out afterwards.
- Paint several objects in one picture when they belong together (seven shells in a row), then cut them apart with `split_shapes`.

## Every painting of the example

### Backgrounds (full sheets)

| File | Aspect, resolution | Subject sentence (as sent) |
|---|---|---|
| `101-bg-parliament.jpg` | 9:16, 2k | A dark, grand parliament debating chamber seen from the floor at standing eye level: tiers of green leather benches on both sides, carved dark wood panelling, brass lamps glowing amber, a tall arched window with cold blue light. The lower quarter of the picture is the empty carpeted floor. No people. |
| `102-bg-munitions-factory.jpg` | 9:16, 2k | Inside a vast British munitions factory in 1915, seen at standing eye level: long workbenches with rows of brass artillery shells, overhead drive belts and pulleys, iron roof trusses, high windows with smoky light. The lower quarter of the picture is the empty factory floor. No people. |
| `104-bg-turin-street.jpg` | 9:16, 2k | An Italian industrial street in Turin in 1920 at dusk, seen at standing eye level: a large brick factory with a saw-tooth roof and tall smoking chimneys behind a high wall, tram lines on a cobbled street, street lamps. The lower quarter of the picture is the empty street. No people. |
| `105-bg-boardroom.jpg` | 9:16, 2k | A wood-panelled boardroom of 1920 seen at standing eye level: a long polished table with leather chairs, dark indistinct oil paintings in heavy gilt frames, a tall window overlooking smoking factory chimneys. The lower quarter of the picture is the empty floor. No people. |
| `106-bg-conference-hall.jpg` | 9:16, 2k | A grand international conference hall of 1920 seen at standing eye level: a long table covered in green cloth, rows of empty chairs, tall windows with heavy curtains, crystal chandeliers, marble columns. The lower quarter of the picture is the empty polished floor. No people. |
| `107-bg-town-street.jpg` | 9:16, 2k | A British town high street in the 1920s at dusk, seen at standing eye level: a brick school, a hospital, a bank with stone columns, small shops with dark windows, a railway bridge in the distance. The lower quarter of the picture is the empty street. No people, no vehicles. |
| `108-bg-kitchen.jpg` | 9:16, 2k | A modest working family's kitchen in 1920, seen at standing eye level: a black cast-iron range stove, shelves with plates and tins, an oil lamp, a small window with rain, damp walls. The lower quarter of the picture is the empty floor. No people. |
| `109-bg-factory-gate.jpg` | 9:16, 2k | A grim factory gate in an English industrial town in the 1920s at dawn, seen at standing eye level: tall iron gates in a high brick wall, a tall chimney, rows of terraced houses, a wet street. The lower quarter of the picture is the empty street. No people. |
| `1-glasgow-square.jpg` | 9:16, 2k | An empty city square in Glasgow in winter 1919, seen from the middle of the square at standing eye level: grand Victorian sandstone civic buildings with warm lit windows across the back, a tall stone column monument, bare trees, a heavy overcast dusk sky with chimney smoke. Wet cobblestones fill the bottom quarter of the picture. No people, no vehicles. |
| `6-pithead.jpg` | 9:16, 2k | A Scottish coal mine in 1919 at dusk, seen at standing eye level: a tall black iron pithead winding tower with two large spoked wheels, a brick engine house with a tall chimney, slag heaps, a row of small miners' cottages, smoke drifting across a cold teal sky with a low band of amber light. Muddy, rutted ground fills the bottom quarter of the picture. No people. |

### Figures and groups (cut out)

| File | Aspect, resolution | Subject sentence (as sent) |
|---|---|---|
| `201-politician.jpg` | 4:5, 2k | A middle-aged politician in a dark suit and tie standing behind a wooden lectern with two slim microphones, facing the viewer straight on in a symmetrical front view, waist up above the lectern, mouth firmly closed in a straight line, stern and self-assured expression. The lectern's front panel is plain wood. An invented person, not resembling any real politician. |
| `203-munition-women.jpg` | 21:9, 2k | Five British women munition workers of 1915 standing shoulder to shoulder, seen from the front, waist up: long buttoned work coats, hair tucked under cotton caps and headscarves, tired but determined faces, looking ahead with interest. Every figure fully inside the picture, not cropped at the sides. |
| `204-italian-strikers.jpg` | 21:9, 2k | A crowd of Italian factory workers on strike in 1919, seen from the front, waist up, filling the full width of the picture: flat caps, moustaches, work jackets and waistcoats, some with arms folded, some with fists raised, defiant expressions. |
| `205-owners.jpg` | 16:9, 2k | Three wealthy industrialists of 1920 standing together, seen from the front, waist up: black frock coats, waistcoats with gold watch chains, top hats, one with a cigar, smug and wary expressions. Invented people. Every figure fully inside the picture. |
| `206-workers-queue.jpg` | 21:9, 2k | A long line of tired working men and women of 1920 queuing one behind another, seen from the side, full length from cap to boots, all facing left: flat caps, shawls, worn coats, heads slightly bowed. Every figure fully inside the picture, boots included. |
| `207-delegates.jpg` | 21:9, 2k | A row of six bankers and treasury officials of 1920 seated behind a long table covered in green cloth, seen from the front, waist up above the table: dark suits, high wing collars, spectacles, moustaches, papers in front of them, stern and self-satisfied expressions. Invented people. |
| `2-crowd-back.jpg` | 21:9, 2k | A packed crowd of about forty 1919 Scottish workers and a few women in shawls, seen from the front, waist up, small in scale, filling the full width of the picture: flat caps, heavy wool coats, mufflers, some raising fists, some holding up completely blank, plain cardboard placards on sticks. Determined, hopeful, cheering. |
| `3-crowd-front.jpg` | 21:9, 2k | Five 1919 Scottish working men and one woman standing shoulder to shoulder, seen from the front, waist up, large in scale, cheering with joy: caps waved in the air, raised fists, open mouths shouting, wool coats and mufflers, one man wearing a dull red scarf. Every figure fully inside the picture, not cropped at the sides. |
| `4-soldiers.jpg` | 21:9, 2k | A line of six British soldiers in 1919 khaki First World War uniforms with round, flat, wide-brimmed steel Brodie helmets, puttees wrapped on the lower legs and rifles with fixed bayonets held upright, standing at attention in a row, full length from helmet to boots, seen from the front at a slight three-quarter angle, faces stern and shadowed under the helmets. Every figure fully inside the picture, boots included. |
| `7-miner.jpg` | 4:5, 2k | Head and shoulders of a stern middle-aged Scottish coal miner of 1919, facing the viewer straight on in a symmetrical front view: soot-streaked face, flat cloth cap, heavy jaw with stubble, lips firmly closed in a straight line, intense eyes, collarless shirt, worn dark jacket, a dull red neckerchief. |

### Objects (cut out)

| File | Aspect, resolution | Subject sentence (as sent) |
|---|---|---|
| `209-shells-row.jpg` | 21:9, 2k | A neat row of seven First World War 18-pounder artillery shell bodies standing upright side by side, as stacked in a 1915 munitions factory: each a fat steel-grey cylinder with a rounded, gently pointed nose and a thin copper driving band near the base, no cartridge cases, no fuzes. The whole row inside the picture with a margin. |
| `301-scissors-chain.jpg` | 1:1, 1k | A large pair of steel scissors snipping through a paper chain of little cut-out paper people holding hands. The whole subject inside the picture with a margin. |
| `302-coins-arrow.jpg` | 1:1, 1k | A short stack of plain copper coins with a bold dull-red arrow rising steeply out of the stack, pointing straight up. The coins have no markings. The whole subject inside the picture with a margin. |
| `303-iron-weight.jpg` | 1:1, 1k | A heavy black cast-iron weight with a handle on top, the old-fashioned kind used on market scales, with no markings at all. The whole subject inside the picture with a margin. |
| `304-cake.jpg` | 1:1, 1k | A small round birthday cake with white icing and a single lit candle, on a plain plate, seen slightly from above. The whole subject inside the picture with a margin. |
| `305-archive-boxes.jpg` | 4:5, 1k | A tall, slightly toppling stack of old cardboard archive boxes and bundles of yellowed papers tied with string; the box labels are blank. The whole subject inside the picture with a margin. |
| `306-book.jpg` | 4:5, 1k | A hardback book standing upright, seen straight on, with a plain dark red cloth cover with no writing on it and a slightly worn spine. The whole subject inside the picture with a margin. |
| `307-money-bag.jpg` | 1:1, 1k | A fat canvas money sack tied at the neck with rope, bulging, a few plain gold coins spilling out at its base; nothing printed or painted on the sack. The whole subject inside the picture with a margin. |
| `308-rubber-stamp.jpg` | 1:1, 1k | A large old-fashioned office rubber stamp with a polished wooden handle, seen from the side, the rubber face at the bottom, with no markings. The whole subject inside the picture with a margin. |
| `309-factory-small.jpg` | 1:1, 1k | A small brick factory with a saw-tooth roof and one tall chimney with a wisp of smoke, seen from the front, like a detailed model. The whole subject inside the picture with a margin. |
| `310-price-tag.jpg` | 1:1, 1k | An old manila paper price tag with a reinforced hole and a loop of string, completely blank, slightly curled. The whole subject inside the picture with a margin. |
| `311-pay-packet.jpg` | 1:1, 1k | A small brown paper wage envelope of the 1920s, slightly worn and creased, completely blank, standing upright seen straight on. The whole subject inside the picture with a margin. |
| `312-italy-map.jpg` | 4:5, 1k | A flat cut-out map of Italy seen from directly above: the long boot-shaped Italian peninsula with the islands of Sicily and Sardinia, accurate coastline, painted in muted greens and ochres like an old school map, no borders, no towns, no rivers, no sea. The whole map inside the picture with a margin. |
| `313-red-flag.jpg` | 4:5, 1k | A plain red cloth flag with no emblem or design of any kind, on a wooden pole, rippling in the wind. The whole subject inside the picture with a margin. |
| `314-farmland.jpg` | 1:1, 1k | A small square plot of farmland like a detailed model, seen slightly from above: ploughed fields, a wooden fence around it, a small stone farmhouse and a tree. The whole subject inside the picture with a margin. |
| `315-mine-small.jpg` | 1:1, 1k | A small coal mine like a detailed model: a black iron pithead winding tower with a large spoked wheel, a small brick engine house and a heap of coal. The whole subject inside the picture with a margin. |
| `316-worker-standing.jpg` | 9:16, 1k | A young British worker of 1920 standing, full length from cap to boots, facing the viewer: flat cap, work jacket, collarless shirt, patched trousers, worn boots, arms at his sides, a hopeful expression. The whole figure inside the picture with a margin, boots included. |
| `317-door.jpg` | 9:16, 1k | A tall, heavy double wooden door with carved panels and brass handles, closed, set in a stone doorframe, seen straight on. The whole door and frame inside the picture with a margin. |
| `318-gold-bars.jpg` | 3:2, 1k | A pyramid stack of gleaming gold bars, plain, with no stamps or markings. The whole subject inside the picture with a margin. |
| `319-school.jpg` | 1:1, 1k | A small Victorian brick village school with tall windows and a little bell tower, seen from the front, like a detailed model. The whole subject inside the picture with a margin. |
| `320-basket.jpg` | 1:1, 1k | A wicker shopping basket with a loaf of bread, potatoes, a bottle of milk and a paper bag of sugar. The whole subject inside the picture with a margin. |
| `321-bank.jpg` | 1:1, 1k | A small neoclassical bank building with stone columns, steps and heavy closed doors, seen from the front, like a detailed model, with nothing written on it. The whole subject inside the picture with a margin. |
| `322-padlock.jpg` | 1:1, 1k | A heavy old iron padlock, closed, slightly rusty, seen straight on. The whole subject inside the picture with a margin. |
| `323-locomotive.jpg` | 3:2, 1k | A British steam railway locomotive of the 1920s, side view, dark green with brass details and red wheels, with no lettering, numbers or badges. The whole locomotive inside the picture with a margin. |
| `324-banner.jpg` | 3:2, 1k | A plain deep red cloth banner stretched between two wooden poles, with a gold fringe along the bottom and nothing written or pictured on it, as carried in a 1920s march. The whole subject inside the picture with a margin. |
| `325-kitchen-table.jpg` | 3:2, 1k | A plain wooden kitchen table of the 1920s seen from the front, with an open household account book, a small tin cash box, a few coins and an oil lamp on it. The whole table inside the picture with a margin. |
| `326-banknotes.jpg` | 1:1, 1k | A thick bundle of plain paper banknotes held by a paper band, seen at a slight angle; the notes are blank with only a faint decorative border, no writing, no numbers, no portraits. The whole subject inside the picture with a margin. |
| `327-materials.jpg` | 3:2, 1k | A pile of building materials: stacked timber planks, steel girders and a few bricks. The whole subject inside the picture with a margin. |
| `328-lathe.jpg` | 3:2, 1k | A heavy cast-iron industrial lathe of about 1915 with drive belts, gears and hand wheels, side view. The whole machine inside the picture with a margin. |
| `329-council-houses.jpg` | 3:2, 1k | A short row of new brick council houses built around 1920, with small front gardens and low fences, like a detailed model, seen from the front. The whole subject inside the picture with a margin. |
| `330-dole-queue.jpg` | 3:2, 1k | A short queue of unemployed men of the 1920s in flat caps and worn coats, waiting in line beside a small plain office door, side view, full length. The whole subject inside the picture with a margin. |
| `5-tank.jpg` | 3:2, 2k | A British First World War Mark IV heavy tank of 1917 to 1918, seen from the side at a slight three-quarter angle: a tall rhomboid, lozenge-shaped hull, with caterpillar tracks running all the way around the outside of the whole hull from front to back and over the top, a short cannon poking out of a box-shaped sponson on the side, NO turret on top, flat riveted dark steel plates streaked with mud. The whole tank inside the picture with a margin. |
| `8-report.jpg` | 4:5, 2k | A thick official British government report from 1919 standing upright, seen straight on: a plain blank grey-blue card cover with no writing at all, a dark cloth spine, tied around the middle with faded red tape, slightly dog-eared corners. |

## Traps

- Changing the style words between requests makes pieces that don't match; nudging colours afterwards (the cut list's `grade`) only helps a little.
- Image models add writing, symbols and flags unless told not to, and sometimes even then: check every painting.
- Models draw the wrong era by default (Second World War tanks for a 1919 scene; rifle cartridges for artillery shells).
- A subject touching the picture's edge gets a straight cut there; ask for a margin.
