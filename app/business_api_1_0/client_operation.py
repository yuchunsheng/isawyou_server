#!/usr/bin/env python

# https://console.faceplusplus.com/app/apikey/list
# face_ai	key = LM9EerMwm487h6j1Ybnmgu-VIlT-KJOj	secret = _cga2gleo-jZTo9-B4G5d626aQS7GmoV

from flask import render_template
from flask import request

from ..face_plus_plus.facepp import API, File

from . import facepp_business


@facepp_business.route('/face_analyze', methods=['POST'])
def create_faceset():

    api = API()
    # create a Faceset to save FaceToken
    ret = api.faceset.create(outer_id='test')

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@facepp_business.route('/face_detect', methods=['GET', 'POST'])
def detect_face():
    if request.method == 'POST':

        api = API()
        # create a Faceset to save FaceToken
        ret = api.faceset.create(outer_id='test')

        return {'current': 100, 'total': 100, 'status': 'Task completed!',
                'result': 42}

    return render_template('index.html')

@facepp_business.route('/faceset_add_face', methods=['POST'])
def add_face():
    api = API()
    # create a Faceset to save FaceToken
    ret = api.faceset.create(outer_id='test')

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}
