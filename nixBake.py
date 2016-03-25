#NixBake - Automate a baking workflow
#Developer: Nicholas Peterson
#GitHub: https://github.com/LongBoolean/nixBake

#Install:
#   Go to the add-ons section in user preferences and click "install from file" 
#   Choose nixBake.py file and click "install from file" to install.
#   To enable the "NixBake" add-on check the checkbox.
#   Remember to click "Save User Settings" if you want these changes to take effect
#       the next time you start blender.
#   To update the addon, remove the old version, and reinstall the new version as before. 
#Usage:
#   The 'NixBake' tab will be added to the toolbar of the 3D view.
#   Unwrap your object and create a material before baking.
#   Select your objects and click the 'Cycles Bake Selected' button to bake your textures. 
#       This will also add a few nodes to the object's material. 
#       (If something goes wrong you can delete these nodes and rebake to recreate the node setup)
#   The 'Toggle Material Output' button will allow you to view the baked image on the object in
#       cycles. (Ensure that viewport shading is set to 'Material' in the 3D view.) 
bl_info = {
    "name" : "NixBake",
    "author" : "Nicholas Peterson",
    "version" : (0,1,3),
    "blender" : (2, 77, 0),
    "location" : "View3D > Tools",
    "description" : "Tool to automate a baking workflow.",
    "category" : "Baking"
}

from bpy import *
import bpy
bpy.types.Object.nix_img_width = bpy.props.IntProperty(
name="Image Width", default=1024, min=0, description="bake image width")
bpy.types.Object.nix_img_height = bpy.props.IntProperty(
name="Image Height", default=1024, min=0, description="bake image height")
bpy.types.Scene.img_name_ext_bool = bpy.props.BoolProperty(
name="bake effects image name", default=False, description="include bake type in image name")
bpy.types.Scene.toggle_material_bool = bpy.props.BoolProperty(
name="add nodes for material toggle", default=False, description="add nodes for material toggle (takes effect after rebaking)")
nix_nodeError = False
nix_current_shade = 'SOLID'

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
        cscene = scene.cycles
        cbk = scene.render.bake
        
        if active_obj != None:
            col = layout.column(align=True)
            col.prop(active_obj, "nix_img_width")
            col.prop(active_obj, "nix_img_height")
            layout.prop(scene, "img_name_ext_bool")
        
        col = layout.column()   
        
        col.prop(cscene, "bake_type") 
        
        col = layout.column()
        
        if cscene.bake_type == 'NORMAL':
            col.prop(cbk, "normal_space", text="Space")

            row = col.row(align=True)
            row.label(text="Swizzle:")
            row.prop(cbk, "normal_r", text="")
            row.prop(cbk, "normal_g", text="")
            row.prop(cbk, "normal_b", text="")

        elif cscene.bake_type == 'COMBINED':
            row = col.row(align=True)
            row.prop(cbk, "use_pass_direct", toggle=True)
            row.prop(cbk, "use_pass_indirect", toggle=True)

            split = col.split()
            split.active = cbk.use_pass_direct or cbk.use_pass_indirect

            col = split.column()
            col.prop(cbk, "use_pass_diffuse")
            col.prop(cbk, "use_pass_glossy")
            col.prop(cbk, "use_pass_transmission")

            col = split.column()
            col.prop(cbk, "use_pass_subsurface")
            col.prop(cbk, "use_pass_ambient_occlusion")
            col.prop(cbk, "use_pass_emit")

        elif cscene.bake_type in {'DIFFUSE', 'GLOSSY', 'TRANSMISSION', 'SUBSURFACE'}:
            row = col.row(align=True)
            row.prop(cbk, "use_pass_direct", toggle=True)
            row.prop(cbk, "use_pass_indirect", toggle=True)
            row.prop(cbk, "use_pass_color", toggle=True)
        
        col = layout.column()
        
        row = layout.row(align=False)
        row.label('Note: Baking can take a long time.', icon='INFO')
        row = layout.row(align=False)
        row.operator('nix.bake', icon='RENDER_STILL', text='Cycles Bake Selected')
        num = len(bpy.context.selected_objects)
        if bpy.context.scene.render.engine != 'CYCLES' or num < 1:
            row.enabled = False
            
        row = layout.row(align=False)
        col = layout.column()
        row = layout.row(align=False)
        
        row.prop(scene, "toggle_material_bool")
        row = layout.row(align=False)
        if bpy.context.scene.render.engine != 'CYCLES' or num < 1 or scene.toggle_material_bool == False:
            row.enabled = False
        row.operator('nix.toggle', text='Toggle Material Output')
        row.operator('nix.shade', icon= 'MATERIAL_DATA',text='')
        
        #matnodes = bpy.context.active_object.material_slots[0].material.node_tree.nodes
        #outnodes = [n for n in matnodes if n.type == 'OUTPUT_MATERIAL' and n.name =='matOutput_nix']
        if len(selected) < 1:
            row.enabled = False
   
