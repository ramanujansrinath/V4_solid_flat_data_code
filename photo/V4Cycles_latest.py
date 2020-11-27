import bpy
from bpy_extras.object_utils import world_to_camera_view
import bmesh
import sys
import os
import math
from mathutils import Vector, Euler
import inspect

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)

def draw(vertSpec,faceSpec):
    print('Drawing medial axis form...')

    edges = []

    faces = []
    for face in faceSpec:
        faces.append((int(face[0])-1,int(face[1])-1,int(face[2])-1))

    vertScale = 1.5
    verts = []
    for vertex in vertSpec:
        verts.append((float(vertex[0])/vertScale,-1*float(vertex[2])/vertScale,float(vertex[1])/vertScale))
        
    # assemble Alden medial axis object
    me = bpy.data.meshes.new('AldenMesh')
    me.from_pydata(verts,edges,faces)
    ob = bpy.data.objects.new('AldenObject', me)
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.link(ob)
    bpy.context.scene.objects.active = ob
    ob.select = True
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
    
    # remove doubles from mesh and smooth surface
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.fill_holes()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.faces_shade_smooth()
    bpy.ops.mesh.mark_sharp(clear=True, use_verts=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
    return ob

def makeRamStimShader(aldenStim,material):
    mat = bpy.data.materials.new('Mat')
    mat.use_nodes = True
    mat.node_tree.nodes.remove(mat.node_tree.nodes[1])

    if material in ['Corrugated','Uncorrugated']:
        col = mat.node_tree.nodes.new('ShaderNodeBsdfGlass')
        col.inputs[0].default_value = (1.0,1.0,1.0,1.0)         # color
        col.inputs[1].default_value = 0.0                       # roughness
        col.inputs[2].default_value = 2.0                       # index of refraction

    elif material in ['Mirror','CorrugatedMirror']:
        col = mat.node_tree.nodes.new('ShaderNodeBsdfGlossy')
        col.inputs[0].default_value = (1.0,1.0,1.0,1.0)
        col.inputs[1].default_value = 0.0

    elif material in ['UVUnwrap']:
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = aldenStim
        aldenStim.select = True

        if len(aldenStim.data.uv_layers) == 0:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)
            bpy.ops.object.mode_set(mode='OBJECT')

        # add texture to diffuse
        root = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/TextureResources/'
        imageName = 'textureGrid.png'
        textureImage = root + imageName

        im = mat.node_tree.nodes.new('ShaderNodeTexImage')
        im.image = bpy.data.images.load(textureImage)
        col = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')

        texCoord = mat.node_tree.nodes.new('ShaderNodeTexCoord')
        mapping = mat.node_tree.nodes.new('ShaderNodeMapping')
        mapping.vector_type = 'TEXTURE'
        mapping.scale[0] = 1.2
        mapping.scale[1] = 1.2
        mapping.scale[2] = 1.2

        mat.node_tree.links.new(texCoord.outputs[2],mapping.inputs[0])
        mat.node_tree.links.new(mapping.outputs[0],im.inputs[0])
        mat.node_tree.links.new(im.outputs[0],col.inputs[0])

    elif material in ['Plain']:
        col = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
        col.inputs[0].default_value = (0.7,0.7,0.7,0.0)
        col.inputs[1].default_value = 0.0;
        # add plain stim code here

    if material in ['Corrugated','CorrugatedMirror']:
        bpy.context.scene.update()
        vertsGlobal = [aldenStim.matrix_world * v.co for v in aldenStim.data.vertices]
        x = [v[0] for v in vertsGlobal]
        y = [v[1] for v in vertsGlobal]
        z = [v[2] for v in vertsGlobal]
        multiplier = max([abs(max(x)-min(x)),abs(max(y)-min(y)),abs(max(z)-min(z))])/70

        corrugationTexture = bpy.data.textures.new('Corrugation',type='CLOUDS')
        corrugationTexture.noise_scale = 0.8
        corrugationTexture.nabla = 0.03
        corrugationTexture.noise_depth = 2.0

        bpy.ops.object.modifier_add(type='DISPLACE')
        corrugation = bpy.context.object.modifiers['Displace']
        corrugation.texture = corrugationTexture
        corrugation.strength = multiplier
        bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Displace')
    
    mat.node_tree.links.new(col.outputs[0],mat.node_tree.nodes[0].inputs[0])

    bpy.ops.object.material_slot_add()
    aldenStim.material_slots[0].material = mat
    bpy.ops.object.material_slot_assign()
    return

