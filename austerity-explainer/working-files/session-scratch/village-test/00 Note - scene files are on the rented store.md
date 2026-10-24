# Note: the village run's scene files are on the rented store (23 October, about 15:45 UTC)

What this file is: where the big Blender files went when this computer's disk filled up (290 MB free).

* Every .blend file over 5 MB in this folder was uploaded to the RunPod store at the same path, and each copy was checked by its checksum.
* Then these local copies were deleted: work/<part>/part.blend, work/<part>/scene.blend, scene/round2/finished_thin036.blend, and every
  .blend1 backup.
* Kept here: scene/ground.blend, scene/round3/combined.blend and scene/round3/finished.blend.
* To get a file back: python3 -I <scratchpad>/runpod/render_client_serverless.py download <the same path>.
