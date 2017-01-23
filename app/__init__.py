import os

from celery import Celery
from flask import Flask
from flask_pymongo import PyMongo

from app.mongodb_helper import MongodbHelper
from config import config

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

    from .celery_workers_facepp import tasks_facepp as facepp_task_blueprint
    app.register_blueprint(facepp_task_blueprint, url_prefix='/facepp')

    from .business_api_1_0 import facepp_business as facepp_business_blueprint
    app.register_blueprint(facepp_business_blueprint, url_prefix='/business')

    from .management_api_1_0 import facepp_manage as facepp_manage_blueprint
    app.register_blueprint(facepp_manage_blueprint, url_prefix='/manage')


    return app

