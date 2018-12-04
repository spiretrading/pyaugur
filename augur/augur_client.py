import json
import websockets

from market_info import MarketInfo

class AugurClient:
  '''Client for connecting and interacting with an Augur Node.'''

  def __init__(self, hostname, port,
      universe='0xe991247b78f937d7b69cfc00f1a487a293557677'):
    self._hostname = hostname
    self._port = port
    self._augur_http = self._build_url(hostname, port)
    self._node = None
    self._sequence_id = 0
    self._universe = universe
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
    self._node = await websockets.connect(self._augur_http)
    self._is_open = True

  def close(self):
    '''Disconnects from an Augur node.'''
    self._is_open = False

  def _require_is_open(self):
    if not self._is_open:
      raise IOError('Client is not open.')

  def _build_url(self, hostname, port, ssl=False):
    self._require_is_open()
    return ''.join(
      ['ws://' if not ssl else 'wss://', hostname, ':', str(port)])

  async def _send_json_rpc(self, method, **params):
    self._require_is_open()
    command_dict = {
      'jsonrpc': '2.0',
      'id': self._sequence_id,
      'method': method,
      'params': params
    }
    self._sequence_id += 1
    json_rpc = json.dumps(command_dict)
    await self._node.send(json_rpc)

  async def _get_response(self):
    self._require_is_open()
    response = json.loads(await self._node.recv())
    return response['result']
