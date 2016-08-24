from __future__ import unicode_literals

import json

from oic import rndstr
from oic.oic import Client, PyoidcError
from oic.oic.message import RegistrationResponse, AuthorizationResponse, \
    AccessTokenResponse
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.oauth2 import SUCCESSFUL
import logging
from .config import config
from .messages import *

_issuer = config["ISSUER"]

_logger = logging.getLogger(__name__)

SESSION_MIRACL_TOKEN_KEY = "miracl_token"
SESSION_MIRACL_NONCE_KEY = "miracl_nonce"
SESSION_MIRACL_STATE_KEY = "miracl_state"
SESSION_MIRACL_USERINFO_KEY = "miracl_userinfo"


class MiraclClient(object):

    def __init__(self, client_id, secret, redirect_uri,
                 allow_empty_state=True, issuer=_issuer):
        super(MiraclClient, self).__init__()

        self.issuer = issuer
        self.allow_empty_state = allow_empty_state
        client = Client(client_authn_method=CLIENT_AUTHN_METHOD)

        self.provider_info = client.provider_config(issuer=self.issuer)

        _logger.info(MIRACL_LOG_RECEIVED_PROVIDER_INFO, self.provider_info)

        self.info = {"client_id": client_id,
                     "client_secret": secret,
                     "redirect_uris": [redirect_uri]
                     }

    def _create_client(self, session):
        if SESSION_MIRACL_STATE_KEY not in session:
            session[SESSION_MIRACL_STATE_KEY] = rndstr()
        if SESSION_MIRACL_NONCE_KEY not in session:
            session[SESSION_MIRACL_NONCE_KEY] = rndstr()

        client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
        client.handle_provider_config(self.provider_info, issuer=self.issuer)
        client_reg = RegistrationResponse(**self.info)
        client.store_registration_info(client_reg)

        if SESSION_MIRACL_TOKEN_KEY in session:
            access_token = AccessTokenResponse().from_dict(
                session[SESSION_MIRACL_TOKEN_KEY])

            client.registration_access_token = access_token

        return client

    def get_authorization_request_url(self, session):
        """
        Returns redirect URL for authorization via M-Pin system. After URL
        redirects back, pass query_string to validate_authorization to complete
        authorization with server.
        :arg session mutable dictionary that contains session variables
        """

        client = self._create_client(session)

        # Regenerate state and nonce on each auth url request
        session[SESSION_MIRACL_STATE_KEY] = rndstr()
        session[SESSION_MIRACL_NONCE_KEY] = rndstr()

        args = {
            "client_id": client.client_id,
            "response_type": "code",
            "scope": ['openid', 'email', 'sub', 'name'],
            "nonce": session[SESSION_MIRACL_NONCE_KEY],
            "redirect_uri": client.registration_response["redirect_uris"][0],
            "state": session[SESSION_MIRACL_STATE_KEY]
        }

        _logger.debug(MIRACL_LOG_AUTHORIZATION_REQUEST, args)

        auth_req = client.construct_AuthorizationRequest(request_args=args)
        request = auth_req.request(client.authorization_endpoint)

        _logger.debug(MIRACL_LOG_AUTHORIZATION_REQUEST_URL, request)

        return request

    def validate_authorization(self, session, query_string):
        """
        Returns access token if validation succeeds or None if query string
        doesn't contain code and state.
        :arg session mutable dictionary that contains session variables
        :arg query_string query string returned from authorization URL.
        """
        if query_string is None or query_string == "":
            # Redirect without parameters means authorization was denied
            return None

        client = self._create_client(session)

        try:
            response = client.parse_response(AuthorizationResponse,
                                             info=query_string,
                                             sformat="urlencoded")
        except PyoidcError as e:
            raise MiraclError(
                MIRACL_MSG_QUERY_STRING_PARSE_FAILED, e).log_exception()

        if "state" in response:
            if response["state"] != session[SESSION_MIRACL_STATE_KEY]:
                raise MiraclError(
                    MIRACL_MSG_STATE_DIFFERS)
        else:
            if not self.allow_empty_state:
                raise MiraclError(MIRACL_MSG_QUERY_STRING_NO_STATE)
            # Workaround for stateless request from Miracl system
            session[SESSION_MIRACL_STATE_KEY] = ""

        args = {
            "redirect_uri": client.registration_response["redirect_uris"][0],
            "client_id": client.client_id,
            "client_secret": client.client_secret
        }

        _logger.debug(MIRACL_LOG_REQUEST_ACCESS_TOKEN, args)
        try:
            resp = client.do_access_token_request(
                scope=['openid', 'email', 'sub', 'name'],
                state=session[SESSION_MIRACL_STATE_KEY],
                request_args=args,
                authn_method="client_secret_basic"
            )
        except PyoidcError as e:
            raise MiraclError(
                MIRACL_MSG_ACCESS_TOKEN_REQUEST_FAILED, e).log_exception()

        resp_dict = resp.to_dict()
        _logger.debug(MIRACL_LOG_REQUEST_TOKEN_RESPONSE, resp_dict)

        if "access_token" in resp_dict:
            session[SESSION_MIRACL_TOKEN_KEY] = resp_dict
            return resp_dict["access_token"]
        else:
            return None

    @staticmethod
    def clear_user_info(session, including_auth=False):
        """
        Clears session from user info
        :arg session mutable dictionary that contains session variables
        :arg including_auth clear also authentication data
        """
        keys = [SESSION_MIRACL_USERINFO_KEY]
        if including_auth:
            keys += [SESSION_MIRACL_NONCE_KEY,
                     SESSION_MIRACL_STATE_KEY,
                     SESSION_MIRACL_TOKEN_KEY]
        for key in keys:
            try:
                del session[key]
            except KeyError:
                pass

    def _request_user_info(self, session):
        if SESSION_MIRACL_TOKEN_KEY not in session:
            return None

        if SESSION_MIRACL_USERINFO_KEY in session:
            _logger.debug(MIRACL_LOG_USER_INFO_RESPONSE_SESSION,
                          session[SESSION_MIRACL_USERINFO_KEY])
            return json.loads(session[SESSION_MIRACL_USERINFO_KEY])

        client = self._create_client(session)

        if "access_token" not in client.registration_access_token:
            return None

        # noinspection PyUnresolvedReferences
        request = client.construct_UserInfoRequest(
            request_args={
                "access_token": client.registration_access_token[
                    "access_token"],
                "client_id": client.client_id,
                "client_secret": client.client_secret
            }
        ).request(client.userinfo_endpoint)

        _logger.debug(MIRACL_LOG_USER_INFO_REQUEST, request)
        try:
            response = client.http_request(
                url=request,
                method='GET',
                headers={
                    "Authorization": "Bearer " +
                                     client.registration_access_token[
                                         "access_token"]
                })
        except PyoidcError as e:
            raise MiraclError(
                MIRACL_MSG_USER_INFO_REQUEST_FAILED, e).log_exception()

        if response.status_code not in SUCCESSFUL:
            return None

        text = response.text
        _logger.debug(MIRACL_LOG_USER_INFO_RESPONSE, response, text)
        try:
            resp_json = json.loads(text)
            session[SESSION_MIRACL_USERINFO_KEY] = text
            return resp_json
        except ValueError as e:
            raise MiraclError(MIRACL_MSG_CORRUPTED_RESPONSE, e)

    def is_authorized(self, session):
        """
        Returns True if access token is in session
        :arg session mutable dictionary that contains session variables
        """
        client = self._create_client(session)
        if client.registration_access_token is not None:
            return True
        return False

    def get_email(self, session):
        """
        Returns e-mail of authenticated user. If user is not authenticated or
        server does not return e-mail as part of user data, returns None.
        Data from user data is cached in session. If fresh data is required,
        use clear_user_info before call to this function.
        :arg session mutable dictionary that contains session variables
        """
        response = self._request_user_info(session)
        if response is not None and "email" in response:
            return response["email"]
        return None

    def get_user_id(self, session):
        """
        Returns user ID of authenticated user. If user is not authenticated or
        server does not return user ID as part of user data, returns None.
        Data from user data is cached in session. If fresh data is required,
        use clear_user_info before call to this function.
        :arg session mutable dictionary that contains session variables
        """
        response = self._request_user_info(session)
        if response is not None and "sub" in response:
            return response["sub"]
        return None


class MiraclError(Exception):

    def __init__(self, message, exception=None):
        self.message = message
        self.exception = exception
        if exception is None:
            Exception.__init__(self, message)
        else:
            Exception.__init__(
                self,
                MIRACL_MSG_EXCEPTION_NESTED.format(message, exception))

    def log_exception(self):
        _logger.error(MIRACL_MSG_EXCEPTION_LOGGED.format(self.message))
        return self
