from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from src.models.rub import Rub
from src.db.connect import get_db_connection
from bson.errors import InvalidId

rubs_bp = Blueprint('rubs', __name__ , url_prefix='/api/rubs')

@rubs_bp.route('/', methods=['GET'])
def get_rubs():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexión con la base de datos"}), 500

    rubs_list = [Rub.from_dict(rub).to_dict() for rub in conn.rubs.find()]
    return jsonify(rubs_list), 200

@rubs_bp.route('/<rub_id>', methods=['GET'])
def get_rub_by_id(rub_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexión con la base de datos"}), 500

    try:
        obj_id = ObjectId(rub_id)
    except Exception:
        return jsonify({"Error": "ID inválido"}), 400

    rub = conn.rubs.find_one({"_id": obj_id})
    if not rub:
        return jsonify({"Error": "Rub no encontrado"}), 404

    return jsonify(Rub.from_dict(rub).to_dict()), 200

@rubs_bp.route('/', methods=['POST'])
def create_rub():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexión con la base de datos"}), 500

    data = request.get_json()
    if not data.get("nombre"):
        return jsonify({"Error": "El campo 'nombre' es obligatorio"}), 400

    new_rub = Rub.from_dict(data)
    insert_data = new_rub.to_dict()
    del insert_data["_id"]  # Evita problemas con MongoDB

    result = conn.rubs.insert_one(insert_data)
    new_rub.id = result.inserted_id

    return jsonify(new_rub.to_dict()), 201

@rubs_bp.route('/<rub_id>', methods=['PUT'])
def update_rub(rub_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexión con la base de datos"}), 500

    try:
        obj_id = ObjectId(rub_id)
    except InvalidId:
        return jsonify({"Error": "ID inválido"}), 400

    rub_data = request.get_json()
    if not rub_data:
        return jsonify({"Error": "Datos insuficientes"}), 400

    if "_id" in rub_data:
        del rub_data["_id"]  # Evita actualizar el ID

    result = conn.rubs.update_one({'_id': obj_id}, {'$set': rub_data})

    return jsonify({"Mensaje": "Rub actualizado"}), 200 if result.modified_count > 0 else 404

@rubs_bp.route('/<rub_id>', methods=['DELETE'])
def delete_rub(rub_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexión con la base de datos"}), 500

    try:
        obj_id = ObjectId(rub_id)
    except InvalidId:
        return jsonify({"Error": "ID inválido"}), 400

    result = conn.rubs.delete_one({'_id': obj_id})

    return jsonify({"Mensaje": "Rub eliminado exitosamente"}), 200 if result.deleted_count > 0 else 404