def correctAldenRotation(aldenStim,camera,sun,rotation,frontLight=0):

    # rotate alden stimulus to sit at 0,0,0, then rotate object to heighten camera
    bpy.ops.object.empty_add(type='PLAIN_AXES',radius=1,location=camera.location)
    rotEmpty = bpy.data.objects['Empty']
    rotEmpty.name = 'AldenZeroEmpty'

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = rotEmpty
    rotEmpty.select = True
    aldenStim.select = True

    bpy.ops.object.parent_set(type='OBJECT',keep_transform=False)

    rotZ = math.atan((rotEmpty.location[0]-aldenStim.location[0])/(rotEmpty.location[1]-aldenStim.location[1]))
    rotX = -math.atan((rotEmpty.location[2]-aldenStim.location[2])/(rotEmpty.location[1]-aldenStim.location[1]))

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = rotEmpty
    rotEmpty.select = True
    bpy.ops.transform.rotate(value=rotX,axis=(1,0,0),constraint_axis=(True,False,False),constraint_orientation='GLOBAL')
    bpy.ops.transform.rotate(value=rotZ,axis=(0,0,1),constraint_axis=(False,False,True),constraint_orientation='GLOBAL')

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = aldenStim
    aldenStim.select = True
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    deleteSingleObject(rotEmpty)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = aldenStim
    aldenStim.select = True
    camera.select = True

    if sun and frontLight==0:
        # create top-down sun lamp
        bpy.ops.object.lamp_add(type='SUN',location=(aldenStim.location[0],aldenStim.location[1],aldenStim.location[2]+math.sqrt((200)**2+(200)**2)),rotation=(0,0,0))

    elif sun and frontLight==1:
        bpy.ops.object.lamp_add(type='SUN',location=(camera.location[0],-500,camera.location[2]),rotation=(math.pi/2,0,0))

    elif sun and frontLight==2:
        # bpy.ops.object.lamp_add(type='SUN',location=(camera.location[0],-500,camera.location[2]),rotation=(math.pi/2,0,0))
        # bpy.ops.object.lamp_add(type='SUN',location=(camera.location[0],0,camera.location[2]+500),rotation=(math.pi/2,0,0))
        # bpy.ops.object.lamp_add(type='SUN',location=(camera.location[0],0,camera.location[2]-500),rotation=(math.pi/2,0,0))
        # bpy.ops.object.lamp_add(type='SUN',location=(camera.location[0]-500,0,camera.location[2]),rotation=(math.pi/2,0,0))
        # bpy.ops.object.lamp_add(type='SUN',location=(camera.location[0]+500,0,camera.location[2]),rotation=(math.pi/2,0,0))
        pass

    for s in bpy.data.objects:
        if s.name.startswith('Sun'):
            s.select = True

    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.scene.objects.active = aldenStim
    # aldenStim.select = True
    # camera.select = True

    bpy.ops.object.parent_set(type='OBJECT',keep_transform=False)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = aldenStim
    aldenStim.select = True
    bpy.ops.transform.rotate(value=-math.pi/180*2.2,axis=(1,0,0),constraint_axis=(True,False,False),constraint_orientation='GLOBAL')

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = camera
    camera.select = True

    for s in bpy.data.objects:
        if s.name.startswith('Sun'):
            s.select = True

    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    return

###
###         ENVIRONMENT: TEXTURE SURFACE
###

def sphericalSurface(aldenStim):

    bpy.context.scene.update()
    vertsGlobal = [aldenStim.matrix_world * v.co for v in aldenStim.data.vertices]
    x = [v[0] for v in vertsGlobal]
    y = [v[1] for v in vertsGlobal]
    z = [v[2] for v in vertsGlobal]
    radiusOptions = [abs(max(x)-aldenStim.location[0]),abs(max(y)-aldenStim.location[1]),abs(min(x)-aldenStim.location[0]),abs(min(y)-aldenStim.location[1]),abs(min(z)-aldenStim.location[2])]

    bpy.ops.mesh.primitive_uv_sphere_add(size=max(radiusOptions)*math.sqrt(2),location=aldenStim.location,rotation=(0,0,0))
    bpy.ops.object.transform_apply(rotation=True)
    bowl = bpy.data.objects['Sphere']
    bowl.name = 'Bowl'

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = bowl
    bowl.select = True

    bpy.ops.object.shade_smooth()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=1)
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.context.scene.update()
    vertices = [vert for vert in bmesh.from_edit_mesh(bpy.context.object.data).verts]

    for ver in vertices:
        verGlobalZ = aldenStim.matrix_world * ver.co

        if verGlobalZ[2] > aldenStim.location[2]:
            ver.select = True

    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return bowl

