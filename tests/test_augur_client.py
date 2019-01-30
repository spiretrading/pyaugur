import os
import sys
import unittest

import asyncio
from web3 import Web3, WebsocketProvider

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
    '../..')))
from augur import AugurClient

class TestEthereumClient(unittest.TestCase):
  def setUp(self):
    self.ethereum = Web3(WebsocketProvider(
      'wss://rinkeby.augur.net/ethereum-ws'))

  def test_ethereum_client(self):
    self.assertEqual(self.ethereum.toHex(0), '0x0')

class TestAugurClient(unittest.TestCase):
  def setUp(self):
    self.loop = asyncio.get_event_loop()
    augur_host = 'localhost'
    augur_port = 9001
    ethereum = Web3(WebsocketProvider('wss://rinkeby.augur.net/ethereum-ws'))
    self.client = AugurClient(augur_host, augur_port, ethereum_client=ethereum)
    self.loop.run_until_complete(self.client.open())

  def test_load_market_info(self):
    # Market Id on Rinkeby.
    market_id = '0x4c537139183c9d1b8338f64ab441f40ed750a14c'
    market_info = self.loop.run_until_complete(
      self.client.load_market_info(market_id))
    self.assertEqual(market_info.id, market_id)

  def test_get_market_id_from_transaction_hash(self):
    hash = '0xc9c4098209341e4490854f079918963ba54233e976c59f5bf70b0d0304ed70b3'
    transaction = self.client.load_transaction_from_hash(hash)
    self.assertEqual(
      transaction.orderId.hex(),
      '5ece8c9d739bcd5046a3196808e56775d3268fd12ceaf70c728fd90bae62f5ed')
    market_id = self.client.load_market_id_from_order_id(transaction.orderId)
    self.assertEqual(market_id, '0x75EC1F1a3356517908eCCb5f6e4FaC619C68bA99')

if __name__ == '__main__':
  unittest.main()
