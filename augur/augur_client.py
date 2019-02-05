import asyncio
from datetime import datetime
from decimal import Decimal
import json

import requests
import websockets

from .market_info import MarketInfo
from .normalized_payout import NormalizedPayout
from .outcome_info import OutcomeInfo
from .reporting_state import ReportingState

def ensure_unix_timestamp(timestamp):
  try:
    return datetime.fromtimestamp(timestamp)
  except OSError:
    return datetime.max

def ensure_unix_timestamp_default_none(timestamp):
  return ensure_unix_timestamp(timestamp) if timestamp else None

def ensure_string(value):
  return value if value else ''

def ensure_decimal_default_to_none(value):
  return Decimal(value) if value else None

def ensure_normalized_payout(object_dict):
  if object_dict is None:
    return None
  default_decimal_list = []
  for payout in object_dict['payout']:
    if payout:
      default_decimal_list.append(Decimal(payout))
  return NormalizedPayout(object_dict['isInvalid'], default_decimal_list)

def ensure_outcome_info(object_dict):
  return OutcomeInfo(
    object_dict['id'],
    Decimal(object_dict['volume']),
    Decimal(object_dict['price']),
    ensure_string(object_dict['description']))

def inverse_dict(kv_dict):
  inverse_dict = {}
  for key, value in kv_dict.items():
    inverse_dict[value] = key
  return inverse_dict

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
    self._ethereum_client = ethereum_client
    self._augur_ws = None
    self._sequence_id = 0
    self._addresses = None
    self._latest_block = self._ethereum_client.eth.blockNumber
    self._is_open = False

  @property
  def contracts(self):
    '''Returns Augur contracts.'''
    self._require_is_open()
    return self._contracts

  @property
  def event_name_to_signature_map(self):
    '''Returns map of event names to event signatures.'''
    self._require_is_open()
    return self._event_name_to_signature_map

  @property
  def event_signature_to_name_map(self):
    '''Returns map of event signatures to event names.'''
    self._require_is_open()
    return self._event_signature_to_name_map

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
    data = (await self._send_request('getMarketsInfo', self._augur_ws,
      dict(marketIds=[id])))[0]
    if data is None:
      return None
    return MarketInfo(
      ensure_string(data['id']),
      ensure_string(data['universe']),
      MarketInfo.Type[data['marketType'].upper()],
      data['numOutcomes'],
      Decimal(data['minPrice']),
      Decimal(data['maxPrice']),
      Decimal(data['cumulativeScale']),
      ensure_string(data['author']),
      ensure_unix_timestamp(data['creationTime']),
      data['creationBlock'],
      Decimal(data['creationFee']),
      Decimal(data['settlementFee']),
      Decimal(data['reportingFeeRate']),
      Decimal(data['marketCreatorFeeRate']),
      Decimal(data['marketCreatorFeesBalance']),
      ensure_string(data['marketCreatorMailbox']),
      data['marketCreatorMailboxOwner'],
      ensure_decimal_default_to_none(data['initialReportSize']),
      ensure_string(data['category']),
      [tag for tag in data['tags'] if tag] if data['tags'] else [],
      ensure_decimal_default_to_none(data['volume']),
      ensure_decimal_default_to_none(data['openInterest']),
      ensure_decimal_default_to_none(data['outstandingShares']),
      ReportingState[data['reportingState'].upper()],
      bool(data['forking']),
      bool(data['needsMigration']),
      ensure_string(data['feeWindow']),
      ensure_unix_timestamp(data['endTime']),
      data['finalizationBlockNumber'],
      ensure_unix_timestamp_default_none(data['finalizationTime']),
      data['lastTradeBlockNumber'],
      ensure_unix_timestamp_default_none(data['lastTradeTime']),
      ensure_string(data['description']),
      data['details'],
      data['scalarDenomination'],
      ensure_string(data['designatedReporter']),
      Decimal(data['designatedReportStake']),
      data['resolutionSource'],
      Decimal(data['numTicks']),
      Decimal(data['tickSize']),
      ensure_normalized_payout(data['consensus']),
      ([ensure_outcome_info(outcome)
        for outcome in data['outcomes'] if outcome]))

  async def start_historical_event_listener(self, event_name_list,
      current_block, on_event, increment_block=1000):
    '''Polls for all Augur events starting at from_block. Once the latest block
    has been reached, the loop will close.

    Args:
      event_name_list (list[string]): List containing names of Augur events.
      current_block (int): Ethereum block to start listener from.
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
    tasks = [self._start_new_block_listener(),
             self._fetch_historical_events(event_name_list, current_block,
                                           on_event, increment_block)]
    # Terminate tasks once the historical listener has completed.
    _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
      task.cancel()

  async def start_event_listener(self, event_name_list, on_event):
    '''Polls for new Augur events.

    Args:
      event_name_list (list[string]): List containing names of Augur events.
      on_event (callback function): Function to run when an Augur event occurs.

    Raise:
      IOError: If there is an issue connecting to the Augur node.
    '''
    self._require_is_open()
    ethereum_uri = self._ethereum_client.providers[0].endpoint_uri
    websocket = await websockets.connect(ethereum_uri)
    topic_list = [self._event_name_to_signature_map[event_name]
                  for event_name in event_name_list]
    address = self._ethereum_client.toChecksumAddress(self._addresses['Augur'])
    await self._send_request('eth_subscribe', websocket, [
      'logs', {
        'address': address,
        'topics': [topic_list],
        'fromBlock': 'latest'
      }])
    async for event in websocket:
      event_json = json.loads(event)['params']['result']
      on_event(event_json)

  def load_transaction_from_hash(self, hash):
    '''Retrieves the transaction data from its hash.

    Args:
      hash (string): Hexadecimal string of a transaction's hash.

    Returns:
      AttributeDict of a transaction.
    '''
    self._require_is_open()
    transaction = self._ethereum_client.eth.getTransactionReceipt(hash)
    if not transaction:
      return None
    return self._decode_input(transaction)

  def load_market_id_from_order_id(self, order_id):
    '''Retrieves the Market Id associated with an Order Id.

    Args:
      order_id (bytes): Bytes32 object containing the address of an Order Id.

    Returns:
      Hexadecimal string of the Market's Id.
    '''
    self._require_is_open()
    get_market_id = self._contracts['Orders'].functions.getMarket
    return get_market_id(order_id).call()

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
      self._contracts = self._contracts_from_abi(self._contract_abi)
      self._event_name_to_signature_map = self._event_signatures_from_abi(
        self._contract_abi)
      self._event_signature_to_name_map = inverse_dict(
        self._event_name_to_signature_map)
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

  async def _send_request(self, method, transport, params={}):
    await self._send_rpc_message(method, transport, params)
    return await self._get_rpc_response(transport)

  async def _send_rpc_message(self, method, transport, params):
    rpc_message = dict(jsonrpc='2.0', id=self._sequence_id, method=method,
      params=params)
    self._sequence_id += 1
    try:
      await transport.send(json.dumps(rpc_message))
    except TypeError as send_error:
      raise IOError(send_error)

  async def _get_rpc_response(self, transport):
    try:
      response = json.loads(await transport.recv())
      if 'error' in response:
        raise IOError('Received error from json rpc: {}'.format(response))
      return response['result']
    except websockets.exceptions.ConnectionClosed as response_error:
      raise IOError(response_error)

  async def _load_sync_data(self):
    sync_data = await self._send_request('getSyncData', self._augur_ws)
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

  def _decode_input(self, input):
    order_created_event = self._contracts['Augur'].events.OrderCreated()
    decoded_input = order_created_event.processReceipt(input)
    if not decoded_input:
      return None
    return decoded_input[0].args

  def _contracts_from_abi(self, abi):
    contracts = {}
    for name, values in abi.items():
      if name in self._addresses:
        contract = self._ethereum_client.eth.contract(
          address=self._ethereum_client.toChecksumAddress(
            self._addresses[name]),
          abi=values)
        contracts[name] = contract
    return contracts

  async def _start_new_block_listener(self):
    self._require_is_open()
    ethereum_uri = self._ethereum_client.providers[0].endpoint_uri
    websocket = await websockets.connect(ethereum_uri)
    await self._send_request('eth_subscribe', websocket, ['newHeads'])
    await asyncio.sleep(0)
    async for block_event in websocket:
      block_event_json = json.loads(block_event)['params']['result']
      self._latest_block = int(block_event_json['number'], 16)

  async def _fetch_historical_events(self, event_name_list, current_block,
      on_event, increment_block=1000):
    topic_list = []
    for event_name in event_name_list:
      event_map = self._event_name_to_signature_map.get(event_name, None)
      if event_map:
        topic_list.append(event_map)
    while current_block < self._latest_block:
      await asyncio.sleep(0)
      event_filter = self._ethereum_client.eth.filter({
        'address': self._ethereum_client.toChecksumAddress(
          self._addresses['Augur']),
        'topics': [topic_list],
        'fromBlock': current_block,
        'toBlock': current_block + increment_block
      })
      events = event_filter.get_all_entries()
      for event in events:
        on_event(event)
      current_block += increment_block
