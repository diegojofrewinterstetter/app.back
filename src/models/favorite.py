from bson import ObjectId

class Favorite:
    def __init__(self, user_uid: str, post_id: list, fecha_post=None):
        self.user_uid = user_uid
        self.post_id = post_id  # Debe ser una lista de ObjectId
        self.fecha_post = fecha_post if fecha_post else None

    def to_dict(self):
    # Para guardar en MongoDB: deja los ObjectId tal cual
        return {
            "user_uid": self.user_uid,
            "post_id": self.post_id,
            "fecha_post": self.fecha_post
        }

    def to_dict_db(self):
        # Para API/JSON: convierte ObjectId a string
        return {
            "user_uid": self.user_uid,
            "post_id": [str(pid) for pid in self.post_id],
            "fecha_post": self.fecha_post
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_uid=data["user_uid"],
            post_id=[ObjectId(str(pid)) for pid in data["post_id"]],
            fecha_post=data.get("fecha_post", None)
        )