# 04 Critics - feasibility, and teaching and pictures

Source: Clara E. Mattei, *The Capital Order* (2022).

## feasibility

The money side holds up. Computer memory, disk space and the schedule do not, as the plan stands.

Checked and right:
- Every reused file exists: build_factory.py, build_town.py, build_street.py, set_dressing.py, assemble_notice_corner.py, build_scripted_props.py, the image tools (align_painting.py, keep_painted_shadows.py, composite_fill.py, find_jumps.py, camera_audit.py) and the graphics.js card functions.
- All named library props exist. The gate pair has separate left and right leaves, so the gates can swing. The library holds 46 props, not 47.
- All 28 Poly Haven models and all 20 surfaces exist under those names.
- A Japanese font (IPAGothic) is installed.
- Held shots really are in the stage (commit 2b62686).
- The painting count adds up to 19.

Money: fal's current price for Flux 3 edit is US$0.024 a megapixel. A 2k painting is about 10 cents for the result alone, and log 32's 20 to 45 cents for two shows the pictures sent are charged too. So plan on about 20 to 30 cents a painting, not 10. Even then, the paintings, ten repaints, the sketches, the narration and a re-record reserve come to about US$9 to 10, under the US$12 line.

Numbers I measured on this machine (notice corner, test logs in SCRATCH/redesign/design/critic-feasibility/):
- Held frames with fire, smoke and flicker: 1.46 s a frame on one helper; with two helpers at once, 2.1 s each, so 1.05 s a frame overall.
- Whole frames (camera moving): about 5.6 s a frame. The earlier two-at-once filming log shows 10.5 to 12 s a frame on each helper, so two helpers gain nothing on moving frames.
- Opening one set takes 20 to 31 s, and the browser uses about 2.6 GB of memory for one projected set.
- Even held frames come out at about 3.6 MB a second of film.

What follows from that:
- One full filming realistically takes 5 to 7 hours, not 3, plus a re-filming (the notice corner was filmed three times). That is still under the 2 seconds a frame ceiling, but only if the chapter stops loading all 16 pages for every 60-frame piece.
- Disk will likely run out near the end: one full-quality copy of the chapter is about 1.4 to 1.6 GB, and the pieces, the joined film and the master each hold one. The plan's 1 GB for film is about 4 times too low.
- The plan counts only machine time. Building, composing and checking 11 views at the notice corner's pace is about 100 to 150 hours of work, so 4 to 6 days.

The order of work should test painted people and the whole-chapter loading before a day is spent building the Works. Recording before 22 October risks re-recording, then re-filming from page 13 or earlier.

1. **must-fix, Section 3 'Computer time' (filming) and section 4 step 10; paper-film/scenes/cinema-chapter.js and tools/film-chapter-parallel.sh:** Every 60-frame piece starts a fresh browser, and cinema-chapter.js builds every page before drawing anything. So each piece would load all six places and about 25 views. Measured: one projected set takes 20 s to open on one helper (31 s with two at once) and uses about 2.6 GB of browser memory. A whole-chapter load is likely over 10 GB on each helper. Two helpers on a 16 GB machine with no swap would run out of memory. If they don't, about 217 pieces at roughly 2 to 4 minutes of loading each adds about 4 to 7 hours of filming. The plan's free tests film only one page, so this would not show up until filming.
   - Fix: Before filming, change the chapter so each piece builds only the pages its frames cover, plus the next page during a page turn. Film in pieces of about 240 to 300 frames, which is still under 30 minutes even at 6 s a frame. Add a free test early: load a stand-in chapter with all six places (plates in place of paintings) and measure memory and loading time on two helpers at once.
