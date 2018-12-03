from functools import wraps

from flask import Response, request, current_app
from flask.sessions import SecureCookieSessionInterface
from flask_login import UserMixin


class ParadeUser(UserMixin):
    pass


class DisabledSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""

    def save_session(self, *args, **kwargs):
        return


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_manager = current_app.auth_manager
        auth_token = request.args.get('sid') or request.cookies.get('sid')
        if not auth_token or not auth_manager.check_token(auth_token):
            return auth_manager.authenticate()
        return f(*args, **kwargs)

    return decorated


class AuthManager(object):
    _login_user = dict()

    def check_auth(self, user_login_key, secret):
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

    def login_user(self, user_key, **kwargs):
        """
        This function put the login-user into session and return the auth token
        :param user_key: the key of login-user
        :param kwargs: the extra arguments about the login-user
        :return: the auth token put in session
        """
        import uuid
        token = str(uuid.uuid3(uuid.NAMESPACE_OID, user_key))
        self._login_user[user_key] = token
        return token

    def check_token(self, user_key, auth_token):
        """
        This function check the auth token per request
        :param user_key: the user key the request announced issue-from
        :param auth_token: the auth token of the login-user
        :return: the loaded user if success otherwise None
        """
        if user_key and auth_token and user_key in self._login_user and self._login_user[user_key] == auth_token:
            user = ParadeUser()
            user.id = user_key
            user.token = auth_token
            return user
        return None

    def authenticate(self):
        """Sends a 401 response that enables basic auth"""
        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401)
