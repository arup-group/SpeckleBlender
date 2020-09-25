import bpy, idprop
from mathutils import Matrix

from .from_speckle import *
from .to_speckle import *
from bpy_speckle.util import find_key_case_insensitive

from speckle.base.resource import SCHEMAS
import speckle.schemas


FROM_SPECKLE_SCHEMAS = {
    SCHEMAS['Mesh']: import_mesh,
    SCHEMAS['Brep']: import_brep,
    SCHEMAS['Line']: import_curve,
    SCHEMAS['Polyline']: import_curve,
    SCHEMAS['Polycurve']: import_curve,
    SCHEMAS['Arc']: import_curve,
}


FROM_SPECKLE = {
    "Mesh": import_mesh, 
    "Brep": import_brep,
    "Curve": import_curve,
    "Line": import_curve,
    "Polyline": import_curve,
    "Polycurve":import_curve,
    "Arc":import_curve,
}


TO_SPECKLE = {
    "MESH": export_mesh,
    "CURVE": export_curve,
    "EMPTY": export_empty,
}

def set_transform(speckle_object, blender_object):
    transform = None
    if hasattr(speckle_object, "transform"):
        transform = speckle_object.transform
    elif speckle_object.properties is not None:
        transform = speckle_object.properties.get("transform", None)

    #transform = find_key_case_insensitive(speckle_object, "transform")
    if transform:
        if len(transform) == 16:
            mat = Matrix(
                [
                    transform[0:4],
                    transform[4:8],
                    transform[8:12],
                    transform[12:16]
                ]
                )
            blender_object.matrix_world = mat

def add_material(smesh, blender_object):
    if blender_object.data == None:
        return
        # Add material if there is one
    #props = find_key_case_insensitive(smesh, "properties")
    props = smesh.properties
    if props:
        material = find_key_case_insensitive(props, "material")
        if material:
            material_name = material.get('name', None)
            if material_name:
                #print ("bpySpeckle: Found material: %s" % material_name)

                mat = bpy.data.materials.get(material_name)

                if mat is None:
                    mat = bpy.data.materials.new(name=material_name)
                blender_object.data.materials.append(mat)
                #del smesh['properties']['material']
                del material


def try_add_property(speckle_object, blender_object, prop, prop_name):
    if prop in speckle_object.keys() and speckle_object[prop] is not None:
        blender_object[prop_name] = speckle_object[prop]


def add_dictionary(prop, blender_object, superkey=None):
    for key in prop.keys():
        key_name = "{}.{}".format(superkey, key) if superkey else "{}".format(key)
        if isinstance(prop[key], dict):
            subtype = prop[key].get("type", None)
            if subtype and subtype in FROM_SPECKLE.keys():
                continue
            else:
                add_dictionary(prop[key], blender_object, key_name)
        elif hasattr(prop[key], "type"):
            subtype = prop[key].type
            if subtype and subtype in FROM_SPECKLE.keys():
                continue
        else:
            try:
                blender_object[key_name] = prop[key]
            except KeyError:
                pass

def add_custom_properties(speckle_object, blender_object):

    if blender_object is None:
        return

    blender_object['_speckle_type'] = "Undefined"
    blender_object['_speckle_name'] = "SpeckleObject"

    if isinstance(speckle_object, dict):
        blender_object['_speckle_type'] = speckle_object.get("type", "Undefined")
        #blender_object['_speckle_transform'] = speckle_object.transform    
        blender_object['_speckle_name'] = speckle_object.get("name", "SpeckleObject")
        properties = speckle_object.get("properties", None)

    elif hasattr(speckle_object, "type"):
        blender_object['_speckle_type'] = speckle_object.type
        #blender_object['_speckle_transform'] = speckle_object.transform
        blender_object['_speckle_name'] = speckle_object.name
        properties = speckle_object.properties

    #try_add_property(speckle_object, blender_object, 'type', '_speckle_type')
    #try_add_property(speckle_object, blender_object, 'transform', '_speckle_transform')
    #try_add_property(speckle_object, blender_object, 'name', '_speckle_name')

    if properties:
        add_dictionary(properties, blender_object, "")

def dict_to_speckle_object(data):
    if 'type' in data.keys() and data['type'] in SCHEMAS.keys():
        obj = SCHEMAS[data['type']].parse_obj(data)
        for key in obj.properties.keys():
            if isinstance(obj.properties[key], dict):
                obj.properties[key] = dict_to_speckle_object(obj.properties[key])
            elif isinstance(obj.properties[key], list):
                for i in range(len(obj.properties[key])):
                    if isinstance(obj.properties[key][i], dict):
                        obj.properties[key][i] = dict_to_speckle_object(obj.properties[key][i])
        return obj
    else:
        for key in data.keys():
            if isinstance(data[key], dict):
                data[key] = dict_to_speckle_object(data[key])
            elif isinstance(data[key], list):
                for i in range(len(data[key])):
                    if isinstance(data[key][i], dict):
                        data[key][i] = dict_to_speckle_object(data[key][i])
        return data

