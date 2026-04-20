import os
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from models import db


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///inventory.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev-secret-key'

    db.init_app(app)
    Migrate(app, db)
    CORS(app)

    from routes import inventory_bp
    app.register_blueprint(inventory_bp)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)