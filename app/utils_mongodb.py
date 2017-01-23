import os
import uuid
from mimetypes import guess_type

from werkzeug.utils import secure_filename
from flask_pymongo import GridFS

from .utils import allowed_file

from . import mongo


def save_file_mongodb(file_obj):

    if file_obj.filename == '':
        return None

    extension = os.path.splitext(file_obj.filename)[1]
    f_name = str(uuid.uuid4()) + extension

    if file_obj and allowed_file(file_obj.filename):
        filename = secure_filename(f_name)
        content_type, _ = guess_type(filename)
        storage = GridFS(mongo.db)
        file_id = storage.put(file_obj, filename=filename, content_type=content_type)

        return str(file_id)