def walls(aldenStim):

    bpy.ops.object.select_all(action='DESELECT')
    scn.objects.active = aldenStim
    aldenStim.select = True

    bpy.context.scene.update()
    vertsGlobal = [aldenStim.matrix_world * v.co for v in aldenStim.data.vertices]
    x = [v[0] for v in vertsGlobal]
    minX = min(x)
    maxX = max(x)
    maxYshift = max([v[1] for v in vertsGlobal])-aldenStim.location[1]

    bpy.ops.transform.rotate(value=-math.pi/180*50,axis=(0,0,1),constraint_axis=(False,False,True),constraint_orientation='GLOBAL')
    bpy.ops.object.transform_apply(rotation=True)

    bpy.context.scene.update()
    vertsGlobal = [aldenStim.matrix_world * v.co for v in aldenStim.data.vertices]
    minZ = min([v[2] for v in vertsGlobal])
    y = [v[1] for v in vertsGlobal]
    x = [v[0] for v in vertsGlobal]
    maxYL = max(y)

    bpy.ops.mesh.primitive_plane_add(radius=160,location=(-160+maxYshift,maxYL,160+minZ),rotation=(math.pi/2,0,0))
    wallL = bpy.data.objects['Plane']
    wallL.name = 'Left Wall'

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = aldenStim
    aldenStim.select = True
    wallL.select = True
    bpy.ops.object.parent_set(type='OBJECT',keep_transform=False)

    bpy.ops.object.select_all(action='DESELECT')
    scn.objects.active = aldenStim
    aldenStim.select = True

    bpy.ops.transform.rotate(value=math.pi/180*120,axis=(0,0,1),constraint_axis=(False,False,True),constraint_orientation='GLOBAL')
    bpy.ops.object.transform_apply(rotation=True)

    bpy.context.scene.update()
    vertsGlobal = [aldenStim.matrix_world * v.co for v in aldenStim.data.vertices]
    minZ = min([v[2] for v in vertsGlobal])
    y = [v[1] for v in vertsGlobal]
    x = [v[0] for v in vertsGlobal]
    maxYR = max(y)

    bpy.ops.mesh.primitive_plane_add(radius=160,location=(160-maxYshift,maxYR,160+minZ),rotation=(math.pi/2,0,0))
    wallR = bpy.data.objects['Plane']
    wallR.name = 'Right Wall'

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = aldenStim
    aldenStim.select = True
    wallR.select = True
    bpy.ops.object.parent_set(type='OBJECT',keep_transform=False)

    bpy.ops.object.select_all(action='DESELECT')
    scn.objects.active = aldenStim
    aldenStim.select = True

    bpy.ops.transform.rotate(value=-math.pi/180*70,axis=(0,0,1),constraint_axis=(False,False,True),constraint_orientation='GLOBAL')
    bpy.ops.object.transform_apply(rotation=True)

    bpy.ops.object.select_all(action='DESELECT')
    scn.objects.active = wallL
    wallL.select = True

    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    bpy.ops.object.select_all(action='DESELECT')
    scn.objects.active = wallR
    wallR.select = True

    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    return wallL, wallR

def triHorizon(aldenStim):

    bpy.context.scene.update()
    vertsGlobal = [aldenStim.matrix_world * v.co for v in aldenStim.data.vertices]
    maxY = max([v[1] for v in vertsGlobal])
    minZ = min([v[2] for v in vertsGlobal])

    startPos = -500
    height = 1000
    width = 500
    centerX = 0

    edges = []
    verts = [(-1,startPos,minZ),(width,startPos+height,minZ),(-width,startPos+height,minZ),(1,startPos,minZ)]
    faces = [(0,1,2,3)]

    me = bpy.data.meshes.new('Horizon')
    me.from_pydata(verts,edges,faces)
    horizonVisible = bpy.data.objects.new('Horizon', me)
    
    bpy.ops.object.select_all(action='DESELECT')
    scn.objects.link(horizonVisible)

    horizonVisible.location += Vector((0,43,0))
    return horizonVisible

###
###         ENVIRONMENT: TEXTURE SELECTION
###

