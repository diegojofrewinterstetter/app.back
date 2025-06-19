from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from src.models.user import User
from src.db.connect import get_db_connection
from bson.errors import InvalidId

us = User()
users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('/', methods=['GET'])
def get_users():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexión con la base de datos"}), 500

    _id = request.args.get('_id')
    email = request.args.get('email')

    if _id:
        try:
            user = conn.users.find_one({"_id": ObjectId(_id)})
            if user:
                user['_id'] = str(user['_id'])
                return jsonify(user), 200
            else:
                return jsonify({"Error": "Usuario no encontrado"}), 404
        except Exception:
            return jsonify({"Error": "ID inválido"}), 400

    if email:
        user = conn.users.find_one({"email": email})
        if user:
            user['_id'] = str(user['_id'])
            return jsonify(user), 200
        else:
            return jsonify({"Error": "Usuario no encontrado"}), 404

    # Si no hay parámetros, devolver todos los usuarios
    usuarios = []
    for user in conn.users.find():
        user['_id'] = str(user['_id'])
        usuarios.append(user)

    return jsonify(usuarios), 200

@users_bp.route('/<user_uid>', methods=['GET'])
def get_user_by_id(user_uid):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexión con la base de datos"}), 500
    try:
        user = conn.users.find_one({"uid": user_uid})
        if user:
            user['_id'] = str(user['_id'])
            return jsonify(user), 200
        else:
            return jsonify({"Error": "Usuario no encontrado"}), 404
    except Exception:
        return jsonify({"Error": "ID inválido"}), 400
    
@users_bp.route('/', methods=['POST'])
def create_user():
    conn = get_db_connection()
    data = request.get_json() 
    if conn is None: 
        return jsonify({"Error": "Error de Conexion con la base de datos"}), 500
    if (not data.get('email') or not data.get('name') or not data.get('uid') or not data.get('url_img')):
        return jsonify({"Error": "Faltan datos"}), 400

    # Validar number_cel solo si viene
    number_cel = data.get('number_cel')
    if number_cel is not None:
        if not str(number_cel).isdigit() or len(str(number_cel)) < 7:
            return jsonify({"Error": "El número de celular debe tener al menos 7 dígitos numéricos"}), 400

    # No agregar number_cel si no viene
    if not number_cel:
        data.pop('number_cel', None)

    newUs = us.from_dict(data)
    
    existing_user = conn.users.find_one({"email": newUs.email})
    if existing_user:
        return jsonify({"Error": "El correo ya existe"}), 400
    
    result = conn.users.insert_one(newUs.to_dict())

    if result.inserted_id:
        newUs._id = str(result.inserted_id)
        return jsonify(newUs.to_dict()), 201

    return jsonify({"Error": "No se pudo crear el usuario"}), 500


@users_bp.route('/<uid>', methods=['PUT'])
def user_update(uid):
    conn = get_db_connection()

    if conn is None:
        return jsonify({"Error": "Error de Conexion con la base de datos"}), 500

    try:
        obj_id = ObjectId(uid)
    except InvalidId:
        return jsonify({"Error": "ID inválido"}), 400

    user_temp = conn.users.find_one({"_id": obj_id})

    if not user_temp:
        return jsonify({"Error": "Usuario no encontrado"}), 404

    data = request.get_json()

    if not data:
        return jsonify({'Error': 'No se han recibido datos para actualizar'}), 400

    user_update = us.from_dict(data)
    user_update._id = uid
    user_update.email = user_temp['email']  # Mantener el email original

    update_data = user_update.to_dict()
    if 'id' in update_data:
        del update_data['id']  # Evitar actualizar _id

    result = conn.users.update_one({'uid': uid}, {'$set': data})

    if result.matched_count == 0:
        return jsonify({"Error": "Usuario no encontrado"}), 404

    if result.modified_count > 0:
        return jsonify({"Message": "Usuario Actualizado"}), 200

    return jsonify({"Error": "No se actualizó ningun documento"}), 404 


@users_bp.route('/<id>', methods=['DELETE'])
def delete_user(id):
    conn = get_db_connection()
    
    if conn is None:
        return jsonify({'Error': 'Error al conectar con la BD'}), 500

    #result = conn.users.delete_one({'_id' : ObjectId(id)})

    #if result.deleted_count == 0:
    #   return jsonify({'Error' : 'Usuario no encontrado'}), 404

    return jsonify({'Message': 'Usuario eliminado exitosamente'}), 200


def validar_email(email):
    if not email:
        return False
    if '@' not in email or '.' not in email:
        return False
    return True