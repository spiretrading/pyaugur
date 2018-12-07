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
    # Ensure timestamps are in seconds.
    response_data['creationTime'] = (
      self._ensure_unix_timestamp(response_data['creationTime']))
    response_data['endTime'] = (
      self._ensure_unix_timestamp(response_data['endTime']))
    # finalization_time and last_trade_time will default to None
    if response_data['finalizationTime']:
      response_data['finalizationTime'] = (
        self._ensure_unix_timestamp(response_data['finalizationTime']))
    if response_data['lastTradeTime']:
      response_data['lastTradeTime'] = (
        self._ensure_unix_timestamp(response_data['lastTradeTime']))
    # Ensure decimals default to None if needed.
    response_data['initialReportSize'] = (
      response_data['initialReportSize']
      if response_data['initialReportSize'] else None)
    response_data['finalizationBlockNumber'] = (
      response_data['finalizationBlockNumber']
      if response_data['finalizationBlockNumber'] else None)
    response_data['lastTradeBlockNumber'] = (
      response_data['lastTradeBlockNumber']
      if response_data['lastTradeBlockNumber'] else None)
    # Ensure all None are omitted from tags.
    response_data['tags'] = [tag for tag in response_data['tags'] if tag]
    # Ensure enum types return None if not set.
    response_data['reportingState'] = (
      ReportingState[response_data['reportingState']]
      if response_data['reportingState'] else None)
    # Ensure string types default to empty strings.
    response_data['details'] = (
      response_data['details']
      if response_data['details'] else '')
    response_data['scalarDenomination'] = (
      response_data['scalarDenomination']
      if response_data['scalarDenomination'] else '')
    response_data['resolutionSource'] = (
      response_data['resolutionSource']
      if response_data['resolutionSource'] else '')
    # Cast NormalizedPayout types.
    if not response_data['consensus']:
      response_data['consensus'] = list()
    else:
      response_data['consensus'] = NormalizedPayout(
        response_data['consensus']['isInvalid'],
        (response_data['consensus']['payout']
          if response_data['consensus']['payout'] else ''))
    # Cast OutcomeInfo types.
    if not response_data['outcomes']:
      response_data['outcomes'] = list()
    else:
      for index, outcome in enumerate(response_data['outcomes']):
        response_data['outcomes'][index] = OutcomeInfo(
          outcome['id'],
          Decimal(outcome['volume']),
          Decimal(outcome['price']),
          outcome['description'] if outcome['description'] else '')
    return MarketInfo(
      response_data['id'],
      response_data['universe'],
      MarketInfo.Type[response_data['marketType'].upper()],
      response_data['numOutcomes'],
      Decimal(response_data['minPrice']),
      Decimal(response_data['maxPrice']),
      Decimal(response_data['cumulativeScale']),
      response_data['author'],
      response_data['creationTime'],
      response_data['creationBlock'],
      Decimal(response_data['creationFee']),
      Decimal(response_data['settlementFee']),
      Decimal(response_data['reportingFeeRate']),
      Decimal(response_data['marketCreatorFeeRate']),
      Decimal(response_data['marketCreatorFeesBalance']),
      response_data['marketCreatorMailbox'],
      response_data['marketCreatorMailboxOwner'],
      response_data['initialReportSize'],
      response_data['category'],
      response_data['tags'],
      Decimal(response_data['volume']),
      Decimal(response_data['openInterest']),
      Decimal(response_data['outstandingShares']),
      response_data['reportingState'],
      response_data['forking'],
      response_data['needsMigration'],
      response_data['feeWindow'],
      response_data['endTime'],
      response_data['finalizationBlockNumber'],
      response_data['finalizationTime'],
      response_data['lastTradeBlockNumber'],
      response_data['lastTradeTime'],
      response_data['description'],
      response_data['details'],
      response_data['scalarDenomination'],
      response_data['designatedReporter'],
      response_data['designatedReportStake'],
      response_data['resolutionSource'],
      Decimal(response_data['numTicks']),
      Decimal(response_data['tickSize']),
      response_data['consensus'],
      response_data['outcomes'])

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
    return datetime.fromtimestamp(int(str(timestamp)[:10]))
