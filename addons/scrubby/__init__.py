# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "scrubby",
    "author" : "yhlai-code",
    "description" : "Some simple operators to control your timeline playback",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "Timeline > Menu > Scrubby",
    "category" : "Animation"
}

import bpy

def register_managed_handler(handler_list, handler):
    def managed_handler(scene):
        def remove_managed_handler():
            handler_list[:] = [h for h in handler_list if h is not managed_handler]
        
        finished = handler(scene)
        if type(finished) != bool:
            remove_managed_handler()
            raise TypeError("Handler needs to return a bool to be managed (True for finished handler)")
        if finished:
            # Unregister the handler if it's finished
            remove_managed_handler()
    
    handler_list.append(managed_handler)


class PlayToEnd(bpy.types.Operator):
    bl_idname = "scrubby.play_to_end"
    bl_label = "Play to End"
    bl_description = "Plan to the end frame"
    bl_options = {'REGISTER'}

    reverse: bpy.props.BoolProperty(name="Reverse")

    @classmethod
    def poll(cls, context):
        return not bpy.context.screen.is_animation_playing


    def execute(self, context):
        def check_stop(scene):
            if not bpy.context.screen.is_animation_playing:
                return True
            if ((self.reverse == False and scene.frame_current == scene.frame_end) or
                (self.reverse == True and scene.frame_current == scene.frame_start)):
                bpy.ops.screen.animation_cancel(restore_frame=False)
                return True
            return False
        
        register_managed_handler(bpy.app.handlers.frame_change_post, check_stop)
        bpy.ops.screen.animation_play(reverse=self.reverse)

        return {'FINISHED'}


class PlayToNextMarker(bpy.types.Operator):
    bl_idname = "scrubby.play_to_next_marker"
    bl_label = "Play to Next Marker"
    bl_description = "Play to the next marker"
    bl_options = {'REGISTER'}

    stop_marker: bpy.props.StringProperty(name="Stop Marker")
    reverse: bpy.props.BoolProperty(name="Reverse")

    @classmethod
    def poll(cls, context):
        return bpy.context.screen.is_animation_playing


    def execute(self, context):
        def is_stop_marker(m):
            return not self.stop_marker or self.stop_marker == m.name
        
        def check_stop(scene):
            if not bpy.context.screen.is_animation_playing:
                return True
            # Treat start and end as markers too
            if (scene.frame_current in (m.frame for m in scene.timeline_markers if is_stop_marker(m)) or
                scene.frame_current == scene.frame_end or
                scene.frame_current == scene.frame_start):
                bpy.ops.screen.animation_cancel(restore_frame=False)
                return True
            return False
        
        register_managed_handler(bpy.app.handlers.frame_change_post, check_stop)
        bpy.ops.screen.animation_play(reverse=self.reverse)

        return {'FINISHED'}


class PlayPingPong(bpy.types.Operator):
    bl_idname = "scrubby.play_ping_pong"
    bl_label = "Play Ping Pong"
    bl_description = "Play to the end frame then to the start frame"
    bl_options = {'REGISTER'}


    @classmethod
    def poll(cls, context):
        return not bpy.context.screen.is_animation_playing


    def execute(self, context):
        during_forward = True
        
        def check_stop(scene):
            nonlocal during_forward

            if not bpy.context.screen.is_animation_playing:
                return True

            if during_forward:
                if scene.frame_current == scene.frame_end:
                    bpy.ops.screen.animation_cancel(restore_frame=False)
                    bpy.ops.screen.animation_play(reverse=True)
                    during_forward = False
            else:
                if scene.frame_current == scene.frame_start:
                    bpy.ops.screen.animation_cancel(restore_frame=False)
                    return True
            
            return False
        
        register_managed_handler(bpy.app.handlers.frame_change_post, check_stop)
        bpy.ops.screen.animation_play()

        return {'FINISHED'}
    

CLASSES_TO_REGISTER = [
    PlayToEnd,
    PlayToNextMarker,
    PlayPingPong,
]

def register():
    [bpy.utils.register_class(klass) for klass in CLASSES_TO_REGISTER]


def unregister():
    try:
        [bpy.utils.unregister_class(klass) for klass in CLASSES_TO_REGISTER]
    except RuntimeError:
        pass