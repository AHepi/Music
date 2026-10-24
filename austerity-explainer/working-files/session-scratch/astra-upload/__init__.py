# SPDX-License-Identifier: GPL-3.0-or-later
"""Astra Painted Workbench: cautious, inspectable painting-workflow controls."""
import json
from pathlib import Path
import bpy
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty,
                       FloatVectorProperty, IntProperty, PointerProperty, StringProperty)
from . import config, core, geometry
from .runtime import ui as runtime_ui

bl_info = {
    "name": "Astra Painted Workbench", "author": "Astra Studio",
    "version": (0, 2, 0), "blender": (5, 1, 0),
    "location": "3D View > Sidebar > Astra Paint",
    "description": "Reversible terrain, grounded clusters, planks and material-specific controls",
    "category": "Material",
}


class ASTRA_PG_Slot(bpy.types.PropertyGroup):
    index: IntProperty()
    link: StringProperty()
    original_material: PointerProperty(type=bpy.types.Material)
    original_data_material: PointerProperty(type=bpy.types.Material)
    had_original_material: BoolProperty()
    had_original_data_material: BoolProperty()
    preview_material: PointerProperty(type=bpy.types.Material)


class ASTRA_PG_PreviewEntry(bpy.types.PropertyGroup):
    snapshot_version: StringProperty()
    object_type: StringProperty()
    obj: PointerProperty(type=bpy.types.Object)
    object_name: StringProperty()
    original_mesh: PointerProperty(type=bpy.types.Mesh)
    preview_mesh: PointerProperty(type=bpy.types.Mesh)
    original_light: PointerProperty(type=bpy.types.Light)
    preview_light: PointerProperty(type=bpy.types.Light)
    active_material_index: IntProperty()
    bevel_name: StringProperty()
    bevel_state: StringProperty()
    slots: CollectionProperty(type=ASTRA_PG_Slot)


class ASTRA_PG_Settings(bpy.types.PropertyGroup):
    preset_id: StringProperty(default="neutral_identity")
    art_status: StringProperty(default="neutral_identity")
    preset_choice: EnumProperty(name="Preset", items=[(p["id"], p["label"], p["description"])
        for p in config.presets()["presets"]])
    material_enabled: BoolProperty(name="Preview material response", default=False)
    family: EnumProperty(name="Material family", items=[(v, v.replace("_", " ").title(), "Explicit family, never inferred from object names") for v in config.FAMILIES], default="wood")
    slot_scope: EnumProperty(name="Slots", items=[("ACTIVE", "Active slot only", "Only the active slot on each selected mesh"), ("ALL", "All supported slots", "Explicitly opt in to all eligible slots on selected meshes")], default="ACTIVE")
    blend: FloatProperty(name="Response blend", default=0, min=0, max=1)
    size: FloatProperty(name="Diffuse size", default=.64, min=.05, max=.95)
    smooth: FloatProperty(name="Diffuse softness", default=.2, min=.01, max=1)
    tilt: FloatProperty(name="Bounded normal tilt", default=0, min=0, max=.08)
    gloss: FloatProperty(name="Painted highlight mix", default=0, min=0, max=.12)
    mark_scale: FloatVectorProperty(name="Local-axis frequency / m", size=3, default=(4, 4, 1), min=.01, max=100)
    geometry_enabled: BoolProperty(name="Preview selected mesh bevel", default=False)
    bevel_width_m: FloatProperty(name="Bevel width (metres)", default=0, min=0, max=.1, precision=5)
    bevel_segments: IntProperty(name="Segments", default=1, min=1, max=4)
    bevel_angle: FloatProperty(name="Minimum edge angle (degrees)", default=45, min=1, max=179)
    lighting_enabled: BoolProperty(name="Adjust selected lights only", default=False)
    light_ev: FloatProperty(name="Energy change (stops)", default=0, min=-3, max=3)
    light_tint: FloatVectorProperty(name="Color multiplier", subtype="COLOR", size=3, default=(1, 1, 1), min=0, max=1)
    experimental_ack: BoolProperty(name="I understand the look is experimental", default=False)
    config_text_name: StringProperty(name="Config Text")
    last_report: StringProperty()
    preview_token: StringProperty()
    preview_config: StringProperty()
    preview_entries: CollectionProperty(type=ASTRA_PG_PreviewEntry)
    reference_lighting: BoolProperty(name="Large light/dark masses inspected")
    reference_palette: BoolProperty(name="Warm/cool and shadow colors inspected")
    reference_depth: BoolProperty(name="Depth, atmosphere and edge loss inspected")
    reference_material: BoolProperty(name="Material marks at hero/near scale inspected")
    reference_people: BoolProperty(name="People/setting coherence inspected")
    reference_contacts: BoolProperty(name="Support/clearance witnesses inspected")
    reference_notes: StringProperty(name="Review notes", description="Record observations and unresolved issues, not a numeric art score")


