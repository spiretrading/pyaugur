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
    self.client = AugurClient(augur_host, augur_port, ethereum=ethereum)
    self.loop.run_until_complete(self.client.open())

  def test_load_market_info(self):
    # Market Id on Rinkeby.
    market_id = '0x4c537139183c9d1b8338f64ab441f40ed750a14c'
    market_info = self.loop.run_until_complete(
      self.client.load_market_info(market_id))
    self.assertEqual(market_info.id, market_id)

if __name__ == '__main__':
  unittest.main()
