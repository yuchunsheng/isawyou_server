from flask import render_template

from . import facepp_manage

from ..face_plus_plus.facepp import API, File


@facepp_manage.route('/faceset/<str:faceset_name>', methods=['POST'])
def create_faceset(faceset_name):

    api = API()
    # create a Faceset to save FaceToken
    ret = api.faceset.create(outer_id=faceset_name)

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@facepp_manage.route('/faceset', methods=['POST'])
def delete_faceset():
    api = API()
    # create a Faceset to save FaceToken
    ret = api.faceset.create(outer_id='test')

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}
