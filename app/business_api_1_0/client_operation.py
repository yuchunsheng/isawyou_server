#!/usr/bin/env python

# https://console.faceplusplus.com/app/apikey/list
# face_ai	key = LM9EerMwm487h6j1Ybnmgu-VIlT-KJOj	secret = _cga2gleo-jZTo9-B4G5d626aQS7GmoV

from flask import render_template
from flask import request

from app import mongodb_helper
from flask_pymongo import GridFS, NoFile, ObjectId, MongoClient

from ..face_plus_plus.facepp_mongodb import API, FileMongodb

from . import facepp_business
from .. import celery, mongo, mongodb_helper


@facepp_business.route('/face_analyze', methods=['POST'])
def create_faceset():

    api = API()
    # create a Faceset to save FaceToken
    ret = api.faceset.create(outer_id='test')

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@facepp_business.route('/face_detect', methods=['GET'])
def detect_face():
    if request.method == 'GET':

        from ..wsgi_aux import app

        mongodb_helper.init_app(app.config)

        fs = GridFS(mongodb_helper.db, 'fs')
        api = API()
        try:
            with fs.get(ObjectId('58642a0a1d41c8329d26ec53')) as fp_read:

                res = api.detect(image_file=FileMongodb(fp_read))
                print(res)

        except NoFile:
            return 'fail'


        return 'done'



@facepp_business.route('/faceset_add_face', methods=['POST'])
def add_face():
    api = API()
    # create a Faceset to save FaceToken
    ret = api.faceset.create(outer_id='test')

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}