2. **must-fix, Section 3 'Disk (about 8 GB free)':** The plan expects a peak of 2.5 to 3 GB, with 1 GB for 'film pieces and the finished film'. Measured: the kit's video settings with film grain give about 3.5 to 3.6 MB a second, even for held frames (a 2-second test was 7.2 MB; the notice corner 45 MB for 13 s). One full-quality copy of a 407 to 435-second chapter is therefore about 1.4 to 1.6 GB. The joined pieces, the silent film and the mixed master make about 4.3 to 4.8 GB; the old chapter 2 still has 763 MB of pieces, 763 MB silent and two masters of 808 and 946 MB on disk. The notice corner's checks alone left 1.4 GB of stills in scratch. Saved .blend files (plus Blender's .blend1 backups) and exports that carry each prop copy (notice-corner-set.glb is 64 MB) add more. Realistic peak: about 7 to 9 GB, against 8.5 GB free.
   - Fix: Rewrite the disk table with these figures. Delete the pieces as soon as the silent film is checked, keep at most two full-quality copies, and clear each view's check stills once it passes. Check free space before every export and filming stretch. Ask the user early whether old files can go: /home/user/work/chapter-2 (3.6 GB of old masters and files), the old chapter-2 pieces and silent film in /home/user/work/paper-pop-up-film-kit/paper-film/out (about 1.5 GB), and the plan3 scratch folder (2.0 GB).
3. **should-fix, Section 3 filming table ('held 0.5 / 1.0 s, moving 3.5 s, two helpers 17% faster') and section 4 test 1's pass mark:** The figures come from the profiler, not from real filming. Real filming of the notice corner gave: held frames with effects 1.46 s on one helper, or 1.05 s a frame with two at once; moving or whole frames 5.6 s a frame, with no gain from two at once (10.5 to 12 s on each helper in the notice corner's filming log). Moving frames cost about 60% more than planned, and the 17% gain for two helpers holds for held frames only. Realistic total for 13,000 frames: about 5 to 7 hours (1.4 to 1.9 s a frame), and more if the Works with three smoking chimneys draws slower than the notice corner. On top of that comes re-filming after the critics; the notice corner was filmed three times. Test 1's own pass mark ('about 4 s or less sliding') already fails on the measured 5.6 s.
   - Fix: Use the measured figures: held with nothing live about 0.8 s, held with effects about 1.05 to 1.5 s, moving 5.6 to 7 s, page-turn frames drawn twice, plus loading. Budget about 6 hours for the first filming and 2 to 3 hours of re-filming. Shrink free test 1 to what is still unknown: held frames with nothing live, the depth blur, glow and shadow settings, and whether joining pieces by material speeds up moving frames. Run moving stretches one at a time and held stretches two at a time.
4. **should-fix, Section 1A 'Reused (files)': build_factory.py:** build_factory.py does much less than the plan assumes:
- Its chimney is a tapering square stack, so No. 1's tall round chimney is new.
- It builds only a sawtooth roof, so No. 2's 'long pitched shed roofs with a roof lantern' is new.
- It puts a water tank on every factory.
- It is a small model (the shed is 3.2 x 2.0 x 1.3) made of hundreds of fixed sizes.
- All windows share one 'window-glow' material and are merged into one piece, so No. 2 'a third lit', flickering windows and windows that change on a word are impossible without splitting them out.
- It bakes corner shading by default.
The plan lists only 'two new options' and a size setting. build_town.py is the same small scale.
   - Fix: List and budget the real changes:
- a round chimney for No. 1, and two square stacks for No. 2;
- a pitched roof with a roof lantern for No. 2;
- the tank switched off for No. 1;
- windows kept as separate pieces in groups for dimming;
- chimneys placed over their gates;
- a scale-up done after building, then surfaces re-mapped at true scale (rather than threading a scale through every number);
- skip the bake (Blender draws the plate itself).
Estimate about 4 to 6 hours for the factories and 1 hour for the town.
5. **should-fix, Section 1A and 1F 'Reused': build_street.py and set_dressing.py:** build_street.py takes no settings (colliery, slope and road width are fixed in the code). It always writes assets/models/pit-village/street.blend, street.glb and camera.json, and assemble_notice_corner.py and assemble_lockout.py open that street.blend. Running it for the Works lane or for Glasgow without changes overwrites the base of the shot the user kept (decision 38). set_dressing.py's export_for_film also always writes into the pit-village folder, and its ground_height falls back to the pit street's 4-degree slope.
   - Fix: Before reusing them, give build_street.py an output folder plus settings for the colliery, lane width and slope, and give export_for_film an output folder and the ground fallback a setting (about 1 to 2 hours). Rebuild the notice corner once afterwards to show it is unchanged.
6. **should-fix, Section 4 'The cheapest tests' (order of work):** The plan's biggest risk is painted people: the Works design rests on the queue (W1, W2, W4). Yet painted figures are tested only at step 3, after about a day of building the whole Works. If they fail and the fallback (caps, lunch tins, stools) is needed, W1, W2 and W4 have to be composed again. The whole-chapter memory and loading risk is not tested at all before filming.
   - Fix: Reorder:
