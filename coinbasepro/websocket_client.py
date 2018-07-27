# -*- coding: utf-8 -*-

# Python Standard Library imports
from __future__ import print_function
import logging
import json
import base64
import hmac
import hashlib
import time
from threading import Thread

# Other imports
from websocket import create_connection, WebSocketConnectionClosedException


DEFAULT_PRODUCTS = ["BTC-USD", "ETH-USD", "LTC-USD", "BCH-USD"]


class WebsocketClient(object):
    """ Provides WebsocketClient connectivity for the Coinbase Pro API. """
    def __init__(self,
                 url="wss://ws-feed.pro.coinbase.com",
                 products=None,
                 should_print=False,
                 logfile=None,
                 auth=False,
                 key="",
                 secret="",
                 passphrase="",
                 channels=None):
        """Instantiates a WebsocketClient.

        Args:
            url (str): Coinbase Pro websocket endpoint.
            products (str or list): Currency pairings to subscribe.
            should_print (bool): Print data to stdout.
            logfile (str): Path to file. Websocket feed is dumped to this file.
            auth (bool): Authenticate the client.
            key (str): Your API key.
            secret (str): Your API secret.
            passphrase (str): Your API passphrase.
            channels (str): Channels to subscribe to.
        """
        self.url = url
        self.products = products
        self.channels = channels
        self.stop = False
        self.error = None
        self.ws = None
        self.thread = None
        self.auth = auth
        self.key = key
        self.secret = secret
        self.passphrase = passphrase
        self.should_print = should_print
        self.logfile = logfile
        return None

    def start(self):
        def _go():
            self._connect()
            self._listen()
            self._disconnect()

        self.stop = False
        self.on_open()
        self.thread = Thread(target=_go)
        self.thread.start()

    def _connect(self):
        if self.products is None:
            self.products = DEFAULT_PRODUCTS
        elif not isinstance(self.products, list):
            self.products = [self.products]

        if self.url[-1] == "/":
            self.url = self.url[:-1]

        if self.channels is None:
            sub_params = {'type': 'subscribe', 'product_ids': self.products}
        else:
            sub_params = {
                'type': 'subscribe',
                'product_ids': self.products,
                'channels': self.channels}

        if self.auth:
            timestamp = str(time.time())
            message = timestamp + 'GET' + '/users/self/verify'
            message = message.encode('ascii')
            hmac_key = base64.b64decode(self.secret)
            signature = hmac.new(hmac_key, message, hashlib.sha256)
            signature_b64 = base64.b64encode(signature.digest())\
                .decode('utf-8').rstrip('\n')
            sub_params['signature'] = signature_b64
            sub_params['key'] = self.key
            sub_params['passphrase'] = self.passphrase
            sub_params['timestamp'] = timestamp

        self.ws = create_connection(self.url)

        logging.info('Websocket subscription params = "{}"'.format(sub_params))
        self.ws.send(json.dumps(sub_params))

    def _listen(self):
        while not self.stop:
            try:
                start_t = 0
                if time.time() - start_t >= 30:
                    # Set a 30 second ping to keep connection alive
                    self.ws.ping("keepalive")
                    start_t = time.time()
                data = self.ws.recv()
                msg = data
            except ValueError as e:
                self.on_error(e)
            except Exception as e:
                self.on_error(e)
            else:
                self.on_message(msg)
        return None

    def _disconnect(self):
        try:
            if self.ws:
                self.ws.close()
        except WebSocketConnectionClosedException as e:
            pass
        return None

        self.on_close()
        return None

    def close(self):
        self.stop = True
        self.thread.join()
        return None

    def on_open(self):
        if self.should_print:
            print("-- Subscribed! --\n")
        return None

    def on_close(self):
        if self.should_print:
            print("\n-- Socket Closed --")
        return None

    def on_message(self, msg):
        if self.logfile:
            with open(self.logfile, 'a') as f:
                f.write(msg + '\n')
        if self.should_print:
            print(msg)
        return None

    def on_error(self, e, data=None):
        self.error = e
        self.stop = True
        print('{} - data: {}'.format(e, data))
        return None
