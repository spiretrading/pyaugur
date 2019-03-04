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

  def __init__(self, hostname, port, abi_path, ethereum_client=None):
    '''Constructs the AugurClient.

    Args:
      hostname (str): Hostname for the Augur node.
      port (int): Listening port for the Augur node.
      abi_path (string): Path to the file containing the Augur ABI.
      ethereum_client (Web3): Web3 object containing methods for interacting
                              with the Ethereum blockchain.
    '''
    self._hostname = hostname
    self._port = port
    self._abi_path = abi_path
    self._ethereum_client = ethereum_client
    self._sequence_id = 0
    self._addresses = None
    self._network_id = 1
    self._is_open = False

  @property
  def network_id(self):
    '''Returns the Augur node network id'''
    self._require_is_open()
    return self._network_id

  @property
  def sync_data(self):
    '''Returns information related to the connected Augur node.'''
    self._require_is_open()
    return self._sync_data

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
    data = (await self._send_request('getMarketsInfo', dict(marketIds=[id])))[0]
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

  def filter_blocks(self, start_block, end_block, filter, handler,
      increment=1000):
    '''Retrieve all event logs specified in the filter from the start_block to
    the end_block.

    Args:
      start_block (int): Starting block number.
      end_block (int): Ending block number.
      filter (dict): Dictionary containing filter parameters.
      handler (callback): Callback function for when an event log is found in
                          the current block.
      increment (int): Specifies the range of blocks from the current_block to
                       look for Augur logs.

    Raises:
      IOError: If there is an issue with communicating with the node.
    '''
    self._require_is_open()
    if start_block < 0:
      raise IOError('start_block cannot be less than 0.')
    if increment <= 0:
      raise IOError('increment cannot be less than or equal to 0.')
    if start_block > end_block:
      raise IOError('start_block cannot be larger than the end_block.')
    asyncio.get_event_loop().create_task(self._filter_blocks(start_block,
      end_block, dict(filter), handler, increment))

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
      self._sync_data = await self._send_request('getSyncData')
      self._addresses = self._sync_data['addresses']
      self._network_id = self._sync_data['netId']
      json_abi = json.loads(open(self._abi_path, 'r').read())
      self._contracts = self._contracts_from_abi(json_abi)
      self._event_name_to_signature_map = self._event_signatures_from_abi(
        json_abi)
      self._event_signature_to_name_map = inverse_dict(
        self._event_name_to_signature_map)
      self._is_open = True
    except (websockets.exceptions.InvalidURI,
        websockets.exceptions.InvalidHandshake, OSError) as ws_error:
      raise IOError(ws_error)

  def close(self):
    '''Disconnects from an Augur node.'''
    self._require_is_open()
    self._is_open = False

  def _require_is_open(self):
    if not self._is_open:
      raise IOError('Client is not open.')

  async def _send_request(self, method, params={}):
    async with websockets.connect('ws://{}:{}'.format(
        self._hostname, self._port)) as websocket:
      await self._send_rpc_message(method, websocket, params)
      return await self._get_rpc_response(websocket)

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

  async def _filter_blocks(self, start_block, end_block, filter, handler,
      increment):
    # _filter_block can accept an end_block greater than the current latest
    # Ethereum block. In such a case, _filter_block will first traverse the
    # blockchain until the latest Ethereum block determined at the time of
    # execution. It will then listen for new blocks until the desired end_block
    # has been reached.
    filter['address'] = self._ethereum_client.toChecksumAddress(
      self._addresses['Augur'])
    latest_block = self._ethereum_client.eth.blockNumber
    last_old_block = min(latest_block, end_block)
    for filter_from in range(start_block, last_old_block, increment):
      filter['fromBlock'] = filter_from
      filter['toBlock'] = min(filter_from + increment, last_old_block)
      events_filter = self._ethereum_client.eth.filter(filter)
      for event in events_filter.get_all_entries():
        if asyncio.iscoroutinefunction(handler):
          await handler(event)
        else:
          handler(event)
    # _filter_blocks subscribes to both newHeads and logs on the same websocket
    # to keep track of any new blocks. If a new block arrives and it is the
    # desired end_block, then _filter_blocks will close the websocket.
    if end_block > latest_block:
      ethereum_uri = self._ethereum_client.providers[0].endpoint_uri
      filter['fromBlock'] = self._ethereum_client.toHex(start_block)
      filter['toBlock'] = self._ethereum_client.toHex(end_block)
      events_filter = self._ethereum_client.eth.filter(filter)
      try:
        async with websockets.connect(ethereum_uri) as websocket:
          await self._send_rpc_message('eth_subscribe', websocket, ['newHeads'])
          await self._get_rpc_response(websocket)
          async for new_block in websocket:
            block_json = json.loads(new_block)['params']['result']
            block_number = self._ethereum_client.toInt(
              hexstr=block_json['number'])
            for event in events_filter.get_new_entries():
              if asyncio.iscoroutinefunction(handler):
                await handler(event)
              else:
                handler(event)
            if block_number == end_block:
              await websocket.close()
      except websockets.exceptions.ConnectionClosed as response_error:
        raise IOError(response_error)
