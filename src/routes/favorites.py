from src.models.favorite import Favorite
from flask import Blueprint, request, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from src.db.connect import get_db_connection
from datetime import datetime

favorites_bp = Blueprint('favorites', __name__, url_prefix='/api/favorites')

@favorites_bp.route('/all/<user_id>', methods=['GET'])
def get_favorits(user_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Database connection failed"}), 500
    if not user_id:
        return jsonify({"Error": "User ID is required"}), 400
    try:
        if conn.users.count_documents({"uid": user_id}) == 0:
            return jsonify({"Error": "Id del usuario no encontrado"}), 404

        favorites = conn.favorites.find({"user_uid": user_id})

        return jsonify([Favorite.from_dict(fav).to_dict_db() for fav in favorites])

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"Error": "Invalid User ID format"}), 400
    
@favorites_bp.route('/one/<user_uid>/<post_id>', methods=['GET'])
def get_favorite(user_uid, post_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Database connection failed"}), 500

    if not user_uid or not post_id:
        return jsonify({"Error": "User UID and Post ID are required"}), 400

    try:
        # Verificar si el usuario existe
        user = conn.users.find_one({"uid": user_uid})
        if not user:
            return jsonify({"Error": "Id del usuario no encontrado"}), 404

        # Validar ObjectId del post
        try:
            post_obj_id = ObjectId(post_id)
        except InvalidId:
            return jsonify({"Error": "Post ID inválido"}), 400

        # Verificar si el post existe
        if conn.posts.count_documents({"_id": post_obj_id}) == 0:
            return jsonify({"Error": "Id del post no encontrado"}), 404

        # Buscar favorito
        favorite = conn.favorites.find_one({
            "user_uid": user_uid,
            "post_id": { "$in": [post_obj_id] }
        })

        if not favorite:
            return jsonify({"Mensaje": "Favorite no encontrado"}), 404

        return jsonify({"Mensaje": "Favorite encontrado"}), 200

    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    

@favorites_bp.route('/CreaDelete', methods=['POST'])
def create_favorite():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Database connection failed"}), 500
    data = request.get_json()
    user_uid = data.get('user_uid')
    post_id = data.get('post_id')
    if user_uid is None or post_id is None:
        return jsonify({"Error": "Se requieren IDs"}), 400
    try:
        user = conn.users.find_one({"uid": user_uid})
        if not user:
            return jsonify({"Error": "Id del usuario no encontrado"}), 404

        post_obj_id = ObjectId(post_id)
        if conn.posts.count_documents({"_id": post_obj_id}) == 0:
            return jsonify({"Error": "Id del post no encontrado"}), 404

        # Buscar si ya existe el favorito
        existing_favorite = conn.favorites.find_one({"user_uid": user_uid, "post_id": [post_obj_id]})
        if existing_favorite:
            fav_delete = conn.favorites.delete_one({"user_uid": user_uid, "post_id": [post_obj_id]})
            if fav_delete.deleted_count == 0:
                return jsonify({"Error": "Failed to delete existing favorite"}), 500
            return jsonify({"Mensaje": "Favorite Delete"}), 200
        else:
            favorite = Favorite(user_uid=user_uid, post_id=[post_obj_id], fecha_post=datetime.now())
            conn.favorites.insert_one(favorite.to_dict())
            return jsonify({"Mensaje": "Favorite Add"}), 201
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"Error": "Invalid User UID or Post ID format"}), 400