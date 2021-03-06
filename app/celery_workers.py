import random

import dlib
import io
import numpy as np
import cv2
from PIL import Image

import time

from flask import Blueprint, jsonify, abort
from flask_pymongo import GridFS, NoFile, ObjectId, MongoClient

from .utils import task_state
from . import celery, mongo, mongodb_helper

tasks_bp = Blueprint('tasks', __name__)

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

@celery.task()
def detect(src_img,dest_img):
    img = cv2.imread(src_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 1)
    for (x,y,w,h) in faces:
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),5)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = img[y:y+h, x:x+w]

    cv2.imwrite(dest_img, img)



@celery.task(bind=True)
def long_task(self):

    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@tasks_bp.route('/status/<task_id>')
def task_status(task_id):
    task = long_task.AsyncResult(task_id)
    return task_state(task)

@celery.task(bind=True)
def detect_face_long_task(self, environ, file_id, base='fs'):

    """Background task that runs a long function with progress reports."""
    message = ''
    self.update_state(state='PROGRESS',
                      meta={'current': 30,
                            'total': 100,
                            'status': 'Upload image'})
    time.sleep(1)

    from .wsgi_aux import app
    with app.request_context(environ):

        # mongo.init_app(app)
        # mongo.init_app(app, config_prefix= 'MONGO')

        fs = GridFS(mongo.db, base)
        try:
            with fs.get(ObjectId(file_id)) as fp_read:
                fileobj = io.BytesIO(fp_read.read())
                image = Image.open(fileobj)
        except NoFile:
            return {'current': 100, 'total': 100, 'status': 'No file!',
                    'result': 0}

        time.sleep(1)
        self.update_state(state='PROGRESS',
                          meta={'current': 50,
                                'total': 100,
                                'status': 'Detect face'})

        detector = dlib.get_frontal_face_detector()
        dets = detector(image, 1)

        for i, d in enumerate(dets):
            message = ("Detection {}: Left: {} Top: {} Right: {} Bottom: {}".format(
                i, d.left(), d.top(), d.right(), d.bottom()))


        time.sleep(1)
        self.update_state(state='PROGRESS',
                          meta={'current': 100,
                                'total': 100,
                                'status': message})

        time.sleep(1)

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}

@celery.task(bind=True)
def detect_face_long_task_without_app(self, file_id, base='fs'):

    """Background task that runs a long function with progress reports."""
    message = ''
    self.update_state(state='PROGRESS',
                      meta={'current': 30,
                            'total': 100,
                            'status': 'Upload image'})
    time.sleep(5)

    # client = MongoClient('localhost:27017')
    # db = client.parks
    # fs = GridFS(db, base)

    from .wsgi_aux import app
    mongodb_helper.init_app(app.config)

    fs = GridFS(mongodb_helper.db, base)
    try:
        with fs.get(ObjectId(file_id)) as fp_read:
            fileobj = io.BytesIO(fp_read.read())
            image = np.array(Image.open(fileobj))
    except NoFile:
        return {'current': 100, 'total': 100, 'status': 'No file!',
                'result': 0}

    time.sleep(5)
    self.update_state(state='PROGRESS',
                      meta={'current': 50,
                            'total': 100,
                            'status': 'Detect face'})

    detector = dlib.get_frontal_face_detector()
    dets = detector(image, 5)

    for i, d in enumerate(dets):
        message = ("Detection {}: Left: {} Top: {} Right: {} Bottom: {}".format(
            i, d.left(), d.top(), d.right(), d.bottom()))


    time.sleep(1)
    self.update_state(state='PROGRESS',
                      meta={'current': 100,
                            'total': 100,
                            'status': message})

    time.sleep(5)

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}

@tasks_bp.route('/mongo/<task_id>')
def mongo_task_status(task_id):
    task = detect_face_long_task_without_app.AsyncResult(task_id)
    return task_state(task)


