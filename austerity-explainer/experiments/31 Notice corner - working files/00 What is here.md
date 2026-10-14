# 31 Notice corner - working files

What this folder is: the working files from rebuilding the picture you liked in our 3D street and from building
the shot checker (log 31 in the project story).

- `test pictures/`: every test picture in order. "round 1" to "round 9" are the camera and placing rounds (round 9
  is after the camera was matched to the picture you liked); "first rebuild" is the frame the four critics
  judged (one copy shows the render fault, the hard black wedge); "lighting round 1" to "16" are the small
  test pictures made while relighting the frame, each checked by the shot checker.
- `checker tests/`: the shot checker's report and marked picture for the good frame and for each of the eleven
  scenes broken on purpose (the names say what was broken), and `measure-all.sh`, which made them. The same
  tests can be run again with `film-kit/paper-film/blender/tests/run-checker-tests.sh`.
- `final frame measurements/`: what Blender measured for the finished frame (`facts.json`, the flat-colour
  pictures).
- `reviews/`: what the helpers and skeptics found: the verifier on the first checker; the five helpers and the
  skeptic on the second; the four critics and the skeptic on the first rebuild.
- `tools/`: the scripts used to match the camera to the picture you liked (`match_camera.py`, landmarks in
  `landmarks.py`), to draw its street lines onto our pictures (`target_lines.py`), and to look inside the prop
  models (`inspect_*.py`).
