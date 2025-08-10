import __main__
import jwt
from functools import wraps
from flask import request, redirect, url_for, current_app
from models.database import User

import hashlib
import secrets
import uuid
import time
import datetime


def get_token():
    return hashlib.sha512(secrets.token_bytes(48)).hexdigest()


def generate_token(user_id, role):
    if not hasattr(__main__, 'auth_cache'):
        __main__.auth_cache = {}

    sub = str(uuid.uuid4())

    iat = int(time.time())
    iss = "Iris"

    not_before_time = datetime.datetime.utcnow()
    expiration_time = not_before_time + datetime.timedelta(minutes=3600)

    token = get_token()

    payload = {
        'sub': sub,
        "iat": iat,
        'exp': expiration_time,
        'nbf': not_before_time,
        'iss': iss,
        "token": token,
    }

    __main__.auth_cache[token] = {"user_id": user_id, "role": role}


    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def verify_token():
    if not hasattr(__main__, 'auth_cache'):
        __main__.auth_cache = {}

    token = request.cookies.get('iris_key')
    if not token:
        return None

    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])

        if payload['token'] not in __main__.auth_cache:
            return None

        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_id():
    payload = verify_token()
    if payload:
        return __main__.auth_cache[payload['token']]['user_id']

    else:
        return None


# A OPTIMISER #
def get_username(user_id=None):
    if not user_id:
        user_id = get_user_id()
    
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            return user.username

    return None


def get_role(user_id=None):
    if not user_id:
        user_id = get_user_id()
    
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            return user.role

    return None


def get_api_all_access(user_id=None):
    if not user_id:
        user_id = get_user_id()
    
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            return user.api_all_access

    return None


def get_api_permissions(user_id=None):
    if not user_id:
        user_id = get_user_id()
    
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            return user.api_permissions

    return None
# A OPTIMISER #

def auth_required(required_roles=None):
    if not hasattr(__main__, 'auth_cache'):
        __main__.auth_cache = {}

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not __main__.backend.auth_required:
                return f(*args, **kwargs)

            payload = verify_token()
            if not payload or payload['token'] not in __main__.auth_cache:
                return redirect(url_for('admin.login'))

            if required_roles:
                if __main__.auth_cache[payload['token']]['role'] not in required_roles:
                    return redirect(url_for('admin.login'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator