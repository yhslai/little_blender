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
#   Utilities
# ------------------------------------------------------------------------

def move_modifier(obj, source, target, after=False, default_index=0):
    target_index = obj.modifiers.find(target)
    move_func = bpy.ops.object.modifier_move_to_index
    if target_index != -1:
        source_index = obj.modifiers.find(source)
        if source_index != -1:
            if source_index < target_index:
                if after:
                    move_func(modifier=source, index=target_index)
                else:
                    move_func(modifier=source, index=target_index-1)
            else:
                if after:
                    move_func(modifier=source, index=target_index+1)
                else:
                    move_func(modifier=source, index=target_index)
    else:
        move_func(modifier=source, index=default_index)



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
#   Symmetrize IK Constraints
#   To work around Blender's bug: https://developer.blender.org/T89715
# ------------------------------------------------------------------------

class SymmetrizeIKConstraints(bpy.types.Operator):
    bl_idname = "bony.symmetrize_ik_constraints"
    bl_label = "Symmetrize IK constraints"
    bl_description = """Blender's built-in symmetrize feature doesn't handle IK constraints correctly.
                        Use this to fix it."""
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
        def symmetrize_ik_constraints(lb, rb):
            rb.ik_min_x = lb.ik_min_x
            rb.ik_max_x = lb.ik_max_x
            rb.ik_min_y = -lb.ik_max_y
            rb.ik_max_y = -lb.ik_min_y
            rb.ik_min_z = -lb.ik_max_z
            rb.ik_max_z = -lb.ik_min_z

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
            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.armature.symmetrize(direction='POSITIVE_X')

        bpy.ops.object.mode_set(mode='OBJECT') 

        for obj in selected:
            for lb in obj.pose.bones:
                rbname = get_right_bone_name(lb.name)
                rb = obj.pose.bones.get(rbname) if rbname else None
                if rb:
                    rb.rotation_mode = lb.rotation_mode
                    symmetrize_ik_constraints(lb, rb)

        return {'FINISHED'}


# ------------------------------------------------------------------------
#   Clear Bone Transforms
# ------------------------------------------------------------------------

class ClearBoneTransforms(bpy.types.Operator):
    bl_idname = "bony.clear_bone_transforms"
    bl_label = "Clear Bone Transforms"
    bl_description = """Clear bone transforms, even the locked ones"""
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
        def clear(bone: bpy.types.Bone):
            bone.location = [0, 0, 0]
            bone.rotation_quaternion = [1, 0, 0, 0]
            bone.scale = [1, 1, 1]

        selected =  bpy.context.selected_objects

        for obj in selected:
            for b in obj.pose.bones:
                clear(b)

        return {'FINISHED'}
            
            
            
# ------------------------------------------------------------------------
#   Apply Shape Keys
# ------------------------------------------------------------------------

def apply_shape_key(obj):
    if hasattr(obj.data, "shape_keys"):
        obj.shape_key_add(name='CombinedKeys', from_mix=True)
        for shapeKey in obj.data.shape_keys.key_blocks:
            obj.shape_key_remove(shapeKey)


class ApplyShapeKeys(bpy.types.Operator):
    bl_idname = "bony.apply_shape_keys"
    bl_label = "Apply Shape Keys"
    bl_description = """Apply all shape keys for selected meshes"""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected = bpy.context.selected_objects

        if len(selected) == 0:
            return False
        for obj in selected:
            if obj.type != 'MESH':
                return False

        return True


    def execute(self, context):
        selected =  bpy.context.selected_objects

        [apply_shape_key(obj) for obj in selected]

        return {'FINISHED'}



# ------------------------------------------------------------------------
#   Initialize Clothing
# ------------------------------------------------------------------------

class InitializeClothing(bpy.types.Operator):
    bl_idname = "bony.initialize_clothing"
    bl_label = "Initialize Clothing"
    bl_description = """Initialize a piece of clothing from selected part of character mesh
                        (Separate, apply shape keys, auto-mirror, fatten, solidify)"""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object.type == "MESH" and context.mode == "EDIT_MESH"


    def execute(self, context):
        def duplicate_separate_mesh():
            bpy.ops.mesh.select_mirror(axis={'X'}, extend=True)
            bpy.ops.mesh.duplicate(mode=1)
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.editmode_toggle()
        
        def active_clothing():
            selected = context.selected_objects
            for obj in selected:
                if obj == context.active_object:
                    # The character model
                    obj.select_set(False)
                else:
                    # The clothing
                    context.view_layer.objects.active = obj
        
        def cleanup_clothing():
            obj = context.active_object
            obj.lock_location = [False, False, False]
            obj.lock_rotation = [False, False, False]
            obj.lock_scale = [False, False, False]
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            bpy.ops.mesh.customdata_custom_splitnormals_clear()


        def auto_mirror():
            automirror = context.scene.automirror
            automirror.axis = 'x'
            automirror.orientation = 'positive'
            automirror.cut = True
            automirror.threshold = 0
            automirror.Use_Matcap = True
            automirror.show_on_cage = True
            bpy.ops.object.automirror()

        def add_thickness():
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.shrink_fatten(
                value=0.005,
                use_even_offset=False,
                use_proportional_edit=False)
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.modifier_add(type='SOLIDIFY')
            

        def prepare_modifiers():
            obj = context.active_object
            mirror = obj.modifiers.get("Mirror")
            if mirror:
                move_modifier(context.active_object, 'Mirror', "Armature")
            solidify = obj.modifiers.get("Solidify")
            if solidify:
                solidify.thickness = 0.005
                move_modifier(context.active_object, 'Solidify', "Armature", after=True)
            subdiv = obj.modifiers.get("Subdivision")
            if subdiv:
                subdiv.levels = 1
                bpy.ops.object.modifier_move_to_index(modifier="Subdivision", index=(len(obj.modifiers) - 1))
                
        
        duplicate_separate_mesh()
        active_clothing()
        apply_shape_key(context.active_object)
        cleanup_clothing()
        try:
            # Skip if Auto Mirro isn't installed
            auto_mirror()
        except AttributeError:
            pass
        add_thickness()
        prepare_modifiers()


        return {'FINISHED'}