def lightingSetupHDR(aldenStim):

    scn = bpy.context.scene

    # position and orient single center camera
    bpy.ops.object.camera_add(location=(0,-500,0), rotation=(math.pi/2,0,0))
    camera = bpy.data.objects['Camera']
    scn.camera = camera

    camera.data.type = 'PERSP'
    camera.data.clip_end = 4000
    camera.data.lens = 500
    camera.data.sensor_fit = 'HORIZONTAL'
    camera.data.sensor_width = 160

    bpy.ops.object.empty_add(type='PLAIN_AXES',radius=1,location=(0,0,0))
    skyEmpty = bpy.data.objects['Empty']
    skyEmpty.name = 'SkyEmpty'

    w = scn.world
    root = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/TextureResources/pro_lighting_skies_demo_hdris/'

    w.use_nodes = True
    texCoord = w.node_tree.nodes.new('ShaderNodeTexCoord')
    texCoord.object = skyEmpty
    jpg = w.node_tree.nodes.new('ShaderNodeTexEnvironment')
    jpg.image = bpy.data.images.load(root+'cloudy08_high.jpg')
    exr = w.node_tree.nodes.new('ShaderNodeTexEnvironment')
    exr.image = bpy.data.images.load(root+'cloudy08_EXR.exr')
    multiply = w.node_tree.nodes.new('ShaderNodeMath')
    multiply.operation = 'MULTIPLY'
    multiply.inputs[1].default_value = 0.2
    add = w.node_tree.nodes.new('ShaderNodeMath')
    add.operation = 'ADD'
    add.inputs[1].default_value = 1.0
    mix = w.node_tree.nodes.new('ShaderNodeMixShader')
    background1 = w.node_tree.nodes[1]
    background2 = w.node_tree.nodes.new('ShaderNodeBackground')
    light = w.node_tree.nodes.new('ShaderNodeLightPath')
    output = w.node_tree.nodes[0]

    w.node_tree.links.new(texCoord.outputs[3],jpg.inputs[0])
    w.node_tree.links.new(texCoord.outputs[3],exr.inputs[0])
    w.node_tree.links.new(jpg.outputs[0],background1.inputs[0])
    w.node_tree.links.new(exr.outputs[0],background2.inputs[0])
    w.node_tree.links.new(exr.outputs[0],multiply.inputs[0])
    w.node_tree.links.new(multiply.outputs[0],add.inputs[0])
    w.node_tree.links.new(add.outputs[0],background1.inputs[1])
    w.node_tree.links.new(add.outputs[0],background2.inputs[1])
    w.node_tree.links.new(background1.outputs[0],mix.inputs[2])
    w.node_tree.links.new(background2.outputs[0],mix.inputs[1])
    w.node_tree.links.new(light.outputs[0],mix.inputs[0])
    w.node_tree.links.new(mix.outputs[0],output.inputs[0])

    bottomLessThan = w.node_tree.nodes.new('ShaderNodeMath')
    bottomLessThan.operation = 'LESS_THAN'
    bottomLessThan.inputs[1].default_value = 0.01
    bottomAdd = w.node_tree.nodes.new('ShaderNodeMixRGB')
    bottomAdd.blend_type = 'ADD'
    bottomColor = w.node_tree.nodes.new('ShaderNodeRGB')
    bottomColor.outputs[0].default_value = (0.072,0.072,0.072,1.0)

    w.node_tree.links.new(exr.outputs[0],bottomLessThan.inputs[0])
    w.node_tree.links.new(exr.outputs[0],bottomAdd.inputs[1])
    w.node_tree.links.new(bottomColor.outputs[0],bottomAdd.inputs[2])
    w.node_tree.links.new(bottomLessThan.outputs[0],bottomAdd.inputs[0])
    w.node_tree.links.new(bottomAdd.outputs[0],background2.inputs[0])

    bpy.context.scene.world.light_settings.use_indirect_light = True
    bpy.context.scene.world.light_settings.gather_method = 'APPROXIMATE'
    bpy.context.scene.world.light_settings.passes = 3

    bpy.context.scene.update()
    vertsGlobal = [aldenStim.matrix_world * v.co for v in aldenStim.data.vertices]
    z = [v[2] for v in vertsGlobal]
    centerHeight = (max(z)-min(z))/2

    skyEmpty.location = Vector((0,0,-0.03-centerHeight/1000)) # subtract the amount of alden scaling
    skyEmpty.rotation_euler = Euler((0,0,math.pi/180*180))

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = skyEmpty
    skyEmpty.select = True

    bpy.ops.transform.resize(value=(10,10,5),constraint_axis=(True, True, True))

    correctAldenRotation(aldenStim,camera,False,-math.pi/180*2.2)
    return

def lightingSetupPlain(aldenStim):

    scn = bpy.context.scene

    # position and orient single, center camera
    bpy.ops.object.camera_add(location=(0,-500,0), rotation=(math.pi/2,0,0))
    camera = bpy.data.objects['Camera']
    scn.camera = camera

    camera.data.type = 'PERSP'
    camera.data.clip_end = 4000
    camera.data.lens = 500
    camera.data.sensor_fit = 'HORIZONTAL'
    camera.data.sensor_width = 160

    # sky gray with sunlight
    bpy.context.scene.world.use_nodes = True
    background = bpy.context.scene.world.node_tree.nodes[1]
    background.inputs[1].default_value = 1.0
    background.inputs[0].default_value = (0.072,0.072,0.072,1.0)
    bpy.context.scene.world.node_tree.links.new(background.outputs[0],bpy.context.scene.world.node_tree.nodes[0].inputs[0])

    correctAldenRotation(aldenStim,camera,True,-math.pi/180*2.2)
    return

