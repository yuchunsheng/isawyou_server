import base64
import json
import os

import cv2
import numpy as np

from bson.json_util import dumps

from flask import Blueprint
from flask import current_app, abort, flash, redirect, request, url_for, render_template

from flask_pymongo import GridFS, NoFile
from mimetypes import guess_type

from werkzeug.utils import secure_filename


from . import mongo

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

@main.route('/')
def home_page():
    return render_template('index.html')
    # return render_template('index.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for("/"))

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            content_type, _ = guess_type(filename)
            storage = GridFS(mongo.db, 'fs')
            storage.put(file, filename=filename, content_type=content_type)

        # return redirect(url_for('home_page', filename=filename))
        return 'file uploaded successfully'


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


@main.route('/uploads/<path:filename>', methods=['POST'])
def save_upload(filename):
    mongo.save_file(filename, request.files['file'])
    return redirect(url_for('get_upload', filename=filename))


@main.route('/uploads/<path:filename>')
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
