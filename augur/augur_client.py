class AugurClient:
  def __init__(self, hostname, port):
    self._is_open = False

  def open(self):
    self._is_open = True

  def close(self):
    self._is_open = False

  def load_market_info(self, id):
    self._require_is_open()
    print('hello')

  def _require_is_open(self):
    if not self._is_open:
      raise IOError('Client is not open.')