def lightingSetupFront(aldenStim):

    scn = bpy.context.scene

    # position and orient single, center camera
    bpy.ops.object.camera_add(location=(0,-500,0), rotation=(math.pi/2,0,0))
    camera = bpy.data.objects['Camera']
    scn.camera = camera

    camera.data.type = 'PERSP'
    camera.data.clip_end = 4000
    camera.data.lens = 500
    camera.data.sensor_fit = 'HORIZONTAL'
    camera.data.sensor_width = 160

    # sky gray with sunlight
    bpy.context.scene.world.use_nodes = True
    background = bpy.context.scene.world.node_tree.nodes[1]
    background.inputs[1].default_value = 1.0
    background.inputs[0].default_value = (0.072,0.072,0.072,1.0)
    bpy.context.scene.world.node_tree.links.new(background.outputs[0],bpy.context.scene.world.node_tree.nodes[0].inputs[0])

    correctAldenRotation(aldenStim,camera,True,-math.pi/180*2.2,frontLight=1)
    return

def lightingSetupFive(aldenStim):

    scn = bpy.context.scene

    # position and orient single, center camera
    bpy.ops.object.camera_add(location=(0,-500,0), rotation=(math.pi/2,0,0))
    camera = bpy.data.objects['Camera']
    scn.camera = camera

    camera.data.type = 'PERSP'
    camera.data.clip_end = 4000
    camera.data.lens = 500
    camera.data.sensor_fit = 'HORIZONTAL'
    camera.data.sensor_width = 160

    # sky gray with sunlight
    bpy.context.scene.world.use_nodes = True
    background = bpy.context.scene.world.node_tree.nodes[1]
    background.inputs[1].default_value = 1.0
    # background.inputs[0].default_value = (0.072,0.072,0.072,1.0)
    background.inputs[0].default_value = (1.0,1.0,1.0,1.0)
    bpy.context.scene.world.node_tree.links.new(background.outputs[0],bpy.context.scene.world.node_tree.nodes[0].inputs[0])

    correctAldenRotation(aldenStim,camera,True,-math.pi/180*2.2,frontLight=2)
    return

