import json
from decimal import Decimal

from coinbasepro import PublicClient
from coinbasepro.auth import CoinbaseProAuth


class AuthenticatedClient(PublicClient):
    """Provides access to authenticated requests on the Coinbase Pro API.

    Attributes:
        api_url (str): The api url for this client instance to use.
        auth (CoinbaseProAuth): Custom authentication handler for each request.
    """
    def __init__(self, key, secret, passphrase,
                 api_url='https://api.pro.coinbase.com',
                 request_timeout=30):
        """Create an AuthenticatedClient instance.

        Args:
            key (str): Your API key.
            secret (str): Your API secret.
            passphrase (str): Your API passphrase.
            api_url (Optional[str]): API URL. Defaults to Coinbase Pro API.
            request_timeout (Optional[int]): Request timeout (in seconds).
        """
        super(AuthenticatedClient, self).__init__(api_url, request_timeout)
        self.auth = CoinbaseProAuth(key, secret, passphrase)

    def get_account(self, account_id):
        """Gets information for a single account.

        Use this endpoint when you know the account_id.

        Args:
            account_id (str): Account id for account you want to get.

        Returns:
            dict: Account information. Example::
                {
                    'id': '29a4fc2b',
                    'currency': 'USD',
                    'balance': Decimal('1000000.0000000000000000'),
                    'available': Decimal('1000000.0000000000000000'),
                    'hold': Decimal('0.0000000000000000'),
                    'profile_id': 'f24b313b',
                }

        Raises:
            See `get_products()`.

        """
        field_conversions = {'balance': Decimal,
                             'available': Decimal,
                             'hold': Decimal}
        r = self._send_message('get', '/accounts/' + account_id)
        # Need to handle empty string `account_id`, which returns all acounts
        if type(r) is list:
            return self._convert_list_of_dicts(r, field_conversions)
        else:
            return self._convert_dict(r, field_conversions)

    def get_accounts(self):
        """Gets a list of trading all accounts.

        When you place an order, the funds for the order are placed on
        hold. They cannot be used for other orders or withdrawn. Funds
        will remain on hold until the order is filled or canceled. The
        funds on hold for each account will be specified.

        Returns:
            list: Info about all accounts. Example::
                [
                    {
                        'id': '71452118-efc7-4cc4-8780-a5e22d4baa53',
                        'currency': 'BTC',
                        'balance': Decimal('0.0000000000000000'),
                        'available': Decimal('0.0000000000000000'),
                        'hold': Decimal('0.0000000000000000'),
                        'profile_id': '75da88c5-05bf-4f54-bc85-5c775bd68254'
                    },
                    {
                        ...
                    }
                ]

        Raises:
            See `get_products()`.

        """
        return self.get_account('')

    def get_account_history(self, account_id, **kwargs):
        """Lists account activity.

        Account activity either increases or decreases your account
        balance.

        Entry type indicates the reason for the account change.
        * transfer:	Funds moved to/from Coinbase to Coinbase Pro
        * match:	Funds moved as a result of a trade
        * fee:	    Fee as a result of a trade
        * rebate:   Fee rebate as per our fee schedule
        * conversion: Funds converted between fiat currency and a
            stablecoin

        If an entry is the result of a trade (match, fee), the details
        field will contain additional information about the trade.

        Args:
            account_id (str): Account id to get history of.
            kwargs (dict): Additional HTTP request parameters.

        Yields:
            History information for the account. Example::
                [
                    {
                        'id': 100,
                        'created_at': datetime(2019, 3, 19, 22, 26, 22, 520000),
                        'amount': Decimal('0.001'),
                        'balance': Decimal('239.669'),
                        'type': 'fee',
                        'details': {
                            'order_id': 'd50ec984-77a8-460a-b958-66f114b0de9b',
                            'trade_id': '74',
                            'product_id': 'BTC-USD'
                        }
                    },
                    {
                        ...
                    }
                ]

        Raises:
            See `get_products()`.

        """
        field_conversions = {'created_at': self._parse_datetime,
                             'amount': Decimal,
                             'balance': Decimal}
        endpoint = '/accounts/{}/ledger'.format(account_id)
        r = self._send_paginated_message(endpoint, params=kwargs)
        return (self._convert_dict(activity, field_conversions)
                for activity in r)

    def get_account_holds(self, account_id, **kwargs):
        """Gets holds on an account.

        Holds are placed on an account for active orders or
        pending withdraw requests.

        As an order is filled, the hold amount is updated. If an order
        is canceled, any remaining hold is removed. For a withdraw,
        once it is completed, the hold is removed.

        The `type` field will indicate why the hold exists. The hold
        type is 'order' for holds related to open orders and 'transfer'
        for holds related to a withdraw.

        The `ref` field contains the id of the order or transfer which
        created the hold.

        Args:
            account_id (str): Account id to get holds of.
            kwargs (dict): Additional HTTP request parameters.

        Yields:
            Hold information for the account. Example::
                [
                    {
                        'id': '82dcd140-c3c7-4507-8de4-2c529cd1a28f',
                        'account_id': 'e0b3f39a-183d-453e-b754-0c13e5bab0b3',
                        'created_at': datetime(2019, 3, 19, 22, 26, 22, 520000),
                        'updated_at': datetime(2019, 3, 19, 22, 26, 24, 520000),
                        'amount': Decimal('4.23'),
                        'type': 'order',
                        'ref': '0a205de4-dd35-4370-a285-fe8fc375a273',
                    },
                    {
                    ...
                    }
                ]

        Raises:
            See `get_products()`.

        """
        field_conversions = {'created_at': self._parse_datetime,
                             'updated_at': self._parse_datetime,
                             'amount': Decimal}
        endpoint = '/accounts/{}/holds'.format(account_id)
        r = self._send_paginated_message(endpoint, params=kwargs)
        return (self._convert_dict(hold, field_conversions) for hold in r)

    def place_order(self,
                    product_id,
                    side,
                    order_type,
                    stop=None,
                    stop_price=None,
                    client_oid=None,
                    stp=None,
                    **kwargs):
        """Places an order.

        The two order types (limit and market) can be placed using this
        method. Specific methods are provided for each order type, but
        if a more generic interface is desired this method is
        available.

        Args:
            product_id (str): Product to order (eg. 'BTC-USD').
            side (str): Order side ('buy' or 'sell').
            order_type (str): Order type ('limit' or 'market').
            stop (Optional[str]): Sets the type of stop order. There
                are two options:
                'loss': Triggers when the last trade price changes to a
                    value at or below the `stop_price`.
                'entry: Triggers when the last trade price changes to a
                    value at or above the `stop_price`.
                `stop_price` must be set when a stop order is specified.
            stop_price (Optional[Decimal]): Trigger price for stop order.
            client_oid (str): Order ID selected by you to identify your
                order. This should be a UUID, which will be broadcast
                in the public feed for `received` messages.
            stp (str): Self-trade prevention flag. Coinbase Pro doesn't
                allow self-trading. This behavior can be modified with
                this flag. Options:
                'dc': Decrease and Cancel (default)
                'co': Cancel oldest
                'cn': Cancel newest
                'cb': Cancel both
            kwargs: Additional arguments can be specified for different
                order types. See the limit/market order methods for
                details.

        Returns:
            dict: Order details. Example::
            {
                'id': 'd0c5340b-6d6c-49d9-b567-48c4bfca13d2',
                'price': Decimal('0.10000000'),
                'size': Decimal('0.01000000'),
                'product_id': 'BTC-USD',
                'side': 'buy',
                'stp': 'dc',
                'type': 'limit',
                'time_in_force': 'GTC',
                'post_only': false,
                'created_at': datetime(2019, 3, 19, 22, 26, 22, 520000),
                'fill_fees': Decimal('0.0000000000000000'),
                'filled_size': Decimal('0.00000000'),
                'executed_value': Decimal('0.0000000000000000'),
                'status': 'pending',
                'settled': False
            }

        Raises:
            See `get_products()`.

        """
        # Market order checks
        if order_type == 'market':
            if kwargs.get('size') is None and kwargs.get('funds') is None:
                raise ValueError('Must specify `size` or `funds` for a market '
                                 'order')

        # Limit order checks
        if order_type == 'limit':
            if (kwargs.get('cancel_after') is not None and
                    kwargs.get('time_in_force') != 'GTT'):
                raise ValueError('May only specify a cancel period when time '
                                 'in_force is `GTT`')
            if (kwargs.get('post_only') is not None and
                    kwargs.get('time_in_force') in ['IOC', 'FOK']):
                raise ValueError('post_only is invalid when time in force is '
                                 '`IOC` or `FOK`')

        # Stop order checks
        if (stop is not None) ^ (stop_price is not None):
            raise ValueError('Both `stop` and `stop_price` must be specified at'
                             'the same time.')

        # Build params dict
        params = {'product_id': product_id,
                  'side': side,
                  'type': order_type,
                  'stop': stop,
                  'stop_price': stop_price,
                  'client_oid': client_oid,
                  'stp': stp}
        params.update(kwargs)

        field_conversions = {'price': Decimal,
                             'size': Decimal,
                             'created_at': self._parse_datetime,
                             'fill_fees': Decimal,
                             'filled_size': Decimal,
                             'executed_value': Decimal}
        r = self._send_message('post', '/orders', data=json.dumps(params))
        return self._convert_dict(r, field_conversions)

    def place_limit_order(self,
                          product_id,
                          side,
                          price,
                          size,
                          stop=None,
                          stop_price=None,
                          client_oid=None,
                          stp=None,
                          time_in_force=None,
                          cancel_after=None,
                          post_only=None):
        """Places a limit order.

        Args:
            product_id (str): Product to order (eg. 'BTC-USD').
            side (str): Order side ('buy' or 'sell).
            price (Decimal): Price per cryptocurrency.
            size (Decimal): Amount of cryptocurrency to buy or sell.
            stop (Optional[str]): Sets the type of stop order. There
                are two options:
                'loss': Triggers when the last trade price changes to
                    a value at or below the `stop_price`.
                'entry: Triggers when the last trade price changes to
                    a value at or above the `stop_price`.
                `stop_price` must be set when a stop order is
                specified.
            stop_price (Optional[Decimal]): Trigger price for stop
                order.
            client_oid (Optional[str]): User-specified Order ID.
            stp (Optional[str]): Self-trade prevention flag. See `
                place_order` for details.
            time_in_force (Optional[str]): Time in force. Options:
                'GTC': Good till canceled
                'GTT': Good till time (set by `cancel_after`)
                'IOC': Immediate or cancel
                'FOK': Fill or kill
            cancel_after (Optional[str]): Cancel after this period for
                'GTT' orders. Options are 'min', 'hour', or 'day'.
            post_only (Optional[bool]): Indicates that the order should
                only make liquidity. If any part of the order results
                in taking liquidity, the order will be rejected and no
                part of it will execute.

        Returns:
            dict: Order details. See `place_order` for example.

        Raises:
            See `get_products()`.

        """
        params = {'product_id': product_id,
                  'side': side,
                  'order_type': 'limit',
                  'price': price,
                  'size': size,
                  'stop': stop,
                  'stop_price': stop_price,
                  'client_oid': client_oid,
                  'stp': stp,
                  'time_in_force': time_in_force,
                  'cancel_after': cancel_after,
                  'post_only': post_only}
        params = dict((k, v) for k, v in params.items() if v is not None)

        return self.place_order(**params)

    def place_market_order(self, product_id, side, size=None, funds=None,
                           stop=None,
                           stop_price=None,
                           client_oid=None,
                           stp=None):
        """Places a market order.

        `size` and `funds` parameters specify the order amount. `funds`
        will limit how much of your quote currency account balance is
        used and `size` will limit the crypto amount transacted.

        Args:
            product_id (str): Product to order (eg. 'BTC-USD').
            side (str): Order side ('buy' or 'sell).
            size (Optional[Decimal]): Desired amount in crypto. Specify
                this and/or `funds`.
            funds (Optional[Decimal]): Desired amount of quote currency
                to use. Specify this and/or `size`.
            stop (Optional[str]): Sets the type of stop order. There are
                two options:
                'loss': Triggers when the last trade price changes to a
                    value at or below the `stop_price`.
                'entry: Triggers when the last trade price changes to a
                    value at or above the `stop_price`.
                `stop_price` must be set when a stop order is
                specified.
            stop_price (Optional[Decimal]): Trigger price for stop
                order.
            client_oid (Optional[str]): User-specified Order ID.
            stp (Optional[str]): Self-trade prevention flag. See
                `place_order` for details.

        Returns:
            dict: Order details. See `place_order` for example.

        Raises:
            See `get_products()`.

        """
        params = {'product_id': product_id,
                  'side': side,
                  'order_type': 'market',
                  'size': size,
                  'funds': funds,
                  'stop': stop,
                  'stop_price': stop_price,
                  'client_oid': client_oid,
                  'stp': stp}
        params = dict((k, v) for k, v in params.items() if v is not None)

        return self.place_order(**params)

    def cancel_order(self, order_id):
        """Cancels a previously placed order.

        If the order had no matches during its lifetime its record may
        be purged. This means the order details will not be available
        with get_order(order_id). If the order could not be canceled
        (already filled or previously canceled, etc), then an
        exception will be raised with the reason indicated in the
        message.

        **Caution**: The order id is the server-assigned order id and
        not the optional client_oid.

        Args:
            order_id (str): The order_id of the order you want to
                cancel.

        Returns:
            list: Containing the order_id of cancelled order. Example::
                ['c5ab5eae-76be-480e-8961-00792dc7e138']

        Raises:
            See `get_products()`.

        """
        return self._send_message('delete', '/orders/' + order_id)

    def cancel_all(self, product_id=None):
        """With best effort, cancels all open orders.

        Args:
            product_id (Optional[str]): Only cancel orders for this
                product_id

        Returns:
            list: A list of ids of the canceled orders. Example::
                [
                    '144c6f8e-713f-4682-8435-5280fbe8b2b4',
                    'debe4907-95dc-442f-af3b-cec12f42ebda',
                    'cf7aceee-7b08-4227-a76c-3858144323ab',
                    'dfc5ae27-cadb-4c0c-beef-8994936fde8a',
                    '34fecfbf-de33-4273-b2c6-baf8e8948be4'
                ]

        Raises:
            See `get_products()`.

        """
        if product_id is not None:
            params = {'product_id': product_id}
        else:
            params = None
        return self._send_message('delete', '/orders', params=params)

    def get_order(self, order_id):
        """Gets a single order by order id.

        If the order is canceled the response may have status code 404
        if the order had no matches.

        **Caution**: Open orders may change state between the request
        and the response depending on market conditions.

        Args:
            order_id (str): The order to get information of.

        Returns:
            dict: Containing information on order. Example::
                {
                    'created_at': datetime(2019, 3, 19, 22, 26, 22, 520000),
                    'executed_value': Decimal('0.0000000000000000'),
                    'fill_fees': Decimal('0.0000000000000000'),
                    'filled_size': Decimal('0.00000000'),
                    'id': '9456f388-67a9-4316-bad1-330c5353804f',
                    'post_only': True,
                    'price': Decimal('1.00000000'),
                    'product_id': 'BTC-USD',
                    'settled': False,
                    'side': 'buy',
                    'size': Decimal('1.00000000'),
                    'status': 'pending',
                    'stp': 'dc',
                    'time_in_force': 'GTC',
                    'type': 'limit'
                }

        Raises:
            See `get_products()`.

        """
        field_conversions = {'created_at': self._parse_datetime,
                             'executed_value': Decimal,
                             'fill_fees': Decimal,
                             'filled_size': Decimal,
                             'price': Decimal,
                             'size': Decimal}
        r = self._send_message('get', '/orders/' + order_id)
        return self._convert_dict(r, field_conversions)

    def get_orders(self, product_id=None, status=None, **kwargs):
        """Lists your current open orders.

        Only open or un-settled orders are returned. As soon as an
        order is no longer open and settled, it will no longer appear
        in the default request.

        Orders which are no longer resting on the order book, will be
        marked with the 'done' status. There is a small window between
        an order being 'done' and 'settled'. An order is 'settled' when
        all of the fills have settled and the remaining holds (if any)
        have been removed.

        For high-volume trading it is strongly recommended that you
        maintain your own list of open orders and use one of the
        streaming market data feeds to keep it updated. You should poll
        the open orders endpoint once when you start trading to obtain
        the current state of any open orders.

        Args:
            product_id (Optional[str]): Only list orders for this
                product
            status (Optional[list/str]): Limit list of orders to
                this status or statuses. Passing 'all' returns orders
                of all statuses.
                ** Options: 'open', 'pending', 'active', 'done',
                    'settled'
                ** default: ['open', 'pending', 'active']

        Yields:
            Information on orders. Example::
                [
                    {
                        'id': 'd0c5340b-6d6c-49d9-b567-48c4bfca13d2',
                        'price': Decimal('0.10000000'),
                        'size': Decimal('0.01000000'),
                        'product_id': 'BTC-USD',
                        'side': 'buy',
                        'stp': 'dc',
                        'type': 'limit',
                        'time_in_force': 'GTC',
                        'post_only': False,
                        'created_at': datetime(2019, 3, 19, 22, 26, 22, 520000),
                        'fill_fees': Decimal('0.0000000000000000'),
                        'filled_size': Decimal('0.00000000'),
                        'executed_value': Decimal('0.0000000000000000'),
                        'status': 'open',
                        'settled': False
                    },
                    {
                        ...
                    }
                ]

        Raises:
            See `get_products()`.

        """
        params = kwargs
        if product_id is not None:
            params['product_id'] = product_id
        if status is not None:
            params['status'] = status

        field_conversions = {'price': Decimal,
                             'size': Decimal,
                             'created_at': self._parse_datetime,
                             'fill_fees': Decimal,
                             'filled_size': Decimal,
                             'executed_value': Decimal}
        orders = self._send_paginated_message('/orders', params=params)
        return (self._convert_dict(order, field_conversions)
                for order in orders)

    def get_fills(self, product_id=None, order_id=None, **kwargs):
        """Gets recent fills for a product or order.

        Either `product_id` or `order_id` must be specified.

        Fees are recorded in two stages. Immediately after the matching
        engine completes a match, the fill is inserted into our
        datastore. Once the fill is recorded, a settlement process will
        settle the fill and credit both trading counterparties.

        The 'fee' field indicates the fees charged for this fill.

        The 'liquidity' field indicates if the fill was the result of a
        liquidity provider or liquidity taker. M indicates Maker and T
        indicates Taker.

        Args:
            product_id (Optional[str]): Limit list to this product_id
            order_id (Optional[str]): Limit list to this order_id
            kwargs (dict): Additional HTTP request parameters.

        Yields:
            Information on fills. Example::
                [
                    {
                        'trade_id': 74,
                        'product_id': 'BTC-USD',
                        'price': Decimal('10.00'),
                        'size': Decimal('0.01'),
                        'order_id': 'd50ec984-77a8-460a-b958-66f114b0de9b',
                        'created_at': datetime(2019, 3, 19, 22, 26, 22, 520000),
                        'liquidity': 'T',
                        'fee': Decimal('0.00025'),
                        'settled': True,
                        'side': 'buy'
                    },
                    {
                        ...
                    }
                ]

        Raises:
            See `get_products()`.

        """
        if (product_id is None) and (order_id is None):
            raise ValueError('Either product_id or order_id must be specified.')
        params = {}
        if product_id:
            params['product_id'] = product_id
        if order_id:
            params['order_id'] = order_id
        params.update(kwargs)

        field_conversions = {'price': Decimal,
                             'size': Decimal,
                             'created_at': self._parse_datetime,
                             'fee': Decimal}

        def convert_volume_keys(fill):
            """Convert any 'volume' keys (like 'usd_volume') to Decimal."""
            for k, v in fill.items():
                if 'volume' in k:
                    fill[k] = Decimal(fill[k])
            return fill
        fills = self._send_paginated_message('/fills', params=params)
        return (self._convert_dict(convert_volume_keys(fill), field_conversions)
                for fill in fills)

    def deposit(self, amount, currency, payment_method_id):
        """Deposits funds from a payment method.

        See AuthenticatedClient.get_payment_methods() to receive
        information regarding payment methods.

        Args:
            amount (Decimal): The amount to deposit.
            currency (str): The type of currency.
            payment_method_id (str): ID of the payment method.

        Returns:
            dict: Information about the deposit. Example::
                {
                    'id': '593533d2-ff31-46e0-b22e-ca754147a96a',
                    'amount': Decimal('10.00'),
                    'currency': 'USD',
                    'payout_at': datetime(2019, 3, 19, 22, 26, 22)
                }

        Raises:
            See `get_products()`.

        """
        params = {'amount': amount,
                  'currency': currency,
                  'payment_method_id': payment_method_id}
        field_conversions = {'amount': Decimal,
                             'payout_at': self._parse_datetime}
        r = self._send_message('post', '/deposits/payment-method',
                               data=json.dumps(params))
        return self._convert_dict(r, field_conversions)

    def deposit_from_coinbase(self, amount, currency, coinbase_account_id):
        """Deposits funds from a Coinbase account.

        You can move funds between your Coinbase accounts and your
        Coinbase Pro trading accounts within your daily limits. Moving
        funds between Coinbase and Coinbase Pro is instant and free.

        See AuthenticatedClient.get_coinbase_accounts() to receive
        information regarding your coinbase_accounts.

        Args:
            amount (Decimal): The amount to deposit.
            currency (str): The type of currency.
            coinbase_account_id (str): ID of the coinbase account.

        Returns:
            dict: Information about the deposit. Example::
                {
                    'id': '593533d2-ff31-46e0-b22e-ca754147a96a',
                    'amount': Decimal('10.00'),
                    'currency: 'BTC',
                }

        Raises:
            See `get_products()`.

        """
        params = {'amount': amount,
                  'currency': currency,
                  'coinbase_account_id': coinbase_account_id}
        r = self._send_message('post', '/deposits/coinbase-account',
                               data=json.dumps(params))
        return self._convert_dict(r, {'amount': Decimal})

    def withdraw(self, amount, currency, payment_method_id):
        """Withdraws funds to a payment method.

        See AuthenticatedClient.get_payment_methods() to receive
        information regarding payment methods.

        Args:
            amount (Decimal): The amount to withdraw.
            currency (str): Currency type (eg. 'BTC')
            payment_method_id (str): ID of the payment method.

        Returns:
            dict: Withdraw details. Example::
                {
                    'id': '593533d2-ff31-46e0-b22e-ca754147a96a',
                    'amount': Decimal('10.00'),
                    'currency': 'USD',
                    'payout_at': datetime(2019, 3, 19, 22, 26, 22)
                }

        Raises:
            See `get_products()`.

        """
        params = {'amount': amount,
                  'currency': currency,
                  'payment_method_id': payment_method_id}
        field_conversions = {'amount': Decimal,
                             'payout_at': self._parse_datetime}
        r = self._send_message('post', '/withdrawals/payment-method',
                               data=json.dumps(params))
        return self._convert_dict(r, field_conversions)

    def withdraw_to_coinbase(self, amount, currency, coinbase_account_id):
        """Withdraws funds to a coinbase account.

        You can move funds between your Coinbase accounts and your
        Coinbase Pro trading accounts within your daily limits. Moving
        funds between Coinbase and Coinbase Pro is instant and free.

        See AuthenticatedClient.get_coinbase_accounts() to receive
        information regarding your coinbase_accounts.

        Args:
            amount (Decimal): The amount to withdraw.
            currency (str): The type of currency (eg. 'BTC')
            coinbase_account_id (str): ID of the coinbase account.

        Returns:
            dict: Information about the deposit. Example::
                {
                    'id': '593533d2-ff31-46e0-b22e-ca754147a96a',
                    'amount': Decimal('10.00'),
                    'currency': 'BTC',
                }

        Raises:
            See `get_products()`.

        """
        params = {'amount': amount,
                  'currency': currency,
                  'coinbase_account_id': coinbase_account_id}
        r = self._send_message('post', '/withdrawals/coinbase',
                               data=json.dumps(params))
        return self._convert_dict(r, {'amount': Decimal})

    def withdraw_to_crypto(self, amount, currency, crypto_address):
        """Withdraws funds to a crypto address.

        Args:
            amount (Decimal): The amount to withdraw
            currency (str): The type of currency (eg. 'BTC')
            crypto_address (str): Crypto address to withdraw to.

        Returns:
            dict: Withdraw details. Example::
                {
                    'id': '593533d2-ff31-46e0-b22e-ca754147a96a',
                    'amount': Decimal('10.00'),
                    'currency': 'BTC',
                }

        Raises:
            See `get_products()`.

        """
        params = {'amount': amount,
                  'currency': currency,
                  'crypto_address': crypto_address}
        r = self._send_message('post', '/withdrawals/crypto',
                               data=json.dumps(params))
        return self._convert_dict(r, {'amount': Decimal})

    def get_payment_methods(self):
        """Gets a list of your payment methods.

        Returns:
            list: Payment method details.

        Raises:
            See `get_products()`.

        """
        field_conversions = {'created_at': self._parse_datetime,
                             'updated_at': self._parse_datetime}
        r = self._send_message('get', '/payment-methods')
        return self._convert_list_of_dicts(r, field_conversions)

    def get_coinbase_accounts(self):
        """Gets a list of your coinbase accounts.

        Returns:
            list: Coinbase account details.

        Raises:
            See `get_products()`.

        """
        field_conversions = {'balance': Decimal,
                             'hold_balance': Decimal}
        r = self._send_message('get', '/coinbase-accounts')
        return self._convert_list_of_dicts(r, field_conversions)

    def create_report(self, report_type, start_date, end_date, product_id=None,
                      account_id=None, report_format='pdf', email=None):
        """Creates report of historic information about your account.

        The report will be generated when resources are available.
        Report status can be queried via `get_report(report_id)`.

        Args:
            report_type (str): 'fills' or 'account'
            start_date (str): Starting date for the report in ISO 8601
            end_date (str): Ending date for the report in ISO 8601
            product_id (Optional[str]): ID of the product to generate a
                fills report for. Required if account_type is 'fills'.
            account_id (Optional[str]): ID of the account to generate
                an account report for. Required if report_type is
                'account'.
            report_format (Optional[str]): 'pdf' or 'csv'. Default is
                'pdf'.
            email (Optional[str]): Email address to send the report to.

        Returns:
            dict: Report details. Example::
                {
                    'id': '0428b97b-bec1-429e-a94c-59232926778d',
                    'type': 'fills',
                    'status': 'pending',
                    'created_at': '2015-01-06T10:34:47.000Z',
                    'completed_at': undefined,
                    'expires_at': '2015-01-13T10:35:47.000Z',
                    'file_url': undefined,
                    'params': {
                        'start_date': '2014-11-01T00:00:00.000Z',
                        'end_date': '2014-11-30T23:59:59.000Z'
                    }
                }

        Raises:
            See `get_products()`.

        """
        params = {'type': report_type,
                  'start_date': start_date,
                  'end_date': end_date,
                  'format': report_format}
        if product_id is not None:
            params['product_id'] = product_id
        if account_id is not None:
            params['account_id'] = account_id
        if email is not None:
            params['email'] = email

        return self._send_message('post', '/reports',
                                  data=json.dumps(params))

    def get_report(self, report_id):
        """Gets report status.

        Use to query a specific report once it has been requested.

        Args:
            report_id (str): Report ID

        Returns:
            dict: Report details, including file url once it is created.

        Raises:
            See `get_products()`.

        """
        return self._send_message('get', '/reports/' + report_id)

    def get_trailing_volume(self):
        """Gets your 30-day trailing volume for all products.

        This is a cached value that's calculated every day at midnight UTC.

        Returns:
            list: 30-day trailing volumes. Example::
                [
                    {
                        'product_id': 'BTC-USD',
                        'exchange_volume': Decimal('11800.00000000'),
                        'volume': Decimal('100.00000000'),
                        'recorded_at': datetime(2019, 3, 19, 22, 26, 22, 520000)
                    },
                    {
                        ...
                    }
                ]

        Raises:
            See `get_products()`.

        """
        field_conversions = {'exchange_volume': Decimal,
                             'volume': Decimal,
                             'recorded_at': self._parse_datetime}
        r = self._send_message('get', '/users/self/trailing-volume')
        return self._convert_dict(field_conversions, r)
