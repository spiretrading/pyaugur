class NormalizedPayout:
  '''Contains a market's outcome payout distribution.'''

  def __init__(self, is_invalid, payout):
    self._is_invalid = is_invalid
    self._payout = payout

  @property
  def is_invalid(self):
    '''Whether the Outcome is Invalid.

    Returns bool
    '''
    return self._is_invalid

  @property
  def payout(self):
    '''Payout Set for the Dispute Crowdsourcer.

    Returns list[decimal.Decimal]
    '''
    return self._payout
