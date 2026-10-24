# Where every picture used in the painted-look study lives (all read-only originals).
SP = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad"
FILM = "/home/user/Music/austerity-explainer/film-kit/assets"
PV = FILM + "/models/pit-village"
SW = SP + "/proc-work/street_wet"
PAIRS = {
 # name: (plate, painting)
 "lockout_dry":  (SP + "/plan3/assemble/round3/plate.png", PV + "/lockout-painted.jpg"),
 "corner_dry":   (SP + "/plan3/corner/final/notice-corner-plate-3.png", PV + "/notice-corner-painted.jpg"),
 "lockout_wet":  (SW + "/work/r35/main_wet_plate.png", SW + "/painter_test/pictures/wet_painting_lined_up.png"),
}
STYLE_GLASGOW = SP + "/plan3/assemble/style-glasgow.jpg"
BEHIND = {"lockout": PV + "/lockout-behind.jpg", "corner": PV + "/notice-corner-behind.jpg"}
WORK = SW + "/grime_and_growth/study/painted_look/work"
NUM = SW + "/grime_and_growth/study/painted_look/numbers"
CROPS = SW + "/grime_and_growth/study/12 Painted look - crops"
PT = FILM + "/models/inflation-chapter-2-newcomers/people-test"
PAIRS["people_dry"] = (PT + "/people-test-plate.jpg", PT + "/people-test-painting.png")
R2 = SW + "/painter_round_2"
PAIRS["lockout_wet_r2"] = (R2 + "/plate/lockout_plate_wet_round2.png", R2 + "/paint/front_painting_lined_up.png")
