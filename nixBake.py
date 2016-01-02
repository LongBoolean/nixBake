#NixBake - Automate a baking workflow
#Developer: Nicholas Peterson
#GitHub: https://github.com/LongBoolean/nixBake
from bpy import *
import bpy
bpy.types.Object.nix_img_width = bpy.props.IntProperty(
name="Image Width", default=1024, min=0, description="bake image width")
bpy.types.Object.nix_img_height = bpy.props.IntProperty(
name="Image Height", default=1024, min=0, description="bake image height")
    
class nixBake (bpy.types.Panel):
    bl_label = 'Nix Bake'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'NixBake'
    

            
    def draw (self, context):
        scene = bpy.context.scene
        selected = bpy.context.selected_objects
        active_obj = bpy.context.active_object
        layout = self.layout
        
        layout.prop(active_obj, "nix_img_width")
        layout.prop(active_obj, "nix_img_height")
        
        #row = layout.row(align=False)
       # row.label('Important: Unwrap before baking.', icon='ERROR')
        row = layout.row(align=False)
        row.operator('nix.bake', icon='RENDER_STILL', text='Cycles Bake Selected')
        num = len(bpy.context.selected_objects)
        if bpy.context.scene.render.engine != 'CYCLES' or num < 1:
            row.enabled = False
        row = layout.row(align=False)
        
        row.label('Note: Baking can take a long time.', icon='INFO')
        row = layout.row(align=False)
        row.operator('nix.toggle', text='Toggle Material Output')
        #matnodes = bpy.context.active_object.material_slots[0].material.node_tree.nodes
        #outnodes = [n for n in matnodes if n.type == 'OUTPUT_MATERIAL' and n.name =='matOutput_nix']
        if len(selected) < 1:
            row.enabled = False
   
        
def toggle(objectList):   
    scene = bpy.context.scene
    for obj in objectList:
        scene.objects.active = obj
        if obj.type == 'MESH':  
            for mat in obj.material_slots:
                node_tree = bpy.data.materials[mat.name].node_tree
                matnodes = node_tree.nodes
                mixnodes = [n for n in matnodes if n.type == 'MIX_SHADER']
                for n in mixnodes:
                    if n.name == 'mix_nix':
                        val = n.inputs[0].default_value
                        if val == 1:
                            n.inputs[0].default_value = 0
                        elif val == 0:
                            n.inputs[0].default_value = 1
        else:
            obj.select = False         
                
def toggleSelected():
    toggle(bpy.context.selected_objects)  
    
def reLink():
    scene = bpy.context.scene
    selected = bpy.context.selected_objects
    for obj in selected:
        scene.objects.active = obj
        #obj = bpy.context.active_object
        #check for existing texture
        if obj.type == 'MESH':
            for mat in obj.material_slots:
                texNodeNix = None
                emitNodeNix = None
                node_tree = bpy.data.materials[mat.name].node_tree
                matnodes = node_tree.nodes    
                emitnodes = [n for n in matnodes if n.type == 'EMISSION']  
                for n in emitnodes:
                    if n.name == 'emit_nix':
                          emitNodeNix = n
                imgnodes = [n for n in matnodes if n.type == 'TEX_IMAGE']         
                for n in imgnodes:
                    if n.name == 'BakeTex_nix':
                        texNodeNix = n
                links = node_tree.links
                imgLink = links.new(texNodeNix.outputs[0], emitNodeNix.inputs[0])
       
