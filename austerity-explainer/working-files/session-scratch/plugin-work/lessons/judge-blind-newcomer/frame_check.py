"""What this does: a tiny check, no picture drawn. It makes a camera set up for the film's tall frame (1080 x 1920),
then asks Blender how wide and how tall the camera's view is at 1080 x 1920 and at the variations tool's default 600 x 400,
for both sensor-fit settings, to see whether a variations picture shows the same part of the place as the film view."""
import bpy
scene = bpy.context.scene
camera_data = bpy.data.cameras.new('film_view')
camera_data.lens_unit = 'FOV'
for fit in ('AUTO', 'VERTICAL'):
    camera_data.sensor_fit = fit
    for width, height in ((1080, 1920), (600, 400), (360, 640)):
        scene.render.resolution_x, scene.render.resolution_y = width, height
        frame = camera_data.view_frame(scene=scene)
        xs = [corner.x for corner in frame]; ys = [corner.y for corner in frame]
        print(f'RESULT sensor_fit={fit} size={width}x{height}: view width {max(xs)-min(xs):.3f}, view height {max(ys)-min(ys):.3f} (at the frame plane)')
