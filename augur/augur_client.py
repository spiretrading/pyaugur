import json
import re

import requests
import websockets

from .market_info import MarketInfo

class AugurClient:
  '''Client for connecting and interacting with an Augur Node.'''

  def __init__(self, hostname, port):
    '''Constructs the AugurClient.

    Args:
      hostname (str): Hostname for the Augur node.
      port (int): Listening port for the Augur node.
    '''
    self._hostname = hostname
    self._port = port
    self._node = None
    self._sequence_id = 0
    self._is_open = False

  async def load_market_info(self, id):
    '''Loads a MarketInfo object from its unique address.

    Args:
      id (str): Hexadecimal string of a market's address.

    Returns:
      MarketInfo: The MarketInfo object containing details of the specific
                  market.
    '''
    self._require_is_open()
    await self._send_json_rpc('getMarketsInfo', marketIds=[id])
    raw_market_info = (await self._get_response())[0]
    if raw_market_info is None:
      return None
    # MarketInfo accepts parameters as snake case, however the node will send
    # a response with keys as camel case. Translating the dict to snake case
    # makes it easier to create a MarketInfo object.
    translated_dict = {
      self._to_snake_case(key): value for key, value in raw_market_info.items()
    }
    market_info = MarketInfo(**translated_dict)
    return market_info

  async def open(self):
    '''Connects to an Augur node.

    Raises:
      IOError: If there is an issue connecting to the Augur node.
    '''
    augur_ws_url = ''.join(['ws://', self._hostname, ':', str(self._port)])
    try:
      self._node = await websockets.connect(augur_ws_url)
      self._is_open = True
    except (websockets.exceptions.InvalidURI,
            websockets.exceptions.InvalidHandshake,
            OSError) as ws_error:
      raise IOError(ws_error)

  def close(self):
    '''Disconnects from an Augur node.'''
    self._is_open = False

  def _require_is_open(self):
    if not self._is_open:
      raise IOError('Client is not open.')

  async def _send_json_rpc(self, method, **params):
    command_dict = {
      'jsonrpc': '2.0',
      'id': self._sequence_id,
      'method': method,
      'params': params
    }
    self._sequence_id += 1
    try:
      json_rpc = json.dumps(command_dict)
      await self._node.send(json_rpc)
    except TypeError as send_error:
      raise IOError(send_error)

  async def _get_response(self):
    try:
      response = json.loads(await self._node.recv())
    except websockets.exceptions.ConnectionClosed as error:
      raise IOError(error)
    return response['result']

  def _to_snake_case(self, text):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