def bake(self):
    selected = bpy.context.selected_objects
    scene = bpy.context.scene
    num_removed = 0
    active_obj = bpy.context.active_object
    for obj in selected:
            scene.objects.active = obj
            obj.nix_img_width = active_obj.nix_img_width
            obj.nix_img_height = active_obj.nix_img_height
    for obj in selected:
        scene.objects.active = obj
        #obj = bpy.context.active_object
        #check for existing texture
        if obj.type == 'MESH':

            texExists = False

            matExists = False
            uvExists = False
            if len(bpy.context.active_object.material_slots) > 0:
                matExists = True
            else:
                self.report({'ERROR'}, "Object Requires Material")
                matExists = False
                
            if len(bpy.context.active_object.data.uv_layers) > 0:
                uvExists = True
            else:
                self.report({'ERROR'}, "Object Requires UV Mapping")
                uvExists = False
                
                
            if matExists == True and uvExists == True:
                for mat in obj.material_slots:
                    outNode = None
                    lastNode = None
                    mixNodeNix = None
                    texNodeNix = None
                    emitNodeNix = None
                    imgExists = False
                    mixNixExists = False
                    emitExists = False
                    matnodes = mat.material.node_tree.nodes
                    outnodes = [n for n in matnodes if n.type == 'OUTPUT_MATERIAL']
                    for n in outnodes:
                        outNode = n
                        lastNode = outNode.inputs[0].links[0].from_node
                        break
                    
                    mixnodes = [n for n in matnodes if n.type == 'MIX_SHADER']
                    for n in mixnodes:
                        if n.name == 'mix_nix':
                            mixNixExists = True
                            mixNodeNix = n
                            
                    if not mixNixExists:
                        node_tree = bpy.data.materials[mat.name].node_tree
                        node = node_tree.nodes.new("ShaderNodeMixShader")
                        node.name = 'mix_nix'
                        mixNodeNix = node
                        mixNodeNix.inputs[0].default_value = 0
                        
                    emitnodes = [n for n in matnodes if n.type == 'EMISSION']  
                    for n in emitnodes:
                        if n.name == 'emit_nix':
                              emitExists = True
                              emitNodeNix = n
                    if not emitExists:
                        node_tree = bpy.data.materials[mat.name].node_tree
                        node = node_tree.nodes.new("ShaderNodeEmission")    
                        node.name = 'emit_nix'
                        emitNodeNix = node     
                        
                    imgnodes = [n for n in matnodes if n.type == 'TEX_IMAGE']         
                    for n in imgnodes:
                        if n.name == 'BakeTex_nix':
                            n.select = True
                            matnodes.active = n
                            texExists = True
                            texNodeNix = n

                    #otherwise create texture node
                    if not texExists:    
                        node_tree = bpy.data.materials[mat.name].node_tree
                        node = node_tree.nodes.new("ShaderNodeTexImage")
                        node.name = 'BakeTex_nix'
                        node.select = True
                        node_tree.nodes.active = node
                        texNodeNix = node
                    else:
                        node = bpy.data.materials[mat.name].node_tree.nodes['BakeTex_nix']
                         
                        texNodeNix = node
                    #check for image
                    image_index = bpy.data.images.find(obj.name + '_bake')
                    if image_index == -1:
                        newimg = bpy.data.images.new(obj.name + '_bake',obj.nix_img_width,obj.nix_img_height)
                        node.image = newimg
                    else:
                        node.image = bpy.data.images[image_index]  
                        node.image.scale( obj.nix_img_width, obj.nix_img_height )
                                
                          
                        
                    #Link nodes together
                    node_tree = bpy.data.materials[mat.name].node_tree
                    links = node_tree.links
                    imgLink = links.new(texNodeNix.outputs[0], emitNodeNix.inputs[0])
                    links.new(emitNodeNix.outputs[0], mixNodeNix.inputs[2])
                    if not mixNixExists:
                        links.new(lastNode.outputs[0], mixNodeNix.inputs[1])
                        links.new(mixNodeNix.outputs[0], outNode.inputs[0])
                    
                    #Unlink image node for baking
                    links.remove(imgLink)
            else:
                obj.select = False
                num_removed += 1
                  
        else:
            obj.select = False
            num_removed = num_removed + 1
    #bake
    print( len(selected))
    wm = bpy.context.window_manager
    #total = len(selected) - num_removed
    #wm.progress_begin(0,total)
    #wm.progress_update(0)
    wm.windows[0].cursor_set('WAIT')
    if len(selected) - num_removed > 0:
        scene.objects.active = selected[0]
        bpy.ops.object.bake(type="COMBINED")
    wm.windows[0].cursor_set('DEFAULT')
    #wm.progress_end()

   
#Define Buttons
class OBJECT_OT_buttonEmpty(bpy.types.Operator):
    bl_label = 'Cycles'
    bl_idname = 'nix.bake'
    bl_description = 'Bake selected objects material to texture (and set up required nodes to do so)'
    
    def execute(self, context): 
        bake(self)
        reLink()
        #self.report({'INFO'}, "finished baking")
        return{'FINISHED'}
class OBJECT_OT_buttonEmpty(bpy.types.Operator):
    bl_label = 'Emit'
    bl_idname = 'nix.emit'
    bl_description = 'test description'
    
    def execute(self, context): 
        setupEmission()
        #self.report({'INFO'}, "setting up emission shader")
        return{'FINISHED'}
class OBJECT_OT_buttonEmpty(bpy.types.Operator):
    bl_label = 'Toggle'
    bl_idname = 'nix.toggle'
    bl_description = 'Switch between object material and baked emit material.'
    
    def execute(self, context): 
        toggleSelected()
        #self.report({'INFO'}, "Toggling material output.")
        return{'FINISHED'}    
def register():
    bpy.utils.register_module(__name__)
        
def unregister():
        bpy.utils.unregister_module(__name__)
        
if __name__ == '__main__':
    register()
        
