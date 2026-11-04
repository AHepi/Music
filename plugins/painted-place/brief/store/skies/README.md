# Skies

What this folder is: whole skies photographed all round with no ground in them, free from Poly Haven (CC0; authors in
`manifest.json`), for `sky_and_haze.photo_sky(scene, name)`: the sky is the world's background and its light. `fetch_skies.py`
downloads them again.

| Sky | What it is |
|---|---|
| `mud_road_puresky` | a flat grey overcast sky, soft even daylight |
| `overcast_soil_puresky` | a heavy grey sky of rolling rain clouds, a paler band low down |
| `kloofendal_48d_partly_cloudy_puresky` | a blue sky with fair-weather clouds and the sun in it, about 48 degrees up: a bright day with hard shadows |

## Traps

- A photographed sky lights the whole place by itself; add lamps only for what the sky cannot give (a window's glow, a
  lantern). An extra big fill light makes the ground brighter than the sky, which reads wrong.
- The sunny sky's sun is in the photograph: it casts the shadows, so no sun lamp is needed. Untouched (`turn=0`), the sun
  stands towards +X and a little towards -Y, about 34 degrees round from +X; `turn` (degrees) swings it the other way
  round, so to put the sun at a bearing B (degrees from +X towards +Y), give `turn = -34 - B`. A sun behind the eye lights
  everything flat; a sun from one side rakes across boards, stones and ruts (the barn by day, log 54, used `turn=-3.7`).
- By day an open door shows a black inside: see the last trap in the brief's `Traps.md`.
- The series' dusk look uses the store's own dusk sky (`sky_and_haze.sky`), not a photograph.
