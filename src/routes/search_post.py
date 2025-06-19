from flask import Blueprint, request, jsonify
from src.db.connect import get_db_connection
from src.models.post import Matricula, Post
from src.models.post import Ubicacion, Certificaciones, Opinion
from bson import ObjectId
from datetime import datetime

post_bp = Blueprint('post', __name__, url_prefix='/api/post')

@post_bp.route('/', methods=['GET'])
def search_posts():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Error de conexión con la base de datos"}), 500

    matricula = request.args.get('matricula') or False
    rubros = request.args.getlist('rubs')
    
    text = request.args.get('text')
    try:
        longitud = float(request.args.get('longitud', -68.8272))
        latitud = float(request.args.get('latitud', -32.8908))
    except (TypeError, ValueError):
        longitud, latitud = -68.8272, -32.8908

    if not (-180 <= longitud <= 180 and -90 <= latitud <= 90):
        longitud, latitud = -68.8272, -32.8908

    point = [longitud, latitud]
    rubs_validos = []
    for rub in rubros:
        temp = conn.rubs.find_one({"_id": ObjectId(rub)})
        if temp:
            rubs_validos.append(temp['_id'])

    geo_query = {"estado": "disponible"}
    if text is not None:
        geo_query["$or"] = [
            {"description": {"$regex": text, "$options": "i"}},
            {"title": {"$regex": text, "$options": "i"}}
        ]
    if rubs_validos:
        geo_query["rubs"] = {"$in": rubs_validos}
    if matricula:
        geo_query["matricula.estado"] = {"$eq": "Aceptada"}

    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": point},
                "distanceField": "distancia",
                "maxDistance": 20000,
                "spherical": True,
                "query": geo_query
            }
        },
        {"$project": {
            "fotos": 1,
            "uid": 1,
            "matricula.estado": 1,
            "title": 1,
            "description": 1,
            "coordenadas": 1,
            "ubicacion.ciudad": 1,
            "ubicacion.longitud": 1,      
            "ubicacion.latitud": 1,       
            "rubs": 1,
            "puntaje_promedio": 1,
            "distancia": 1,
            "id": 1
        }},
        {"$limit": 10}
    ]

    results = list(conn.posts.aggregate(pipeline))
    if not results:
        return jsonify({
            "message": "No se encontraron resultados",
            "debug": {
                "rubros_enviados": rubros,
                "rubros_validos": rubs_validos,
                "text": text,
                "coordenadas": point,
                "query_usado": geo_query
            }
        }), 404
    
    posts_result = []
    for post in results:
        _id = str(post.get('_id'))
        uid = post.get('uid')
        uid = str(uid) if uid else None
        rubs_list = post.get('rubs', [])
        rubs_list = [str(rub) for rub in rubs_list]
        ubicacion = Ubicacion(**post.get('ubicacion', {}))
        coordenadas = post.get('coordenadas', {})
        fotos = post.get('fotos', [])
        puntaje_promedio = post.get('puntaje_promedio')
        titulo = post.get('title', '')
        descripcion = post.get('description', '')
        fecha_post = post.get('fecha_post', None)
        matricula = post.get('matricula.estado')
        coords = coordenadas.get('coordinates', [0, 0])
        post_obj = Post(
            titulo=titulo,
            descripcion=descripcion,
            uid=uid if uid is None else uid,   # UID se guarda tal cual (string)
            matricula=matricula,
            ubicacion=ubicacion,
            rubs=rubs_list,
            fotos=fotos,
            puntaje_promedio=puntaje_promedio,
            fecha_post=fecha_post,
            id=_id,
            certificaciones=[],
            opiniones=[],
            latitud=coords[0],
            longitud=coords[1]
        )
        posts_result.append(post_obj.to_dict())

    return jsonify(posts_result), 200

