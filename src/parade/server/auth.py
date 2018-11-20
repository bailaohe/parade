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
    return username == 'admin' and password == 'secret'


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


@bp.route('/login', methods=('GET',))
def login():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    ## 通过Flask-Login的login_user方法登录用户

    # 如果请求中有next参数，则重定向到其指定的地址，
    # 没有next参数，则重定向到"index"视图
    print(request.referrer)
    next = request.args.get('next')
    next += '&' if '?' in next else '?'
    next += 'authtoken=123'

    return redirect(next or url_for('index'))


class ParadeUser(UserMixin):
    pass


class CustomSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""

    def save_session(self, *args, **kwargs):
        return
