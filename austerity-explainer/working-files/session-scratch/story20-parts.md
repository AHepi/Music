=== PIECES (append after 23) ===
24. **Blender models** (`film-code/blender/`, models in `film-code/assets/models/inflation-chapter-2/`):
    scripts that build the two brick works, the model town, the near-corner props and the reviewer's
    desk in Blender, bake their corner shading, and save each as one model file (.glb). The Blender
    MCP server was used to inspect and improve them. Hands finished models to the cinema stage, which
    lights and films them.
25. **Camera and frame checks** (`film-code/tools/camera_audit.py`, `frame_check.py`): the first
    measures every shot of the film against your camera rule (still unless a move is needed, at most
    three moves a shot); the second says where each object lands in the tall frame for a camera
    position, before anything is drawn. Hands problems back to the page files.

=== WORDS (append to word list) ===
| Still shot | A stretch of a page where the camera holds still, except for at most three named camera moves. The engine refuses a fourth. |
| Camera move | One of the moves from your camera rule: zoom in or out, pan left, right, up or down, move up or down. |
| Blender | A free program for making 3D models. Here it builds the factories, town, props and desk by script; the cinema stage films them. |
| MCP server | A small program that lets me drive another program through a set of named tools. Blender's official one also gives building advice and searches Blender's manual. |
| Triangle | The small flat pieces a 3D model's surface is made of. More triangles means finer shapes, but slower drawing. |
| Baked shading | Soft shadows in corners and creases worked out once in Blender and painted onto the model, so the stage doesn't have to work them out every frame. |
| Camera check | The tool that measures every shot's camera against your rule and lists any that break it. |
| Frame check | The tool that says where each object will land in the tall frame for a camera position, before any picture is drawn. |
| Near corners | The bottom corners of the frame, closest to the camera. Filled with soft barrels, crates and a cart so the bottom third isn't empty. |
| Button zone | The strip down the right side and along the bottom of a phone video where apps put their like and share buttons; words are kept out of it. |
