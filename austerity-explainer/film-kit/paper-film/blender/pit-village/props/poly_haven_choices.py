# What this does: the list of Poly Haven models (all CC0, free) chosen for the 1920s British pit
# village, each with what it is in the film, the texture size to fetch, and a target triangle budget.
# Both download_poly_haven.py (outside Blender) and convert_poly_haven.py (inside Blender) read it.
#
# Chosen by looking at Poly Haven's pictures of each model. Left out on purpose: modern oil drums
# (Barrel_01, Barrel_02, barrel_03), the green military crates, the car wheel rim, the zinc gate
# latch, the fibreglass sledgehammer, the rubber-gripped hatchet, the flame-painted enamel pot,
# green wellingtons, the labelled rusty can, the "WATER" manhole cover, the sticker suitcase
# and the yard broom (its handle has a modern blue band).

CHOICES = [
    # (Poly Haven id, file name in the film, what it is, texture size)
    ('street_lamp_01', 'gas-lamp-post', 'Victorian cast-iron gas lamp on a post (street lamp)', '2k'),
    ('street_lamp_02', 'gas-lamp-wall-bracket', 'gas lantern on a wrought-iron wall bracket', '2k'),
    ('large_iron_gate', 'iron-gates-pair', 'pair of tall wrought-iron gates (pithead or yard gate)', '2k'),
    ('Lantern_01', 'hurricane-lantern', 'brass hurricane lantern with glass globe', '1k'),
    ('wooden_lantern_01', 'wooden-lantern', 'wooden-framed candle lantern with carry handle', '1k'),
    ('vintage_oil_lamp', 'parlour-oil-lamp', 'parlour paraffin lamp with painted glass font', '1k'),
    ('wine_barrel_01', 'wooden-barrel', 'oak barrel with iron hoops (beer or water barrel)', '1k'),
    ('wooden_bucket_01', 'wooden-pail', 'wooden pail with iron hoops and handle', '1k'),
    ('wooden_bucket_02', 'wooden-wash-tub', 'wooden wash tub with iron hoops', '1k'),
    ('wooden_crate_01', 'wooden-chest', 'iron-handled wooden chest', '1k'),
    ('wooden_crate_02', 'wooden-chest-lettered', 'wooden chest with carved initials W E C', '1k'),
    ('metal_jug', 'milk-can', 'small galvanised milk can (29 cm; a dairy churn would be about 70 cm)', '1k'),
    ('metal_trash_can', 'dustbins', 'two galvanised dustbins with lids', '1k'),
    ('barrel_stove', 'brazier-drum', 'rusted iron drum with burnt holes (pickets\' brazier)', '1k'),
    ('oil_tin', 'paraffin-tin', 'black square paraffin tin', '1k'),
    ('small_oil_can_01', 'oil-can', 'pump oil can with long spout', '1k'),
    ('watering_can_metal_01', 'watering-can', 'galvanised watering can', '1k'),
    ('wicker_basket_01', 'wicker-basket-tray', 'shallow wicker basket', '1k'),
    ('wicker_basket_02', 'wicker-basket-lidded', 'square wicker basket with lid', '1k'),
    ('wooden_ladder', 'step-ladder', 'wooden step ladder', '1k'),
    ('picke_dirty_01', 'pick-axe', 'dirty iron pick with wooden shaft', '1k'),
    ('rusted_spade_01', 'spade', 'rusted spade with wooden D-handle', '1k'),
    ('wooden_axe', 'felling-axe', 'long-handled axe', '1k'),
    ('cross_pein_hammer', 'hammer', 'cross-pein hammer with wooden handle', '1k'),
    ('crowbar_01', 'crowbar', 'iron crowbar', '1k'),
    ('handsaw_wood', 'handsaw', 'wood-handled handsaw', '1k'),
    ('painted_wooden_bench', 'settle-bench', 'painted wooden settle bench', '1k'),
    ('wooden_stool_01', 'wooden-stool', 'turned wooden stool', '1k'),
    ('folding_wooden_stool', 'folding-stool', 'folding wooden stool', '1k'),
    ('Rockingchair_01', 'rocking-chair', 'wooden rocking chair', '1k'),
    ('painted_wooden_chair_01', 'kitchen-chair', 'painted kitchen chair', '1k'),
    ('wooden_table_02', 'kitchen-table', 'plain wooden kitchen table', '1k'),
    ('painted_wooden_cabinet', 'kitchen-dresser', 'chipped painted kitchen cupboard', '1k'),
    ('mantel_clock_01', 'mantel-clock', 'wooden mantel clock', '1k'),
    ('tea_set_01', 'tea-set', 'china tea set (pot, cups, saucers)', '1k'),
    ('jug_01', 'flowered-jug', 'china jug with flowers', '1k'),
]

TRIANGLE_LIMIT = 30000
