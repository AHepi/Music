31. **Rebuilding the picture you liked in our street, and a tool that finds what is wrong with a shot**
    (decision 37). You said: "Yup redo with your props. See if new understanding of camera movement can
    help." Then: "The camera angle is wrong as well. The lines don't converge the same way." Pointing at the
    yellow lines in "30 Why it works": "You were right here." And: "Can you develop a tool that can calculate
    these things automatically and pinpoint what exactly is wrong."
    - **The rebuild.** The picture you liked was rebuilt in our 3D street with our own props and our sharp
      notice: the notice on its board on two posts, the drum with a burnt-down fire, the chair with its back
      to the board and the lantern on its seat, the pail at the chair's feet, a gas lamp behind the board,
      the handcart and sacks small on the road, the colliery gates shut.
    - **The camera.** You were right: the street's lines ran together differently. The camera was then
      matched to the picture you liked by lining up its landmarks (the winding wheels' hubs, the chimney's
      top, the colliery gate, the left roofline, both kerbs) with ours. Ours stood 0.42 m too high and was
      turned 1 degree too little; matched, the street's lines meet at 0.684 across, 0.440 down, against
      0.706, 0.424 in the picture you liked (the lines in a painting never meet at one exact point).
    - **The shot checker** ("07 Composing a shot", section "Checking a shot automatically"). Blender measures
      the 3D scene itself: it draws every prop in its own flat colour (once as the camera sees it, once
      alone), and writes down the camera, where the street's lines meet, the lights, and for every prop how
      far away it is, how big, and what it stands on. A second program checks every composing rule it can
      and writes a report: the problems worst first, each with a fix in metres, then what passed and what
      it can't check; and a copy of the frame with each problem boxed and numbered. It takes about a minute.
      For example, given our first camera, its first fix was "Lower the camera about 0.42 m; move it about
      0.29 m to the left (across the street); turn it about 1.0 degrees left", which puts it exactly where
      matching the landmarks had put it.
    - **How it was tested.** I broke the scene on purpose eleven ways and checked each one: a camera too
      high, a camera tipped up, a pail lifted 5 m into the air, a chair pushed away from its lantern, a pail
      pushed out of the frame, a lantern dropped on the pavement, a drum moved so its edge just meets the
      chair's, props sunk into the pavement, a lamp post standing right along the board's edge, a drum
      moved behind the board, and a lamp post across the notice's words. Each report's first fix named the
      planted fault, and the sizes were close: the pail pushed 0.25 m right got "move pail about 0.25 m to
      the left"; the drum sunk 0.30 m got "raise drum by 0.30 m".
    - **Checked by helpers.** Five independent helpers then tried to break the tool: one did exactly what its
      reports said and checked again, one planted new faults, one read its code, one read its reports as you
      would, and a skeptic checked their 50 findings. Faults they found, now fixed: putting the lantern back
      on its chair would have dropped it to the pavement; it missed a post standing along the board's edge
      and a post across the notice; it told you to move every prop when the camera stood too far back; it
      offered a camera turn that its own camera check then undid; its numbers sat on top of each other on the
      marked picture; the camera's lean had the wrong sign; and some words had two names. Every report now
      says which version of the tool made it.
    - **What the critics found in the rebuilt frame, and what was done** (four critics and a skeptic):
      - the chair faced the wrong way (its back to the fire, hiding the lantern): turned round;
      - a hard black wedge across the road: not the lighting but a fault of the render (Blender ran out of
        shadow memory, "Shadow buffer full" in its log); the checker now reads the render's log;
      - everything near white (the notice, the board, the chair's seat, the drum's top): the fire's light
        cut from 900 to 160 W and raised, the lantern's from 60 to 5 W, the board's timber darkened by half,
        a narrow warm light from just over the coals aimed at the notice's lower part, so it is lit from
        below;
      - the notice in the strip where phone apps put their buttons: the camera slid 0.14 m to the right
        without turning, so where the lines meet stays put (the checker's own fix; the critics worked out
        0.12 m by hand);
      - a far street lamp touching the board's post right where the lines meet: removed; the posts cut
        level with the board; the corner lamp's glass made amber and dimmer; the pail's thin wire handle
        removed (the painter would smear it);
      - the left half a black, empty mass: a soft cool light on the left-hand houses (now about 0.6 of the
        sky's brightness, as in the picture you liked), the sacks and dustbins moved into view, one dim lit
        window, and the handcart moved to where the picture you liked has it.
    - **Where the rebuilt frame stands** ("31 Notice corner - rebuilt and lit"): the shot checker passes 30 of its 36 checks on the
      finished still: the camera (within 0.02 m of the camera that best matches the picture you liked), where
      the lines meet (right at the board's edge), no two edges just touching, the story props one group in
      front of the board, the notice clear of the phone buttons, the notice the brightest thing (3.1 times the
      frame's average, 60% of the brightest parts), warm light on 2.9% of the frame and nearly all of it round
      the story props, no big dark shape where the eye enters, a dim sky, and every strong thing within 0.11 of
      the frame's width of the others (the main rule). Six remain: the quiet left half holds 34% of the
      weight (aim 40); the notice is only 0.07 warmer at its bottom than its top (needs 0.10; the picture you
      liked: 0.17); and four places that differ from the picture you liked on purpose (our notice is
      shorter, which would mean laying it out again; the pail is a little shorter; the lamp post and lantern
      sit a little further left, to keep clear edges and the phone buttons). By eye, the corner lamp's glass
      still looks nearly white rather than amber, and the drum's inside rim pale pink. Two new critics and a
      skeptic are checking the still now.
    - **Not checked, or unsure:** the checker measures only what shows on screen and each prop's outline
      box, so a prop poking into another in 3D is not caught; rule 7 (columns), most of rule 9 and rule 11
      (whether the camera turns during a move) are not checked. Which light lights a warm patch is worked
      out from distance alone, ignoring anything that shades it. The plate for painting (the bigger picture
      the painter repaints) has not been drawn with the new lighting yet, and nothing has been painted or
      filmed this round.
    - **Cost:** nothing (all of it in Blender). About US$5.40 of the picture allowance is left.