def shade():
    global nix_current_shade
    if bpy.context.space_data.viewport_shade == 'MATERIAL':
        bpy.context.space_data.viewport_shade = nix_current_shade
    else:
        nix_current_shade = bpy.context.space_data.viewport_shade
        bpy.context.space_data.viewport_shade = 'MATERIAL'
    
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
                #create between image and emission node
                links = node_tree.links
                imgLink = links.new(texNodeNix.outputs[0], emitNodeNix.inputs[0])
       
def finalize():
    global nix_nodeError
    scene = bpy.context.scene
    if scene.toggle_material_bool == False or nix_nodeError:
        removeNodes();
        nix_nodeError = False
def removeNodes():
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
                mixNodeNix = None
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
                mixnodes = [n for n in matnodes if n.type == 'MIX_SHADER']         
                for n in mixnodes:
                    if n.name == 'mix_nix':
                        mixNodeNix = n
                #remove the added nix nodes from the material
                if texNodeNix:
                    node_tree.nodes.remove(texNodeNix)
                if emitNodeNix:
                    node_tree.nodes.remove(emitNodeNix)
                if mixNodeNix:
                    #relink to material node
                    goOn = True;
                    if len(mixNodeNix.inputs[1].links) > 0:
                        lastNode = mixNodeNix.inputs[1].links[0].from_node 
                    else:
                        goOn = False
                    if len(mixNodeNix.outputs[0].links) > 0:
                        outNode = mixNodeNix.outputs[0].links[0].to_node 
                    else:
                        goOn = False
                    links = node_tree.links
                    if goOn:
                        links.new(lastNode.outputs[0], outNode.inputs[0])#fixme: will choose wrong slot if lastNode used other than slot 0
                    node_tree.nodes.remove(mixNodeNix)
            
def bake(self):
    global nix_nodeError
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
            if len(obj.material_slots) > 0:
                matExists = True
            else:
                self.report({'ERROR'}, obj.name + " Requires Material")
                matExists = False
                
            if len(obj.data.uv_layers) > 0:
                uvExists = True
            else:
                self.report({'ERROR'}, obj.name + " Requires UV Mapping")
                uvExists = False
                
                
            if matExists == True and uvExists == True:
                for mat in obj.material_slots:
                    bpy.data.materials[mat.name].use_nodes = True
                    outNode = None
                    lastNode = None
                    lastNodeError = True
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
                        if len(outNode.inputs[0].links) > 0:
                            lastNode = outNode.inputs[0].links[0].from_node 
                            lastNodeError = False
                        else:
                            self.report({'ERROR'}, obj.name + " material nodes not connected to output.")
                            nix_nodeError = True
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
                    img_ext = '_bake'
                    if scene.img_name_ext_bool == True:
                        img_ext = img_ext + '_' + scene.cycles.bake_type
                    image_index = bpy.data.images.find(obj.name + img_ext)
                    if image_index == -1:
                        newimg = bpy.data.images.new(obj.name + img_ext,obj.nix_img_width,obj.nix_img_height)
                        node.image = newimg
                    else:
                        node.image = bpy.data.images[image_index]  
                        node.image.scale( obj.nix_img_width, obj.nix_img_height )
                                
                          
                       
                    #Link nodes together
                    node_tree = bpy.data.materials[mat.name].node_tree
                    links = node_tree.links
                    imgLink = links.new(texNodeNix.outputs[0], emitNodeNix.inputs[0])
                    links.new(emitNodeNix.outputs[0], mixNodeNix.inputs[2])
                    if scene.toggle_material_bool == True: 
                        if not mixNixExists and not lastNodeError:
                            links.new(lastNode.outputs[0], mixNodeNix.inputs[1]) #fixme: will choose wrong slot if lastNode used other than slot 0
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
        bakeType = scene.cycles.bake_type
        bpy.ops.object.bake(type=bakeType)
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
        finalize()
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
    
class OBJECT_OT_buttonEmpty(bpy.types.Operator):
    bl_label = 'Shade'
    bl_idname = 'nix.shade'
    bl_description = 'Toggle Viewport Shading'
    
    def execute(self, context): 
        shade()
        #self.report({'INFO'}, "Toggling viewport shading.")
        return{'FINISHED'}   
    
def register():
    bpy.utils.register_module(__name__)
        
def unregister():
        bpy.utils.unregister_module(__name__)
        
if __name__ == '__main__':
    register()
        
