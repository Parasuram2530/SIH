import os
from flask import Flask, jsonify, render_template
from config import Config
from extensions import mongo, jwt
from routes.citizen import citizen_bp
from routes.staff import staff_bp


def create_app():
    app = Flask(__name__, static_folder="public", static_url_path="/")
    app.config.from_object(Config)

    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)

    mongo.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(citizen_bp, url_prefix="/citizen")  
    app.register_blueprint(staff_bp, url_prefix="/staff")     

    @app.route("/")
    def home():
        return render_template("home.html")

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app = create_app()
    app.run(debug=True, port=port)