(a) Free, about 1 hour: load the stand-in chapter to test memory and loading (see the first finding).
(b) About 3 to 5 hours: build the 5 figure poses, stand 4 of them in the existing pit-village street near the notice corner, and draw a plate and a helper plate. Ask approval for 2 paintings (about US$0.45: one painting and its 'behind' copy) to test faces, head counts, turned figures and leaving shadows.
(c) Then build the Works (free test 2), and only then paint W3 and W1.
7. **should-fix, Section 4 step 3 (record the narration in the first paid step) and the risk 'Facts that change soon':** Today is 15 October. New price figures come on 22 October and unemployment figures on 4 November, which may change spoken lines on pages 1, 13 and 15. Re-recording one page moves every later time. Filming pieces are named by frame number from the chapter's start, so every piece after the first changed page must be filmed again: from page 13 that is about 3,200 frames (1.5 to 2 hours); from page 1, the whole chapter. The plan covers changing the cards, not the recording or the re-filming.
   - Fix: Build and compose on the estimated timeline. Record after 22 October (and check the 4 November figure) and before the page files are timed, or film pages 13 to 16 last. Keep a re-record reserve of about US$0.30. Separate the first paid request (the paint test) from the narration.
8. **should-fix, Section 'People' (how the figures come and go) and shots 3b, 12b, 7b, 13; paper-film/scenes/projected-set.js:** Several parts of the plan need stage code that doesn't exist yet, and none of it is listed or budgeted:
(a) Showing the 'behind' painting on a word while the camera holds. projected-set.js switches to it only when the camera moves, but the queue goes in on page 3 and comes back on page 12 with the camera still.
(b) Fading a group of painted figures, with their shadow area taken from the helper plate.
(c) Two views of one set on one page (W3 then W1 on page 3; K1 and S1b taking turns on page 13). Each needs its own copy of the set, projector and two distance maps of about 38 MB each.
(d) Swapping a state picture onto a set (W2 flat out; S1b).
(e) Lit windows that dim and ripple, and placards that appear.
(f) The 100-dot panel, which graphics.js doesn't have.
In log 29 the first handover between paintings took three tries.
   - Fix: Add these to the plan with an estimate of about 6 to 10 hours, tested on page 3 in free test 2. Make the window ripple and placards change in steps (the held-shot key changes only when a window or placard changes), so they redraw about 30 times instead of on every frame.
9. **should-fix, Section 1A 'Plates and paintings' (W2) and section 3 painting table:** W2's plate is drawn in the slowed state: the queue, the gate half shut, a third of the windows lit. But W2 is seen flat out for about 36 s (pages 4, 5, 6 and 11) and slowed for only about 5 s (page 12). The free composite can only remove the queue. It cannot add the painted glow of blazing windows, or paint the open leaf with its crates and handcart if they are not in the plate. So the most-seen gate view would have its subject partly unpainted 3D next to paint.
   - Fix: Draw W2's main plate flat out, with its 'behind' painting. Paint the slowed state as a third painting with the flat-out painting as its style picture, patched in only where it differs, as planned for S1b. That adds about US$0.25. The total becomes 20 paintings.
10. **minor, Section 3 'Spending' and the 'In short' figures (10 cents a painting):** fal's price list gives Flux 3 edit (blackforestlabs/flux-3/edit-image) at US$0.024 a megapixel. A 2k painting (1504 x 2672, about 4 MP) is about 10 cents for the result alone. Log 32's 20 to 45 cents for two shows the pictures sent are also charged, so a main painting with a full-size style picture is about 25 to 30 cents and a 'behind' painting about 19 cents. The 'low' column can't happen. It doesn't break the limit: 20 paintings, 10 repaints, 4 sketches, the narration and a re-record reserve come to about US$9 to 10, under US$12.
   - Fix: Plan on about US$0.25 a painting and show one cost column, not low and high. Send the style picture at about 1 MP, which saves about 7 cents a painting.
