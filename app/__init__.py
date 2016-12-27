
from flask import Flask, request
from config import config, Config

from flask_pymongo import PyMongo

mongo = PyMongo()

def create_app(config_name):
    app = Flask(__name__)
    mongo.init_app(app)

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    from .app import main as main_blueprint
    app.register_blueprint(main_blueprint)

