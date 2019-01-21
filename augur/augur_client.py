import asyncio
from datetime import datetime
from decimal import Decimal
import json
import os
import re

import requests
import websockets

from .market_info import MarketInfo
from .normalized_payout import NormalizedPayout
from .outcome_info import OutcomeInfo
from .reporting_state import ReportingState

def _ensure_unix_timestamp(timestamp):
  try:
    return datetime.fromtimestamp(timestamp)
  except OSError:
    return datetime.max

def _ensure_unix_timestamp_default_none(timestamp):
  return _ensure_unix_timestamp(timestamp) if timestamp else None

def _ensure_string(value):
  return value if value else ''

def _ensure_decimal_default_to_none(value):
  return Decimal(value) if value else None

def _ensure_normalized_payout(object_dict):
  if object_dict is None:
    return None
  default_decimal_list = []
  for payout in object_dict['payout']:
    if payout:
      default_decimal_list.append(Decimal(payout))
  return NormalizedPayout(object_dict['isInvalid'], default_decimal_list)

def _ensure_outcome_info(object_dict):
  return OutcomeInfo(
    object_dict['id'],
    Decimal(object_dict['volume']),
    Decimal(object_dict['price']),
    _ensure_string(object_dict['description']))

class AugurClient:
  '''Client for connecting and interacting with an Augur Node.'''

  def __init__(self, hostname, port, ethereum_client=None):
    '''Constructs the AugurClient.

    Args:
      hostname (str): Hostname for the Augur node.
      port (int): Listening port for the Augur node.
      ethereum_client (Web3): Web3 object containing methods for interacting
                              with the Ethereum blockchain.
    '''
    self._hostname = hostname
    self._port = port
    self._augur_ws = None
    self._ethereum_client = ethereum_client
    self._sequence_id = 0
    self._addresses = None
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
      _ensure_string(data['id']),
      _ensure_string(data['universe']),
      MarketInfo.Type[data['marketType'].upper()],
      data['numOutcomes'],
      Decimal(data['minPrice']),
      Decimal(data['maxPrice']),
      Decimal(data['cumulativeScale']),
      _ensure_string(data['author']),
      _ensure_unix_timestamp(data['creationTime']),
      data['creationBlock'],
      Decimal(data['creationFee']),
      Decimal(data['settlementFee']),
      Decimal(data['reportingFeeRate']),
      Decimal(data['marketCreatorFeeRate']),
      Decimal(data['marketCreatorFeesBalance']),
      _ensure_string(data['marketCreatorMailbox']),
      data['marketCreatorMailboxOwner'],
      _ensure_decimal_default_to_none(data['initialReportSize']),
      _ensure_string(data['category']),
      [tag for tag in data['tags'] if tag] if data['tags'] else [],
      _ensure_decimal_default_to_none(data['volume']),
      _ensure_decimal_default_to_none(data['openInterest']),
      _ensure_decimal_default_to_none(data['outstandingShares']),
      ReportingState[data['reportingState'].upper()],
      bool(data['forking']),
      bool(data['needsMigration']),
      _ensure_string(data['feeWindow']),
      _ensure_unix_timestamp(data['endTime']),
      data['finalizationBlockNumber'],
      _ensure_unix_timestamp_default_none(data['finalizationTime']),
      data['lastTradeBlockNumber'],
      _ensure_unix_timestamp_default_none(data['lastTradeTime']),
      _ensure_string(data['description']),
      data['details'],
      data['scalarDenomination'],
      _ensure_string(data['designatedReporter']),
      Decimal(data['designatedReportStake']),
      data['resolutionSource'],
      Decimal(data['numTicks']),
      Decimal(data['tickSize']),
      _ensure_normalized_payout(data['consensus']),
      ([_ensure_outcome_info(outcome)
        for outcome in data['outcomes'] if outcome]))

  async def start_historical_event_listener(self, event_name_list, from_block,
      on_event, increment_block=1000):
    '''Polls for all Augur events starting at from_block. Once the latest block
    has been reached, the loop will close.

    Args:
      event_name_list (list[string]): List containing names of Augur events.
      from_block (int): Ethereum block to start listener from.
      on_event (callback function): Function to run when an Augur event occurs.
      increment_block (int): The number of blocks from the current_block to
                             create a range of blocks to filter from. There are
                             many blocks that will not contain an Augur event,
                             so setting this number to a high value will search
                             from a larger pool of blocks each iteration.

    Raise:
      IOError: If there is an issue connecting to the Augur node.
    '''
    self._require_is_open()
    current_block = from_block
    topic_0_list = []
    for event_name in event_name_list:
      topic_0_list.append(self._event_name_to_signature_map[event_name])
    while current_block < self._ethereum_client.eth.blockNumber:
      await asyncio.sleep(0)
      event_filter = self._ethereum_client.eth.filter({
        'address': self._ethereum_client.toChecksumAddress(
          self._addresses['Augur']),
        'topics': [topic_0_list],
        'fromBlock': current_block,
        'toBlock': current_block + increment_block
      })
      events = event_filter.get_all_entries()
      for event in events:
        on_event(event)
      current_block += increment_block

  async def start_event_listener(self, event_name_list, on_event):
    '''Polls for new Augur events.

    Args:
      event_name_list (list[string]): List containing names of Augur events.
      on_event (callback function): Function to run when an Augur event occurs.

    Raise:
      IOError: If there is an issue connecting to the Augur node.
    '''
    self._require_is_open()
    topic_0_list = []
    for event_name in event_name_list:
      topic_0_list.append(self._event_name_to_signature_map[event_name])
    event_filter = self._ethereum_client.eth.filter({
      'address': self._ethereum_client.toChecksumAddress(
        self._addresses['Augur']),
      'topics': [topic_0_list],
      'fromBlock': 'latest'
    })
    while True:
      await asyncio.sleep(0)
      events = event_filter.get_new_entries()
      for event in events:
        on_event(event)

  async def open(self):
    '''Connects to an Augur node and associated resources.

    Raises:
      IOError: If there is an issue connecting to the Augur node.
    '''
    try:
      self._augur_ws = await websockets.connect('ws://{}:{}'.format(
        self._hostname, str(self._port)))
      await self._load_sync_data()
      abi_url = ('https://raw.githubusercontent.com/AugurProject/augur-core/'
                 'master/output/contracts/abi.json')
      contract_abi_request = requests.get(abi_url)
      self._contract_abi = contract_abi_request.json()
      self._event_name_to_signature_map = self._event_signatures_from_abi(
        self._contract_abi)
      self._is_open = True
    except (websockets.exceptions.InvalidURI,
        websockets.exceptions.InvalidHandshake, OSError) as ws_error:
      raise IOError(ws_error)

  def close(self):
    '''Disconnects from an Augur node.'''
    self._require_is_open()
    self._augur_ws.close()
    self._is_open = False

  def _require_is_open(self):
    if not self._is_open:
      raise IOError('Client is not open.')

  async def _run_command(self, method, **params):
    await self._send_json_rpc(method, **params)
    return await self._get_response()

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
      await self._augur_ws.send(json_rpc)
    except TypeError as send_error:
      raise IOError(send_error)

  async def _get_response(self):
    try:
      response = json.loads(await self._augur_ws.recv())
      if 'error' in response:
        raise IOError('Received error from json rpc: {}'.format(response))
      return response['result']
    except websockets.exceptions.ConnectionClosed as response_error:
      raise IOError(response_error)

  async def _load_sync_data(self):
    '''Load sync data from the Augur Node.'''
    sync_data = await self._run_command('getSyncData')
    self._addresses = sync_data['addresses']

  def _event_signatures_from_abi(self, abi):
    event_name_to_signature_map = {}
    for abi_events in abi['Augur']:
      if abi_events['type'] == 'event':
        event_input_types = []
        for input in abi_events['inputs']:
          event_input_types.append(input['type'])
        event_definition = '{}({})'.format(
          abi_events['name'], ','.join(event_input_types))
        event_name_to_signature_map[abi_events['name']] = (
          self._ethereum_client.sha3(text=event_definition).hex())
    return event_name_to_signature_map