def from_speckle_object(speckle_object, scale, name=None):

    if isinstance(speckle_object, dict):
        speckle_type = speckle_object.get("type", None)
        if speckle_type in SCHEMAS.keys():
            speckle_object = SCHEMAS[speckle_type].parse_obj(speckle_object)

            if speckle_object == None:
                return
        else:
            return
    if isinstance(speckle_object, speckle.schemas.SpeckleObject):
        if type(speckle_object) not in FROM_SPECKLE_SCHEMAS.keys():
            return

        if name:
            speckle_name = name
        elif speckle_object.name:
            speckle_name = speckle_object.name
        elif speckle_object.id:
            speckle_name = speckle_object.id
        else:
            speckle_name = "Unidentified Speckle Object"

        obdata = FROM_SPECKLE_SCHEMAS[type(speckle_object)](speckle_object, scale, speckle_name)

        if speckle_name in bpy.data.objects.keys():
            blender_object = bpy.data.objects[speckle_name]
            blender_object.data = obdata
            if hasattr(obdata, "materials"):
                blender_object.data.materials.clear()
        else:
            blender_object = bpy.data.objects.new(speckle_name, obdata) 


        blender_object.speckle.object_id = str(speckle_object.id)
        blender_object.speckle.enabled = True

        add_custom_properties(speckle_object, blender_object)
        add_material(speckle_object, blender_object)
        set_transform(speckle_object, blender_object)

        return blender_object 

    else:
        print("Invalid input:")
        print(speckle_object)
        return None

    '''
    speckle_type = speckle_object.type

    if speckle_type:

        subtypes = speckle_type.split('/')
        speckle_id = speckle_object.id

        if name:
            speckle_name = name
        elif speckle_id:
            speckle_name = speckle_id
        else:
            speckle_name = "Unidentified Speckle Object"

        obdata = None

        for st in reversed(subtypes):
            if st in FROM_SPECKLE.keys():
                obdata = FROM_SPECKLE[st](speckle_object, scale, speckle_name)
                break

        if obdata == None:
            print("Failed to convert {} type".format(speckle_type))

        if speckle_name in bpy.data.objects.keys():
            blender_object = bpy.data.objects[speckle_name]
            blender_object.data = obdata
            if hasattr(obdata, "materials"):
                blender_object.data.materials.clear()
        else:
            blender_object = bpy.data.objects.new(speckle_name, obdata) 


        #blender_object.speckle.object_id = speckle_object.id
        blender_object.speckle.enabled = True

        add_custom_properties(speckle_object, blender_object)
        add_material(speckle_object, blender_object)
        set_transform(speckle_object, blender_object)

        return blender_object             

    return None
    '''

def get_speckle_subobjects(attr, scale, name):

    subobjects = []
    for key in attr.keys():
        if isinstance(attr[key], dict):
            subtype = attr[key].get("type", None)
            if subtype:
                name = "{}.{}".format(name, key)
                #print("{} :: {}".format(name, subtype))
                subobject = from_speckle_object(attr[key], scale, name)
                add_custom_properties(attr[key], subobject)

                subobjects.append(subobject)
                props = attr[key].get("properties", None)
                if props:
                    subobjects.extend(get_speckle_subobjects(props, scale, name))
        elif hasattr(attr[key], "type"):
            subtype = attr[key].type
            if subtype:
                name = "{}.{}".format(name, key)
                #print("{} :: {}".format(name, subtype))
                subobject = from_speckle_object(attr[key], scale, name)
                add_custom_properties(attr[key], subobject)

                subobjects.append(subobject)
                props = attr[key].get("properties", None)
                if props:
                    subobjects.extend(get_speckle_subobjects(props, scale, name))
    return subobjects

ignored_keys=["speckle", "_speckle_type", "_speckle_name", "_speckle_transform", "_RNA_UI", "transform"]

def get_blender_custom_properties(obj, max_depth=1000):
    global ignored_keys

    if max_depth < 0:
        return obj
    
    if hasattr(obj, 'keys'):
        d = {}
        for key in obj.keys():
            if key in ignored_keys:
                continue
            d[key] = get_blender_custom_properties(obj[key], max_depth-1)
        return d
    elif isinstance(obj, list) or isinstance(obj, tuple) or isinstance(obj, idprop.types.IDPropertyArray):
        return [get_blender_custom_properties(o, max_depth-1) for o in obj]
    else:
        return obj


def to_speckle_object(blender_object, scale):
    blender_type = blender_object.type

    speckle_object = {}

    if blender_type in TO_SPECKLE.keys():
        speckle_object = TO_SPECKLE[blender_type](blender_object, scale)

    speckle_object.properties = get_blender_custom_properties(blender_object)

    # Set object transform
    #speckle_object.transform = [y for x in blender_object.matrix_world for y in x]
    speckle_object.properties['transform'] = [y for x in blender_object.matrix_world for y in x]

    return speckle_object

