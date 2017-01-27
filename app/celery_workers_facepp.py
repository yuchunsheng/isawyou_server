import random

import dlib
import io
import numpy as np
import cv2
from PIL import Image

import time

from flask import Blueprint, jsonify, abort
from flask_pymongo import GridFS, NoFile, ObjectId, MongoClient

from .face_plus_plus.facepp import API, FileMongodb
from . import celery, mongo, mongodb_helper

tasks_facepp = Blueprint('facepp', __name__)


@celery.task(bind=True)
def facepp_detect(self, file_id, base='fs'):
    message = ''
    self.update_state(state='PROGRESS',
                      meta={'current': 30,
                            'total': 100,
                            'status': 'Upload image'})

    api = get_api()
    fs = get_mongodb_fs()
    try:
        with fs.get(ObjectId(file_id)) as fp_read:

            res = api.detect(image_file=FileMongodb(fp_read))

    except NoFile:
        return {'current': 100, 'total': 100, 'status': 'No file!',
                'result': 0}

    self.update_state(state='PROGRESS',
                      meta={'current': 50,
                            'total': 100,
                            'status': 'Done'})

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': res}


@celery.task(bind=True)
def facepp_add_faceset(self, faceset_id, base='fs'):

    self.update_state(state='PROGRESS',
                      meta={'current': 30,
                            'total': 100,
                            'status': 'Upload image'})

    api = get_api()
    try:

        ret = api.faceset.create(outer_id=faceset_id)

    except NoFile:
        return {'current': 100, 'total': 100, 'status': 'No file!',
                'result': 0}

    self.update_state(state='PROGRESS',
                      meta={'current': 100,
                            'total': 100,
                            'status': 'Done'})

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': ret}


def get_mongodb_fs(base='fs'):

    from .wsgi_aux import app
    mongodb_helper.init_app(app.config)
    fs = GridFS(mongodb_helper.db, base)

    return fs


def get_api():
    return API()


