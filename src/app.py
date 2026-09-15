import os
from flask import Flask, render_template
from config import Config
from models.models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def home():
        return render_template('index.html')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
