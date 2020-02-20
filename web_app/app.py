from flask import Flask
from dotenv import load_dotenv
import os
from web_app.routes import routes
from web_app.twitter_service import twitter_api_client
from web_app.models import db, migrate

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['TWITTER_API_CLIENT'] = twitter_api_client()
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(routes)
    return app

