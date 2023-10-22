from internal.filemanipulator import FileManipulator
import json

class Collision:

    fm = None
    json_root = {}

    def __init__(self, data, format_type="binary", endian="big"):
        if format_type == "binary":
            self.fm = FileManipulator()
            self.fm.from_bytes(data, endian)
            self.decompile()
        elif format_type == "json":
            self.json_root = data
        elif format_type == "text":
            self.json_root = json.loads(data)
        else:
            raise Exception("Invalid format type specified.")
    
    def decompile(self):
        self.fm.seek(0x0C)
        class_version = self.fm.r_int()
        self.fm.seek(0x28)
        contents_version = self.fm.r_str_null()
        self.json_root["class_version"] = class_version
        self.json_root["contents_version"] = contents_version
        supported = False
        if class_version == 7 and contents_version == "Havok-7.0.0-r1":
            supported = True
        if not supported:
            raise Exception("Unsupported collision version.")
        collisions = []
        self.fm.seek(0x370)
        exporter = self.fm.r_str_null()
        self.fm.align(16)
        source_path = self.fm.r_str_null()
        self.fm.align(16)
        self.json_root["exporter"] = exporter
        self.json_root["source_path"] = source_path
        self.fm.move(0x7C)
        num_collisions = self.fm.r_int()
        print(num_collisions)
        self.fm.move(0x70)
        for i in range(num_collisions):
            self.fm.move(0x220)
            collision = {}
            collsion_name = self.fm.r_str_null()
            collision["name"] = collsion_name
            self.fm.align(16)
            self.fm.move(0x50)
            self.fm.move(0x14)
            unknown = []
            num_unkown_values = self.fm.r_int()
            self.fm.move(8)
            for i in range(num_unkown_values):
                value = self.fm.r_byte()
                # convert to int
                value = int.from_bytes(value, "big")
                unknown.append(value)
            self.fm.align(16)
            self.fm.move(0x34)
            collision["unknown"] = unknown
            unknown_2 = []
            num_unkown_values_2 = self.fm.r_int()
            self.fm.move(0x138)
            for i in range(num_unkown_values_2):
                value = self.fm.r_ushort()
                unknown_2.append(value)
            self.fm.align(16)
            collision["unknown_2"] = unknown_2
            vertices = []
            faces = []
            self.fm.move(0x1C)
            num_vertices = self.fm.r_int()
            self.fm.move(0x20)
            num_faces = int(self.fm.r_int() / 4)
            self.fm.move(0x3C)
            for i in range(num_vertices):
                vertex = []
                for j in range(3):
                    value = self.fm.r_float()
                    vertex.append(value)
                vertices.append((vertex[0], vertex[1], vertex[2]))
                self.fm.move(4)
            for i in range(num_faces):
                face = []
                for j in range(3):
                    value = self.fm.r_int()
                    face.append(value)
                faces.append((face[0], face[1], face[2]))
                self.fm.move(4)

            collision["vertices"] = vertices
            collision["faces"] = faces
            collisions.append(collision)
        self.json_root["collisions"] = collisions

    def get_text(self):
        return json.dumps(self.json_root, indent=4)
        
    def get_json(self):
        return self.json_root

    def get_obj(self):
        text = ""
        text += """
        # Epic Mickey Collision\n
        # Extracted using EpicMickeyLib by Ryan "abso1utezer0" Koop\n
        #\n
        # Metadata:\n
        # Class Version: """ + str(self.json_root["class_version"]) + """\n
        # Contents Version: """ + self.json_root["contents_version"] + """\n
        # Exporter: """ + self.json_root["exporter"] + """\n
        # Source Path: """ + self.json_root["source_path"] + """\n\n"""
        largest_vertex_index = 0
        i = 0
        for collision in self.json_root["collisions"]:
            current_add_to = largest_vertex_index
            text += "# Collision: " + collision["name"] + "\n"
            text += "g collision_" + str(i) + "\n"
            text += "o " + collision["name"] + "\n"
            for vertex in collision["vertices"]:
                text += "v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n"
            largest_vertex_index += len(collision["vertices"])
            for face in collision["faces"]:
                text += "f " + str(face[0] + 1 + current_add_to) + " " + str(face[1] + 1 + current_add_to) + " " + str(face[2] + 1 + current_add_to) + "\n"
            text += "\n"
            i += 1
        return text