class ASTRA_OT_Inspect(bpy.types.Operator):
    bl_idname = "astra_style.inspect"
    bl_label = "Inspect Selection"
    bl_description = "Create a read-only target plan with explicit supported/skipped reasons"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            report = core.preflight(context, config.from_settings(context.scene.astra_style))
            text = core.write_report(context.scene, "preflight", report)
            self.report({"INFO"}, f"{report['eligible_objects']} eligible objects; see Text: {text.name}")
            return {"FINISHED"}
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class ASTRA_OT_Preview(bpy.types.Operator):
    bl_idname = "astra_style.preview"
    bl_label = "Start Reversible Preview"
    bl_description = "Edit only selected eligible data copies. Revert restores originals; no file is saved"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and not context.scene.astra_style.preview_token

    def execute(self, context):
        try:
            s = context.scene.astra_style
            report = core.preview(context, config.from_settings(s), acknowledged=s.experimental_ack)
            core.write_report(context.scene, "preview", report)
            self.report({"INFO"}, "Preview active. Inspect rendered pixels, then Revert or Keep")
            return {"FINISHED"}
        except (ValueError, RuntimeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class ASTRA_OT_Revert(bpy.types.Operator):
    bl_idname = "astra_style.revert"
    bl_label = "Revert Preview"
    bl_description = "Restore tracked original data, independent of current selection; stop if outside edits conflict"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and bool(context.scene.astra_style.preview_token)

    def execute(self, context):
        try:
            report = core.revert(context.scene)
            core.write_report(context.scene, "revert", report)
            self.report({"INFO"}, "Original data restored")
            return {"FINISHED"}
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class ASTRA_OT_Keep(bpy.types.Operator):
    bl_idname = "astra_style.keep"
    bl_label = "Keep Preview"
    bl_description = "Keep these selected edits and release the revert snapshot. Normal Blender Undo remains available"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and bool(context.scene.astra_style.preview_token)

    def execute(self, context):
        core.write_report(context.scene, "kept", core.keep(context.scene))
        self.report({"INFO"}, "Edits kept. This does not mark the look artistically accepted")
        return {"FINISHED"}


class ASTRA_OT_LoadPreset(bpy.types.Operator):
    bl_idname = "astra_style.load_preset"
    bl_label = "Load Settings Only"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not context.scene.astra_style.preview_token

    def execute(self, context):
        s = context.scene.astra_style
        config.to_settings(config.load_preset(s.preset_choice), s)
        self.report({"INFO"}, "Settings loaded; no scene assets changed")
        return {"FINISHED"}


class ASTRA_OT_ExportConfig(bpy.types.Operator):
    bl_idname = "astra_style.export_config"
    bl_label = "Config to Text"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        s = context.scene.astra_style
        value = json.loads(s.preview_config) if s.preview_token else config.from_settings(s)
        text = core.write_report(context.scene, "config", value)
        s.config_text_name = text.name
        return {"FINISHED"}


class ASTRA_OT_ImportConfig(bpy.types.Operator):
    bl_idname = "astra_style.import_config"
    bl_label = "Load Config Text"
    bl_description = "Validate JSON as data only. Unknown fields and unsupported versions are rejected"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not context.scene.astra_style.preview_token

    def execute(self, context):
        s = context.scene.astra_style
        text = bpy.data.texts.get(s.config_text_name)
        try:
            if text is None:
                raise ValueError("Choose a Blender Text containing config JSON")
            value = config.parse(text.as_string())
            config.to_settings(value, s)
            self.report({"INFO"}, "Config loaded; no scene assets changed")
            return {"FINISHED"}
        except (ValueError, TypeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class ASTRA_OT_Audit(bpy.types.Operator):
    bl_idname = "astra_style.audit_geometry"
    bl_label = "Audit Evaluated Selection"
    bl_description = "Synchronize transforms and report actual evaluated geometry; no automatic overlap verdict"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        report = geometry.audit(context, context.selected_objects)
        report["runtime"] = core.runtime(context)
        text = core.write_report(context.scene, "geometry audit", report)
        self.report({"INFO"}, "Evaluated evidence in Text: " + text.name)
        return {"FINISHED"}


class ASTRA_OT_Support(bpy.types.Operator):
    bl_idname = "astra_style.sample_support"
    bl_label = "Probe Active Support"
    bl_description = "Active selected mesh is the explicit physical support; other selected meshes are bottom-band targets"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        try:
            if context.active_object not in context.selected_objects:
                raise ValueError("Select the active physical support and at least one target")
            if len(context.selected_objects) < 2:
                raise ValueError("Select the active physical support and at least one target")
            report = geometry.sample_support(context, context.active_object, context.selected_objects)
            report["runtime"] = core.runtime(context)
            text = core.write_report(context.scene, "support samples", report)
            self.report({"INFO"}, "Finite samples, no global pass: " + text.name)
            return {"FINISHED"}
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class ASTRA_OT_Guidance(bpy.types.Operator):
    bl_idname = "astra_style.guidance"
    bl_label = "Open Guide in Text"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        text = bpy.data.texts.new("Astra Workbench Guide")
        text.write((Path(__file__).parent / "docs" / "GUIDANCE.md").read_text())
        context.scene.astra_style.last_report = text.name
        self.report({"INFO"}, "Open Text Editor: " + text.name)
        return {"FINISHED"}


class ASTRA_OT_ReviewRecord(bpy.types.Operator):
    bl_idname = "astra_style.record_review"
    bl_label = "Record Human Review"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        s = context.scene.astra_style
        keys = ("lighting", "palette", "depth", "material", "people", "contacts")
        report = {"kind": "human_review_record", "runtime": core.runtime(context),
                  "inspected": {key: getattr(s, "reference_" + key) for key in keys},
                  "notes": s.reference_notes, "art_acceptance": "not_determined",
                  "notice": "Checked boxes record inspection only. They do not establish acceptance or a score."}
        core.write_report(context.scene, "human review", report)
        return {"FINISHED"}


class ASTRA_PT_Workbench(bpy.types.Panel):
    bl_label = "Painted Workbench 0.2.0"
    bl_idname = "ASTRA_PT_workbench"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Astra Paint"

    def draw(self, context):
        layout, s = self.layout, context.scene.astra_style
        layout.label(text="Art acceptance: pending", icon="INFO")
        layout.label(text="Edits selected eligible object IDs")
        if s.preview_token:
            box = layout.box()
            box.label(text=f"Preview: {len(s.preview_entries)} tracked objects")
            box.label(text="Revert before changing settings")
            box.label(text="Revert discards edits to preview copies")
            box.label(text="Slot/tracked-bevel changes block Revert")
            row = box.row(align=True)
            row.operator("astra_style.revert", icon="LOOP_BACK")
            row.operator("astra_style.keep", icon="CHECKMARK")
        options = layout.column()
        options.enabled = not bool(s.preview_token)
        options.prop(s, "preset_choice")
        options.operator("astra_style.load_preset")
        box = options.box()
        box.prop(s, "material_enabled")
        col = box.column()
        col.enabled = s.material_enabled
        for prop in ("family", "slot_scope", "blend", "size", "smooth", "tilt", "gloss", "mark_scale"):
            col.prop(s, prop)
        col.label(text="Response only; pigment is authored separately")
        box = options.box()
        box.prop(s, "geometry_enabled")
        col = box.column()
        col.enabled = s.geometry_enabled
        for prop in ("bevel_width_m", "bevel_segments", "bevel_angle"):
            col.prop(s, prop)
        col.label(text="No auto chips, shrink, or contact repair")
        box = options.box()
        box.prop(s, "lighting_enabled")
        col = box.column()
        col.enabled = s.lighting_enabled
        col.prop(s, "light_ev")
        col.prop(s, "light_tint")
        col.label(text="World, camera and atmosphere untouched")
        options.prop(s, "experimental_ack")
        row = options.row(align=True)
        row.operator("astra_style.inspect", icon="VIEWZOOM")
        row.operator("astra_style.preview", icon="SHADING_RENDERED")
        layout.separator()
        layout.operator("astra_style.audit_geometry")
        layout.operator("astra_style.sample_support")
        layout.operator("astra_style.guidance", icon="TEXT")
        if s.last_report:
            layout.label(text="Text: " + s.last_report)


class ASTRA_PT_Config(bpy.types.Panel):
    bl_label = "Versioned JSON / LLM Handoff"
    bl_idname = "ASTRA_PT_config"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Astra Paint"
    bl_parent_id = "ASTRA_PT_workbench"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        s = context.scene.astra_style
        self.layout.operator("astra_style.export_config")
        self.layout.prop_search(s, "config_text_name", bpy.data, "texts")
        self.layout.operator("astra_style.import_config")
        self.layout.label(text="JSON only. No code or recipe execution")


class ASTRA_PT_Reference(bpy.types.Panel):
    bl_label = "Whole-Image Reference Check"
    bl_idname = "ASTRA_PT_reference"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Astra Paint"
    bl_parent_id = "ASTRA_PT_workbench"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        s = context.scene.astra_style
        self.layout.label(text="Fixed-camera A/B, original references")
        for name in ("lighting", "palette", "depth", "material", "people", "contacts"):
            self.layout.prop(s, "reference_" + name)
        self.layout.prop(s, "reference_notes")
        self.layout.operator("astra_style.record_review")
        self.layout.label(text="Inspection is not acceptance")


CLASSES = (ASTRA_PG_Slot, ASTRA_PG_PreviewEntry, ASTRA_PG_Settings,
           ASTRA_OT_Inspect, ASTRA_OT_Preview, ASTRA_OT_Revert, ASTRA_OT_Keep,
           ASTRA_OT_LoadPreset, ASTRA_OT_ExportConfig, ASTRA_OT_ImportConfig,
           ASTRA_OT_Audit, ASTRA_OT_Support, ASTRA_OT_Guidance, ASTRA_OT_ReviewRecord,
           ASTRA_PT_Workbench, ASTRA_PT_Config, ASTRA_PT_Reference)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.astra_style = PointerProperty(type=ASTRA_PG_Settings)
    runtime_ui.register()


def unregister():
    runtime_ui.unregister()
    # Restore untouched previews on disable. Outside edits are never overwritten.
    for scene in bpy.data.scenes:
        if scene.astra_style.preview_token:
            try:
                core.revert(scene)
            except ValueError as exc:
                print("Astra preview retained for recovery after re-enable:", exc)
    del bpy.types.Scene.astra_style
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
