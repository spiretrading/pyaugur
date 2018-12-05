import json
import requests
import websockets

from market_info import MarketInfo

class AugurClient:
  '''Client for connecting and interacting with an Augur Node.'''

  def __init__(self, hostname, port):
    self._hostname = hostname
    self._port = port
    self._augur_ws = None
    self._node = None
    self._sequence_id = 0
    self._contract_addresses = None
    self._is_open = False

  async def load_market_info(self, id):
    '''Loads a MarketInfo object from its unique address.

    Returns MarketInfo
    '''
    self._require_is_open()
    await self._send_json_rpc('getMarketsInfo', marketIds=[id])
    raw_market_info = await self._get_response()
    market_info = MarketInfo(**raw_market_info[0])
    return market_info

  async def open(self):
    '''Connects to an Augur node.'''
    self._augur_ws = ''.join(['ws://', self._hostname, ':', str(self._port)])
    self._contract_addresses = self._get_contract_addresses()
    try:
      self._node = await websockets.connect(self._augur_ws)
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

  def _get_contract_addresses(self):
    try:
      with open('addresses.json') as f:
        return json.load(f)
    except OSError as file_error:
      raise IOError(file_error)
