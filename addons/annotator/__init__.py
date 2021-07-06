bl_info = {
    "name": "Annotator",
    "description": "Operators to control annotation layers",
    "author": "yhlai-code",
    "version": (0, 0, 1),
    "blender": (2, 80, 3),
    # TODO: Support its own Pie Menu?
    "location": "None. Use with Search Menu or Pie Menu Editor",
    "category": "Add Mesh"
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


class SelectAnnotationLayer(bpy.types.Operator):
    bl_idname = "annotator.select_layer"
    bl_label = "Select annotation layer"
    bl_description = """Select annotation layer (create it if not found)"""
    bl_options = {'REGISTER', 'UNDO'}

    layer_color: bpy.props.EnumProperty(
            #(identifier, name, description, icon, number)
                    items = [('RED', 'Red', '', 0), 
                            ('PURPLE', 'Purple', '', 1),
                            ('BLUE', 'Blue', '', 2),
                            ('CYAN', 'Cyan', '', 3),
                            ('GREEN', 'Green', '', 4),
                            ('YELLOW', 'Yellow', '', 5)],
                    name = "Layer Color",
                    default = 'RED')

    COLOR_SET = {
        'RED': (.752, .024, .028),
        'PURPLE': (.752, .013, .657),
        'BLUE': (.216, .382, .964),
        'CYAN': (.000, .715, .875),
        'GREEN': (.000, .764, .070),
        'YELLOW': (.989, .716, .029),
    }


    @classmethod
    def poll(cls, context):
        tool = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False).idname
        return "annotate" in tool


    def execute(self, context):
        gp = bpy.context.scene.grease_pencil
        layer_name = f"_{self.layer_color}_annotator"
        gpl = next((l for l in gp.layers if l.info == layer_name), None)
        if gpl:
            gp.layers.active = gpl
        else:
            bpy.ops.gpencil.layer_annotation_add()
            gpl = gp.layers.active 
            gpl.info = layer_name
            gpl.color = self.COLOR_SET[self.layer_color]
            
        return {'FINISHED'}


class RemoveAnnotation(bpy.types.Operator):
    bl_idname = "annotator.remove_layer"
    bl_label = "Remove annotation layer"
    bl_description = """Remove annotation layer"""
    bl_options = {'REGISTER', 'UNDO'}

    remove_all: bpy.props.BoolProperty(name="remove all", default=False)

    @classmethod
    def poll(cls, context):
        tool = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False).idname
        return "annotate" in tool


    def execute(self, context):
        if self.remove_all:
            gp = bpy.context.scene.grease_pencil
            while len(gp.layers) > 0:
                bpy.ops.gpencil.layer_annotation_remove()
        else:
            bpy.ops.gpencil.layer_annotation_remove()

        return {'FINISHED'}


def register():
    bpy.utils.register_class(SelectAnnotationLayer)
    bpy.utils.register_class(RemoveAnnotation)


def unregister():
    bpy.utils.unregister_class(SelectAnnotationLayer)
    bpy.utils.unregister_class(RemoveAnnotation)