def makeEnvironmentTexture(environment,kind='Bowl'):

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = environment
    environment.select = True

    mat = bpy.data.materials.new('Mat')
    mat.use_nodes = True

    if kind == 'Bowl':
        makeFade(environment)

        light = mat.node_tree.nodes.new('ShaderNodeLightPath')
        transp = mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
        mix = mat.node_tree.nodes.new('ShaderNodeMixShader')

        diffuse = mat.node_tree.nodes[1]
        diffuse.inputs[0].default_value = (1.0,1.0,1.0,1.0)

        attr = mat.node_tree.nodes.new('ShaderNodeAttribute')
        attr.attribute_name = 'Fading Bowl'
        mix2 = mat.node_tree.nodes.new('ShaderNodeMixShader')

        mat.node_tree.links.new(light.outputs[0],mix.inputs[0])
        mat.node_tree.links.new(mix2.outputs[0],mix.inputs[1])
        mat.node_tree.links.new(transp.outputs[0],mix.inputs[2])
        mat.node_tree.links.new(transp.outputs[0],mix2.inputs[2])
        mat.node_tree.links.new(diffuse.outputs[0],mix2.inputs[1])
        mat.node_tree.links.new(attr.outputs[0],mix2.inputs[0])
        mat.node_tree.links.new(mix.outputs[0],mat.node_tree.nodes[0].inputs[0])
        shift = 0

    elif kind in ['Floor_Hex','Dense_Scrub','Cracked_Soil','Wall_Wooden','Wall_Mosaic']:

        root = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/TextureResources/textures_com/'
        
        if len(environment.data.uv_layers) == 0:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)

            bpy.ops.mesh.subdivide(number_cuts=100)
            bpy.ops.mesh.subdivide(number_cuts=2)
            bpy.ops.object.mode_set(mode='OBJECT')

        texCoord = mat.node_tree.nodes.new('ShaderNodeTexCoord')
        mapping = mat.node_tree.nodes.new('ShaderNodeMapping')
        mapping.vector_type = 'TEXTURE'

        # displacement part one:
        wallDisp = bpy.data.textures.new('Displacement',type='IMAGE')
        bpy.ops.object.modifier_add(type='DISPLACE')
        wallTex = bpy.context.object.modifiers['Displace']
        wallTex.texture = wallDisp
        wallTex.texture_coords = 'UV'
        
        extraFloor = bpy.context.scene.world.node_tree.nodes['RGB'].outputs[0]

        if kind == 'Wall_Wooden':
            mapping.scale[0] = 0.25
            mapping.scale[1] = 0.25
            mapping.scale[2] = 0.25
            wallTex.strength = 0.3
            shift = wallTex.strength
            wallTex.mid_level = 1.0

        elif kind == 'Wall_Mosaic':
            mapping.scale[0] = 0.3/4
            mapping.scale[1] = 0.3/4
            mapping.scale[2] = 0.3/4
            wallTex.strength = 0.1
            shift = wallTex.strength
            wallTex.mid_level = 1.0

        elif kind == 'Floor_Hex':
            mapping.scale[0] = 0.15/2
            mapping.scale[1] = 0.3/2*1.5
            mapping.scale[2] = 0.15/2
            wallTex.strength = 0.2
            shift = wallTex.strength
            wallTex.mid_level = 0.0
            extraFloor.default_value = (0.279,0.246,0.205,1.0)

        elif kind == 'Cracked_Soil':
            mapping.scale[0] = 0.1/2
            mapping.scale[1] = 0.2/2*1.5
            mapping.scale[2] = 0.1/2
            bpy.ops.object.shade_smooth()
            wallTex.strength = 1.0
            shift = wallTex.strength
            wallTex.mid_level = 0.0
            extraFloor.default_value = (0.098,0.084,0.080,1.0)

        elif kind == 'Dense_Scrub':
            mapping.scale[0] = 0.05/2
            mapping.scale[1] = 0.25/2*1.5
            mapping.scale[2] = 0.25/2
            bpy.ops.object.shade_smooth()
            wallTex.strength = 0.2
            shift = wallTex.strength
            wallTex.mid_level = 0.0
            makeScrub(environment,kind)
            kind = 'Scrub'
            extraFloor.default_value = (0.231,0.216,0.181,1.0)

        # displacement part two:
        wallDisp.image = bpy.data.images.load(root+kind+'_Displace.jpg')
        wallDisp.crop_max_x = 1/mapping.scale[0]
        wallDisp.crop_max_y = 1/mapping.scale[1]

        if kind == 'Floor_Hex':
            bpy.ops.object.modifier_remove(modifier='Displace')

        else:
            bpy.ops.object.modifier_apply(apply_as='DATA',modifier='Displace')

        im = mat.node_tree.nodes.new('ShaderNodeTexImage')
        im.image = bpy.data.images.load(root+kind+'.jpg')

        imNormal = mat.node_tree.nodes.new('ShaderNodeTexImage')
        imNormal.image = bpy.data.images.load(root+kind+'_Normal.jpg')
        imNormal.color_space = 'NONE'

        diffuse = mat.node_tree.nodes[1]
        normalMap = mat.node_tree.nodes.new('ShaderNodeNormalMap')

        mat.node_tree.links.new(texCoord.outputs[2],mapping.inputs[0])
        mat.node_tree.links.new(diffuse.outputs[0],mat.node_tree.nodes[0].inputs[0])
        mat.node_tree.links.new(mapping.outputs[0],im.inputs[0])
        mat.node_tree.links.new(mapping.outputs[0],imNormal.inputs[0])
        mat.node_tree.links.new(im.outputs[0],diffuse.inputs[0])
        mat.node_tree.links.new(imNormal.outputs[0],normalMap.inputs[1])
        mat.node_tree.links.new(normalMap.outputs[0],diffuse.inputs[2])

    bpy.ops.object.material_slot_add()
    environment.material_slots[0].material = mat
    bpy.ops.object.material_slot_assign()  
    return shift

def makeFade(environment):

    colorLayer = environment.data.vertex_colors.new('Fading Bowl')

    verts = [v for v in environment.data.vertices]
    allZ = [v.co.z for v in verts]
    minZ = min(allZ)
    maxZ = max(allZ)

    for face in environment.data.polygons:
        for vert,loop in zip(face.vertices,face.loop_indices):
            colorMulti = (verts[vert].co.z-minZ)/(maxZ-minZ)
            colorLayer.data[loop].color = (1.0*colorMulti,1.0*colorMulti,1.0*colorMulti) #,1.0*colorMulti)

    return

###
###         SCRUB
###

def stereotypicalGrass(xMin=None,xMax=None,yMin=None,yMax=None,leeway=None):

    # load plants for grouping
    root = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/TextureResources/'
    numVarieties = 4

    for hue in range(0,numVarieties):
        bpy.ops.wm.collada_import(filepath=root+'scrubBlockPlantFinal.dae')

    # add plants to group
    plants1 = [p for p in bpy.context.scene.objects if p.name.startswith('Plant1')]
    plants2 = [p for p in bpy.context.scene.objects if p.name.startswith('Plant2')]
    bpy.ops.object.group_add()
    bpy.data.groups[0].name = 'Grasses'

    # resize and color plant1
    for hue in range(0,numVarieties):
        plant = plants1[hue]

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = plant
        plant.select = True
        plant.location = Vector((0,0,4000))
        bpy.ops.transform.resize(value=(12,12,12),constraint_axis=(True, True, True))
        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.object.group_link(group='Grasses')
        plantHue(plant,hue)

    # resize and color plant2
    for hue in range(0,numVarieties):
        plant = plants2[hue]

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = plant
        plant.select = True
        plant.location = Vector((0,0,4000))
        bpy.ops.transform.resize(value=(12,12,12),constraint_axis=(True, True, True))
        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.object.group_link(group='Grasses')
        plantHue(plant,hue)
    return

