from flask import Blueprint
from flask import Flask
from flask import render_template

from . import mongo

main = Blueprint('main', __name__)


@main.route('/')
def home_page():
    online_users = mongo.db.users.find({'online': True})
    return render_template('index.html', online_users=online_users)