from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")

def create_app():
    app = Flask(__name__, template_folder="../templates")
    app.config["SECRET_KEY"] = "iern-secret-2024"

    # MySQL config — change password to yours
    app.config["MYSQL_HOST"]     = "localhost"
    app.config["MYSQL_USER"]     = "root"
    app.config["MYSQL_PASSWORD"] = "root@123"        # ← put your MySQL password here
    app.config["MYSQL_DB"]       = "iern"

    CORS(app)
    socketio.init_app(app)

    from app.routes.patient   import patient_bp
    from app.routes.driver    import driver_bp
    from app.routes.hospital  import hospital_bp
    from app.routes.ml_api    import ml_bp
    from app.routes.ambulance import ambulance_bp

    app.register_blueprint(patient_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(hospital_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(ambulance_bp)

    return app
