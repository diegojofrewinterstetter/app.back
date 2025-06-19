class User:
    def __init__(self, email=None, name=None, uid=None, last_name=None, url_img=None, number_cel=None, verify=False, _id=None):
        self._id = str(_id) if _id else None
        self.email = email
        self.name = name
        self.uid = uid
        self.last_name = last_name
        self.url_img = url_img
        self.number_cel = number_cel
        self.verify = verify

    def to_dict(self):
        data = {
            "email": self.email,
            "name": self.name,
            "uid": self.uid,
            "last_name": self.last_name,
            "url_img": self.url_img,
            "verify": self.verify
        }
        # Solo incluir number_cel si es un string válido (al menos 7 dígitos numéricos)
        if self.number_cel and str(self.number_cel).isdigit() and len(str(self.number_cel)) >= 7:
            data["number_cel"] = str(self.number_cel)
        
        if self._id:
            data["_id"] = self._id
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            email=data.get("email"),
            name=data.get("name"),
            uid=data.get("uid"),
            last_name=str(data.get("last_name") or ""),
            url_img=data.get("url_img"),
            number_cel=str(data.get("number_cel")) if data.get("number_cel") else None,
            verify=data.get("verify", False),
            _id=data.get("_id")
        )