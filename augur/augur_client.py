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
    data = (await self._get_response())[0]
    if data is None:
      return None
    # Everything above is good. -----------------------------------------------
    data = {
      'id': None,
      'universe': None,
      'market_type': None,
      'num_outcomes': None,
      'min_price': '0',
      'max_price': '0',
      'cumulative_scale': '0',
      'author': None,
      'creation_time': None,
      'creation_block': None,
      'creation_fee': '0',
      'settlement_fee': '0',
      'reporting_fee_rate': '0',
      'market_creator_fee_rate': '0',
      'market_creator_fees_balance': '0',
      'market_creator_mailbox': None,
      'market_creator_mailbox_owner': None,
      'initial_report_size': None,
      'category': None,
      'tags': ['test', 'test2', None, 'test3'],
      'volume': '0',
      'open_interest': '0',
      'outstanding_shares': '0',
      'reporting_state': 'pre_reporting',
      'forking': None,
      'needs_migration': None,
      'fee_window': None,
      'end_time': None,
      'finalization_block_number': None,
      'finalization_time': None,
      'last_trade_block_number': None,
      'last_trade_time': None,
      'description': None,
      'details': None,
      'scalar_denomination': None,
      'designated_reporter': None,
      'designated_report_stake': None,
      'resolution_source': None,
      'num_ticks': None,
      'tick_size': None,
      'consensus': None,
      'outcomes': None
    }
    # Properties should default to string.
    return MarketInfo(
      self._ensure_string(data['id']),
      self._ensure_string(data['universe']),
      MarketInfo.Type[data['market_type']] if data['market_type'] else None,
      data['num_outcomes'],
      Decimal(data['min_price']),
      Decimal(data['max_price']),
      Decimal(data['cumulative_scale']),
      self._ensure_string(data['author']),
      self._ensure_unix_timestamp(data['creation_time']),
      data['creation_block'],
      Decimal(data['creation_fee']),
      Decimal(data['settlement_fee']),
      Decimal(data['reporting_fee_rate']),
      Decimal(data['market_creator_fee_rate']),
      Decimal(data['market_creator_fees_balance']),
      self._ensure_string(data['market_creator_mailbox']),
      data['market_creator_mailbox_owner'],
      self._ensure_decimal(data['initial_report_size']),
      data['category'],
      [tag for tag in data['tags'] if tag] if data['tags'] else [],
      Decimal(data['volume']),
      Decimal(data['open_interest']),
      Decimal(data['outstanding_shares']),
      ReportingState[data['reporting_state'].upper()],
      data['forking'],
      data['needs_migration'],
      data['fee_window'],
      self._ensure_unix_timestamp(data['end_time']),
      data['finalization_block_number'],
      self._ensure_unix_timestamp(data['finalization_time']),
      data['last_trade_block_number'],
      self._ensure_unix_timestamp(data['last_trade_time']),
      self._ensure_string(data['description']),
      data['details'],
      data['scalar_denomination'],
      self._ensure_string(data['designated_reporter']),
      self._ensure_decimal(data['designated_report_stake']),
      data['resolution_source'],
      self._ensure_decimal(data['num_ticks']),
      self._ensure_decimal(data['tick_size']),
      data['consensus'],
      data['outcomes'])

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

  def _ensure_unix_timestamp(self, timestamp):
    try:
      return datetime.fromtimestamp(timestamp) if timestamp else None
    except OSError:
      return datetime.max

  def _ensure_string(self, value):
    return value if value else ''

  def _ensure_decimal(self, value):
    return Decimal(value) if value else None
