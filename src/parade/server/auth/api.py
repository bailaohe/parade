from flask import Blueprint, request, redirect, url_for
from flask_restful import Api
from flask import current_app

bp = Blueprint('auth', __name__, url_prefix='/auth')
api = Api(bp)


def login_response(uid, sid):
    from flask import make_response
    next = request.args.get('next')
    response = make_response(redirect(next) if next else redirect(url_for('index')))
    response.set_cookie('uid', uid)
    response.set_cookie('sid', sid)
    return response


@bp.route('/login', methods=('POST',))
def login():
    username = request.args.get('username', None)
    password = request.args.get('password', None)

    uid = current_app.auth_manager.check_auth(username, password)
    if not uid:
        return current_app.auth_manager.authenticate()

    sid = current_app.auth_manager.login_user(uid, username=username, password=password)

    from flask import make_response
    response = make_response("login succeeded!", 200)
    response.set_cookie('uid', uid)
    response.set_cookie('sid', sid)
    return response


@bp.route('/login-view', methods=('GET',))
def login_view():
    auth = request.authorization
    if not auth:
        return current_app.auth_manager.authenticate()
    uid = current_app.auth_manager.check_auth(auth.username, auth.password)
    if not uid:
        return current_app.auth_manager.authenticate()

    sid = current_app.auth_manager.login_user(uid, username=auth.username, password=auth.password)

    return login_response(uid, sid)


@bp.route('/login-redirect', methods=('POST',))
def login_redirect():
    username = request.form.get('username', None)
    password = request.form.get('password', None)

    uid = current_app.auth_manager.check_auth(username, password)
    if not uid:
        return current_app.auth_manager.authenticate()

    sid = current_app.auth_manager.login_user(uid, username=username, password=password)

    return login_response(uid, sid)
