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
    return MarketInfo(
      self._ensure_string(data['id']),
      self._ensure_string(data['universe']),
      MarketInfo.Type[data['marketType'].upper()],
      data['numOutcomes'],
      Decimal(data['minPrice']),
      Decimal(data['maxPrice']),
      Decimal(data['cumulativeScale']),
      self._ensure_string(data['author']),
      self._ensure_unix_timestamp(data['creationTime']),
      data['creationBlock'],
      Decimal(data['creationFee']),
      Decimal(data['settlementFee']),
      Decimal(data['reportingFeeRate']),
      Decimal(data['marketCreatorFeeRate']),
      Decimal(data['marketCreatorFeesBalance']),
      self._ensure_string(data['marketCreatorMailbox']),
      data['marketCreatorMailboxOwner'],
      self._ensure_decimal_default_none(data['initialReportSize']),
      self._ensure_string(data['category']),
      [tag for tag in data['tags'] if tag] if data['tags'] else [],
      self._ensure_decimal_default_none(data['volume']),
      self._ensure_decimal_default_none(data['openInterest']),
      self._ensure_decimal_default_none(data['outstandingShares']),
      ReportingState[data['reportingState'].upper()],
      bool(data['forking']),
      bool(data['needsMigration']),
      self._ensure_string(data['feeWindow']),
      self._ensure_unix_timestamp(data['endTime']),
      data['finalizationBlockNumber'],
      self._ensure_unix_timestamp_default_none(data['finalizationTime']),
      data['lastTradeBlockNumber'],
      self._ensure_unix_timestamp_default_none(data['lastTradeTime']),
      self._ensure_string(data['description']),
      data['details'],
      data['scalarDenomination'],
      self._ensure_string(data['designatedReporter']),
      Decimal(data['designatedReportStake']),
      data['resolutionSource'],
      Decimal(data['numTicks']),
      Decimal(data['tickSize']),
      self._ensure_normalized_payout(data['consensus']),
      ([self._ensure_outcome_info(outcome)
        for outcome in data['outcomes'] if outcome]))

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
      return datetime.fromtimestamp(timestamp)
    except OSError:
      return datetime.max

  def _ensure_unix_timestamp_default_none(self, timestamp):
    return self._ensure_unix_timestamp(timestamp) if timestamp else None

  def _ensure_string(self, value):
    return value if value else ''

  def _ensure_decimal_default_none(self, value):
    return Decimal(value) if value else None

  def _ensure_normalized_payout(self, value):
    if value is None:
      return None
    default_decimal_list = []
    for payout in value['payout']:
      if payout:
        default_decimal_list.append(Decimal(payout))
    return NormalizedPayout(value['isInvalid'], default_decimal_list)

  def _ensure_outcome_info(self, value):
    return OutcomeInfo(
      value['id'],
      Decimal(value['volume']),
      Decimal(value['price']),
      self._ensure_string(value['description']))
