The reference set (from the user's uploads). Per surface folder:
  colour.png                      the colour picture (RGB, 1254 x 1254, seamless tile)
  normal.png                      the uploaded normal map with its green channel FLIPPED so it reads as OpenGL (Blender) convention
  normal_as_uploaded_directx.png  the normal map exactly as uploaded (DirectX convention, green points down)
  height_as_uploaded.png          the uploaded displacement map, 8-bit, exactly as uploaded
  height.png                      same height, smoothed 0.8 px and stretched to 16-bit (what the mine scene used)
mud_golden has only a colour picture (no maps were uploaded for it).
Surfaces: brick, slate, wood, metal, mud, gravel, mud_golden.