@post_bp.route('/searchById/<post_id>', methods=['GET'])
def get_post_by_id(post_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Error de conexión con la base de datos"}), 500
    try:
        obj_id = ObjectId(post_id)
        post = conn.posts.find_one({"_id": obj_id})
        response = Post.from_dict(post).to_dict()
        return jsonify(response), 200
    except Exception as e:
        print(f"Error al buscar el post por ID: {e}")
        return jsonify({"error": "ID inválido"}), 400

@post_bp.route('/searchByUser/<user_id>', methods=['GET'])
def get_posts_by_user(user_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Error de conexión con la base de datos"}), 500
    try:
        # Ahora buscamos por el campo 'uid' (que es un string)
        posts = list(conn.posts.find({
            "uid": user_id,
            "estado": {"$ne": "eliminado"}
        }))
        if not posts:
            return jsonify({"message": "No se encontraron posts para este usuario"}), 404
        response = [Post.from_dict(post).to_dict() for post in posts]
        return jsonify(response), 200
    except Exception as e:
        print(f"Error al buscar los posts por usuario: {e}")
        return jsonify({"error": "ID inválido"}), 400
  
@post_bp.route('/update/<id>', methods=['PUT'])
def update_post(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexion con la base de datos"}), 500
    try:
        id_post = ObjectId(id)
        post_data = conn.posts.find_one({"_id": id_post})
        if post_data is None:
            return jsonify({"Error": "Post no encontrado"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"Error": "No se han recibido datos para actualizar"}), 400

        update_fields = {}

        # Validar y actualizar título
        if 'title' in data:
            if not isinstance(data['title'], str) or len(data['title']) < 5:
                return jsonify({"Error": "El título debe tener al menos 5 caracteres"}), 400
            update_fields['title'] = data['title']

        # Validar y actualizar descripción
        if 'description' in data:
            if not isinstance(data['description'], str) or len(data['description']) < 10:
                return jsonify({"Error": "La descripción debe tener al menos 10 caracteres"}), 400
            update_fields['description'] = data['description']

        # Agregar nuevas URLs a fotos (solo agrega, no reemplaza)
        if 'fotos' in data:
            if not isinstance(data['fotos'], list) or not all(isinstance(f, str) for f in data['fotos']):
                return jsonify({"Error": "Las fotos deben ser una lista de strings"}), 400
            update_fields['fotos'] = post_data.get('fotos', []) + data['fotos']

        # Actualizar matrícula (solo url, estado siempre "Pendiente")
        if 'matricula' in data:
            matricula_data = data['matricula']
            if not isinstance(matricula_data, dict) or 'url' not in matricula_data or not isinstance(matricula_data['url'], str):
                return jsonify({"Error": "La matrícula debe ser un objeto con el campo 'url'"}), 400
            update_fields['matricula'] = {
                "estado": "Pendiente",
                "url": matricula_data['url']
            }

        # Actualizar ubicación (todos los campos requeridos y tipos correctos)
        if 'ubicacion' in data:
            ubicacion_data = data['ubicacion']
            required_fields = ['direccion', 'ciudad', 'localidad', 'latitud', 'longitud']
            if not all(field in ubicacion_data for field in required_fields):
                return jsonify({"Error": "Ubicación incompleta"}), 400
            try:
                latitud = float(ubicacion_data['latitud'])
                longitud = float(ubicacion_data['longitud'])
            except Exception:
                return jsonify({"Error": "Latitud y longitud deben ser números"}), 400
            update_fields['ubicacion'] = {
                "direccion": ubicacion_data['direccion'],
                "ciudad": ubicacion_data['ciudad'],
                "localidad": ubicacion_data['localidad'],
                "latitud": latitud,
                "longitud": longitud
            }

        if not update_fields:
            return jsonify({"Error": "No se enviaron campos válidos para actualizar"}), 400

        result = conn.posts.update_one({"_id": id_post}, {"$set": update_fields})
        if result.matched_count == 0:
            return jsonify({"Error": "Post no encontrado"}), 404

        return jsonify({"message": "Post actualizado exitosamente"}), 200
    except Exception as e:
        print(f"Error al actualizar el post: {e}")
        return jsonify({"Error": "ID inválido"}), 400

@post_bp.route('/updateEstado/<id>', methods=['PUT'])
def update_estado_post(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexion con la base de datos"}), 500
    try:
        estado = request.args.get('estado')
        if not estado:
            return jsonify({"Error": "Estado no proporcionado"}), 400
        if estado not in ['disponible', 'en pausa', "eliminado"]:
            return jsonify({"Error": "Estado Desconocido"}), 400
        id_post = ObjectId(id)
        post_data = conn.posts.find_one({"_id": id_post})
        if post_data is None:
            return jsonify({"Error": "Post no encontrado"}), 404
        result = conn.posts.update_one({"_id": id_post}, {"$set": {"estado": estado}})
        if result.matched_count == 0:
            return jsonify({"Error": "Post no encontrado"}), 404
        return jsonify({"message": "Estado actualizado exitosamente"}), 200
    except Exception as e:
        return jsonify({"Error": "ID inválido"}), 400

@post_bp.route('/create', methods=['POST'])
def create_post():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexion con la base de datos"}), 500
    
    data = request.get_json()
    if not data:
        return jsonify({"Error": "No se han recibido datos para crear el post"}), 400
    
    uid = data.get('uid')
    if not conn.users.find_one({"uid": uid}):
        return jsonify({"Error": "Usuario no encontrado"}), 404
    
    rubs = data.get('rubs', [])
    if not isinstance(rubs, list) or not all(isinstance(rub, str) for rub in rubs):
        return jsonify({"Error": "Rubs deben ser una lista de strings"}), 400
    if rubs:
        rubs_validos = []
        for rub in rubs:
            temp = conn.rubs.find_one({"_id": ObjectId(rub)})
            if temp:
                rubs_validos.append(temp['_id'])
        if not rubs_validos:
            return jsonify({"Error": "Rubs no válidos"}), 400

    if isinstance(data.get('title'), str) and len(data['title']) < 5:
        return jsonify({"Error": "El título debe tener al menos 5 caracteres"}), 400
    if isinstance(data.get('description'), str) and len(data['description']) < 5:
        return jsonify({"Error": "La descripción debe tener al menos 5 caracteres"}), 400
    
    # Ahora certificaciones es solo una lista de URLs (strings)
    cert_data = data.get('certificaciones', [])
    if not isinstance(cert_data, list) or not all(isinstance(cert, str) for cert in cert_data):
        return jsonify({"Error": "Las certificaciones deben ser una lista de URLs (strings)"}), 400
    certificaciones = cert_data
        
    if isinstance(data.get('ubicacion'), dict):
        ubicacion_data = data['ubicacion']
        if not ubicacion_data.get('ciudad') or not ubicacion_data.get('latitud') or not ubicacion_data.get('longitud'):
            return jsonify({"Error": "Ubicación incompleta"}), 400
        ubicacion  = Ubicacion(**ubicacion_data)
    else:
        return jsonify({"Error": "Ubicación debe ser un objeto con ciudad, latitud y longitud"}), 400

    fotos = None
    if isinstance(data.get('fotos'), list) or isinstance(data.get('fotos'), str):
        fotos = data['fotos']

    puntaje_promedio = None
    if isinstance(data.get('puntaje_promedio'), (int, float)):
        puntaje_promedio = data['puntaje_promedio']
    if puntaje_promedio is None:
        puntaje_promedio = 5.0
    matricula = None
    if isinstance(data.get('matricula'), dict) and data.get('matricula') is not None:
        matricula = Matricula("Pendiente", data['matricula']['url'])

    fecha_post = None
    if isinstance(data.get('fecha_post'), str):
        fecha_post = data['fecha_post']

    latitud = float(ubicacion.latitud)
    longitud = float(ubicacion.longitud)

    if not (-180 <= longitud <= 180 and -90 <= latitud <= 90):
        longitud, latitud = -68.8272, -32.8908
        ubicacion = Ubicacion(ciudad=ubicacion.ciudad, latitud=latitud, longitud=longitud)
    
    if not fecha_post:
        fecha_post = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Pasa la lista de URLs directamente en certificaciones
    post_new = Post(
        titulo=data.get('title', ''),
        descripcion=data.get('description', ''),
        uid=uid,
        fecha_post=fecha_post,
        ubicacion=ubicacion,
        certificaciones=certificaciones,  # <-- lista de URLs
        opiniones=[],
        rubs=rubs_validos,
        fotos=fotos,
        puntaje_promedio=puntaje_promedio,
        matricula=matricula if 'matricula' in locals() else None,
        latitud=ubicacion.latitud,
        longitud=ubicacion.longitud
    )
    fecha_post_dt = datetime.now()
    geo = {
        "type": "Point",
        "coordinates": [longitud, latitud]
    }
    try:
        conn.posts.insert_one({
            "title": post_new.title,
            "description": post_new.description,
            "uid": post_new.uid,
            "fecha_post": fecha_post_dt,
            "ubicacion": {
                **post_new.ubicacion.to_dict(),
                "latitud": longitud,
                "longitud": latitud
            },
            "certificaciones": post_new.certificaciones,  # <-- lista de URLs
            "opiniones": [opinion.to_dict() for opinion in post_new.opiniones],
            "rubs": post_new.rubs,
            "fotos": post_new.fotos,
            "puntaje_promedio": float(post_new.puntaje_promedio) if post_new.puntaje_promedio is not None else 0.0,
            "matricula": matricula.to_dict() if matricula else None,
            "coordenadas": geo,
            "estado": "disponible"
        })
        return jsonify({"message": "Post creado exitosamente"}), 201
    except Exception as e:
        print(f"Error al crear el post: {e}")
        return jsonify({"Error": "Error al crear el post"}), 500  
    

@post_bp.route('/validate_matricula/<id_post>', methods=['PUT'])
def validate_matricula(id_post):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexion con la base de datos"}), 500
    try:
        obj_id = ObjectId(id_post)
        post = conn.posts.find_one({"_id": obj_id})
        if not post:
            return jsonify({"Error": "Post no encontrado"}), 404

        data = request.get_json()
        if not data or 'estado' not in data:
            return jsonify({"Error": "Debe enviar el campo 'estado'"}), 400

        estado = data['estado']
        if estado not in ['Aceptada', 'Pendiente', 'Rechazada']:
            return jsonify({"Error": "Estado de matrícula inválido"}), 400

        matricula = post.get('matricula')
        if not matricula or 'url' not in matricula or not isinstance(matricula['url'], str):
            return jsonify({"Error": "El post no tiene matrícula válida para validar"}), 400

        result = conn.posts.update_one(
            {"_id": obj_id},
            {"$set": {"matricula.estado": estado}}
        )
        if result.matched_count == 0:
            return jsonify({"Error": "Post no encontrado"}), 404

        return jsonify({"message": f"Estado de matrícula actualizado a '{estado}'"}), 200
    except Exception as e:
        print(f"Error al validar matrícula: {e}")
        return jsonify({"Error": "ID inválido"}), 400

@post_bp.route('/add_opinion/<id_post>', methods=['POST'])
def add_opinion(id_post):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Error de conexion con la base de datos"}), 500
    try:
        obj_id = ObjectId(id_post)
        post = conn.posts.find_one({"_id": obj_id})
        if not post:
            return jsonify({"Error": "Post no encontrado"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"Error": "No se han recibido datos de opinión"}), 400

        required_fields = ['id_user', 'comentario', 'puntaje']
        if not all(field in data for field in required_fields):
            return jsonify({"Error": "Faltan campos requeridos en la opinión"}), 400

        try:
            # Modificar también aquí si deseas usar 'uid' en lugar de 'id_user'
            id_user = ObjectId(data['id_user'])
        except Exception:
            return jsonify({"Error": "id_user inválido"}), 400

        comentario = data['comentario']
        if not isinstance(comentario, str) or not comentario.strip():
            return jsonify({"Error": "El comentario debe ser un string no vacío"}), 400

        puntaje = data['puntaje']
        if not isinstance(puntaje, int) or not (1 <= puntaje <= 5):
            return jsonify({"Error": "El puntaje debe ser un entero entre 1 y 5"}), 400

        timestamp = datetime.now()

        nueva_opinion = {
            "id_user": id_user,
            "comentario": comentario,
            "puntaje": puntaje,
            "timestamp": timestamp
        }

        result = conn.posts.update_one(
            {"_id": obj_id},
            {"$push": {"opiniones": nueva_opinion}}
        )
        if result.matched_count == 0:
            return jsonify({"Error": "Post no encontrado"}), 404

        post_actualizado = conn.posts.find_one({"_id": obj_id})
        opiniones = post_actualizado.get('opiniones', [])
        if opiniones:
            promedio = sum(op['puntaje'] for op in opiniones) / len(opiniones)
        else:
            promedio = puntaje

        conn.posts.update_one(
            {"_id": obj_id},
            {"$set": {"puntaje_promedio": float(promedio)}}
        )

        return jsonify({"message": "Opinión agregada exitosamente", "puntaje_promedio": promedio}), 201

    except Exception as e:
        print(f"Error al agregar opinión: {e}")
        return jsonify({"Error": "ID inválido o error interno"}), 400