11. **minor, Section 1 'Fetch from Poly Haven' (B, D, F) and section 3 'Fetched from Poly Haven':** Several chosen models carry lettering or branding the plan doesn't deal with:
- vintage_suitcase has 'weathered travel stickers' (the pit-village choices list turned down 'the sticker suitcase' for this reason), and it is G2's main story prop;
- plastic_crate_01 has a 'GALLER STORAGE' print;
- portable_generator is yellow with branding;
- CashRegister_01 has decals;
- cement_bag has branding, text and safety icons (the plan does note this one).
modular_electricity_poles is a 131 m kit of 200,610 polygons, and the converter's 30,000-triangle thinning would wreck it. convert_poly_haven.py and prop_library.py write into the pit-village props folder and its index.json, from a fixed list of choices.
   - Fix: Use plastic_crate_02 rather than _01. Drop the generator. Build the 1915 suitcase by script, which is simple, or paint out its stickers. Strip the decals or build the till. Cut out one pole before converting. Give the converter a new choices list and an output folder. Budget about 2 to 3 hours.
12. **minor, Section 4 step 10 (find_jumps.py on the film):** find_jumps.py loads every frame of the film as 32-bit numbers. For 12,208 frames that is about 6.3 GB, and the frame-to-frame difference step makes two more copies of that size, about 19 GB in all, on a 16 GB machine with no swap. Run on the whole chapter, it will crash.
   - Fix: Run it one piece or page at a time. The planned cuts are then listed per piece.
13. **minor, Section 2 shots 12a (K1) and 1a/16b (C1):** These slides magnify the subject far more than anything tested. K1 goes from 2.6 m to 1.4 m (1.9 times), and C1's 1.3 m slide is toward a near basket; the notice corner slid from 6.4 m to 4.9 m (1.3 times). The painting has about 1.33 plate pixels per film pixel at the plate's spot, so at 1.9 times it is stretched about 1.4 times and goes soft. Near props also show more sides the plate never saw, which wear their own tinted surfaces. That could mean extra repaints or new plates.
   - Fix: Keep these slides to about 1.3 times, for example K1 from 2.6 m to 2.0 m, or draw the plate from the middle of the slide. Check the 'weights' view and the end frame with the plate as a stand-in before paying for the painting.
14. **should-fix, Whole plan: no estimate of work hours, only machine time (12 h Blender plus 3 h filming):** The schedule depends on hours of work, not machine time. The notice corner took about 9 hours for one view: composing, three critic rounds, painting and three filmings, not counting building the checker. The shot checker is tuned to the notice: its rules about the subject being a notice, warmth from below and words hidden are notice-specific, so each new view needs its own check file and some rule changes.
Rough build estimates:
- the Works: 10 to 18 h (factories 4 to 6, wall, gates, bank and small props 3 to 5, figures 3 to 6, lane and town 2 to 3);
- checkout and corner shop: 6 to 10 h;
- building site: 6 to 9 h (the mini digger alone 3 to 5);
- kitchen: 3 to 5 h;
- Glasgow tenements, works and placards: 8 to 14 h;
- Poly Haven: 2 to 3 h;
- stage code: 6 to 10 h.
Then composing, checking and critics at 3 to 5 hours a view (33 to 55 h), 16 page files (about 16 h), filming (8 to 10 h of machine time) and critique and fixes (10 to 15 h). In all about 100 to 150 hours, or 4 to 6 days, spanning the 22 October and 4 November figure dates.
   - Fix: Add a work-time table and a first milestone the user can watch: pages 3 to 5 at the Works, after about 2 days. Keep the plan's 'first to go' list: kitchen, then the walkers, then the bank across the street.
15. **minor, Section 3 'Disk' line 'Props are loaded from the library and never copied per set', and the repository rule (decision 30):** Props are copied: place_prop puts each prop's .glb (with its pictures) into the .blend file, and export_for_film puts them into each set's .glb (notice-corner-set.glb is 64 MB, notice-corner.blend 87 MB for one view). works.blend, with two factories, the lane, the town, figures and four cameras, and its set .glb will probably pass GitHub's 100 MB limit, so the 'save everything to the repository' step would fail.
   - Fix: Keep pictures outside the .blend files or split the sets. Check every file's size before committing, and add Blender's .blend1 backups to the ignore list.

## teaching-and-pictures

Teaching, pictures and accuracy check of the synthesis shot plan (SCRATCH/redesign/design/synthesis/shot-plan.md). I measured the plan's camera spots with simple lens maths, using the film's lens from assemble_notice_corner.py (60.4 degrees top to bottom, level camera). The script is at SCRATCH/redesign/design/critic-teaching-and-pictures/geometry_check.py.

