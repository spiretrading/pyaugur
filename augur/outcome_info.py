class OutcomeInfo:
  '''Details for individual outcomes of a Market.'''

  def __init__(self, id, volume, price, description):
    self._id = id
    self._volume = volume
    self._price = price
    self._description = description

  @property
  def id(self):
    '''Market Outcome ID

    Returns int
    '''
    return self._id

  @property
  def volume(self):
    '''Trading volume for this Outcome.

    Returns decimal.Decimal
    '''
    return self._volume

  @property
  def price(self):
    '''Last price at which the outcome was traded. If no trades have taken place
    in the Market, this value is set to the Market midpoint. If there is no
    volume on this Outcome, but there is volume on another Outcome in the
    Market, price is set to 0 for Yes/No Markets and Categorical Markets.

    Returns decimal.Decimal
    '''
    return self._price

  @property
  def description(self):
    '''Description for the Outcome.

    Returns str
    '''
    return self._description
