# Kit sync notes

What this file is: when this plugin kit was last brought up to date with the austerity project's film kit
(`austerity-explainer/film-kit/` in its repository), what was copied, what the plugin changed on its own (keep
those on the next copy), and what still waits. Read it before copying film kit files into the plugin again.

## Last copy: 16 October 2026

From the film kit as committed at `ae74a9b` (every copied file was checked equal to that commit).
92 files, 1.33 MB: 11 older plugin copies replaced (each was an earlier film kit version the plugin had
never changed) and 81 new files.

- Replaced: `paper-film/scenes/cinema-chapter.js` (lazy chapters, run-on join, held shots),
  `cinema-kit.js` (`kit.moving`, `kit.movingFromHere`), `graphics.js` (`dotPanel`, `ruleCard`, `guessRing`,
  `nameTag`, `priceArrow`, `pointer`, `topShade`, `buildWords`, `TEXT_LEFT`, `TEXT_RIGHT`),
  `paper-film/stage/cinema-stage.js` and `.html` (held shots, `prepareFrame`), `paper-film/tools/check_shot.py`
  (rule 7's `story_reaches_down`), `render-paper-film.mjs`, `profile_frame.mjs`; docs 01, 05 and 07.
- New: `narration-tools/estimate_timeline.py`; tools `make_state_picture.py`, `make_behind_picture.py`,
  `fit_station_proxies.py`, `station_plates.py`; scene code `projected-set.js`, `pit-village-effects.js`; the
  worked example scenes (notice corner, people test, lockout test, projection test, Works states test, lazy
  loading test, chapter 2 for newcomers with pages 3 to 5 and `works-effects.js`, house sample, relief and
  graphics tests, the petrol station tests); Blender `pit-village/` (street, set dressing, props library,
  fonts' licences, three shots), `figures/`, `inflation-chapter-2-newcomers/props/`, the checker's tests
  (`tests/notice_corner_test_scene.py`, `run-checker-tests.sh`); examples (notice corner, people test,
  projection test, lockout test, house sample, chapter 2 for newcomers: the estimated timeline and the W1 to W3
  check files; chapter 1's captions and transcripts); `.gitignore`.

## Changed in the plugin only (keep these; merge by hand if the film kit changes the same file)

| File | What the plugin has that the film kit doesn't |
|---|---|
| `paper-film/scenes/cinema-test-pages.js` | `?chapter=` (any chapter, not only chapter 2) and `&timeline=` (the estimated timeline). |
| `paper-film/scenes/cinema-chapter-template.js` and `cinema-chapter-template/` | The commented template for a new chapter. |
| `paper-film/tools/contact_sheet.py`, `make_cover.py` | Plugin tools. |
| `paper-film/tools/find-browser.mjs` (new) | The browser search, shared by the drawing tools. |
| `paper-film/tools/render-paper-film.mjs` | Uses `find-browser.mjs`; `--stills` takes commas as well as spaces and stops on anything that is not a number (the film kit's reads "1,2" as one time, NaN). |
| `paper-film/tools/profile_frame.mjs` | Uses `find-browser.mjs` (the film kit's looks only in `/opt/pw-browsers`), and prepares the timed frames first, so it works on a lazy chapter (the film kit's stops with "page 1 is not built yet"). |
| `paper-film/scenes/cinema-kit.js` | Exports `setFading(piece, pose)` (the same function as `house-sample/page-1.js`), so a cut-out fades smoothly. `piece.set({ opacity })` is unchanged: chapter 2's pages 1, 4, 6 and 9 pass opacity and would draw differently. |
| `paper-film/scenes/projected-set.js` | Exports `skyCard(kit, projection, painting, projector)`: the painted sky on a far card, which the film kit's scenes write out by hand. |
| `paper-film/tools/check-shot.sh`, `paper-film/blender/tests/run-checker-tests.sh` | Read BLENDER and BLENDER_DISPLAY from `machine-settings.env` (written by `explainer-film-setup`) instead of one machine's folder; `check-shot.sh` needs BLEND (the scene file) said out loud, or `BLEND=none`. |
| `docs/paper-look - 00 START HERE.md` | Written for the plugin's kit (no pictures or models inside; a smoke test that needs none). |
| `docs/paper-look - 01`, `05`, `07` | Film kit text with plugin notes: where the kit is, `setFading` and `skyCard` in the kit, slides not turns (05 still said "push in with the lens"), `BLEND=` in 07's check-shot example. |
| `paper-film/pieces/00 What goes here.md`, `examples/inflation-chapter-2-newcomers/00 About these examples.md` | Plugin notes. |
| `paper-film/scenes/graphics.js` | Page events (log 35): each drawing function notes what it drew (kind, words, times, strength, box) when `paper-film/tools/page_events.mjs` switches the notes on (`globalThis.pageEvents`); off, nothing is noted. The fade-in numbers are named constants and exported as `APPEAR_DELAYS` (same values). Stills drawn with the film kit's file, and with this one with the notes on and off, are the same byte for byte (`calculators/tests/test_page_events.py`). A copy from the film kit must keep these. |
| `paper-film/scenes/cinema-kit.js` | Besides `setFading`: `wordClock` notes every lookup (with every time its word is said and the line that asked) when the page-events notes are on. |
| `paper-film/tools/page_events.mjs`, `check_page_layout.mjs`, `paper-film/scenes/page-events-test.js` (new) | The page timing tools and their small test chapter (log 35). |
| `narration-tools/lint_script.py`, `sound_gates.py` (new) | The script gate and the sound gates (log 35); tested by `calculators/tests/test_lint_script.py` and `test_sound_gates.py`. |
| `narration-tools/mix_narration_over_music.sh` | Pads the ducked music to the narration's length (ffmpeg 6.1's sidechaincompress ends 0.36-0.44 s early, so the film kit's copy makes chapter 2's mix 0.36 s short on this machine); `MUSIC_LEVEL_DB`, `STEMS_DIR`, `STEMS_ONLY`; gates: lengths, and with a 5th argument (the timeline) the music 18 dB under the voice and alignment with the narration. Apart from the padded last 0.4 s, its mix is the film kit's sample for sample. |
| `narration-tools/finish_film.sh` | Gates after finishing (lengths, -15 LUFS and true peak on the encoded copy, size, alignment); 6th argument the timeline, else exit 3. |
| `narration-tools/mix_voice_over_music.sh` | A length gate at the end. |
| `narration-tools/find_loud_words.py` | Its measure is a function, `word_peak_levels` (sound_gates.py uses it); its printout is the film kit's, byte for byte (checked on chapter 2). |
| `paper-film/tools/add_music_bed.sh` | loudnorm aims at -1.5 dBTP (at -1 the AAC copy came out -0.9, as log 32's clip did), then gates for length, loudness and true peak. |

Worth copying back to the film kit: `find-browser.mjs` with the `--stills` fix and `profile_frame.mjs`'s lazy-page fix, the page-events notes in `graphics.js` and `cinema-kit.js` with `page_events.mjs` and `check_page_layout.mjs`, `setFading` and `skyCard` in the
shared code, and the machine settings in `check-shot.sh`; the mix script's length fix and the sound gates
(the film kit's mix of chapter 2 comes out 0.36 s short today).

## Waiting for a later copy (round 5 is still changing them)

- `paper-film/blender/inflation-chapter-2-newcomers/works/` (all 9 files: `assemble_works.py`, `works_kit.py`,
  `build_factories.py`, `build_far_town.py`, `build_works.sh`, `draw_works_views.py`, `paint_works_pictures.py`,
  `make_works_sheet.py`, `make_works_continuity_sheet.py`): W4 is being fixed in `assemble_works.py`, and the
  folder is one chain (`build_works.sh` runs them in order), so it is copied whole or not at all.
- `paper-film/blender/inflation-chapter-2-newcomers/checkout/` (all files, with its fonts' licences): checkout
  C1 is being built.
- `examples/inflation-chapter-2-newcomers/works-w4-shot-check.json` and `checkout-c1-shot-check.json`.
- Copied now but may change when round 5 finishes, so compare again then:
  `paper-film/scenes/inflation-chapter-2-newcomers/` (pages 3 to 5, `works-effects.js`),
  `paper-film/scenes/works-states-test.js`, `paper-film/tools/make_state_picture.py`.

## Left out on purpose

- Pictures, sound and models: `paper-film/pieces/*/` (111 MB of paper pieces), `assets/` (983 MB: paintings,
  painted rooms, Blender models, textures), chapter 1's recordings, stills and cover. The plugin stays small:
  no file in it is over 5 MB.
- Your soundtrack (never stored).
- Nothing copied holds a password or key; no file names one of the project's working (scratch) folders.
