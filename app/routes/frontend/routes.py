from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def index():
    return render_template('index.html')

@frontend_bp.route('/login')
def login():
    return render_template('login.html')

@frontend_bp.route('/signin')
def signin():
    return render_template('signin.html')