What holds up:
- The spine works for teaching: the checkout bookends, the busy site then the stopped one, the queue as the chapter's central picture, the letter on the kitchen table, the suitcase under the rent notice, and the two-factory return with the cards A REAL CASE and IN OUR PICTURE.
- I checked every card against the narration. Each figure on screen is one Malina says, and every repeated word is counted correctly.
- Mattei appears only as a typed name card under MATTEI ARGUES, which stays on to the end of page 14. "MMT" appears nowhere, there are no portraits, and no party or chain colours are planned.
- The three guesses are each answered by a cut back to the right picture. The rule is said twice, in the same words, in the same places.
- The people approach is sound: painted figures only at the Works, and empty props made for a person everywhere else.

What fails is mostly geometry, and it repeats the trap the notice corner solved. Several subjects stand on walls that run along the camera's line of sight, or behind such walls:
- In W1 and W2, the gate is seen edge-on, and the factory's windows and chimney are out of frame. That hides the chapter's key moments: the gate opening, the men going in, the windows lighting and the slowdown.
- In G2, the rent notice is squashed and pushed to the frame's edge.
- In W3, the bank is out of frame, and the street lines meet on No. 2's gate, not on the pier between the gates. Turning the camera can't fix this (rule 1).
- In the kitchen and at the checkout, a level camera at standing height drops table-height subjects off the bottom of the frame.

Other problems:
- Accuracy: the nearly bare grocer's window is shown under GLASGOW 1915, but the ledger puts the worst shortages in 1917.
- Words on screen: about 130 cards, roughly one every 3 seconds, against the user's "minimal... not subtitles".
- Page 14 drops Malina's "probably" and leaves the American view unmarked for a moment.
- Smaller points: page 3 has no picture for "more things to buy", page 10's clue vanishes during the guess, the rule-card layout is cramped, the model looks like the 1915 real case, and there are a few era details.

All of these can be fixed before anything is built or paid for.

1. **must-fix, Place A, views W1 and W2 (pages 3, 4, 5, 6, 11, 12): camera 'on the pavement at the wall's foot, about 1 m out from the wall', looking along the wall to the gate:** From 1 m out and 12-13 m along, the gate is seen at about 4.5 degrees: its face and its No. 1 / No. 2 board shrink to about 8% of their width. Everything behind the wall is out of frame, because the frame's edge is 18 degrees from the centre. No. 1's chimney is about 47 degrees off, its windows about 27 and No. 2's chimneys about 34. So the shut and chained gate, the gate swinging open, 'the machines start' (windows lighting, chimney smoking), page 4's blazing windows and page 12's dimming windows, thinning smoke and half-shut gate cannot be seen. These are the chapter's key teaching moments. The claim that each gate view shows the other factory's chimneys also fails.
   - Fix: Use the notice corner's trick: the subject stands straight ahead. Put No. 1's queue on the lane's left pavement leading up to its gate, and stand W1 on that pavement in line with the gate's left pier (where the brazier is), facing straight up the lane. The gate is then face-on with its board readable (0.3 m letters are about 41 px at 12 m). The lane's lines meet at the pier's edge, the backs lead to the gate, and No. 1's chimney and windows rise above the gate in the same column. W2 is the mirror image on the right pavement. Run the shot checker on both before anything else is built.
2. **must-fix, Place A, view W3, both gates (pages 3, 5, 9, 10, 15, 16; the master painting):** From the right-hand pavement the lane's lines meet straight ahead of the camera, 0.15-0.18 of the frame's width right of the shared pier. That is on No. 2's gate, a doorway (rule 1), and turning the camera can't close the gap. The bank 'halfway up the lane on the left' is outside the frame at 15 m. Even 19-22 m away it is a sliver about 43 px wide, with NEW MONEY letters about 12 px tall. The No. 1 / No. 2 boards are about 16 px. The whole subject sits in a band 0.43-0.55 down the frame, with the bottom 45% empty cobbles, so rule 7's bottom third holds nothing.
   - Fix: Stand W3 on the lane's centre line at a person's spot. Either use the far pavement of a cross street at the lane's mouth, or go up to an upstairs window or a footbridge over the lane's mouth, still level. The user's own words: 'Move up to see the bigger picture'. Compare both with the shot checker. Put the bank in the last third of the lane, or on a cut-away corner at the lane's mouth with its door and window facing the camera. Plan for no in-world lettering being readable in W3 (boards, sacks, drums): typed labels carry it.