def plantHue(plant,plantHue):

    shade = 2

    if plantHue == 0:
        dark = (0.105/shade,0.108/shade,0.042/shade,1.0)
        light = (0.26/shade,0.22/shade,0.11/shade,1.0)
        plant.rotation_euler[2] = math.pi*0/2

    elif plantHue == 1:
        dark = (0.108/shade,0.071/shade,0.043/shade,1.0)
        light = (0.26/shade,0.20/shade,0.09/shade,1.0)
        plant.rotation_euler[2] = math.pi*1/2

    elif plantHue == 2:
        dark = (0.105/shade,0.108/shade,0.042/shade,1.0)
        light = (0.20/shade,0.17/shade,0.08/shade,1.0)
        plant.rotation_euler[2] = math.pi*2/2

    elif plantHue == 3:
        dark = (0.105/shade,0.108/shade,0.042/shade,1.0)
        light = (0.38/shade,0.32/shade,0.15/shade,1.0)
        plant.rotation_euler[2] = math.pi*3/2

    matGradient = bpy.data.materials.new('Mat')
    matGradient.use_nodes = True
    gradient = matGradient.node_tree.nodes.new('ShaderNodeValToRGB')
    gradient.color_ramp.elements[0].color = dark
    gradient.color_ramp.elements[0].position = 0.0
    gradient.color_ramp.elements[1].color = light
    gradient.color_ramp.elements[1].position = 1.0
    matGradient.node_tree.links.new(gradient.outputs[0],matGradient.node_tree.nodes[1].inputs[0])
    bpy.ops.object.material_slot_add()
    plant.material_slots[0].material = matGradient
    bpy.ops.object.material_slot_assign()
    return

def makeScrub(horizon,kind,xMin=None,xMax=None,yMin=None,yMax=None,leeway=None):

    stereotypicalGrass()
    bpy.context.scene.objects.active = horizon
    bpy.ops.object.select_all(action='DESELECT')
    horizon.select = True

    particlesOrig = [p for p in bpy.data.particles]
    bpy.ops.object.particle_system_add()
    particles = [p for p in bpy.data.particles]
    particleGroup = [p for p in particles if p not in particlesOrig][0]
    particleGroup.type = 'HAIR'

    particleGroup.render_type = 'GROUP'
    particleGroup.dupli_group = bpy.data.groups['Grasses']
    particleGroup.use_rotation_dupli = True

    particleGroup.size_random = 0.5
    particleGroup.particle_size = 0.05
    particleGroup.child_type = 'INTERPOLATED'
    particleGroup.child_length = 0.8
    particleGroup.roughness_1_size = 10
    particleGroup.clump_factor = 0.1

    particleGroup.use_advanced_hair = True
    particleGroup.use_rotations = True
    particleGroup.rotation_mode = 'OB_X'

    particleGroup.count = 20
    particleGroup.child_nbr = 50
    particleGroup.rendered_child_count = 50

    if kind == 'Dense_Scrub':
        particleGroup.count = 200

    verts = horizon.data.vertices

    # bpy.ops.paint.weight_gradient() api context problem
    # workaround: Ko. on blenderartists.org forum: https://blenderartists.org/forum/showthread.php?400534-Weight-Paint-Scripting-Context-Issue
    if not horizon.vertex_groups:
        horizon.vertex_groups.new(name='Sv_VGroup')

    obVertexGroup = horizon.vertex_groups[0]

    for vertex in verts:
        vertGlobal = horizon.matrix_world * vertex.co

        if xMin == None:
            obVertexGroup.add([vertex.index],1.4-(vertex.co.y+1)/50,'REPLACE')

        else:

            if vertGlobal[0] > (xMin-leeway) and vertGlobal[0] < (xMax+leeway) and vertGlobal[1] > (yMin-leeway) and vertGlobal[1] < (yMax+leeway):
                obVertexGroup.add([vertex.index],0.0,'REPLACE')

            else:
                obVertexGroup.add([vertex.index],1.4-(vertex.co.y+1)/50,'REPLACE')

    horizon.data.update()
    bpy.ops.texture.new()
    tex = bpy.data.textures[0]
    tex.type = 'VORONOI'
    slot = particleGroup.texture_slots.add()
    slot.texture = tex
    slot.use_map_length = True
    slot.use_map_clump = True
    return

###
###         RENDER
###

def render(destination):

    bpy.context.scene.render.filepath = destination
    bpy.context.scene.frame_set(0)
    bpy.ops.render.render(write_still=True)
    return

