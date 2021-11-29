# -*- encoding: utf-8 -*-

import unittest
import mock
import json
from collections import OrderedDict

import requests

from statuscake_api.client import Client
from statuscake_api.exceptions import (
    APIError, NetworkError, InvalidResponse, HTTPError,
)

M_ENVIRON = {
    'STATUSCAKE_ENDPOINT': 'statuscake_env',
    'STATUSCAKE_API_KEY': 'api key from environ',
}

M_CUSTOM_CONFIG_PATH = './tests/fixtures/custom_statuscake.conf'

API_KEY = 'fake api key'
ENDPOINT = 'statuscake_api-eu'
ENDPOINT_BAD = 'laponie'
BASE_URL = 'https://api.statuscake.com/v1'
FAKE_URL = 'http://gopher.statuscake_api.net/'

FAKE_METHOD = 'MeThOd'
FAKE_PATH = '/unit/test'

TIMEOUT = 180

class testClient(unittest.TestCase):
    ## test helpers

    def test_init(self):
        # nominal
        api = Client(ENDPOINT, API_KEY)
        self.assertEqual(API_KEY, api._api_key)
        self.assertEqual(TIMEOUT, api._timeout)

        # override default timeout
        timeout = (1, 1)
        api = Client(ENDPOINT, API_KEY, timeout=timeout)
        self.assertEqual(timeout, api._timeout)


    def test_init_from_config(self):
        with mock.patch.dict('os.environ', M_ENVIRON):
            api = Client()

        self.assertEqual(M_ENVIRON['STATUSCAKE_API_KEY'],    api._api_key)

    def test_init_from_custom_config(self):
        # custom config file
        api = Client(config_file=M_CUSTOM_CONFIG_PATH)

        self.assertEqual('This is a fake custom application key', api._api_key)


    ## test wrappers

    def test__canonicalize_kwargs(self):
        api = Client(ENDPOINT, API_KEY)

        self.assertEqual({}, api._canonicalize_kwargs({}))
        self.assertEqual({'from': 'value'}, api._canonicalize_kwargs({'from': 'value'}))
        self.assertEqual({'_to': 'value'}, api._canonicalize_kwargs({'_to': 'value'}))
        self.assertEqual({'from': 'value'}, api._canonicalize_kwargs({'_from': 'value'}))

    @mock.patch.object(Client, 'call')
    def test_get(self, m_call):
        # basic test
        api = Client(ENDPOINT, API_KEY)
        self.assertEqual(m_call.return_value, api.get(FAKE_URL))
        m_call.assert_called_once_with('GET', FAKE_URL, None)

        # append query string
        m_call.reset_mock()
        api = Client(ENDPOINT, API_KEY)
        self.assertEqual(m_call.return_value, api.get(FAKE_URL, param="test"))
        m_call.assert_called_once_with('GET', FAKE_URL+'?param=test', None)

        # append to existing query string
        m_call.reset_mock()
        api = Client(ENDPOINT, API_KEY)
        self.assertEqual(m_call.return_value, api.get(FAKE_URL+'?query=string', param="test"))
        m_call.assert_called_once_with('GET', FAKE_URL+'?query=string&param=test', None)

        # boolean arguments
        m_call.reset_mock()
        api = Client(ENDPOINT, API_KEY)
        self.assertEqual(m_call.return_value, api.get(FAKE_URL+'?query=string', checkbox=True))
        m_call.assert_called_once_with('GET', FAKE_URL+'?query=string&checkbox=true', None)

        # keyword calling convention
        m_call.reset_mock()
        api = Client(ENDPOINT, API_KEY)
        self.assertEqual(m_call.return_value, api.get(FAKE_URL, _from="start", to="end"))
        try:
            m_call.assert_called_once_with('GET', FAKE_URL+'?to=end&from=start', None)
        except:
            m_call.assert_called_once_with('GET', FAKE_URL+'?from=start&to=end', None)


    @mock.patch.object(Client, 'call')
    def test_delete(self, m_call):
        api = Client(ENDPOINT, API_KEY)
        self.assertEqual(m_call.return_value, api.delete(FAKE_URL))
        m_call.assert_called_once_with('DELETE', FAKE_URL, None)

    @mock.patch.object(Client, 'call')
    def test_post(self, m_call):
        PAYLOAD = {
            'arg1': object(),
            'arg2': object(),
            'arg3': object(),
            'arg4': False,
        }

        api = Client(ENDPOINT, API_KEY)
        self.assertEqual(m_call.return_value, api.post(FAKE_URL, **PAYLOAD))
        m_call.assert_called_once_with('POST', FAKE_URL, PAYLOAD)

    @mock.patch.object(Client, 'call')
    def test_put(self, m_call):
        PAYLOAD = {
            'arg1': object(),
            'arg2': object(),
            'arg3': object(),
            'arg4': False,
        }

        api = Client(ENDPOINT, API_KEY)
        self.assertEqual(m_call.return_value, api.put(FAKE_URL, **PAYLOAD))
        m_call.assert_called_once_with('PUT', FAKE_URL, PAYLOAD)

    ## test core function

    @mock.patch('statuscake_api.client.Session.request')
    def test_call_no_sign(self, m_req):
        m_res = m_req.return_value
        m_json = m_res.json.return_value

        api = Client(ENDPOINT, API_KEY)

        # nominal
        m_res.status_code = 200
        self.assertEqual(m_json, api.call(FAKE_METHOD, FAKE_PATH, None))
        m_req.assert_called_once_with(
            FAKE_METHOD, BASE_URL+'/unit/test',
            headers={}, data='',
            timeout=TIMEOUT
        )
        m_req.reset_mock()

        # data, nominal
        m_res.status_code = 200
        data = {'key': 'value'}
        self.assertEqual(m_json, api.call(FAKE_METHOD, FAKE_PATH, data))
        m_req.assert_called_once_with(
            FAKE_METHOD, BASE_URL+'/unit/test',
            headers={'Content-type': 'application/x-www-form-urlencoded'},
            data=data, timeout=TIMEOUT
        )
        m_req.reset_mock()

        # request fails, somehow
        m_req.side_effect = requests.RequestException
        self.assertRaises(HTTPError, api.call, FAKE_METHOD, FAKE_PATH, None)
        m_req.side_effect = None

        # response decoding fails
        m_res.json.side_effect = ValueError
        self.assertRaises(InvalidResponse, api.call, FAKE_METHOD, FAKE_PATH, None)
        m_res.json.side_effect = None

        m_res.status_code = 0
        self.assertRaises(NetworkError, api.call, FAKE_METHOD, FAKE_PATH, None)
        m_res.status_code = 99
        self.assertRaises(APIError, api.call, FAKE_METHOD, FAKE_PATH, None)
        m_res.status_code = 306
        self.assertRaises(APIError, api.call, FAKE_METHOD, FAKE_PATH, None)


    @mock.patch('statuscake_api.client.Session.request')
    def test_call_query_id(self, m_req):
        m_res = m_req.return_value
        m_json = m_res.json.return_value
        m_res.headers = {}

        api = Client(ENDPOINT, API_KEY)

        m_res.status_code = 99
        self.assertRaises(APIError, api.call, FAKE_METHOD, FAKE_PATH, None)
        try:
            api.call(FAKE_METHOD, FAKE_PATH, None)
            self.assertEqual(0, 1)   # should fail as method have to raise APIError
        except APIError as e:
            pass


    @mock.patch('statuscake_api.client.Session.request', return_value="Let's assume requests will return this")
    def test_raw_call(self, m_req):
        api = Client(ENDPOINT, API_KEY)
        r = api.raw_call(FAKE_METHOD, FAKE_PATH, None)
        self.assertEqual(r, "Let's assume requests will return this")
