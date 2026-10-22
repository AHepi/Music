# Builds the contact sheets for the person from the concept images (JPG, under 400 KB each).
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
C="/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/concept/"
OUT="/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/31 Japanese garden character - pictures/"
F=lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", s)
BG=(24,24,28); FG=(235,230,222); GOOD=(150,215,150); BAD=(235,150,130); MID=(235,205,120)
def tile(path, w, h, label, tone=FG, fs=15, lines=1, fit="cover"):
    im=Image.open(path).convert("RGB")
    im=ImageOps.fit(im,(w,h),Image.LANCZOS) if fit=="cover" else ImageOps.contain(im,(w,h),Image.LANCZOS)
    pad=fs*lines+10
    t=Image.new("RGB",(w,h+pad),BG)
    t.paste(im,((w-im.size[0])//2,(h-im.size[1])//2))
    d=ImageDraw.Draw(t)
    parts=label.split("\n")
    for i,p in enumerate(parts): d.text((8,h+5+i*(fs+2)),p,font=F(fs),fill=tone if i==0 else FG)
    return t
def grid(tiles, cols, gap=8, title=None, W=None):
    w,h=tiles[0].size
    rows=(len(tiles)+cols-1)//cols
    th=34 if title else 0
    S=Image.new("RGB",(cols*w+(cols+1)*gap, th+rows*h+(rows+1)*gap),BG)
    if title: ImageDraw.Draw(S).text((gap,6),title,font=F(20),fill=FG)
    for i,t in enumerate(tiles): S.paste(t,(gap+(i%cols)*(w+gap), th+gap+(i//cols)*(h+gap)))
    return S
def save(img,name,limit=400*1024):
    q=88
    while True:
        p=OUT+name
        img.save(p,quality=q,optimize=True,progressive=True)
        if os.path.getsize(p)<=limit or q<=40: break
        q-=4
    print(name,img.size,os.path.getsize(p)//1024,"KB q",q)
G=C+"gen/"; R=C+"refs/"
# ---------- hero
w,h=620,413
hero=[
 tile(R+"hero.jpg",w,h,"ORIGINAL (current realistic render)",FG),
 tile(G+"hero_A2_posts_nb2.jpg",w,h,"BEST: posts + beams, rule sentence (Nano Banana 2)\nin style; but added a moon (remove)",GOOD,13,2),
 tile(G+"hero_r1_nb2.jpg",w,h,"Round 1, Nano Banana 2: in style, grass too yellow\nbridge: posts + pegs",GOOD,13,2),
 tile(G+"hero_r1_flux3.jpg",w,h,"Round 1, Flux 3: in style, little added\npegs look like dark teeth, no posts",MID,13,2),
 tile(G+"hero_A2_stones_nb2.jpg",w,h,"Stone-pier try (Nano Banana 2): REJECTED\ncel-shaded outlines, turquoise water",BAD,13,2),
 tile(G+"hero_r1_nbpro.jpg",w,h,"Round 1, Pro: REJECTED, photographic\ngrass, flowers, moss streaks",BAD,13,2),
 tile(G+"hero_V1_nbpro.jpg",w,h,"Second helper V1 (Pro): REJECTED, photographic\nmoss and grass, posts stand above deck",BAD,13,2),
 tile(G+"hero_V2_nbpro.jpg",w,h,"Second helper V2 (Pro): REJECTED, photographic\nwood and grass; long planks, iron cramps",BAD,13,2),
 tile(G+"hero_V3_nb2.jpg",w,h,"Second helper V3 (Nano Banana 2): BORDERLINE\ndetail numbers match original; moss/grass look more real",MID,13,2),
]
save(grid(hero,3,title="31 Concepts - hero view: paint-overs of the current picture (green = keep, red = breaks 'part of the design, not more realistic')"),"31 Concepts - hero paint-overs.jpg")
# ---------- veranda
w,h=950,634
ver=[
 tile(R+"veranda.jpg",w,h,"ORIGINAL (current realistic render)",FG,15),
 tile(G+"veranda_V2_nb2.jpg",w,h,"BEST: Nano Banana 2 with the rule sentence\nhedge blobs kept, pegged deck, simple moss",GOOD,15,2),
 tile(G+"veranda_A_nbpro.jpg",w,h,"First try, Pro: REJECTED, photographic hedges,\nwet deck stains, hair-fine grass",BAD,15,2),
 tile(G+"veranda_B_nb2.jpg",w,h,"First try, Nano Banana 2: REJECTED, leafy hedges,\ndense hair-like grass",BAD,15,2),
]
save(grid(ver,2,title="31 Concepts - veranda view: paint-overs"),"31 Concepts - veranda paint-overs.jpg")
# ---------- element sheets
w,h=620,413
el=[
 tile(G+"sheet_bridge.jpg",w,h,"Bridge: side, plan, details (posts on stone\nfootings, two beams, pegs, cramps)",GOOD,13,2),
 tile(G+"sheet_plank2.jpg",w,h,"Plank wood: worn edge, crack, knot, pegs,\nmoss and mould, cramp, chip (planks run pale)",GOOD,13,2),
 tile(G+"sheet_roof.jpg",w,h,"Roof tiles: varied tone, chips, moss, lichen,\ndrip stains, ridge cap, eave end-cap",GOOD,13,2),
 tile(G+"sheet_trees.jpg",w,h,"Maple and pine: silhouettes, leaf cluster, bark\n(faint ghost of the house at the top)",GOOD,13,2),
 tile(G+"sheet_pond.jpg",w,h,"Pond edge: clear water over stone bed, ripples,\nlilies, iris, reeds, algae line, moss",GOOD,13,2),
 tile(G+"sheet_lantern.jpg",w,h,"Stone lantern: worn edges, moss, cracks,\nglowing window",GOOD,13,2),
 tile(G+"sheet_grass.jpg",w,h,"Grass and moss ground: tufts, cushions,\nflowers, leaves, twigs, earth patch",GOOD,13,2),
 tile(G+"sheet_plank.jpg",w,h,"Plank sheet, first try: REJECTED (pasted the\nwhole garden in and wrote text labels)",BAD,13,2),
]
save(grid(el,3,title="31 Concepts - element sheets in the garden's art style (full size in concept/gen/)"),"31 Concepts - element sheets.jpg")
# ---------- swatches
w,h=620,620
sw=[
 tile(C+"swatches/31_swatch_plank_weathered.png",w,h,"Plank wood: USABLE (joins at a butt gap)",GOOD,15),
 tile(C+"swatches/31_swatch_plaster.png",w,h,"Plaster: USABLE (edge jump 1.5-2.6 of 255)",GOOD,15),
 tile(C+"swatches/31_swatch_grass_moss_ground.png",w,h,"Grass+moss: USABLE after repair; flat, repeats",GOOD,15),
 tile(C+"swatches/31_swatch_pond_bed_stones.png",w,h,"Pond bed: USABLE after repair; big stones repeat",MID,15),
 tile(C+"swatches/31_swatch_moss_cushion.png",w,h,"Moss: tiles, but fish-scale regular",MID,15),
 tile(C+"swatches/31_swatch_roof_tiles_blended_WEAK.png",w,h,"Roof: WEAK, too blue, ghost lichen in the blend",BAD,15),
]
save(grid(sw,3,title="31 Concepts - tileable swatches (flat, top-down), after seam check and repair"),"31 Concepts - swatches.jpg")
# ---------- seam test (shifted by half; the join is the cross in the middle)
w,h=620,620
names=[("plank","Plank"),("plaster","Plaster"),("grass","Grass+moss (first try)"),("moss","Moss (first try)"),("pondbed","Pond bed (first try)"),("roof","Roof (first try)")]
st=[]
for k,l in names:
    tone=GOOD if k in("plank","plaster") else BAD
    st.append(tile(C+"seams/seam_%s_shifted.jpg"%k,w,h,"%s, shifted by half: join = centre cross"%l,tone,14))
save(grid(st,3,title="31 Concepts - seam test: each first-try swatch moved half a picture over; the middle cross is where it joins itself"),"31 Concepts - swatch seam test.jpg")
# ---------- index sheet
def texttile(w,h,lines,fs=15):
    t=Image.new("RGB",(w,h+fs*2+10),(36,36,42)); d=ImageDraw.Draw(t)
    y=10
    for s,c in lines:
        d.text((10,y),s,font=F(fs),fill=c); y+=fs+6
    return t
w,h=465,310
rule=[("THE RULE (the person, 22 Oct):",MID),("\"These things need to be integrated into the style.",FG),("So it's just part of design.\"",FG),("",FG),("Wear, moss, cracks, joinery, grass, ripples",FG),("are DESIGNED elements in the garden's own",FG),("simplified, chunky language, not realism",FG),("laid on top. Green = follows it, red = breaks it.",FG)]
how=[("HOW TO USE THESE TARGETS",MID),("Hero + veranda: the look to match at the end.",FG),("Sheets: what each part is made of (bridge",FG),("construction, plank wear, tiles, trees...).",FG),("Swatches: flat colour pictures for the",FG),("surfaces. Seams checked, see seam test sheet.",FG),("All full-size files: concept/gen and",FG),("concept/swatches (PNG).",FG)]
idx=[
 tile(R+"hero.jpg",w,h,"HERO - original (today)",FG,14),
 tile(G+"hero_A2_posts_nb2.jpg",w,h,"HERO TARGET: posts+beams, moss, pegs (moon: ignore)",GOOD,14),
 tile(R+"veranda.jpg",w,h,"VERANDA - original (today)",FG,14),
 tile(G+"veranda_V2_nb2.jpg",w,h,"VERANDA TARGET: pegged deck, simple moss",GOOD,14),
 tile(G+"sheet_bridge.jpg",w,h,"Bridge construction (side, plan, details)",GOOD,14),
 tile(G+"sheet_plank2.jpg",w,h,"Plank wood: wear, cracks, pegs, moss",GOOD,14),
 tile(G+"sheet_roof.jpg",w,h,"Roof tiles: varied, moss, lichen, drips",GOOD,14),
 tile(G+"sheet_trees.jpg",w,h,"Maple and pine",GOOD,14),
 tile(G+"sheet_pond.jpg",w,h,"Pond edge: clear water, stone bed, iris",GOOD,14),
 tile(G+"sheet_lantern.jpg",w,h,"Stone lantern: worn, moss, cracks",GOOD,14),
 tile(G+"sheet_grass.jpg",w,h,"Grass and moss ground",GOOD,14),
 texttile(w,h,rule),
 tile(C+"swatches/31_swatch_plank_weathered.png",w,h,"Swatch: plank wood (usable)",GOOD,14),
 tile(C+"swatches/31_swatch_plaster.png",w,h,"Swatch: plaster (usable)",GOOD,14),
 tile(C+"swatches/31_swatch_grass_moss_ground.png",w,h,"Swatch: grass+moss (usable, flat)",GOOD,14),
 tile(C+"swatches/31_swatch_pond_bed_stones.png",w,h,"Swatch: pond bed (usable)",MID,14),
 tile(C+"swatches/31_swatch_moss_cushion.png",w,h,"Swatch: moss (regular)",MID,14),
 tile(C+"swatches/31_swatch_roof_tiles_blended_WEAK.png",w,h,"Swatch: roof tiles (weak)",BAD,14),
 texttile(w,h,how),
 texttile(w,h,[("NOT KEPT (see the other sheets)",MID),("Photographic hero/veranda tries (Pro, second",FG),("helper's V1 and V2; V3 is borderline), the",FG),("cel-shaded stone-pier try, the first plank sheet.",FG)]),
]
save(grid(idx,4,title="31 Concepts - the targets we work from (Japanese garden, art-directed paint-overs, element sheets, swatches)"),"31 Concepts - the targets we work from.jpg")
