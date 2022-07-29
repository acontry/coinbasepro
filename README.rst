CoinbasePro: A Python API
=========================

.. image:: https://img.shields.io/pypi/v/coinbasepro.svg
    :target: https://pypi.org/project/coinbasepro/

.. image:: https://img.shields.io/pypi/l/coinbasepro.svg
    :target: https://pypi.org/project/coinbasepro/

.. image:: https://img.shields.io/pypi/pyversions/coinbasepro.svg
    :target: https://pypi.org/project/coinbasepro/

Features
--------
- Full support of Coinbase Pro/Coinbase Exchange REST API
- Rate-limiting - no more 429 error responses!
- Pythonic abstractions for a clean interface
    - Return values are returned as Python data types instead of all string values:

    .. code-block:: python

        >>> import coinbasepro as cbp
        >>> client = cbp.PublicClient()
        # datetime and Decimal are among the return types in the dict returned
        # by this call:
        >>> client.get_product_ticker('BTC-USD')
        {'trade_id': 2845680,
        'price': Decimal('2496.69000000'),
        'size': Decimal('0.00100000'),
        'time': datetime.datetime(2019, 3, 20, 23, 53, 59, 596000),
        'bid': Decimal('2496.69'), 'ask': Decimal('2496.7'),
        'volume': Decimal('771.51495215')}

    - Paginated endpoints are abstracted as generators:

    .. code-block:: python

        >>> import itertools
        # get_product_trades is a generator
        >>> client.get_product_trades('BTC-USD')
        <generator object PublicClient.get_product_trades.<locals>.<genexpr> at 0x1098d6f68>

        # Get 2 most recent trades. For many trade requests (>100), multiple
        # HTTP requests will be made under the hood.
        >>> list(itertools.islice(client.get_product_trades('BTC-USD'), 2))
        [{'time': datetime.datetime(2019, 3, 21, 0, 2, 45, 609000),
        'trade_id': 2845779,
        'price': Decimal('2463.38000000'),
        'size': Decimal('0.00100000'),
        'side': 'buy'},
        {'time': datetime.datetime(2019, 3, 21, 0, 2, 39, 877000),
        'trade_id': 2845778,
        'price': Decimal('2463.39000000'),
        'size': Decimal('0.00100000'),
        'side': 'sell'}]

    - Warts in the Coinbase REST API are smoothed out:

    .. code-block:: python

        # CBPro API returns raw candles from this call as tuples, which would
        # require user to look up value meaning in API docs. This python API
        # returns candles as a list of dicts, similar to other API endpoints.

        # Get first candle:
        >>> client.get_product_historic_rates('BTC-USD')[0]
        {'time': datetime.datetime(2019, 3, 21, 0, 6),
        'low': Decimal('2463.3'),
        'high': Decimal('2463.31'),
        'open': Decimal('2463.3'),
        'close': Decimal('2463.31'),
        'volume': Decimal('0.006')}

    - Python API uses typing available in Python3:

    .. code-block:: python

        # Example function prototype in API
        def get_product_ticker(self, product_id: str) -> Dict[str, Any]:

- Exceptions to enable easy handling of Coinbase error responses

.. code-block:: python

    >>> client.get_product_ticker(product_id='fake_product')
    coinbasepro.exceptions.CoinbaseAPIError: NotFound

.. code-block:: python

    >>> auth_client = cbp.AuthenticatedClient(key='fake',
                                              secret='fake',
                                              passphrase='fake')
    >>> auth_client.get_accounts()
    coinbasepro.exceptions.BadRequest: Invalid API Key

.. code-block:: python

    # Authenticated client using API key which doesn't have withdrawal
    # privileges:
    >>> auth_client.withdraw_to_coinbase(0.01, 'BTC', 'fake_acct_id')
    coinbasepro.exceptions.InvalidAuthorization: Forbidden

.. code-block:: python

    # This call throws a BadRequest exception
    >>> auth_client.get_order('invalid_order_num')
    coinbasepro.exceptions.BadRequest: Invalid order id

    # CoinbaseAPIError is the parent exception for all exceptions the API
    # throws, so catching this will catch anything
    >>> try:
    >>>     auth_client.get_order('invalid_order_num')
    >>> except cbp.exceptions.CoinbaseAPIError as e:
    >>>     print('Caught error: {}'.format(e))
    Caught error: Invalid order id


Installation
------------

.. code-block:: bash

    $ pip install coinbasepro

Development
------------

Environment Setup
+++++++++++++++++

1. Create virtual environment using preferred tool
2. Bootstrap `pip-tools` by installing dev requirements directly:

.. code-block:: bash

    $ pip install -r requirements.txt

Once `pip-tools` is installed in your environment, you can update requirements by:

.. code-block:: bash

    $ make install-requirements

3. (Optional) Install `pre-commit git hooks <https://pre-commit.com/#3-install-the-git-hook-scripts>`_.
This will run pre-commit with every commit, which should fix any lint issues
before you push changes to your remote branch.
