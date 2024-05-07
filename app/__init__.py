from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import stripe
db = SQLAlchemy()
load_dotenv()
def create_app():
    app = Flask(__name__)
    app.secret_key = 'casestudy'
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Pranavpokemon1@localhost/pba_project2'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    CORS(app, supports_credentials=True, origins="*")

    db.init_app(app)
    
    from app.api.routes import api_blueprint
    app.register_blueprint(api_blueprint)

    return app