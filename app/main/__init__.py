# app/main/__init__.py  (Blueprint creation)

from flask import Blueprint

main = Blueprint('main', __name__)

# can use from main import views
from . import views, errors