3. **must-fix, Place F, view G2, the close mouth (page 7):** The factor's notice is on the pilaster beside the close, with the camera near the kerb 7 m down the street. The notice falls 0.89-1.05 across the frame, in the phone-button strip or out of frame, and is squashed to 25-34% of its width. The street's lines meet at the street's far end, not at the close's arch, so 'turned so... meet at the close's arch edge' is impossible. The placards in the side tenements' windows are slivers too: 0.10 m letters are about 11 px at 15 m.
   - Fix: Make the close face the camera: put it at the end of a short street or at a T-junction, with the notice on its pilaster face-on and the suitcase on its step. The facing tenement's windows then light up and take placards face-on, and the lines meet at the arch's edge. Otherwise stand the notice square to the camera in line with it, as the notice-corner board was. Put one placard in the nearest ground-floor window, within about 5 m, so its words read (about 33 px).
4. **must-fix, Place E, view K1 (pages 12, 13), and places B and C, views C1 and J1 (pages 1, 8, 9, 11, 15, 16):** With a level camera at 1.6 m, a letter on a 0.75 m table at the slide's end (1.4 m) falls below the frame. At 1.8 m it sits 0.91 down, under the strip at the bottom where phone apps show their caption. A basket on a 0.9 m belt or counter sits 0.90 down at 1.5 m and goes off the frame nearer than about 1.2 m. 'Where the shopper stands' and 'where the customer stands at the counter' are too close.
   - Fix: Film K1 from seated eye height across the table, from 'the other chair' (about 1.2 m): the letter is then 0.78 down at 1.4 m. Or stand about 2.9 m away and slide from about 4.1 m to 2.9 m. Place C1 and J1 where the next shopper in line stands, about 2.4 m from the basket, which puts it 0.75 down the frame.
5. **must-fix, Place F, view G1 (page 6, and page 7a titled GLASGOW 1915):** The 'nearly bare' grocer's window (three tins on a lot of empty shelf) is shown beside a 1914-15 recruiting poster, and on page 7a under GLASGOW 1915 and CROWDS OF WAR WORKERS. Ledger C2-XA02 says 1915 losses were about 1.31 million tons against 6.24 million in 1917, 'the worst losses came two years later'. Nothing in the ledger says shop windows were bare in 1915. The picture claims acute scarcity two years early (lesson 83: check pictures against the history).
   - Fix: Show 'fewer', not 'none': a display thinning out, with gaps between stocked stands and a half-empty tier. The slide on 'fewer things to buy' still lands. Have the history helper check the window against 1915 with the picture in hand. Alternatively, open page 7 on G2 rather than holding G1 under the 1915 card.
