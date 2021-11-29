Lightweight wrapper around Statuscake's APIs. 
Heavily inspired by the OVH python client https://github.com/ovh/python-ovh

.. code:: python

    # -*- encoding: utf-8 -*-

    import statuscake_api

    client = statuscake_api.Client(
        api_key='<api_key>',
    )

    # Print nice welcome message
    print("Welcome", client.get('/uptime'))

Installation
============

The python wrapper works with Python 2.7 and Python 3.4+.

The easiest way to get the latest stable release is to grab it from `pypi
<https://pypi.python.org/pypi/statuscake>`_ using ``pip``.

.. code:: bash

    pip install statuscake_api

Alternatively, you may get latest development version directly from Git.

.. code:: bash

    pip install -e git+https://github.com/alkivi-sas/python-statuscake-api.git#egg=statuscake_api

Example Usage
=============

1. Create an application
************************

Go to your statuscake account and get your API KEY

2. Configure your application
*****************************

The easiest and safest way to use your application's credentials is to create an
``statuscake.conf`` configuration file in application's working directory. Here is how
it looks like:

.. code:: ini

    [default]
    ; general configuration: default endpoint
    endpoint=my_user

    [my_user]
    ; configuration specific to 'my_user' endpoint
    api_key=my_api_key

Depending on the API you want to use, you may set the several ``endpoint`` to handle severals accounts

See Configuration_ for more information on available configuration mechanisms.

.. note:: When using a versioning system, make sure to add ``statuscake.conf`` to ignored
          files. It contains confidential/security-sensitive information!


Get all tests
------------------------------

.. code:: python

    # -*- encoding: utf-8 -*-

    import statuscake_api

    # create a client
    client = statuscake_api.Client()

    finished = False
    page = 1
    tests = []
    while not finished:
        params = {'page': page}

        response = client.get('/uptime', **params)

        test = response['data']
        tests = tests + test

        if 'metadata' in response:
            page_count = response['metadata']['page_count']
            if page < page_count:
                page += 1
            else:
                finished = True
        else:
            finished = True
    print(f'We have fetched {len(tests)}')


Add new test
--------------

When array in parameters, you need to add [] for the parameter


.. code:: python

    # -*- encoding: utf-8 -*-

    import statuscake_api

    # create a client
    client = statuscake_api.Client()

    new_test = {
         'name': 'test-connection',
         'test_type': 'PING',
         'website_url': '8.8.8.8',
         'check_rate': 60,
         'tags_csv': 'test,api',
         'contact_groups_csv': '31173',
         'regions[]': ['paris', 'london'],
     }
     test = client.post('/uptime', **new_test)



Environment vars and predefined configuration files
---------------------------------------------------

Alternatively it is suggested to use configuration files or environment
variables so that the same code may run seamlessly in multiple environments.
Production and development for instance.

This wrapper will first look for direct instantiation parameters then
``STATUSCAKE_ENDPOINT``, ``STATUSCAKE_APPLICATION_KEY``, ``STATUSCAKE_APPLICATION_SECRET`` and
``STATUSCAKE_CONSUMER_KEY`` environment variables. If either of these parameter is not
provided, it will look for a configuration file of the form:

.. code:: ini

    [default]
    ; general configuration: default endpoint
    endpoint=statuscake-eu

    [statuscake-eu]
    ; configuration specific to 'statuscake-eu' endpoint
    application_key=my_app_key
    application_secret=my_application_secret
    consumer_key=my_consumer_key

The client will successively attempt to locate this configuration file in

1. Current working directory: ``./statuscake.conf``
2. Current user's home directory ``~/.statuscake.conf``
3. System wide configuration ``/etc/statuscake.conf``

This lookup mechanism makes it easy to overload credentials for a specific
project or user.

Example usage:

.. code:: python

    client = statuscake_api.Client()

Custom configuration file
-------------------------

You can also specify a custom configuration file. With this method, you won't be able to inherit values from environment.

Example usage:

.. code:: python

    client = statuscake_api.Client(config_file='/my/config.conf')
