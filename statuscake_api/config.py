# -*- encoding: utf-8 -*-

"""
The straightforward way to use STATUSCAKE's API keys is to embed them directly in the
application code. While this is very convenient, it lacks of elegance and
flexibility.

Alternatively it is suggested to use configuration files or environment
variables so that the same code may run seamlessly in multiple environments.
Production and development for instance.

This wrapper will first look for direct instantiation parameters then
``STATUSCAKE_ENDPOINT``, ``STATUSCAKE_API_KEY`` environment variables. If either of these parameter is not
provided, it will look for a configuration file of the form:

.. code:: ini

    [default]
    ; general configuration: default endpoint
    endpoint=user-1

    [user-1]
    ; configuration specific to 'user-1' endpoint
    api_key=my_api_key

The client will successively attempt to locate this configuration file in

1. Current working directory: ``./statuscake.conf``
2. Current user's home directory ``~/.statuscake.conf``
3. System wide configuration ``/etc/statuscake.conf``

This lookup mechanism makes it easy to overload credentials for a specific
project or user.
"""

import os

try:
    from ConfigParser import RawConfigParser, NoSectionError, NoOptionError
except ImportError: # pragma: no cover
    # Python 3
    from configparser import RawConfigParser, NoSectionError, NoOptionError

__all__ = ['config']

#: Locations where to look for configuration file by *increasing* priority
CONFIG_PATH = [
    '/etc/statuscake.conf',
    os.path.expanduser('~/.statuscake.conf'),
    os.path.realpath('./statuscake.conf'),
]

class ConfigurationManager(object):
    '''
    Application wide configuration manager
    '''
    def __init__(self):
        '''
        Create a config parser and load config from environment.
        '''
        # create config parser
        self.config = RawConfigParser()
        self.config.read(CONFIG_PATH)

    def get(self, section, name):
        '''
        Load parameter ``name`` from configuration, respecting priority order.
        Most of the time, ``section`` will correspond to the current api
        ``endpoint``. ``default`` section only contains ``endpoint`` and general
        configuration.

        :param str section: configuration section or region name. Ignored when
            looking in environment
        :param str name: configuration parameter to lookup
        '''
        # 1/ try env
        try:
            return os.environ['STATUSCAKE_'+name.upper()]
        except KeyError:
            pass

        # 2/ try from specified section/endpoint
        try:
            return self.config.get(section, name)
        except (NoSectionError, NoOptionError):
            pass

        # not found, sorry
        return None

    def read(self, config_file):
        # Read an other config file
        self.config.read(config_file)

#: System wide instance :py:class:`ConfigurationManager` instance
config = ConfigurationManager()
