from datetime import datetime
from decimal import Decimal
import json
import re

import websockets

from .market_info import MarketInfo
from .normalized_payout import NormalizedPayout
from .outcome_info import OutcomeInfo
from .reporting_state import ReportingState

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

    Raises:
      IOError: If there is an issue with communicating with the node.
    '''
    self._require_is_open()
    await self._send_json_rpc('getMarketsInfo', marketIds=[id])
    response_data = (await self._get_response())[0]
    if response_data is None:
      return None
    market_info_dict = {}
    casting_map = {
      'id': str,
      'universe': str,
      'market_type': MarketInfo.Type,
      'min_price': Decimal,
      'max_price': Decimal,
      'cumulative_scale': Decimal,
      'author': str,
      'creation_time': datetime,
      'creation_fee': Decimal,
      'settlement_fee': Decimal,
      'reporting_fee_rate': Decimal,
      'market_creator_fee_rate': Decimal,
      'market_creator_fees_balance': Decimal,
      'market_creator_mailbox': str,
      'market_creator_mailbox_owner': str,
      'initial_report_size': Decimal,
      'category': str,
      'tags': list,
      'volume': Decimal,
      'open_interest': Decimal,
      'outstanding_shares': Decimal,
      'reporting_state': ReportingState,
      'end_time': datetime,
      'finalization_time': datetime,
      'last_trade_time': datetime,
      'description': str,
      'details': str,
      'scalar_denomination': str,
      'designated_reporter': str,
      'designated_report_stake': Decimal,
      'resolution_source': str,
      'num_ticks': Decimal,
      'tick_size': Decimal,
      'consensus': NormalizedPayout,
      'outcomes': OutcomeInfo,
    }
    for key, value in response_data.items():
      new_key = self._to_snake_case(key)
      to_cast_type = casting_map.get(new_key, None)
      if not value:
        if to_cast_type is list:
          new_value = [x for x in value if x is not None]
        elif to_cast_type is str:
          new_value = '' if not value else value
      elif to_cast_type is None:
        new_value = value
      elif to_cast_type is MarketInfo.Type or to_cast_type is ReportingState:
        new_value = to_cast_type[value.upper()]
      elif to_cast_type is NormalizedPayout:
        new_value = to_cast_type(*value)
      elif to_cast_type is OutcomeInfo:
        new_value = [OutcomeInfo(**properties) for properties in value]
      elif to_cast_type is datetime:
        # Augur can store timestamps in microseconds which will raise an
        # OSError for datetime.fromtimestamp, which requires the timestamp
        # be in seconds.
        new_value = to_cast_type.fromtimestamp(int(str(value)[:10]))
      else:
        if value:
          new_value = to_cast_type(value)
      market_info_dict[new_key] = new_value
    return MarketInfo(**market_info_dict)

  async def open(self):
    '''Connects to an Augur node.

    Raises:
      IOError: If there is an issue connecting to the Augur node.
    '''
    try:
      self._node = await websockets.connect(
        'ws://{}:{}'.format(self._hostname, str(self._port)))
      self._is_open = True
    except (websockets.exceptions.InvalidURI,
        websockets.exceptions.InvalidHandshake, OSError) as ws_error:
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
      return response['result']
    except websockets.exceptions.ConnectionClosed as response_error:
      raise IOError(response_error)

  def _to_snake_case(self, text):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
