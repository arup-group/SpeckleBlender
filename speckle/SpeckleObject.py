import json

class SpeckleObject(object):
    def __init__(self):
        self.type = "SpeckleObject"
        self._id = None
        self.hash = "1234"
        self.geometryHash = "5678"
        self.applicationId = "Blender"
        self.properties = []

class SpeckleMesh(SpeckleObject):
    def __init__(self):
        SpeckleObject.__init__( self )
        self.type = "Mesh"
        self.vertices = []
        self.faces = []
        self.colors = []

    def from_Lists(self, verts, faces):
        for v in verts:
            self.vertices.extend(v)

        for f in faces:
            if len(f) == 3:
                self.faces.append(0)
            elif len(f) == 4:
                self.faces.append(1)
            self.faces.extend(f)

    def to_json(self):
        return json.dumps(self.__dict__)

if __name__ == '__main__':

    verts = [(0,0,0), (0,0,1), (0,1,1), (0,1,0)]
    faces = [(0,1,2), (0,1,2,3), (1,2,3)]

    sm = SpeckleMesh()
    sm.from_Lists(verts, faces)
    j = sm.to_json()

    payload = {"objects":[x.__dict__ for x in [sm]]}
    print (json.dumps(payload))



