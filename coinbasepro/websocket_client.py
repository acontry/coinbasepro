# -*- coding: utf-8 -*-

# Python Standard Library imports
import base64
from datetime import datetime
import hashlib
import hmac
import json
import logging
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
                 channels=["full"],
                 keepalive_timer=30):
        """Instantiates a WebsocketClient.

        Link to Coinbase Pro documentation:
            "docs.pro.coinbase.com/#the-code-classprettyprintfullcode-channel"

        Args:
            url (str): Coinbase Pro websocket endpoint.
            products (str or list): Currency pairings to subscribe.
            shouldself._print (bool): Print data to stdout.
            logfile (str): Path to file. Websocket feed is dumped to this file.
            auth (bool): Authenticate the client.
            key (str): Your API key.
            secret (str): Your API secret.
            passphrase (str): Your API passphrase.
            channels (list): Channels to subscribe to.
            keepalive_timer (int): Host keepalive/ping interval.
        """
        self.url = url
        self.products = products
        self.channels = channels
        self.stop = False
        self.ws = None
        self.thread = None
        self.auth = auth
        self.key = key
        self.secret = secret
        self.passphrase = passphrase
        self.should_print = should_print
        self.logfile = logfile
        self.keepalive_timer = keepalive_timer
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
        return None

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
        return None

    def _listen(self):
        while not self.stop:
            try:
                start_t = 0
                if time.time() - start_t >= self.keepalive_timer:
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
        self.close()
        return None

    def close(self):
        self.stop = True
        try:
            self.thread.join()
        except Exception as e:
            logging.info(e)
        self.on_close()
        return None

    def on_open(self):
        """ Logs / prints Websocket start. """
        utc_now = datetime.utcnow()
        sub_message = "-- Subscribed at {} UTC --".format(utc_now)
        logging.info(sub_message)
        self._print(sub_message + '\n')  # newline for legibility
        return None

    def on_close(self):
        """ Logs / prints Websocket close. """
        utc_now = datetime.utcnow()
        closed_message = "-- Socket Closed at {} UTC --".format(utc_now)
        logging.info(closed_message)
        self._print('\n' + closed_message)  # newline for legibility
        return None

    def on_message(self, msg):
        if self.logfile:
            with open(self.logfile, 'a') as f:
                f.write(msg + '\n')
        self._print(msg)
        return None

    def on_error(self, e, data=None):
        logging.info(e)
        self.stop = True
        self._print('{} - data: {}'.format(e, data))
        return None

    def _print(self, msg):
        if self.should_print:
            print(msg)
        return None
