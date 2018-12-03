class MarketInfo:
  def __init__(self, id, universe, marketType, numOutcomes, minPrice, maxPrice,
      cumulativeScale, author, creationTime, creationBlock, creationFee,
      settlementFee, reportingFeeRate, marketCreatorFeeRate,
      marketCreatorFeesBalance, marketCreatorMailbox, marketCreatorMailboxOwner,
      initialReportSize, category, tags, volume, openInterest,
      outstandingShares, reportingState, forking, needsMigration, feeWindow,
      endTime, finalizationBlockNumber, finalizationTime, lastTradeBlockNumber,
      lastTradeTime, description, details, scalarDenomination,
      designatedReporter, designatedReportStake, resolutionSource, numTicks,
      tickSize, consensus, outcomes):
    self._id = id
    self._universe = universe
    self._marketType = marketType
    self._numOutcomes = numOutcomes
    self._minPrice = minPrice
    self._maxPrice = maxPrice
    self._cumulativeScale = cumulativeScale
    self._author = author
    self._creationTime = creationTime
    self._creationBlock = creationBlock
    self._creationFee = creationFee
    self._settlementFee = settlementFee
    self._reportingFeeRate = reportingFeeRate
    self._marketCreatorFeeRate = marketCreatorFeeRate
    self._marketCreatorFeesBalance = marketCreatorFeesBalance
    self._marketCreatorMailbox = marketCreatorMailbox
    self._marketCreatorMailboxOwner = marketCreatorMailboxOwner
    self._initialReportSize = initialReportSize
    self._category = category
    self._tags = tags
    self._volume = volume
    self._openInterest = openInterest
    self._outstandingShares = outstandingShares
    self._reportingState = reportingState
    self._forking = forking
    self._needsMigration = needsMigration
    self._feeWindow = feeWindow
    self._endTime = endTime
    self._finalizationBlockNumber = finalizationBlockNumber
    self._finalizationTime = finalizationTime
    self._lastTradeBlockNumber = lastTradeBlockNumber
    self._lastTradeTime = lastTradeTime
    self._description = description
    self._details = details
    self._scalarDenomination = scalarDenomination
    self._designatedReporter = designatedReporter
    self._designatedReportStake = designatedReportStake
    self._resolutionSource = resolutionSource
    self._numTicks = numTicks
    self._tickSize = tickSize
    self._consensus = consensus
    self._outcomes = outcomes

  @property
  def id(self):
    '''Address of a Market, as a hexadecimal str.

    Returns str
    '''
    return self._id

  @property
  def universe(self):
    '''Address of a Universe, as a hexadecimal str.

    Returns str
    '''
    return self._universe

  @property
  def marketType(self):
    '''Type of Market ("yesNo", "categorical", or "scalar").

    Returns str
    '''
    return self._marketType

  @property
  def numOutcomes(self):
    '''Total possible Outcomes for the Market.

    Returns decimal.Decimal
    '''
    return self._numOutcomes

  @property
  def minPrice(self):
    '''Minimum price allowed for a share on a Market, in ETH. For Yes/No &
    Categorical Markets, this is 0 ETH. For Scalar Markets, this is the bottom
    end of the range set by the Market creator.

    Returns datetime.datetime
    '''
    return self._minPrice

  @property
  def maxPrice(self):
    '''Maximum price allowed for a share on a Market, in ETH. For Yes/No &
    Categorical Markets, this is 1 ETH. For Scalar Markets, this is the top end
    of the range set by the Market creator.

    Returns decimal.Decimal
    '''
    return self._maxPrice

  @property
  def cumulativeScale(self):
    '''Difference between maxPrice and minPrice.

    Returns decimal.Decimal
    '''
    return self._cumulativeScale

  @property
  def author(self):
    '''Ethereum address of the creator of the Market, as a hexadecimal str.

    Returns str
    '''
    return self._author

  @property
  def creationTime(self):
    '''Timestamp when the Ethereum block containing the Market creation was
    created, in seconds.

    Returns datetime.datetime
    '''
    return self._creationTime

  @property
  def creationBlock(self):
    '''Number of the Ethereum block containing the Market creation.

    Returns int
    '''
    return self._creationBlock

  @property
  def creationFee(self):
    '''Fee paid by the Market Creator to create the Market, in ETH.

    Returns decimal.Decimal
    '''
    return self._creationFee

  @property
  def settlementFee(self):
    '''Fee extracted when a Complete Set is Settled. It is the combination of
    the Creator Fee and the Reporting Fee.

    Returns decimal.Decimal
    '''
    return self._settlementFee

  @property
  def reportingFeeRate(self):
    '''Percentage rate of ETH sent to the Fee Window containing the Market
    whenever shares are settled. Reporting Fees are later used to pay REP
    holders for Reporting on the Outcome of Markets.

    Returns decimal.Decimal
    '''
    return self._reportingFeeRate

  @property
  def marketCreatorFeeRate(self):
    '''Percentage rate of ETH paid to the Market creator whenever shares are
    settled.

    Returns decimal.Decimal
    '''
    return self._marketCreatorFeeRate

  @property
  def marketCreatorFeesBalance(self):
    '''Amount of claimable fees the Market creator has not collected from the
    Market, in ETH.

    Returns decimal.Decimal
    '''
    return self._marketCreatorFeesBalance

  @property
  def marketCreatorMailbox(self):
    '''Ethereum address of the Market Creator, as a hexadecimal str.

    Returns str
    '''
    return self._marketCreatorMailbox

  @property
  def marketCreatorMailboxOwner(self):
    '''Ethereum address of the Market Creator Mailbox, as a hexadecimal str.

    Returns str
    '''
    return self._marketCreatorMailboxOwner

  @property
  def initialReportSize(self):
    '''Size of the No-Show Bond (if the Initial Report was submitted by a First
    Public Reporter instead of the Designated Reporter).

    Returns decimal.Decimal or None
    '''
    return self._initialReportSize

  @property
  def category(self):
    '''Name of the category the Market is in.

    Returns str
    '''
    return self._category

  @property
  def tags(self):
    '''Names with which the Market has been tagged.

    Returns list<(str or None)>
    '''
    return self._tags

  @property
  def volume(self):
    '''Trading volume for this Outcome.

    Returns decimal.Decimal
    '''
    return self._volume

  @property
  def openInterest(self):
    '''Open interest for the Market.

    Returns decimal.Decimal
    '''
    return self._openInterest

  @property
  def outstandingShares(self):
    '''Number of Complete Sets in the Market.

    Returns decimal.Decimal
    '''
    return self._outstandingShares

  @property
  def reportingState(self):
    '''Reporting state name.

    Returns REPORTING_STATE or None
    '''
    return self._reportingState

  @property
  def forking(self):
    '''Whether the Market has Forked.

    Returns bool or int
    '''
    return self._forking

  @property
  def needsMigration(self):
    '''Whether the Market needs to be migrated to its Universe's Child Universe
    (i.e., the Market is not Finalized, and the Forked Market in its Universe is
    Finalized).

    Returns bool or int
    '''
    return self._needsMigration

  @property
  def feeWindow(self):
    '''Contract address of the Fee Window the Market is in, as a hexadecimal
    str.

    Returns str
    '''
    return self._feeWindow

  @property
  def endTime(self):
    '''Timestamp when the Market event ends, in seconds.

    Returns datetime.datetime
    '''
    return self._endTime

  @property
  def finalizationBlockNumber(self):
    '''Ethereum block int in which the Market was Finalized.

    Returns int or None
    '''
    return self._finalizationBlockNumber

  @property
  def finalizationTime(self):
    '''Timestamp when the Market was finalized (if any), in seconds.

    Returns datetime.datetime or None
    '''
    return self._finalizationTime

  @property
  def lastTradeBlockNumber(self):
    '''Ethereum block int in which the last trade occurred for this Market.

    Returns int or None
    '''
    return self._lastTradeBlockNumber

  @property
  def lastTradeTime(self):
    '''Unix timestamp when the last trade occurred in this Market.

    Returns datetime.datetime or None
    '''
    return self._lastTradeTime

  @property
  def description(self):
    '''Description of the Market.

    Returns str
    '''
    return self._description

  @property
  def details(self):
    '''Stringified JSON object containing resolutionSource, tags,
    longDescription, and outcomeNames (for Categorical Markets).

    Returns str or None
    '''
    return self._details

  @property
  def scalarDenomination(self):
    '''Denomination used for the numerical range of a Scalar Market (e.g.,
    dollars, degrees Fahrenheit, parts-per-billion).

    Returns str or None
    '''
    return self._scalarDenomination

  @property
  def designatedReporter(self):
    '''Ethereum address of the Market's designated report, as a hexadecimal
    str.

    Returns str
    '''
    return self._designatedReporter

  @property
  def designatedReportStake(self):
    '''Size of the Designated Reporter Stake, in attoETH, that the Designated
    Reporter must pay to submit the Designated Report for this Market.

    Returns str
    '''
    return self._designatedReportStake

  @property
  def resolutionSource(self):
    '''Reference source used to determine the Outcome of the Market event.

    Returns str or None
    '''
    return self._resolutionSource

  @property
  def numTicks(self):
    '''Number of possible prices, or ticks, between a Market's minimum price and
    maximum price.

    Returns decimal.Decimal
    '''
    return self._numTicks

  @property
  def tickSize(self):
    '''Smallest recognized amount by which a price of a security or future may
    fluctuate in the Market.

    Returns decimal.Decimal
    '''
    return self._tickSize

  @property
  def consensus(self):
    '''Consensus Outcome for the Market.

    Returns NormalizedPayout or None
    '''
    return self._consensus

  @property
  def outcomes(self):
    '''Array of OutcomeInfo objects.

    Returns list<OutcomeInfo>
    '''
    return self._outcomes


