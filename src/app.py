from flask import Flask
from flask_cors import CORS
from src.routes.users import users_bp
from src.routes.search_post import post_bp
from src.routes.favorites import favorites_bp
from src.routes.rubs import rubs_bp
from src.routes.upload import upload_bp


app = Flask(__name__)
#CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

app.register_blueprint(users_bp)
app.register_blueprint(post_bp)
app.register_blueprint(favorites_bp)
app.register_blueprint(rubs_bp)
app.register_blueprint(upload_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)