from bson import ObjectId
from typing import Optional

class Rub:
    def __init__(self, nombre: str, icono: str = "", id: Optional[ObjectId] = None):
        self.nombre = nombre
        self.icono = icono
        self.id = id

    def to_dict(self):
        return {
            "_id": str(self.id) if self.id else None,  # MongoDB usa "_id"
            "nombre": self.nombre,
            "icono": self.icono
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            nombre=data.get("nombre"),
            icono=data.get("icono", ""),
            id=ObjectId(data["_id"]) if "_id" in data and ObjectId.is_valid(data["_id"]) else None
        )