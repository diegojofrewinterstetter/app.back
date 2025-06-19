from datetime import datetime
from bson import ObjectId
from typing import List, Optional, Union

class Certificaciones:
    def __init__(self, nombre: str = "", institucion: str = "", ano: str = "", url: str = ""):
        self.nombre = nombre
        self.institucion = institucion
        self.ano = ano
        self.url = url

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "institucion": self.institucion,
            "ano": self.ano,
            "url": self.url
        }

class Matricula:
    def __init__(self, estado: str = "", url: str = ""):
        self.estado = estado
        self.url = url
    def to_dict(self):
        return {
            "estado": self.estado,
            "url": self.url
        }
    
class Ubicacion:
    def __init__(self, ciudad: str = "", direccion: str = "", localidad: str = "", latitud: float = 0.0, longitud: float = 0.0):
        self.ciudad = ciudad
        self.direccion = direccion
        self.localidad = localidad
        self.latitud = latitud
        self.longitud = longitud
    
    def getCiudad(self):
        return self.ciudad
    
    def to_dict(self):
        return {
            "ciudad": self.ciudad,
            "direccion": self.direccion,
            "localidad": self.localidad,
            "latitud": self.latitud,
            "longitud": self.longitud
        }

class Opinion:
    def __init__(self, uid=None, comentario="", puntaje=0, timestamp=None):
        self.uid = uid
        self.comentario = comentario
        self.puntaje = puntaje
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "uid": self.uid,
            "comentario": self.comentario,
            "puntaje": self.puntaje,
            "timestamp": self.timestamp
        }

class Post:
    def __init__(self, titulo, descripcion, uid, fecha_post, ubicacion, certificaciones, opiniones, rubs=None, fotos=None, id=None, matricula=None, puntaje_promedio=None, latitud=0.0, longitud=0.0, ciudad=""):
        self.title = titulo
        self.description = descripcion
        self.uid = uid
        self.fecha_post = fecha_post
        self.matricula = matricula
        self.ubicacion = ubicacion
        self.coordenadas = [latitud, longitud]
        self.certificaciones = certificaciones  # ahora es string
        self.opiniones = opiniones
        self.fotos = fotos
        self.puntaje_promedio = puntaje_promedio
        self.id = id
        self.rubs = rubs or []
        self.ciudad = ciudad

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "puntaje_promedio": self.puntaje_promedio,
            "matricula": self.matricula.to_dict() if hasattr(self.matricula, "to_dict") else self.matricula,
            "coordenadas": self.coordenadas,
            "uid": self.uid,
            "fecha_post": self.fecha_post,
            "ubicacion": self.ubicacion.to_dict() if self.ubicacion else None,
            "certificaciones": self.certificaciones,  # string
            "opiniones": [op.to_dict() for op in self.opiniones],
            "rubs": [str(rub) for rub in self.rubs] if self.rubs else [],
            "fotos": self.fotos,
            "_id": str(self.id) if self.id else None
        }

    @classmethod
    def from_dict(cls, data):
        ubicacion = Ubicacion(**data['ubicacion']) if 'ubicacion' in data and data['ubicacion'] else None
        opiniones = [Opinion(**op) for op in data.get('opiniones', [])]
        raw_coords = data.get('coordenadas', [0.0, 0.0])
        if isinstance(raw_coords, dict):
            coords = raw_coords.get('coordinates', [0.0, 0.0])
        else:
            coords = raw_coords
        latitud = coords[0] if len(coords) > 0 else 0.0
        longitud = coords[1] if len(coords) > 1 else 0.0

        return cls(
            titulo=data.get('title', ''),
            descripcion=data.get('description', ''),
            uid=data.get('uid'),
            fecha_post=data.get('fecha_post', ''),
            ubicacion=ubicacion,
            certificaciones=data.get('certificaciones', ''),  # string
            opiniones=opiniones,
            rubs=[ObjectId(rub) if not isinstance(rub, ObjectId) else rub for rub in data.get('rubs', [])],
            fotos=data.get('fotos'),
            id=data.get('_id'),
            matricula=data.get('matricula'),
            puntaje_promedio=data.get('puntaje_promedio'),
            latitud=latitud,
            longitud=longitud,
            ciudad=data.get('ciudad', '')
        )