6. **should-fix, Words on screen, every page (section 2):** The plan has about 130 typed cards in about 6.7 minutes of speech, one every 3 seconds. Page 2 has about 11 in 15 seconds, and pages 12 and 13 about 10-11 each. Many cards repeat whole sentences (TRIES TO STOP PRICES GOING UP TOO FAST, OUR GOVERNMENT CAN'T RUN OUT OF ITS OWN MONEY, THE GOVERNMENT SPENDS NEW MONEY, THE SAME NEW MONEY IS SPENT, INCLUDING HELP PAYING WAGES, JOBS HARDER TO FIND). The user's decision 13 says words 'should be minimal. They aren't dialogue or subtitles... only to aid memory'. Newcomers got lost because the chapter moved too fast, and reading while listening splits their attention.
   - Fix: Aim for about 3-4 cards a page. Keep:
- names (THE QUIET FACTORY, THE FLAT-OUT FACTORY, THE USUAL CURE);
- every spoken figure;
- the questions and guesses;
- the rule cards;
- the markers (A REAL CASE, IN OUR PICTURE, THEY ARGUE with its claim, MOST ECONOMISTS AGREE, AMERICA'S VERSION..., MATTEI ARGUES);
- labels that point at things (WORKERS / MATERIALS / MACHINES).
Cut the sentence-length paraphrases and let Malina and the picture carry them.
7. **should-fix, Page 14, shot 14a cards:** Malina says the cure 'would probably mean fewer jobs', but the card says FEWER JOBS, dropping a qualifier the script says to keep. The American view's cards (FEWER JOBS, UNFORTUNATE, NOT THE GOAL) are not tied to their owner once the AMERICA'S VERSION heading is replaced. NOT THE GOAL lands at 337.0 s and the name card at 337.7 s, so it is barely readable before Mattei's card arrives.
   - Fix: Card: PROBABLY FEWER JOBS. Keep AMERICA'S VERSION OF OUR RESERVE BANK as a heading over its two cards, the same way MATTEI ARGUES heads hers. Hold those cards until about 339 s with CLARA E. MATTEI coming in below them, then swap the whole block to MATTEI ARGUES.
8. **should-fix, Place A, view W4, inside No. 2's yard (page 14):** The waiting men face the camera, because they face the gate. The nearest at 6.5 m is about 444 px tall with a head about 58 px, so the painter will paint faces. The first paid test covers only W1's men seen from behind. Also, from inside the yard a queue standing along the outer wall is hidden by the wall: only men directly in front of the opening show through the bars, not 'the queue of 8'. And nothing in the story group shows 'higher wages'.
   - Fix: With the first finding's fix, the queue stands on the pavement in line with the gate, so it shows through the bars. Make W4's men dark own-surface silhouettes rimmed by the lane's lamps from the start, or add a W4 painting to the first paid test. Put a pay envelope lettered WAGES (a short form of 'higher wages') on the upturned crate by the mug. The group then reads 'his wages, and the men who could take his place'.
9. **should-fix, Page 3, shot 3b (W1 after 'go in'):** 'More money... and more things to buy' has no picture. After the men go in, only windows and smoke change, so the newcomer sees work starting but no goods. A 1.2-second fade of the men risks reading as ghosts, and it is the key cause-and-effect step.
   - Fix: On 'things' (71.2 s), have stacked crates lettered THIS WAY UP appear inside No. 1's open gate (own surfaces, camera held). On page 5's SAME THINGS TO BUY, No. 2's crates visibly stay the same while the price arrow climbs: more, same, and later fewer, in pictures. For 'go in', make a plain cut within the held shot to the after-state the first choice (it reads as time passing), with the fade as the fallback.
10. **should-fix, Page 9, shot 9b (W3 with the bank):** Even placed where it can be seen, the bank is a small sliver at the left edge and the NEW MONEY sacks are unreadable, so 'never reached the factory' is shown by nothing happening, which is weak. Sacks of money are also the physical-cash picture the plan rejected for One world's Tokyo paper cash ('misleads about what new money sitting in the banks was').
   - Fix: On 'most' (2), a typed tag NEW MONEY lands on the bank's lit window. A dotted line then runs from it toward the gates and stops halfway as NEVER REACHED THE FACTORY lands. Drop the stencilled sacks, or keep them only as dressing.
11. **should-fix, Page 10, shot 10b (the third guess on W3):** The clue the guess depends on (ABOUT 3 IN 100 OUT OF WORK, on the 100-dot panel) disappears on the cut to W3. The newcomer has to hold the number in mind for the 4-second guess.
   - Fix: Carry the dot panel, small, into the W3 frame and keep it through the hold beside WHICH ONE?.
12. **should-fix, Pages 1 and 16, shot 1a and 16b (C1's newspaper headline):** At about 2.5 m, 4 cm headline letters are about 26 px and 6 cm about 40 px. A headline that long can't use 6 cm letters on a tabloid page, and a rack shows only the top fold. So the plan's own 40-px test will almost certainly fail, and the label THE WARNING would point at an unreadable paper. The masthead 'THE HILLSIDE HERALD' echoes the New Zealand Herald.
   - Fix: Plan on the typed card as the main carrier now. Or carry the warning on a newsagent's street bill in a wire frame at the counter's end: 4-5 big words, a real New Zealand sight, readable at that distance. Choose a masthead without 'Herald' or any real paper's word.
13. **should-fix, Pages 5 and 16 (W3 rule cards and the QUIET / FLAT OUT tags):** The cards over No. 2 have only the strip from 0.50 to 0.90 across. '→ MOSTLY MORE THINGS MADE' doesn't fit half the frame at a readable size, so each side wraps to about 6 lines. The chimneys and the live smoke rise through the dim sky band where the cards go, putting off-white type over grey smoke.
   - Fix: Lay the cards out now, because they must be identical on pages 5 and 16. Stack the quiet rule above the flat-out rule, each across 0.05-0.90 with a thin line to its chimney. Keep the smoke out of the card band or darken the band behind the type.
14. **should-fix, Place A against place F, and every place's light:** The imagined Works (gas lamps, brick, caps, dusk, 'any industrial town of the early twentieth century') and Glasgow 1915 (gas lamps, setts, caps, dusk) look like the same world. Page 6b cuts from Glasgow to W2 as if it were the next street. 'Now a real case' is the one line the script says must never be cut, and the picture doesn't mark the change. All six places are at dusk or night, so the whole chapter runs in one light.
   - Fix: Give the real cases their own light. For example, Glasgow on a grey November afternoon with the gas and window lights just coming on, while the Works stays in its single blue dusk. Then the switch from imagined picture to real case is seen, not only read. Keep the cards.
15. **minor, Place A layout (pages 3 to 5):** The two factories share one lane, one wall and a bank 7 m apart, while Malina says 'think of each one as a whole country'. A newcomer may ask why the men waiting at No. 1 don't walk next door to the busy factory, which undercuts the model.
   - Fix: Keep EACH ONE = A WHOLE COUNTRY on screen to the end of shot 3a. Consider a high dividing wall or a railway line between the two works so they read as two places in one frame.
16. **minor, Page 12, shot 12b:** The tag FLAT OUT stays on a factory that is visibly slowing, with a queue at its gate, so the label contradicts the picture.
   - Fix: Change it to THE FLAT-OUT FACTORY SLOWS, Malina's own words, on 'slows'.
17. **minor, Pages 6 and 7 lettering and set (G1, G2):** Several 1915 details need care:
- Real 1914-15 text-only recruiting posters often carry figures (ages, heights, '100,000 men', a poster number, the printer's line).
- The poster's slogan, like page 10's PLEASE SANITISE YOUR HANDS, breaks the plan's own rule that in-world lettering is names or short forms of what Malina says.
- The rent-strike districts (Govan, Partick) mostly had plain painted closes; glazed-tile closes mark better-off tenements.
- The rolling counter on page 7 shows figures Malina doesn't say while it rolls.
   - Fix: Pick poster wording with no figures and leave off the number and printer's line. Write the poster and the sanitise sign into the lettering rules as the stated era exceptions. Paint the close plain, with a two-tone band. Land ABOUT 20,000 FAMILIES whole on 'twenty' instead of rolling up to it.
18. **minor, New Zealand sets, B and D (pages 1, 10, 11, 15):** Several New Zealand details need care:
- A 2025-26 checkout bag rack must not hold single-use plastic carrier bags (banned from July 2019).
- Milk would be in a plastic bottle.
- A 2020 site sign must avoid the government's yellow-and-white 'Unite against COVID-19' stripes and a QR-code poster.
- On page 15, a six-item basket tagged $100 looks wrong to New Zealand viewers.
   - Fix: Use reusable or paper bags and a plastic milk bottle. Keep the sanitise sign plain, in words only. Make page 15's basket visibly full, so 'imagine the basket cost a hundred dollars' is believable.
19. **minor, Page 13, view S1b (the stopped site in 2026):** The ledger has no line on New Zealand building slowing in 2023-26. The stopped site pictures 'people put out of work' well, but it also says house building stopped and hints that the cure caused it. The plan lists this risk.
   - Fix: Keep NOT THE ONLY REASON on screen whenever S1b shows (13b and 13d). Give the fact helper the picture itself (lesson 83), and add a ledger line if one exists.
20. **minor, Page 7a, G1 walkers ('crowds of war workers'):** Eight figures, the nearest about 112 px tall, read as a few people walking, not crowds. Small, far-off figures are also the safest painted people, because no faces show at about 50 px.
   - Fix: If they are kept, use more figures further away (40-80 m), or point the CROWDS label at the works' gate instead.
21. **minor, Interiors C1 and J1 (top of the frame):** C1 puts the lane lamp, the CHECKOUT sign and rows of ceiling lights in the top third, and J1 has bright white shop light. That is exactly where the cards go, against rules 5 and 12 (dim top, titles away from the brightest lamp).
   - Fix: Switch off or dim the near ceiling rows (closing time, as planned) and keep a dark ceiling patch for the cards. Check it with the shot checker's brightest-parts measure.
22. **minor, Same-plan 'turned so the lines meet' wording for S1 (page 2's site):** S1 is 'turned so the fence line, the kerb and the frame's top plate meet at the gate's far post'. That works only if the camera stands in line with that post along the fence, the same error as W3 and G2.
   - Fix: Rewrite each view's camera spot as 'stand in line with the subject's edge' (rule 1, log 31), not 'turned so', and let the shot checker confirm it.

