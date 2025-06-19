from flask import Blueprint, request, jsonify
import boto3

upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

@upload_bp.route('/photo', methods=['POST'])
def upload_photo():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No se recibió archivo"}), 400

    # Subir a S3 (ejemplo)
    s3 = boto3.client('s3')
    bucket = 'superfix20'
    carpeta = "imagenes post"
    nombre_archivo = f"{carpeta}/{file.filename}"

    s3.upload_fileobj(file, bucket, nombre_archivo)

    url = f"https://{bucket}.s3.amazonaws.com/{nombre_archivo}"
    return jsonify({"url": url}), 200

@upload_bp.route('/pdf', methods=['POST'])
def upload_pdf():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No se recibió archivo"}), 400

    # Subir a S3 (ejemplo)
    s3 = boto3.client('s3')
    bucket = 'superfix20'
    carpeta = "documentos post"
    nombre_archivo = f"{carpeta}/{file.filename}"

    s3.upload_fileobj(file, bucket, nombre_archivo)

    url = f"https://{bucket}.s3.amazonaws.com/{nombre_archivo}"

    return jsonify({"url": url}), 200