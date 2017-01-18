import os

from celery import Celery
from flask import Flask, request

from app.mongodb_helper import MongodbHelper
from config import config, Config

from flask_pymongo import PyMongo

mongo = PyMongo()

mongodb_helper = MongodbHelper()

celery = Celery(__name__,
                broker=os.environ.get('CELERY_BROKER_URL', 'amqp://test:devserver@localhost:5672/test'),
                backend=os.environ.get('CELERY_BROKER_URL', 'amqp://test:devserver@localhost:5672/test'))


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    mongo.init_app(app)

    mongodb_helper.init_app(app.config)

    celery.conf.update(config[config_name].CELERY_CONFIG)

    from .app import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .celery_workers import tasks_bp as celery_task_blueprint
    app.register_blueprint(celery_task_blueprint, url_prefix='/celery')

    return app

