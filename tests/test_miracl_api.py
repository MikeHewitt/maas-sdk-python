import unittest

import miracl_api
from mock import patch
from oic.oauth2.message import Message


def _generate_ok_response(data=None):
    if data is None:
        data = {}
    return Message().from_dict(data)


def _generate_err_response(error, message=""):
    return Message().from_dict({
        "error": error,
        "error_message": message
    })


class TestBasics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = miracl_api.MiraclClient("MOCK_CLIENT", "MOCK_SECRET",
                                          "http://nothing")

    def test_auth_request_url(self):
        session = {}
        url = self.api.get_authorization_request_url(session)
        self.assertIsNotNone(url)
        self.assertTrue(miracl_api.SESSION_MIRACL_STATE_KEY in session)
        self.assertTrue(miracl_api.SESSION_MIRACL_NONCE_KEY in session)

    def test_request_token_good(self):
        response = _generate_ok_response({"access_token": "MOCK_TOKEN"})

        with patch("oic.oic.Client.do_access_token_request") as mock:
            mock.return_value = response
            session = {}
            self.api.get_authorization_request_url(session)
            query_string = "code=MOCK_CODE&state={0}".format(
                session[miracl_api.SESSION_MIRACL_STATE_KEY])
            token = self.api.validate_authorization(session, query_string)
            self.assertEqual("MOCK_TOKEN", token)

    def test_request_token_no_state(self):
        response = _generate_ok_response({"access_token": "MOCK_TOKEN"})

        with patch("oic.oic.Client.do_access_token_request") as mock:
            mock.return_value = response
            session = {}
            query_string = "code=MOCK_CODE&state="
            token = self.api.validate_authorization(session, query_string)
            self.assertEqual("MOCK_TOKEN", token)


class TestExpectedFailures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = miracl_api.MiraclClient("MOCK_CLIENT", "MOCK_SECRET",
                                          "http://nothing")

    def test_request_token_empty_url(self):
        session = {}
        self.api.get_authorization_request_url(session)
        self.assertIsNone(self.api.validate_authorization(session, ""))

    def test_request_token_garbage_url(self):
        session = {}
        self.api.get_authorization_request_url(session)
        self.assertRaises(miracl_api.MiraclError,
                          self.api.validate_authorization, session, "garbage")

    def test_request_token_server_error(self):
        response = _generate_ok_response({"error": "MOCK_ERROR"})

        with patch("oic.oic.Client.do_access_token_request") as mock:
            mock.return_value = response
            session = {}
            self.api.get_authorization_request_url(session)
            query_string = "code=MOCK_CODE&state={0}".format(
                session[miracl_api.SESSION_MIRACL_STATE_KEY])
            token = self.api.validate_authorization(session, query_string)
            self.assertIsNone(token)


class TestUnexpectedFalures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = miracl_api.MiraclClient("MOCK_CLIENT", "MOCK_SECRET",
                                          "http://nothing")

    def test_request_token_wrong_state(self):
        response = _generate_ok_response({"access_token": "MOCK_TOKEN"})

        with patch("oic.oic.Client.do_access_token_request") as mock:
            mock.return_value = response
            session = {}
            self.api.get_authorization_request_url(session)
            query_string = "code=MOCK_CODE&state={0}".format("wrong_state")
            self.assertRaises(miracl_api.MiraclError,
                              self.api.validate_authorization,
                              session, query_string)
