class NormalizedPayout:
  def __init__(self, isInvalid, payout):
    self._isInvalid = isInvalid
    self._payout = payout

  @property
  def isInvalid(self):
    '''Whether the Outcome is Invalid.

    Returns bool or int
    '''
    return self._isInvalid

  @property
  def payout(self):
    '''Payout Set for the Dispute Crowdsourcer.

    Returns list<int or str>
    '''
    return self._payout


