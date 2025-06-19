from pymongo import MongoClient  # Ya importaste esto
import certifi


cs = certifi.where()

def get_db_connection():
    try:
        client = MongoClient('mongodb://localhost:27017')

        db = client["app-bd"]
        print("Conexión a MongoDB exitosa")
        return db
    except Exception as e:
        print("Error conectando a la BD:", e)
        return None
