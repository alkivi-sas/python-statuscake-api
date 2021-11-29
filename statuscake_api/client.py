# -*- encoding: utf-8 -*-

"""
This module provides a simple python wrapper over the Statuscake API
"""

import hashlib
import urllib
import keyword
import time
import json
from requests import Session
from requests.exceptions import RequestException
from requests.auth import AuthBase

try:
    from urllib import urlencode
except ImportError: # pragma: no cover
    # Python 3
    from urllib.parse import urlencode

from .config import config
from .exceptions import (
    APIError, InvalidResponse, HTTPError, NetworkError
)

#: Default timeout for each request. 180 seconds connect, 180 seconds read.
TIMEOUT = 180


class BearerAuth(AuthBase):
    """
    Will add proper headers for requests call.
    """
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class Client(object):
    """
    Low level Statuscake Client. It abstracts all the authentication and request
    signing logic.

    All low level request logic including signing and error handling takes place
    in :py:func:`Client.call` function. Convenient wrappers
    :py:func:`Client.get` :py:func:`Client.post`, :py:func:`Client.put`,
    :py:func:`Client.delete` should be used instead. :py:func:`Client.post`,
    :py:func:`Client.put` both accept arbitrary list of keyword arguments
    mapped to ``data`` param of :py:func:`Client.call`.
    """

    def __init__(self, endpoint=None, api_key=None, timeout=TIMEOUT,
                 config_file=None):
        """
        Creates a new Client. No credential check is done at this point.

        If any of ``endpoint``, ``api_key`` is not provided, this client will attempt to locate
        from them from environment, ~/.statuscake.conf or /etc/statuscake.conf.

        See :py:mod:`statuscake.config` for more information on supported
        configuration mechanisms.

        ``timeout`` can either be a float or a tuple. If it is a float it
        sets the same timeout for both connection and read. If it is a tuple
        connection and read timeout will be set independently. To use the
        latter approach you need at least requests v2.4.0. Default value is
        180 seconds for connection and 180 seconds for read.

        :param str endpoint: API endpoint to use.
        :param str api_key: Statuscake API Key
        :param tuple timeout: Connection and read timeout for each request
        :param float timeout: Same timeout for both connection and read
        """
        # Load a custom config file if requested
        if config_file is not None:
            config.read(config_file)

        # load endpoint
        if endpoint is None:
            endpoint = config.get('default', 'endpoint')

        # load keys
        if api_key is None:
            api_key = config.get(endpoint, 'api_key')
        self._api_key = api_key

        self._endpoint = 'https://api.statuscake.com/v1'

        # use a requests session to reuse HTTPS connections between requests
        self._session = Session()
        self._session.auth = BearerAuth(api_key)

        # Override default timeout
        self._timeout = timeout

    ## high level API

    def _canonicalize_kwargs(self, kwargs):
        """
        If an API needs an argument colliding with a Python reserved keyword, it
        can be prefixed with an underscore. For example, ``from`` argument of
        ``POST /email/domain/{domain}/redirection`` may be replaced by ``_from``

        :param dict kwargs: input kwargs
        :return dict: filtered kawrgs
        """
        arguments = {}

        for k, v in kwargs.items():
            if k[0] == '_' and k[1:] in keyword.kwlist:
                k = k[1:]
            arguments[k] = v

        return arguments

    def _prepare_query_string(self, kwargs):
        """
        Boolean needs to be send as lowercase 'false' or 'true' in querystring.
        This function prepares arguments for querystring and encodes them.

        :param dict kwargs: input kwargs
        :return string: prepared querystring
        """
        arguments = {}

        for k, v in kwargs.items():
            if isinstance(v, bool):
                v = str(v).lower()
            arguments[k] = v

        return urlencode(arguments)

    def get(self, _target, **kwargs):
        """
        'GET' :py:func:`Client.call` wrapper.

        Query string parameters can be set either directly in ``_target`` or as
        keyword arguments. If an argument collides with a Python reserved
        keyword, prefix it with a '_'. For instance, ``from`` becomes ``_from``.

        :param string _target: API method to call
        """
        if kwargs:
            kwargs = self._canonicalize_kwargs(kwargs)
            query_string = self._prepare_query_string(kwargs)
            if '?' in _target:
                _target = '%s&%s' % (_target, query_string)
            else:
                _target = '%s?%s' % (_target, query_string)

        return self.call('GET', _target, None)

    def put(self, _target, **kwargs):
        """
        'PUT' :py:func:`Client.call` wrapper

        Body parameters can be set either directly in ``_target`` or as keyword
        arguments. If an argument collides with a Python reserved keyword,
        prefix it with a '_'. For instance, ``from`` becomes ``_from``.

        :param string _target: API method to call
        """
        kwargs = self._canonicalize_kwargs(kwargs)
        return self.call('PUT', _target, kwargs)

    def post(self, _target, **kwargs):
        """
        'POST' :py:func:`Client.call` wrapper

        Body parameters can be set either directly in ``_target`` or as keyword
        arguments. If an argument collides with a Python reserved keyword,
        prefix it with a '_'. For instance, ``from`` becomes ``_from``.

        :param string _target: API method to call
        """
        kwargs = self._canonicalize_kwargs(kwargs)
        return self.call('POST', _target, kwargs)

    def delete(self, _target):
        """
        'DELETE' :py:func:`Client.call` wrapper

        :param string _target: API method to call
        """
        return self.call('DELETE', _target, None)

    ## low level helpers

    def call(self, method, path, data=None):
        """
        Low level call helper. 

        :param str method: HTTP verb. Usually one of GET, POST, PUT, DELETE
        :param str path: api entrypoint to call, relative to endpoint base path
        :param data: any json serializable data to send as request's body
        :raises HTTPError: when underlying request failed for network reason
        :raises InvalidResponse: when API response could not be decoded
        """
        # attempt request
        try:
            result = self.raw_call(method=method, path=path, data=data)
        except RequestException as error:
            raise HTTPError("Low HTTP request failed error", error)

        status = result.status_code

        # attempt to decode and return the response
        try:
            if status != 204:
                json_result = result.json()
            else:
                json_result = None
        except ValueError as error:
            raise InvalidResponse("Failed to decode API response", error)

        # error check
        if status >= 100 and status < 300:
            return json_result
        elif status == 0:
            raise NetworkError()
        else:
            message = json_result.get('message', '')
            errors = json_result.get('errors', {})
            for error, error_msg in errors.items():
                full_error = ", ".join(error_msg)
                message += f"\n{error}: {full_error}"
            raise APIError(message)

    def raw_call(self, method, path, data=None):
        """
        Lowest level call helper.
        Will return a vendored ``requests.Response`` object or let any
        ``requests`` exception pass through.

        :param str method: HTTP verb. Usually one of GET, POST, PUT, DELETE
        :param str path: api entrypoint to call, relative to endpoint base path
        :param data: any json serializable data to send as request's body
        """
        body = ''
        target = self._endpoint + path
        headers = {}

        if data is not None:
            headers['Content-type'] = 'application/x-www-form-urlencoded'
            body = data

        return self._session.request(method, target, headers=headers,
                                     data=body, timeout=self._timeout)
