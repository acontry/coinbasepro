import json
from decimal import Decimal
from typing import Any, Dict, Iterator, List, Optional, Union

from coinbasepro import PublicClient
from coinbasepro.auth import CoinbaseProAuth
from coinbasepro.rate_limiter import RateLimiter


class AuthenticatedClient(PublicClient):
    """Provides access to authenticated requests on the Coinbase Pro API.

    Attributes:
        api_url: The api url for this client instance to use.
        auth: Custom authentication handler for each request.
    """

    def __init__(
        self,
        key: str,
        secret: str,
        passphrase: str,
        api_url: str = "https://api.pro.coinbase.com",
        request_timeout: int = 30,
        public_rate_limit: int = 3,
        public_burst_size: int = 6,
        auth_rate_limit: int = 5,
        auth_burst_size: int = 10,
    ):
        """Create an AuthenticatedClient instance.

        Args:
            key: Your API key.
            secret: Your API secret.
            passphrase: Your API passphrase.
            api_url: API URL. Defaults to Coinbase Pro API.
            request_timeout: Request timeout (in seconds).
            public_rate_limit: Number of requests per second allowed
                for public endpoints. Set to zero to disable
                rate-limiting.
            public_burst_size: Number of requests that can be bursted
                when rate-limiting is enabled for public endpoints.
            auth_rate_limit: Number of requests per second allowed
                for auth endpoints. Set to zero to disable
                rate-limiting.
            auth_burst_size: Number of requests that can be bursted
                when rate-limiting is enabled for auth endpoints.
        """
        super(AuthenticatedClient, self).__init__(
            api_url, request_timeout, public_rate_limit, public_burst_size
        )
        self.auth = CoinbaseProAuth(key, secret, passphrase)
        if auth_rate_limit > 0:
            self.a_rate_limiter = RateLimiter(
                burst_size=auth_burst_size, rate_limit=auth_rate_limit
            )
        else:
            self.a_rate_limiter = None

    def get_account(self, account_id: str) -> Dict[str, Any]:
        """Get information for a single account.

        Use this endpoint when you know the account_id. API key must
        belong to the same profile as the account.

        Args:
            account_id: Account id for account you want to get.

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
        return self._get_account_helper(account_id)

    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get a list of trading all accounts.

        When you place an order, the funds for the order are placed on
        hold. They cannot be used for other orders or withdrawn. Funds
        will remain on hold until the order is filled or canceled. The
        funds on hold for each account will be specified.

        Returns:
            Info about all accounts. Example::
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
        return self._get_account_helper("")

    def get_account_history(
        self, account_id: str, **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """List account activity.

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
            account_id: Account id to get history of.
            kwargs: Additional HTTP request parameters.

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
        field_conversions = {
            "created_at": self._parse_datetime,
            "amount": Decimal,
            "balance": Decimal,
        }
        endpoint = "/accounts/{}/ledger".format(account_id)
        r = self._send_paginated_message(
            endpoint, params=kwargs, rate_limiter=self.a_rate_limiter
        )
        return (self._convert_dict(activity, field_conversions) for activity in r)

    def get_account_holds(self, account_id: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """Get holds on an account.

        Holds are placed on an account for active orders or
        pending withdraw requests.

        As an order is filled, the hold amount is updated. If an order
        is canceled, any remaining hold is removed. For withdrawals,
        the hold is removed after it is completed.

        The `type` field will indicate why the hold exists. The hold
        type is 'order' for holds related to open orders and 'transfer'
        for holds related to a withdraw.

        The `ref` field contains the id of the order or transfer which
        created the hold.

        Args:
            account_id: Account id to get holds of.
            kwargs: Additional HTTP request parameters.

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
        field_conversions = {
            "created_at": self._parse_datetime,
            "updated_at": self._parse_datetime,
            "amount": Decimal,
        }
        endpoint = "/accounts/{}/holds".format(account_id)
        r = self._send_paginated_message(
            endpoint, params=kwargs, rate_limiter=self.a_rate_limiter
        )
        return (self._convert_dict(hold, field_conversions) for hold in r)

    def get_account_transfers(
        self, account_id: str, **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """List past withdrawals and deposits for an account.

        Args:
            account_id: Account id to get holds of.
            kwargs: Additional HTTP request parameters.

        Yields:
            Account deposits and withdrawals. Example::
                [
                    {
                        "id": "19ac524d-8827-4246-a1b2-18dc5ca9472c",
                        "type": "withdraw",
                        "created_at": datetime(2019, 3, 19, 22, 26, 22, 520000),
                        "completed_at": datetime(2019, 3, 19, 22, 26, 22, 520000),
                        "canceled_at": None,
                        "processed_at": None,
                        "user_nonce": 1234,
                        "amount": "1.00000000",
                        "details": {
                          "coinbase_account_id": "2b760113-fbba-5600-ac74-36482c130768",
                          "coinbase_transaction_id": "5e697ed49f8417148f3366ea",
                          "coinbase_payment_method_id": ""
                        }
                    },
                    {
                    ...
                    }
                ]

        Raises:
            See `get_products()`.

        """
        return self._get_transfers_helper(f"/accounts/{account_id}/transfers", **kwargs)

    def get_all_transfers(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """List all  transfers.

        Includes in-progress and completed transfers of funds in/out of
        any of the user's accounts.

        Args:
            kwargs: Additional HTTP request parameters.

        Yields:
            Transfers. Example::
                [
                    {
                        "id": "19ac524d-8827-4246-a1b2-18dc5ca9472c",
                        "type": "withdraw",
                        "created_at": datetime(2019, 3, 19, 22, 26, 22, 520000),
                        "completed_at": datetime(2019, 3, 19, 22, 26, 22, 520000),
                        "canceled_at": None,
                        "processed_at": None,
                        "user_nonce": 1234,
                        "amount": "1.00000000",
                        "details": {
                          "coinbase_account_id": "2b760113-fbba-5600-ac74-36482c130768",
                          "coinbase_transaction_id": "5e697ed49f8417148f3366ea",
                          "coinbase_payment_method_id": ""
                        }
                    },
                    {
                    ...
                    }
                ]

        Raises:
            See `get_products()`.

        """
        return self._get_transfers_helper("/transfers", **kwargs)

    def get_transfer(self, transfer_id: str) -> Dict[str, Any]:
        """Get information on a single transfer.

        Includes in-progress and completed transfers of funds in/out of
        any of the user's accounts.

        Args:
            transfer_id: ID of the transfer to fetch.
            kwargs: Additional HTTP request parameters.

        Returns:
            A transfer. Example::
                {
                    "id": "19ac524d-8827-4246-a1b2-18dc5ca9472c",
                    "type": "withdraw",
                    "created_at": datetime(2019, 3, 19, 22, 26, 22, 520000),
                    "completed_at": datetime(2019, 3, 19, 22, 26, 22, 520000),
                    "canceled_at": None,
                    "processed_at": None,
                    "user_nonce": 1234,
                    "amount": "1.00000000",
                    "details": {
                      "coinbase_account_id": "2b760113-fbba-5600-ac74-36482c130768",
                      "coinbase_transaction_id": "5e697ed49f8417148f3366ea",
                      "coinbase_payment_method_id": ""
                    }
                }

        Raises:
            See `get_products()`.

        """
        field_conversions = {
            "created_at": self._parse_datetime,
            "completed_at": self._parse_datetime,
            "canceled_at": self._parse_datetime,
            "processed_at": self._parse_datetime,
            "user_nonce": self._parse_optional_int,
            "amount": Decimal,
        }
        r = self._send_message(
            "get", f"/transfers/{transfer_id}", rate_limiter=self.a_rate_limiter
        )
        return self._convert_dict(r, field_conversions)

    def get_address_book(self) -> List[Dict[str, Any]]:
        """Get all addresses stored in the address book.

        Returns:
            List of addresses. Example::
                [
                    {
                        "id": "e9c483b8-c502-11ec-9d64-0242ac120002",
                        "address": "1JmYrFBLMSCLBwoL87gdQ5Qc9MLvb2egKk",
                        "currency": "ETH",
                        "label": "my wallet",
                        "last_used": None,
                        "address_book_added_at": datetime(2019, 3, 19, 22, 26, 22, 520000),
                        "destination_tag": None
                    },
                    {
                    ...
                    }
                ]
        """
        field_conversions = {
            "last_used": self._parse_datetime,
            "address_book_added_at": self._parse_datetime,
        }
        r = self._send_message("get", "/address-book", rate_limiter=self.a_rate_limiter)
        return self._convert_list_of_dicts(r, field_conversions)

    def place_order(
        self,
        product_id: str,
        side: str,
        order_type: str,
        stop: Optional[str] = None,
        stop_price: Optional[Union[float, Decimal]] = None,
        client_oid: Optional[str] = None,
        stp: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Place an order.

        The two order types (limit and market) can be placed using this
        method. Specific methods are provided for each order type, but
        if a more generic interface is desired this method is
        available.

        Args:
            product_id: Product to order (eg. 'BTC-USD').
            side: Order side ('buy' or 'sell').
            order_type: Order type ('limit' or 'market').
            stop: Sets the type of stop order. There are two options:
                'loss': Triggers when the last trade price changes to a
                    value at or below the `stop_price`.
                'entry: Triggers when the last trade price changes to a
                    value at or above the `stop_price`.
                `stop_price` must be set when a stop order is specified.
            stop_price: Trigger price for stop order.
            client_oid: Order ID selected by you to identify your
                order. This should be a UUID, which will be broadcast
                in the public feed for `received` messages.
            stp: Self-trade prevention flag. Coinbase Pro doesn't allow
                self-trading. This behavior can be modified with this
                flag. Options:
                'dc': Decrease and Cancel (default)
                'co': Cancel oldest
                'cn': Cancel newest
                'cb': Cancel both
            kwargs: Additional arguments can be specified for different
                order types. See the limit/market order methods for
                details.

        Returns:
            Order details. Example::
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
            ValueError: Incorrect order parameters.
            See `get_products()`.

        """
        # Market order checks
        if order_type == "market":
            if kwargs.get("size") is None and kwargs.get("funds") is None:
                raise ValueError("Must specify `size` or `funds` for a market " "order")

        # Limit order checks
        if order_type == "limit":
            if (
                kwargs.get("cancel_after") is not None
                and kwargs.get("time_in_force") != "GTT"
            ):
                raise ValueError(
                    "May only specify a cancel period when time " "in_force is `GTT`"
                )
            if kwargs.get("post_only") is not None and kwargs.get("time_in_force") in [
                "IOC",
                "FOK",
            ]:
                raise ValueError(
                    "post_only is invalid when time in force is " "`IOC` or `FOK`"
                )

        # Stop order checks
        if (stop is not None) ^ (stop_price is not None):
            raise ValueError(
                "Both `stop` and `stop_price` must be specified at" "the same time."
            )

        # Build params dict
        params = {
            "product_id": product_id,
            "side": side,
            "type": order_type,
            "stop": stop,
            "stop_price": stop_price,
            "client_oid": client_oid,
            "stp": stp,
        }
        params.update(kwargs)

        field_conversions = {
            "price": Decimal,
            "size": Decimal,
            "created_at": self._parse_datetime,
            "fill_fees": Decimal,
            "filled_size": Decimal,
            "executed_value": Decimal,
        }
        r = self._send_message(
            "post", "/orders", data=json.dumps(params), rate_limiter=self.a_rate_limiter
        )
        return self._convert_dict(r, field_conversions)

    def place_limit_order(
        self,
        product_id: str,
        side: str,
        price: Union[float, Decimal],
        size: Union[float, Decimal],
        stop: Optional[str] = None,
        stop_price: Optional[Union[float, Decimal]] = None,
        client_oid: Optional[str] = None,
        stp: Optional[str] = None,
        time_in_force: Optional[str] = None,
        cancel_after: Optional[str] = None,
        post_only: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Place a limit order.

        Args:
            product_id: Product to order (eg. 'BTC-USD').
            side: Order side ('buy' or 'sell).
            price: Price per cryptocurrency.
            size: Amount of cryptocurrency to buy or sell.
            stop: Sets the type of stop order. There are two options:
                'loss': Triggers when the last trade price changes to
                    a value at or below the `stop_price`.
                'entry: Triggers when the last trade price changes to
                    a value at or above the `stop_price`.
                `stop_price` must be set when a stop order is
                specified.
            stop_price: Trigger price for stop order.
            client_oid: User-specified Order ID.
            stp: Self-trade prevention flag. See `place_order` for
                details.
            time_in_force: Time in force. Options:
                'GTC': Good till canceled
                'GTT': Good till time (set by `cancel_after`)
                'IOC': Immediate or cancel
                'FOK': Fill or kill
            cancel_after: Cancel after this period for 'GTT' orders.
                Options are 'min', 'hour', or 'day'.
            post_only: Indicates that the order should only make
                liquidity. If any part of the order results in taking
                liquidity, the order will be rejected and no part of
                it will execute.

        Returns:
            Order details. See `place_order` for example.

        Raises:
            ValueError: Incorrect order parameters.
            See `get_products()`.

        """
        params = {
            "product_id": product_id,
            "side": side,
            "order_type": "limit",
            "price": price,
            "size": size,
            "stop": stop,
            "stop_price": stop_price,
            "client_oid": client_oid,
            "stp": stp,
            "time_in_force": time_in_force,
            "cancel_after": cancel_after,
            "post_only": post_only,
        }
        params = dict((k, v) for k, v in params.items() if v is not None)

        return self.place_order(**params)

    def place_market_order(
        self,
        product_id: str,
        side: str,
        size: Union[float, Decimal] = None,
        funds: Union[float, Decimal] = None,
        stop: Optional[str] = None,
        stop_price: Optional[Union[float, Decimal]] = None,
        client_oid: Optional[str] = None,
        stp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place a market order.

        `size` and `funds` parameters specify the order amount. `funds`
        will limit how much of your quote currency account balance is
        used and `size` will limit the crypto amount transacted.

        Args:
            product_id: Product to order (eg. 'BTC-USD').
            side: Order side ('buy' or 'sell).
            size: Desired amount in crypto. Specify
                this and/or `funds`.
            funds: Desired amount of quote currency
                to use. Specify this and/or `size`.
            stop: Sets the type of stop order. There are
                two options:
                'loss': Triggers when the last trade price changes to a
                    value at or below the `stop_price`.
                'entry: Triggers when the last trade price changes to a
                    value at or above the `stop_price`.
                `stop_price` must be set when a stop order is
                specified.
            stop_price: Trigger price for stop order.
            client_oid: User-specified Order ID.
            stp: Self-trade prevention flag. See `place_order` for
                details.

        Returns:
            Order details. See `place_order` for example.

        Raises:
            ValueError: Incorrect order parameters.
            See `get_products()`.

        """
        params = {
            "product_id": product_id,
            "side": side,
            "order_type": "market",
            "size": size,
            "funds": funds,
            "stop": stop,
            "stop_price": stop_price,
            "client_oid": client_oid,
            "stp": stp,
        }
        params = dict((k, v) for k, v in params.items() if v is not None)

        return self.place_order(**params)

    def cancel_order(self, order_id: str) -> List[str]:
        """Cancel a previously placed order.

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
            List containing the order_id of cancelled order. Example::
                ['c5ab5eae-76be-480e-8961-00792dc7e138']

        Raises:
            See `get_products()`.

        """
        return self._send_message(
            "delete", "/orders/" + order_id, rate_limiter=self.a_rate_limiter
        )

    def cancel_all(self, product_id: Optional[str] = None) -> List[str]:
        """With best effort, cancel all open orders.

        Args:
            product_id: Only cancel orders for this product_id.

        Returns:
            A list of ids of the canceled orders. Example::
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
            params = {"product_id": product_id}
        else:
            params = None
        return self._send_message(
            "delete", "/orders", params=params, rate_limiter=self.a_rate_limiter
        )

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get a single order by order id.

        If the order is canceled the response may have status code 404
        if the order had no matches.

        **Caution**: Open orders may change state between the request
        and the response depending on market conditions.

        Args:
            order_id: The order to get information of.

        Returns:
            Information on order. Example::
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
        field_conversions = {
            "created_at": self._parse_datetime,
            "executed_value": Decimal,
            "fill_fees": Decimal,
            "filled_size": Decimal,
            "price": Decimal,
            "size": Decimal,
        }
        r = self._send_message(
            "get", "/orders/" + order_id, rate_limiter=self.a_rate_limiter
        )
        return self._convert_dict(r, field_conversions)

    def get_orders(
        self,
        product_id: Optional[str] = None,
        status: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> Iterator[Dict[str, Any]]:
        """List your current open orders.

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
            product_id: Only list orders for this product.
            status: Limit list of orders to this status or statuses.
                Passing 'all' returns orders of all statuses.
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
            params["product_id"] = product_id
        if status is not None:
            params["status"] = status

        field_conversions = {
            "price": Decimal,
            "size": Decimal,
            "created_at": self._parse_datetime,
            "fill_fees": Decimal,
            "filled_size": Decimal,
            "executed_value": Decimal,
        }
        orders = self._send_paginated_message(
            "/orders", params=params, rate_limiter=self.a_rate_limiter
        )
        return (self._convert_dict(order, field_conversions) for order in orders)

    def get_fills(
        self, product_id: Optional[str] = None, order_id: Optional[str] = None, **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """Get recent fills for a product or order.

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
            product_id: Limit list to this product_id.
            order_id: Limit list to this order_id.
            kwargs: Additional HTTP request parameters.

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
            ValueError: If at least one filter param isn't specified.
            See `get_products()`.

        """
        if (product_id is None) and (order_id is None):
            raise ValueError("Either product_id or order_id must be specified.")
        params = {}
        if product_id:
            params["product_id"] = product_id
        if order_id:
            params["order_id"] = order_id
        params.update(kwargs)

        field_conversions = {
            "price": Decimal,
            "size": Decimal,
            "created_at": self._parse_datetime,
            "fee": Decimal,
        }

        def convert_volume_keys(fill):
            """Convert any 'volume' keys (like 'usd_volume') to Decimal."""
            for k, v in fill.items():
                if "volume" in k and v is not None:
                    fill[k] = Decimal(fill[k])
            return fill

        fills = self._send_paginated_message(
            "/fills", params=params, rate_limiter=self.a_rate_limiter
        )
        return (
            self._convert_dict(convert_volume_keys(fill), field_conversions)
            for fill in fills
        )

    def deposit(
        self, amount: Union[float, Decimal], currency: str, payment_method_id: str
    ) -> Dict[str, Any]:
        """Deposit funds from a payment method.

        See AuthenticatedClient.get_payment_methods() to receive
        information regarding payment methods.

        Args:
            amount: The amount to deposit.
            currency: The type of currency.
            payment_method_id: ID of the payment method.

        Returns:
            Information about the deposit. Example::
                {
                    'id': '593533d2-ff31-46e0-b22e-ca754147a96a',
                    'amount': Decimal('10.00'),
                    'currency': 'USD',
                    'payout_at': datetime(2019, 3, 19, 22, 26, 22)
                }

        Raises:
            See `get_products()`.

        """
        params = {
            "amount": amount,
            "currency": currency,
            "payment_method_id": payment_method_id,
        }
        field_conversions = {"amount": Decimal, "payout_at": self._parse_datetime}
        r = self._send_message(
            "post",
            "/deposits/payment-method",
            data=json.dumps(params),
            rate_limiter=self.a_rate_limiter,
        )
        return self._convert_dict(r, field_conversions)

    def deposit_from_coinbase(
        self, amount: Union[float, Decimal], currency: str, coinbase_account_id: str
    ) -> Dict[str, Any]:
        """Deposit funds from a Coinbase account.

        You can move funds between your Coinbase accounts and your
        Coinbase Pro trading accounts within your daily limits. Moving
        funds between Coinbase and Coinbase Pro is instant and free.

        See AuthenticatedClient.get_coinbase_accounts() to receive
        information regarding your coinbase_accounts.

        Args:
            amount: The amount to deposit.
            currency: The type of currency.
            coinbase_account_id: ID of the coinbase account.

        Returns:
            Information about the deposit. Example::
                {
                    'id': '593533d2-ff31-46e0-b22e-ca754147a96a',
                    'amount': Decimal('10.00'),
                    'currency: 'BTC',
                }

        Raises:
            See `get_products()`.

        """
        params = {
            "amount": amount,
            "currency": currency,
            "coinbase_account_id": coinbase_account_id,
        }
        r = self._send_message(
            "post",
            "/deposits/coinbase-account",
            data=json.dumps(params),
            rate_limiter=self.a_rate_limiter,
        )
        return self._convert_dict(r, {"amount": Decimal})

    def generate_crypto_address(self, account_id: str) -> Dict[str, Any]:
        """Generate a one-time crypto address for depositing crypto.

        Args:
            account_id: ID of the coinbase account.

        Returns:
            The created address, plus metadata. Example::
                {
                    "id": "fc9fed1e-d25b-54d8-b52b-7fa250c9ae2d",
                    "address": "0xd518A6B23D8bCA15B9cC46a00Be8a818E34Ca79E",
                    "address_info": {
                        "address": "0xd518A6B23D8bCA15B9cC46a00Be8a818E34Ca79E"
                    },
                    "name": "New exchange deposit address",
                    "created_at": datetime(2019, 3, 19, 22, 26, 22),
                    "updated_at": datetime(2019, 3, 19, 22, 26, 22),
                    "network": "ethereum",
                    "uri_scheme": "ethereum",
                    "resource": "address",
                    "resource_path": "/v2/accounts/faf4b657-a48c-56b2-bec2-77567e3f4f97/addresses/fc9fed1e-d25b-54d8-b52b-7fa250c9ae2d",
                    "warnings": [
                        {
                            "title": "Only send Orchid (OXT) to this address",
                            "details": "Sending any other digital asset, including Ethereum (ETH), will result in permanent loss.",
                            "image_url": "https://dynamic-assets.coinbase.com/22b24ad9886150535671f158ccb0dd9d12089803728551c998e17e0f503484e9c38f3e8735354b5e622753684f040488b08d55b8ef5fef51592680f0c572bdfe/asset_icons/023010d790b9b1f47bc285802eafeab3d83c4de2029fe808d59935fbc54cdd7c.png"
                        }
                    ],
                    "deposit_uri": "ethereum:0x4575f41308ec1483f3d399aa9a2826d74da13deb/transfer?address=0xd518A6B23D8bCA15B9cC46a00Be8a818E34Ca79E",
                    "callback_url": null,
                    "exchange_deposit_address": true
                }

        Raises:
            See `get_products()`.

        """
        params = {"account_id": account_id}
        field_conversions = {
            "created_at": self._parse_datetime,
            "updated_at": self._parse_datetime,
        }
        r = self._send_message(
            "post",
            f"/coinbase-accounts/{account_id}/addresses",
            data=json.dumps(params),
            rate_limiter=self.a_rate_limiter,
        )
        return self._convert_dict(r, field_conversions)

    def withdraw(
        self, amount: Union[float, Decimal], currency: str, payment_method_id: str
    ) -> Dict[str, Any]:
        """Withdraw funds to a payment method.

        See AuthenticatedClient.get_payment_methods() to receive
        information regarding payment methods.

        Args:
            amount: The amount to withdraw.
            currency: Currency type (eg. 'BTC').
            payment_method_id: ID of the payment method.

        Returns:
            Withdraw details. Example::
                {
                    'id': '593533d2-ff31-46e0-b22e-ca754147a96a',
                    'amount': Decimal('10.00'),
                    'currency': 'USD',
                    'payout_at': datetime(2019, 3, 19, 22, 26, 22)
                }

        Raises:
            See `get_products()`.

        """
        params = {
            "amount": amount,
            "currency": currency,
            "payment_method_id": payment_method_id,
        }
        field_conversions = {"amount": Decimal, "payout_at": self._parse_datetime}
        r = self._send_message(
            "post",
            "/withdrawals/payment-method",
            data=json.dumps(params),
            rate_limiter=self.a_rate_limiter,
        )
        return self._convert_dict(r, field_conversions)

    def withdraw_to_coinbase(
        self, amount: Union[float, Decimal], currency: str, coinbase_account_id: str
    ) -> Dict[str, Any]:
        """Withdraw funds to a coinbase account.

        You can move funds between your Coinbase accounts and your
        Coinbase Pro trading accounts within your daily limits. Moving
        funds between Coinbase and Coinbase Pro is instant and free.

        See AuthenticatedClient.get_coinbase_accounts() to receive
        information regarding your coinbase_accounts.

        Args:
            amount: The amount to withdraw.
            currency: The type of currency (eg. 'BTC').
            coinbase_account_id: ID of the coinbase account.

        Returns:
            Information about the deposit. Example::
                {
                    'id': '593533d2-ff31-46e0-b22e-ca754147a96a',
                    'amount': Decimal('10.00'),
                    'currency': 'BTC',
                }

        Raises:
            See `get_products()`.

        """
        params = {
            "amount": amount,
            "currency": currency,
            "coinbase_account_id": coinbase_account_id,
        }
        r = self._send_message(
            "post",
            "/withdrawals/coinbase-account",
            data=json.dumps(params),
            rate_limiter=self.a_rate_limiter,
        )
        return self._convert_dict(r, {"amount": Decimal})

    def withdraw_to_crypto(
        self, amount: Union[float, Decimal], currency: str, crypto_address: str
    ) -> Dict[str, Any]:
        """Withdraw funds to a crypto address.

        Args:
            amount: The amount to withdraw.
            currency: The type of currency (eg. 'BTC').
            crypto_address: Crypto address to withdraw to.

        Returns:
            Withdraw details. Example::
                {
                    'id': '593533d2-ff31-46e0-b22e-ca754147a96a',
                    'amount': Decimal('10.00'),
                    'currency': 'BTC',
                }

        Raises:
            See `get_products()`.

        """
        params = {
            "amount": amount,
            "currency": currency,
            "crypto_address": crypto_address,
        }
        r = self._send_message(
            "post",
            "/withdrawals/crypto",
            data=json.dumps(params),
            rate_limiter=self.a_rate_limiter,
        )
        return self._convert_dict(r, {"amount": Decimal})

    def get_crypto_withdrawal_fee_estimate(
        self, currency: str, crypto_address: str
    ) -> Dict[str, Any]:
        """Get the fee estimate for the crypto withdrawal to crypto address

        Args:
            currency: The type of currency (eg. 'BTC').
            crypto_address: Crypto address to withdraw to.

        Returns:
            Fee estimate details. Example::
                {
                    "fee": Decimal(0.01)
                }

        Raises:
            See `get_products()`.

        """
        params = {
            "currency": currency,
            "crypto_address": crypto_address,
        }
        r = self._send_message(
            "get",
            "/withdrawals/fee-estimate",
            params=params,
            rate_limiter=self.a_rate_limiter,
        )
        return self._convert_dict(r, {"fee": Decimal})

    def get_payment_methods(self) -> List[Dict[str, Any]]:
        """Get a list of your payment methods.

        Returns:
            Payment method details.

        Raises:
            See `get_products()`.

        """
        field_conversions = {
            "created_at": self._parse_datetime,
            "updated_at": self._parse_datetime,
        }
        r = self._send_message(
            "get", "/payment-methods", rate_limiter=self.a_rate_limiter
        )
        return self._convert_list_of_dicts(r, field_conversions)

    def get_coinbase_accounts(self) -> List[Dict[str, Any]]:
        """Get a list of your coinbase accounts.

        Returns:
            Coinbase account details.

        Raises:
            See `get_products()`.

        """
        field_conversions = {"balance": Decimal, "hold_balance": Decimal}
        r = self._send_message(
            "get", "/coinbase-accounts", rate_limiter=self.a_rate_limiter
        )
        return self._convert_list_of_dicts(r, field_conversions)

    def get_fees(self) -> Dict[str, Any]:
        """Get current maker/taker fee rates and 30-day trailing volume.

        Returns:
            Fee details. Example::
                {
                    "maker_fee_rate": Decimal('0.0050'),
                    "taker_fee_rate": Decimal('0.0050'),
                    "usd_volume": Decimal('43806.92')
                }

        Raises:
            See `get_products()`.

        """
        field_conversions = {
            "maker_fee_rate": Decimal,
            "taker_fee_rate": Decimal,
            "usd_volume": Decimal,
        }
        r = self._send_message(
            "get",
            "/fees",
            rate_limiter=self.a_rate_limiter,
        )
        return self._convert_dict(r, field_conversions)

    def create_report(
        self,
        report_type: str,
        start_date: str,
        end_date: str,
        product_id: Optional[str] = None,
        account_id: Optional[str] = None,
        report_format: str = "pdf",
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create report of historic information about your account.

        The report will be generated when resources are available.
        Report status can be queried via `get_report(report_id)`.

        Args:
            report_type: 'fills' or 'account'
            start_date: Starting date for the report in ISO 8601
            end_date: Ending date for the report in ISO 8601
            product_id: ID of the product to generate a fills report
                for. Required if account_type is 'fills'.
            account_id: ID of the account to generate an account report
                for. Required if report_type is 'account'.
            report_format: 'pdf' or 'csv'. Default is 'pdf'.
            email: Email address to send the report to.

        Returns:
            Report details. Example::
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
        params = {
            "type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "format": report_format,
        }
        if product_id is not None:
            params["product_id"] = product_id
        if account_id is not None:
            params["account_id"] = account_id
        if email is not None:
            params["email"] = email

        return self._send_message(
            "post",
            "/reports",
            data=json.dumps(params),
            rate_limiter=self.a_rate_limiter,
        )

    def get_report(self, report_id: str) -> Dict[str, Any]:
        """Get report status.

        Use to query a specific report once it has been requested.

        Args:
            report_id: Report ID

        Returns:
            Report details, including file url once it is created.

        Raises:
            See `get_products()`.

        """
        return self._send_message(
            "get", "/reports/" + report_id, rate_limiter=self.a_rate_limiter
        )

    def get_trailing_volume(self) -> List[Dict[str, Any]]:
        """Get your 30-day trailing volume for all products.

        This is a cached value that's calculated every day at midnight UTC.

        Returns:
            30-day trailing volumes. Example::
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
        field_conversions = {
            "exchange_volume": Decimal,
            "volume": Decimal,
            "recorded_at": self._parse_datetime,
        }
        r = self._send_message(
            "get", "/users/self/trailing-volume", rate_limiter=self.a_rate_limiter
        )
        return self._convert_dict(field_conversions, r)

    def _get_account_helper(
        self, account_id: str
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        field_conversions = {"balance": Decimal, "available": Decimal, "hold": Decimal}
        r = self._send_message(
            "get", "/accounts/" + account_id, rate_limiter=self.a_rate_limiter
        )
        # Need to handle empty string `account_id`, which returns all accounts
        if type(r) is list:
            return self._convert_list_of_dicts(r, field_conversions)
        else:
            return self._convert_dict(r, field_conversions)

    def _get_transfers_helper(
        self, endpoint: str, **kwargs
    ) -> Iterator[Dict[str, Any]]:
        field_conversions = {
            "created_at": self._parse_datetime,
            "completed_at": self._parse_datetime,
            "canceled_at": self._parse_datetime,
            "processed_at": self._parse_datetime,
            "user_nonce": self._parse_optional_int,
            "amount": Decimal,
        }
        r = self._send_paginated_message(
            endpoint, params=kwargs, rate_limiter=self.a_rate_limiter
        )
        return (self._convert_dict(hold, field_conversions) for hold in r)
