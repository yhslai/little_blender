bl_info = {
    "name": "Bony",
    "description": "Provide a little help to work with bones",
    "author": "yhlai-code",
    "version": (0, 0, 1),
    "blender": (2, 80, 3),
    "location": "View3D > Sidebar > Bony",
    "category": "Rigging"
}

import bpy
import re

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )


# ------------------------------------------------------------------------
#   Copy Custom Shape
# ------------------------------------------------------------------------


class CopyCustomShapes(bpy.types.Operator):
    bl_idname = "bony.copy_custom_shape"
    bl_label = "Copy Custom Shape"
    bl_description = """Copy all the bone custom shapes from active object to all the other selected objects
                        (the whole armature structure needs to be identical) """
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected =  bpy.context.selected_objects
        source =  bpy.context.active_object
        
        if (source is None
                or source.type != 'ARMATURE'
                or len(selected) <= 1):
            return False
        for s in selected:
            if s.type != 'ARMATURE':
                return False

        return True


    def execute(self, context):
        def copy_custom_shapes(source: bpy.types.Pose, target: bpy.types.Pose):
            for source_bone in source.bones:
                target_bone = target.bones.get(source_bone.name)
                if target_bone:
                    target_bone.custom_shape = source_bone.custom_shape
        
        selected =  bpy.context.selected_objects
        source =  bpy.context.active_object

        for target in selected:
            if target is not source and source.pose and target.pose:
                copy_custom_shapes(source.pose, target.pose) 

        return {'FINISHED'}


# ------------------------------------------------------------------------
#   Rename Daz Bones
# ------------------------------------------------------------------------

class RenameDazBones(bpy.types.Operator):
    bl_idname = "bony.rename_daz_bones"
    bl_label = "Rename Daz Bones"
    bl_description = """Rename bones imported from Daz3D to follow Blender's naming convention
                        (e.g. lForearmBend -> ForearmBend_L) """
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected = bpy.context.selected_objects

        if len(selected) == 0:
            return False
        for obj in selected:
            if obj.type != 'ARMATURE':
                return False

        return True


    def execute(self, context):
        def repl(match):
            return f"{match.group(2)}_{match.group(1).upper()}"

        selected =  bpy.context.selected_objects

        for obj in selected:
            for bone in obj.pose.bones:
                p = re.compile(r"^(l|r)([A-Z]+.*)$")
                bone.name = p.sub(repl, bone.name)

        return {'FINISHED'}


# ------------------------------------------------------------------------
#   Symmetrify Bones Roll
# ------------------------------------------------------------------------

class SymmetrifyBonesRoll(bpy.types.Operator):
    bl_idname = "bony.symmetrify_bones_roll"
    bl_label = "Symmetrify Bones Roll"
    bl_description = """Make the axes of bones on the right side match that of the left side,
                        so it's easier to copy-paste pose from one side to the other
                        (would try to symmetrify Limit Rotation constrait if any) """
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected = bpy.context.selected_objects

        if len(selected) == 0:
            return False
        for obj in selected:
            if obj.type != 'ARMATURE':
                return False

        return True


    def execute(self, context):
        def symmetrify_limit_rotation(lb, rb):
            lcons = lb.constraints.get("Limit Rotation")
            rcons = rb.constraints.get("Limit Rotation")
            if lcons and rcons:
                rcons.min_x = lcons.min_x
                rcons.max_x = lcons.max_x
                rcons.min_y = -lcons.max_y
                rcons.max_y = -lcons.min_y
                rcons.min_z = -lcons.max_z
                rcons.max_z = -lcons.min_z

        def get_right_bone_name(lbname):
            p = re.compile(r"^(.+)_L$")
            match = p.match(lbname)
            if match:
                return f"{match.group(1)}_R"
            else:
                return None

        bpy.ops.object.mode_set(mode = 'EDIT')

        selected =  bpy.context.selected_objects

        for obj in selected:
            for leb in obj.data.edit_bones:
                rbname = get_right_bone_name(leb.name)
                reb = obj.data.edit_bones.get(rbname) if rbname else None
                if reb:
                    reb.roll = -leb.roll
        bpy.ops.object.mode_set(mode='OBJECT') 
        bpy.context.view_layer.update()

        for obj in selected:
            for lb in obj.pose.bones:
                rbname = get_right_bone_name(lb.name)
                rb = obj.pose.bones.get(rbname) if rbname else None
                if rb:
                    rb.rotation_mode = lb.rotation_mode
                    symmetrify_limit_rotation(lb, rb)

        return {'FINISHED'}


# ------------------------------------------------------------------------
#   Main Panel
# ------------------------------------------------------------------------

class BonyPanel(bpy.types.Panel):
    bl_idname = "BONY_PANEL"
    bl_label = "Bony Panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Bony"
    bl_context = "objectmode"   


    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        layout.label(text="General: ")
        col1 = layout.column(align=True)
        col1.operator(CopyCustomShapes.bl_idname, text="Copy Custom Shapes", icon="BONE_DATA")
        col1.operator(SymmetrifyBonesRoll.bl_idname, text="Symmetrify Bones Roll", icon="BONE_DATA")

        layout.label(text="For Daz3D: ")
        col2 = layout.column(align=True)
        col2.operator(RenameDazBones.bl_idname, text="Rename Daz Bones", icon="BONE_DATA")

        layout.separator()


def register():
    bpy.utils.register_class(BonyPanel)
    bpy.utils.register_class(CopyCustomShapes)
    bpy.utils.register_class(SymmetrifyBonesRoll)
    bpy.utils.register_class(RenameDazBones)


def unregister():
    bpy.utils.unregister_class(BonyPanel)
    bpy.utils.unregister_class(CopyCustomShapes)
    bpy.utils.unregister_class(SymmetrifyBonesRoll)
    bpy.utils.unregister_class(RenameDazBones)
