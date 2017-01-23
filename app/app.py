import base64
import json
import numpy as np
import cv2
from bson.json_util import dumps
from mimetypes import guess_type


from flask import Blueprint, jsonify
from flask import current_app, abort, flash, redirect, request, url_for, render_template
from flask_pymongo import GridFS, NoFile

from werkzeug.utils import secure_filename


from .utils_mongodb import save_file_mongodb
from .utils import allowed_file
from . import mongo
from .celery_workers import long_task, detect_face_long_task, detect_face_long_task_without_app


main = Blueprint('main', __name__)


@main.route('/')
def home_page():
    return render_template('index.html')
    # return render_template('index.html')


@main.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for("/"))

        file_obj = request.files['file']
        file_id = save_file_mongodb(file_obj)

        # return redirect(url_for('home_page', filename=filename))
        return file_id


@main.route('/show', methods=['GET'])
def show_image():
    return mongo.send_file('sky.jpg')


@main.route('/signUp')
def signUp():
    return render_template('signUp.html')


@main.route('/signUpUser', methods=['POST'])
def sign_up_user():

    user =  request.form['username']
    password = request.form['password']

    ENCODING = 'utf-8'

    storage = GridFS(mongo.db, 'fs')

    try:
        fileobj = storage.get_version(filename='sky.jpg', version=-1).read()
    except NoFile:
        abort(404)


    base64_bytes = base64.b64encode(fileobj)
    image_base64_string = base64_bytes.decode(ENCODING)

    return json.dumps({'status':'OK','image':image_base64_string});


@main.route('/imageEdge', methods=['GET'])
def image_edge():

    ENCODING = 'utf-8'

    storage = GridFS(mongo.db, 'fs')
    print('image edge detection')

    try:
        fileobj = storage.get_version(filename='sky.jpg', version=-1).read()
        file_bytes = np.asarray(bytearray(fileobj), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 0)  # Here as well I get returned nothing

        edges = cv2.Canny(img, 100, 200)

        # encode to jpeg format
        # encode param image quality 0 to 100. default:95
        # if you want to shrink data size, choose low image quality.
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        result, encimg = cv2.imencode('.jpg', edges, encode_param)
        if False == result:
            print('could not encode image!')
            abort(404)
    except NoFile:
        abort(404)


    base64_bytes = base64.b64encode(encimg)
    image_base64_string = base64_bytes.decode(ENCODING)

    result = "data:image/jpeg;base64," + image_base64_string

    return render_template('show_image.html', image = result)
    # return json.dumps({'status':'OK','image':image_base64_string});


@main.route('/uploads', methods=['POST'])
def save_upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            # flash('No file part')
            return 'No file part'
        file_obj = request.files['file']
        file_id = save_file_mongodb(file_obj)
        task = long_task.delay(file_id)
        # return jsonify({}), 202, {'Location': url_for('taskstatus',
        return task.id


@main.route('/faceDetect', methods=['POST'])
def detect_face():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            # flash('No file part')
            return 'No file part'
        file_obj = request.files['file']
        file_id = save_file_mongodb(file_obj)

        text_types = (str, bytes)


        environ = {k: v for k, v in request.environ.items()
                   if isinstance(v, text_types)}

        # task = detect_face_long_task.delay(environ, file_id)
        task = detect_face_long_task_without_app.delay(file_id)
        # return jsonify({}), 202, {'Location': url_for('taskstatus',
        return task.id




@main.route('/images/<path:filename>')
def get_upload(filename):
    return mongo.send_file(filename)


#a base urls that returns all the parks in the collection (of course in the future we would implement paging)
@main.route("/ws/parks")
def parks():

    #query the DB for all the parkpoints
    result = mongo.db.parkpoints.find()

    # result_list = []
    # for doc in result:
    #     result_list.append(dumps( doc))

    #Now turn the results into valid JSON
    return str(dumps(result))
