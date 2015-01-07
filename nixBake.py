from bpy import *
import bpy


class nixBake (bpy.types.Panel):
    bl_label = 'Nix Bake'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'NixBake'
    
    def draw (self, context):
        layout = self.layout
        
        row = layout.row(align=False)
        row.label('Important: Unwrap before baking.', icon='ERROR')
        row = layout.row(align=False)
        row.operator('nix.bake', icon='RENDER_STILL', text='Cycles Bake Selected')
        num = len(bpy.context.selected_objects)
        if bpy.context.scene.render.engine != 'CYCLES' or num < 1:
            row.enabled = False
        row = layout.row(align=False)
        
        row.label('Note: Baking can take a long time.', icon='INFO')
        
        
def bake():
    scene = bpy.context.scene
    selected = bpy.context.selected_objects
    object = bpy.ops.object
    num_removed = 0
    for obj in selected:
        scene.objects.active = obj
        #obj = bpy.context.active_object
        #check for existing texture
        if obj.type == 'MESH':
            texExists = False
            matnodes = bpy.context.active_object.material_slots[0].material.node_tree.nodes
            imgnodes = [n for n in matnodes if n.type == 'TEX_IMAGE']
            for n in imgnodes:
                if n.image.name == obj.name + '_gen':
                    n.select = True
                    matnodes.active = n
                    texExists = True

            #otherwise create texture and node
            if not texExists:    
                node_tree = bpy.data.materials[obj.material_slots[0].material.name].node_tree
                node = node_tree.nodes.new("ShaderNodeTexImage")
                node.select = True
                node_tree.nodes.active = node
                newimg = bpy.data.images.new(obj.name + '_gen',1024,1024)
                node.image = newimg
            else: #remove old image and create a new image
                node_tree = bpy.data.materials[obj.material_slots[0].material.name].node_tree
                node = node_tree.nodes.active
                bpy.data.images[node.image.name].user_clear()
                bpy.data.images.remove(node.image)
                newimg = bpy.data.images.new(obj.name + '_gen',1024,1024)
                #bpy.data.images[node.image.name] = bpy.data.images.new(obj.name + '_gen',2048,1024)
                node.image = newimg
        else:
            obj.select = False
            num_removed = num_removed + 1
    #bake
    print( len(selected))
    if len(selected) - num_removed > 0:
       
        scene.objects.active = selected[0]
        bpy.ops.object.bake(type="COMBINED")

       
#Define Buttons
class OBJECT_OT_buttonEmpty(bpy.types.Operator):
    bl_label = 'Cycles'
    bl_idname = 'nix.bake'
    bl_description = 'test description'
    
    def execute(self, context):
        
        bake()
        self.report({'INFO'}, "finished baking")
        return{'FINISHED'}
    
        
def register():
    bpy.utils.register_module(__name__)
        
def unregister():
        bpy.utils.unregister_module(__name__)
        
if __name__ == '__main__':
    register()
        
    
