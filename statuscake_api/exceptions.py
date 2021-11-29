# -*- encoding: utf-8 -*-

"""
All exceptions used in Statuscake SDK derives from `APIError`
"""

class APIError(Exception):
    pass

class HTTPError(APIError):
    """Raised when the request fails at a low level (DNS, network, ...)"""

class InvalidResponse(APIError):
    """Raised when api response is not valid json"""

class NetworkError(APIError):
    """Raised when there is an error from network layer."""