# ------------------------------------------------------------------------
#   Reposition Bones
#   Find closest vertices for each bones, store them in a vertex group,
#   and reposition it when the mesh changes (by shape key or manually).
# ------------------------------------------------------------------------

class BindBoneToVertices(bpy.types.Operator):
    bl_idname = "bony.initialize_clothing"
    bl_label = "Initialize Clothing"
    bl_description = """Initialize a piece of clothing from selected part of character mesh
                        (Separate, apply shape keys, auto-mirror, fatten, solidify)"""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object.type == "MESH" and context.mode == "EDIT_MESH"


    def execute(self, context):
        def duplicate_separate_mesh():
            bpy.ops.mesh.select_mirror(axis={'X'}, extend=True)
            bpy.ops.mesh.duplicate(mode=1)
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.editmode_toggle()


class RepositionBonesToBoundVertices(bpy.types.Operator):
    bl_idname = "bony.initialize_clothing"
    bl_label = "Initialize Clothing"
    bl_description = """Initialize a piece of clothing from selected part of character mesh
                        (Separate, apply shape keys, auto-mirror, fatten, solidify)"""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object.type == "MESH" and context.mode == "EDIT_MESH"


    def execute(self, context):
        def duplicate_separate_mesh():
            bpy.ops.mesh.select_mirror(axis={'X'}, extend=True)
            bpy.ops.mesh.duplicate(mode=1)
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.editmode_toggle()


# ------------------------------------------------------------------------
#   Main Panel
# ------------------------------------------------------------------------

class BonyObjectPanel(bpy.types.Panel):
    bl_idname = "BONY_OBJECT_PANEL"
    bl_label = "Bony Object Panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Bony"
    bl_context = "objectmode"   


    @classmethod
    def poll(self, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        layout.label(text="Bones: ")
        col1 = layout.column(align=True)
        col1.operator(CopyCustomShapes.bl_idname, icon="BONE_DATA")
        col1.operator(SymmetrizeIKConstraints.bl_idname, icon="BONE_DATA")
        col1.operator(ClearBoneTransforms.bl_idname, icon="OUTLINER_OB_ARMATURE")
        
        layout.label(text="  [Reposition Bones]", icon="BONE_DATA")
        row1 = layout.row(align=True)
        row1.operator(BindBoneToVertices.bl_idname, text="Bind")
        row1.operator(RepositionBonesToBoundVertices.bl_idname, text="Reposition")

        layout.label(text="Mesh: ")
        col2 = layout.column(align=True)
        col2.operator(ApplyShapeKeys.bl_idname, icon="SHAPEKEY_DATA")

        layout.label(text="For Daz3D: ")
        col3 = layout.column(align=True)
        col3.operator(RenameDazBones.bl_idname, icon="BONE_DATA")

        layout.separator()

        
class BonyMeshPanel(bpy.types.Panel):
    bl_idname = "BONY_MESH_PANEL"
    bl_label = "Bony Mesh Panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Bony"
    bl_context = "mesh_edit"   


    @classmethod
    def poll(self, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        layout.label(text="Clothing: ")
        col1 = layout.column(align=True)
        col1.operator(InitializeClothing.bl_idname, text="Initialize Clothing", icon="MOD_CLOTH")

        layout.separator()




CLASSES_TO_REGISTER = [
    BonyObjectPanel,
    BonyMeshPanel,
    CopyCustomShapes,
    SymmetrizeIKConstraints,
    ClearBoneTransforms,
    RenameDazBones,
    ApplyShapeKeys,
    InitializeClothing,
    BindBoneToVertices,
    RepositionBonesToBoundVertices,
]

def register():
    [bpy.utils.register_class(klass) for klass in CLASSES_TO_REGISTER]


def unregister():
    try:
        [bpy.utils.unregister_class(klass) for klass in CLASSES_TO_REGISTER]
    except RuntimeError:
        pass