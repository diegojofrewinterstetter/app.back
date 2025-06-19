from pymongo import MongoClient
import certifi

MONGO_URL = "mongodb://usuario:%24adminL@cluster0.mongodb.net/nombreDB?retryWrites=true&w=majority"
cs = certifi.where()

def test_connection():
    try:
        client = MongoClient(MONGO_URL, tlsCAFile=cs)
        db = client["appsinnombre7"]
        print("Conexión exitosa a la BD")
        # Probar listar colecciones
        print("Colecciones:", db.list_collection_names())
    except Exception as e:
        print("Error al conectar:", e)

if __name__ == "__main__":
    test_connection()

