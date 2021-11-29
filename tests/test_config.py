# -*- encoding: utf-8 -*-

from statuscake_api import config
import unittest
import mock
import os

M_CONFIG_PATH = [
    './tests/fixtures/etc_statuscake.conf',
    './tests/fixtures/home_statuscake.conf',
    './tests/fixtures/pwd_statuscake.conf',
]

M_CUSTOM_CONFIG_PATH = './tests/fixtures/custom_statuscake.conf'

M_ENVIRON = {
    'STATUSCAKE_ENDPOINT': 'endpoint from environ',
    'STATUSCAKE_API_KEY': 'application key from environ',
}

class testConfig(unittest.TestCase):
    def setUp(self):
        """Overload configuration lookup path"""
        self._orig_CONFIG_PATH = config.CONFIG_PATH
        config.CONFIG_PATH = M_CONFIG_PATH

    def tearDown(self):
        """Restore configuration lookup path"""
        config.CONFIG_PATH = self._orig_CONFIG_PATH

    def test_real_lookup_path(self):
        home = os.environ['HOME']
        pwd = os.environ['PWD']

        self.assertEqual([
           '/etc/statuscake.conf',
           home+'/.statuscake.conf',
           pwd+'/statuscake.conf',

        ], self._orig_CONFIG_PATH)

    def test_config_get_conf(self):
        conf = config.ConfigurationManager()

        self.assertEqual('statuscake', conf.get('default', 'endpoint'))
        self.assertEqual('This is a *fake* home api key',    conf.get('statuscake', 'api_key'))
        self.assertEqual('This is a fake local application key',   conf.get('statuscake_local', 'api_key'))

        self.assertTrue(conf.get('statuscake-eu', 'non-existent') is None)
        self.assertTrue(conf.get('statuscake-ca', 'api_key') is None)
        self.assertTrue(conf.get('statuscake-laponie', 'api_key') is None)

    def test_config_get_conf_env_rules_them_all(self):
        conf = config.ConfigurationManager()

        with mock.patch.dict('os.environ', M_ENVIRON):
            self.assertEqual(M_ENVIRON['STATUSCAKE_ENDPOINT'],           conf.get('wathever', 'endpoint'))
            self.assertEqual(M_ENVIRON['STATUSCAKE_API_KEY'],    conf.get('wathever', 'api_key'))

        self.assertTrue(conf.get('statuscake-eu', 'non-existent') is None)

    def test_config_get_custom_conf(self):
        conf = config.ConfigurationManager()
        conf.read(M_CUSTOM_CONFIG_PATH)

        self.assertEqual('statuscake_custom', conf.get('default', 'endpoint'))
        self.assertEqual('This is a fake custom application key',   conf.get('statuscake_custom', 'api_key'))
        self.assertTrue(conf.get('statuscake-eu', 'non-existent') is None)
