from flask import Blueprint, request

facepp_business = Blueprint('facepp_business', __name__)

from . import client_operation