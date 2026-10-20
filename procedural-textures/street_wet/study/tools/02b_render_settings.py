# What this does: prints the render engine and the EEVEE ray-tracing setting saved in a .blend (to check how the plates of the shots are drawn). Changes nothing.
import bpy
s = bpy.context.scene
print('RENDERSETTINGS', bpy.data.filepath.split('/')[-1], s.render.engine, 'raytracing', getattr(s.eevee, 'use_raytracing', None), 'samples', s.eevee.taa_render_samples, 'view', s.view_settings.view_transform, s.view_settings.look, 'exposure', round(s.view_settings.exposure, 2))
