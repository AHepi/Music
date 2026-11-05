# 57 The Japanese garden board's helper - report

What this file is: the report, word for word, of the helper that made the board of real photographs for the Japanese garden (5 November 2026, 19:46 to 20:02). Saved by the session.

---

The Japanese garden board is finished and in the plugin. It has 12 photographs, a `Board.md` and a `sources.json`, laid out like the town street and barn boards. I finished at about 20:02 by this computer's clock.

**The 12 photographs I kept**

All are Library of Congress stereograph cards (two pictures side by side on a card). I cut each down to its left picture by hand: I measured the picture's edges on a ruler grid, then looked at every crop. All 12 are marked "no known restrictions on publication". The year is the year the card was published.

| No. | Title, place, year | Library item | What it is for |
|---|---|---|---|
| 01 | Stepping stones across a garden pond, Suizenji Park Kumamoto, 1904 | 2020684982 | Pond, stepping stones, boulders at the water's edge, grass bank |
| 02 | Stepping-stone path by a pond with pruned pines, the old garden of Hikone, 1904 | 2020684895 | Stone path along the pond, rocks in the bank, iris, a pine pruned flat, a small stone lantern |
| 03 | Arched wooden bridge over a pond, Kameido Tokyo, 1901 | 2020684950 | High half-round bridge: posts, cross beams, railing, reflection |
| 04 | Lotus leaves filling a pond below an arched bridge, Osaka, 1904 | 2020634345 | Lotus, plus a low bridge on posts and a high arched one |
| 05 | Three-storey pavilion over a pond, Kinkakuji Kyoto, 1896 | 2020633584 | Three-storey timber building with up-curved roofs and railings, on a stone base at the water |
| 06 | Stone lanterns below a temple's curved eaves, Zojoji Tokyo, 1901 | 2020634285 | Deep curved roof edge up close; tall weathered stone lanterns |
| 07 | Stone lantern and stone water basin in a tea garden, Japan, 1896 | 2020637396 | Another kind of lantern; a carved square stone basin on a stand; rocks; thatch and plank walls |
| 08 | Bamboo fence and arbour in a garden, Sugita, 1896 | 2020634437 | How a bamboo fence is built: close-packed sticks, rails, X-braces |
| 09 | Bamboo grove with a brushwood fence, Kyoto, 1896 | 2020632652 | Living bamboo; a low fence of branches |
| 10 | Two-storey timber building with verandas round a garden, Kyoto, 1902 | 2020632679 | Two storeys with verandas and railings along the front, tiled roofs |
| 11 | Thatched inn with paper lanterns under its eaves, Japan, 1896 | 2020637401 | An inn: upper veranda, a row of hanging paper lanterns, cloth curtains |
| 12 | Paper screens and mats in a room at an inn, near Hiroshima, 1904 | 2020637397 | Paper screens (shōji) up close, straw mats, timber posts |

Good ones I left out only because the board stops at 12 (Library item numbers, in case the session wants to swap one in):
- 2020632746: old stone lanterns with moss, Nara
- 99401509: a small pond with mossy rocks
- 2020633578: a pine trained on a bamboo frame, with tiled roofs
- 2020634193: a tall bamboo screen fence

**What I looked for and could not find**
- A stone basin fed by a bamboo spout. There is a basin (07) and there is bamboo (08, 09), but never the two together.
- A Japanese maple seen up close. The two maple cards I found were marked "rights not evaluated" and "publication may be restricted".
- One picture of a two- or three-storey inn under curved tiled roofs. 06, 10 and 11 each show part of one.
- Mist over wooded mountains behind a building. The only near match was a hand-coloured 1890 print of the Fujiya hotel at Miyanoshita. Its rights note covers the United States only, and the hotel is small and far off, so I left it out.
- A large glazed jar by a door. 07 has big bowl-shaped plant pots, nothing more.
- A garden wet after rain.
- Hand-coloured lantern slides or photochrom prints of Japanese gardens. The searches turned up none.

The Board.md lists all of these as things the builder must take from its own knowledge.

**Mistakes I made and how I fixed them**
- I first had a script find the picture edges on the cards, and it got them wrong: it was fooled by the cards' printed lettering. I dropped it and measured every card by eye on a ruler grid instead.
- My first crops still showed small bits of the cards' rounded top corners. I cut further in at the top and right, then checked again on the contact sheet. They are clean now.
- Four of the Library's records failed to load the first time. I tried to remove their empty folders so I could retry, and a safety check blocked that. Nothing was removed. I retried into a new folder instead: two came through, one failed again, and one has no picture at all. None of the four went on the board. One of the two that came through, a tea house at Shiobara, turned out to be marked "rights not evaluated".
- The first Golden Pavilion card I chose had a narrower rights note ("no known restrictions in the U.S."). I swapped it for another card of the same building with the plain note, which is also clearer.
- For card 08, the Library's date says 1904, but the card itself reads "Copyright 1896" (I read it on the card) and the Library's publication note also says 1896. I used 1896 and wrote this in `sources.json`.

**Things for the session**
- The plugin's `skills/make-a-painted-place/SKILL.md` (line 12) names the existing boards. You may want to add `japanese garden` there. I didn't, because I was told to write only the new folder.
- `austerity-explainer/project-notes/Decisions.md` shows as changed in the project's change list. That wasn't me: I never opened it.

**Files I created**
- In the plugin, the folder `/home/claude/music/plugins/painted-place/brief/boards/japanese garden/`, holding the 12 photographs, `Board.md` (with a traps section at the bottom) and `sources.json`. Nothing else in the plugin was touched.
- The contact sheet for you to look at: `/home/claude/store-work/garden57/board/board_sheet.jpg`
- Everything else is in the scratch folder `/home/claude/store-work/garden57/board/`:
  - `scripts/`: the search, download, ruler, crop, board-making and contact-sheet scripts. `measure.py` is the edge-finding script that failed.
  - `found/`, `found2/`, `found3/`: the downloads, each picture in its own folder.
  - `searches/`, `look/`, `crops/`, `staging/`: search results, check sheets, test crops, and a first build of the board.

---

## Traps

- This is the helper's own account; the session looked at the contact sheet before the builder started.
- The Decisions.md change it saw was the session's own (decision 82), made while it worked.
