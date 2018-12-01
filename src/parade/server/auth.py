from functools import wraps

from flask import Blueprint, request, Response, redirect, url_for
from flask.sessions import SecureCookieSessionInterface
from flask_login import UserMixin, login_user
from flask_restful import Api

bp = Blueprint('auth', __name__, url_prefix='/auth')
api = Api(bp)

_login_user = dict()


def check_auth(user_login_key, secret):
    """
    This function is called to check if a user/secret combination is valid.
    :param user_login_key: the login_key to login user
    :param secret: the secret to login user
    :return: the user_key of login-user or None if check failed
    """
    import hashlib
    hl = hashlib.md5()
    hl.update('parade'.encode(encoding='utf-8'))
    if user_login_key == 'parade' and secret == hl.hexdigest():
        return 'parade'

    return None


def login_user(user_key, **kwargs):
    """
    This function put the login-user into session and return the auth token
    :param user_key: the key of login-user
    :param kwargs: the extra arguments about the login-user
    :return: the auth token put in session
    """
    import uuid
    token = str(uuid.uuid3(uuid.NAMESPACE_OID, user_key))
    _login_user[user_key] = token
    return token


def check_token(user_key, auth_token):
    """
    This function check the auth token per request
    :param user_key: the user key the request announced issue-from
    :param auth_token: the auth token of the login-user
    :return: the loaded user if success otherwise None
    """
    if user_key and auth_token and user_key in _login_user and _login_user[user_key] == auth_token:
        user = ParadeUser()
        user.id = user_key
        user.token = auth_token
        return user
    return None


def authenticate():
    """Sends a 401 response that enables basic auth"""
    #return Response(
    #    'Could not verify your access level for that URL.\n'
    #    'You have to login with proper credentials', 401,
    #    {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401)


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_token = request.args.get('sid') or request.cookies.get('sid')
        if not check_token(auth_token):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


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

    uid = check_auth(username, password)
    if not uid:
        return authenticate()

    sid = login_user(uid, username=username, password=password)

    from flask import make_response
    response = make_response("login succeeded!", 200)
    response.set_cookie('uid', uid)
    response.set_cookie('sid', sid)
    return response


@bp.route('/login-view', methods=('GET',))
def login_view():
    auth = request.authorization
    if not auth:
        return authenticate()
    uid = check_auth(auth.username, auth.password)
    if not uid:
        return authenticate()

    sid = login_user(uid, username=auth.username, password=auth.password)

    return login_response(uid, sid)


@bp.route('/login-redirect', methods=('POST',))
def login_redirect():
    username = request.form.get('username', None)
    password = request.form.get('password', None)

    uid = check_auth(username, password)
    if not uid:
        return authenticate()

    sid = login_user(uid, username=username, password=password)

    return login_response(uid, sid)


class ParadeUser(UserMixin):
    pass


class DisabledSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""

    def save_session(self, *args, **kwargs):
        return