def deleteAllObjects():

    while bpy.context.scene.objects:

        for ob in bpy.context.scene.objects:
            bpy.context.scene.objects.active = ob
            bpy.ops.object.select_all(action='DESELECT')
            ob.select = True
            bpy.ops.object.delete(use_global=False)

    deleteAllNodes()
    return

def deleteAllNodes():

    if bpy.context.scene.world.node_tree:

        for node in bpy.context.scene.world.node_tree.nodes:

            if node not in [bpy.context.scene.world.node_tree.nodes[0],bpy.context.scene.world.node_tree.nodes[1]]:
                bpy.context.scene.world.node_tree.nodes.remove(node)

    return

def deleteSingleObject(ob):

    bpy.context.scene.objects.active = ob
    bpy.ops.object.select_all(action='DESELECT')
    ob.select = True
    bpy.ops.object.delete(use_global=False)
    return

###
###         MAIN
###

def doLandscape(aldenStim,landscapeType):

    lightingSetupHDR(aldenStim)                         # HDR lighting
    plane = triHorizon(aldenStim)
    aldenShift = makeEnvironmentTexture(plane,landscapeType)
    plane.location[2] = plane.location[2] - aldenShift
    return

def doRoom(aldenStim,floorType,wallLtype,wallRtype):

    lightingSetupHDR(aldenStim)                         # HDR lighting
    plane = triHorizon(aldenStim)
    wallL,wallR = walls(aldenStim)
    aldenShift = makeEnvironmentTexture(plane,floorType)
    makeEnvironmentTexture(wallL,wallLtype)
    makeEnvironmentTexture(wallR,wallRtype)
    plane.location[2] = plane.location[2] - aldenShift
    wallL.location[2] = wallL.location[2] - aldenShift
    wallR.location[2] = wallR.location[2] - aldenShift
    return

def main(vertSpec,faceSpec,environmentDetail,outputDestination):
    # mirror   glass
    # 0 	 5 closed
    # 1 	 6 open grass
    # 2 	 7 open soil
    # 3 	 8 uncorrugated bowl
    # 4 	 9 corrugated bowl

    deleteAllObjects()
    aldenStim = draw(vertSpec,faceSpec)

    if environmentDetail in range(0,4):
        makeRamStimShader(aldenStim,'Mirror')

    elif environmentDetail == 4:
        makeRamStimShader(aldenStim,'CorrugatedMirror')

    elif environmentDetail in range(5,9):
        makeRamStimShader(aldenStim,'Uncorrugated')

    elif environmentDetail == 9:
        makeRamStimShader(aldenStim,'Corrugated')

    elif environmentDetail == 10:
        makeRamStimShader(aldenStim,'UVUnwrap')

    elif environmentDetail == 11:
        makeRamStimShader(aldenStim,'Plain')

    # closed [Mirror, Uncorrugated]
    if environmentDetail in [0,5]:
        floorType = 'Floor_Hex'
        wallLtype = 'Wall_Mosaic'
        wallRtype = 'Wall_Wooden'
        doRoom(aldenStim,floorType,wallLtype,wallRtype)

    # open grass [Mirror, Uncorrugated]
    elif environmentDetail in [1,6]:
        landscapeType = 'Dense_Scrub'
        doLandscape(aldenStim,landscapeType)

    # open soil [Mirror, Uncorrugated]
    elif environmentDetail in [2,7]:
        landscapeType = 'Cracked_Soil'
        doLandscape(aldenStim,landscapeType)

    # bowl [Mirror, CorrugatedMirror, Uncorrugated, Corrugated]
    elif environmentDetail in [3,4,8,9]:
        lightingSetupPlain(aldenStim)
        bowl = sphericalSurface(aldenStim)
        makeEnvironmentTexture(bowl,'Bowl')

    elif environmentDetail in [11]:
        lightingSetupFront(aldenStim)

    elif environmentDetail in [10]:
        lightingSetupFive(aldenStim)

    bpy.context.scene.render.resolution_x = 1280
    bpy.context.scene.render.resolution_y = 960
    render(outputDestination) 
    return

###
###         BLENDER INSTANCE RESET & SETUP, RUN MAIN
###

scn = bpy.context.scene

# use cycles render engine
scn.render.engine = 'CYCLES'

# use GPU
scn.cycles.device = 'CPU'

# bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
# devs = bpy.context.user_preferences.addons['cycles'].preferences.devices
# for d in devs:
#     if d.type == 'CUDA':
#         d.use = True
#     else:
#         d.use = False

bpy.context.scene.render.tile_x = 32
bpy.context.scene.render.tile_y = 32
bpy.context.scene.render.resolution_percentage = 100

# remove caustics to get rid of fireflies
scn.cycles.caustics_refractive = False
scn.cycles.caustics_reflective = False
scn.cycles.samples = 512

if __name__ == "__main__":
    main()
