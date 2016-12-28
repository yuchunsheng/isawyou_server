import json
import os
from bson.json_util import dumps

from flask import Blueprint
from flask import current_app, flash, redirect, request, url_for, render_template

from flask_pymongo import GridFS
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
