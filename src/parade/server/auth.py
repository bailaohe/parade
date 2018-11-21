from functools import wraps

from flask import Blueprint, request, Response, redirect, url_for
from flask.sessions import SecureCookieSessionInterface
from flask_login import UserMixin, login_user
from flask_restful import Api

bp = Blueprint('auth', __name__, url_prefix='/auth')
api = Api(bp)


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return True


def login_user(user_key, **kwargs):
    return 'implement-me'


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_request():
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def check_request():
    # first, try to login using the api_key url arg
    auth_token = request.args.get('sid') or request.cookies.get('sid')
    if auth_token:
        user = ParadeUser()
        user.id = auth_token
        return user
    return None


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def login_response(sid):
    from flask import make_response
    next = request.args.get('next')
    response = make_response(redirect(next) if next else redirect(url_for('index')))
    response.set_cookie('sid', sid)
    return response


@bp.route('/login', methods=('POST',))
def login():
    user_key = request.args.get('username', None)
    password = request.args.get('password', None)

    return login_user(user_key, password=password)


@bp.route('/login-view', methods=('GET',))
def login_view():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    sid = login_user(auth.username, password=auth.password)

    return login_response(sid)


@bp.route('/login-redirect', methods=('POST',))
def login_redirect():
    user_key = request.form.get('username', None)
    password = request.form.get('password', None)

    sid = login_user(user_key, password=password)

    return login_response(sid)


class ParadeUser(UserMixin):
    pass


class DisabledSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""

    def save_session(self, *args, **kwargs):
        return
