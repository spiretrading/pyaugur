class MarketInfo:
  def __init__(self, id, universe, market_type, num_outcomes, min_price,
      max_price, cumulative_scale, author, creation_time, creation_block,
      creation_fee, settlement_fee, reporting_fee_rate, market_creator_fee_rate,
      market_creator_fees_balance, market_creator_mailbox,
      market_creator_mailbox_owner, initial_report_size, category, tags, volume,
      open_interest, outstanding_shares, reporting_state, forking,
      needs_migration, fee_window, end_time, finalization_block_int,
      finalization_time, last_trade_block_int, last_trade_time, description,
      details, scalar_denomination, designated_reporter,
      designated_report_stake, resolution_source, num_ticks, tick_size,
      consensus, outcomes):
    self._id = id
    self._universe = universe
    self._market_type = market_type
    self._num_outcomes = num_outcomes
    self._min_price = min_price
    self._max_price = max_price
    self._cumulative_scale = cumulative_scale
    self._author = author
    self._creation_time = creation_time
    self._creation_block = creation_block
    self._creation_fee = creation_fee
    self._settlement_fee = settlement_fee
    self._reporting_fee_rate = reporting_fee_rate
    self._market_creator_fee_rate = market_creator_fee_rate
    self._market_creator_fees_balance = market_creator_fees_balance
    self._market_creator_mailbox = market_creator_mailbox
    self._market_creator_mailbox_owner = market_creator_mailbox_owner
    self._initial_report_size = initial_report_size
    self._category = category
    self._tags = tags
    self._volume = volume
    self._open_interest = open_interest
    self._outstanding_shares = outstanding_shares
    self._reporting_state = reporting_state
    self._forking = forking
    self._needs_migration = needs_migration
    self._fee_window = fee_window
    self._end_time = end_time
    self._finalization_block_int = finalization_block_int
    self._finalization_time = finalization_time
    self._last_trade_block_int = last_trade_block_int
    self._last_trade_time = last_trade_time
    self._description = description
    self._details = details
    self._scalar_denomination = scalar_denomination
    self._designated_reporter = designated_reporter
    self._designated_report_stake = designated_report_stake
    self._resolution_source = resolution_source
    self._num_ticks = num_ticks
    self._tick_size = tick_size
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
  def market_type(self):
    '''Type of Market ("yesNo", "categorical", or "scalar").

    Returns str
    '''
    return self._market_type

  @property
  def num_outcomes(self):
    '''Total possible Outcomes for the Market.

    Returns int
    '''
    return self._num_outcomes

  @property
  def min_price(self):
    '''Minimum price allowed for a share on a Market, in ETH. For Yes/No &
    Categorical Markets, this is 0 ETH. For Scalar Markets, this is the bottom
    end of the range set by the Market creator.

    Returns decimal.Decimal
    '''
    return self._min_price

  @property
  def max_price(self):
    '''Maximum price allowed for a share on a Market, in ETH. For Yes/No &
    Categorical Markets, this is 1 ETH. For Scalar Markets, this is the top end
    of the range set by the Market creator.

    Returns decimal.Decimal
    '''
    return self._max_price

  @property
  def cumulative_scale(self):
    '''Difference between maxPrice and minPrice.

    Returns decimal.Decimal
    '''
    return self._cumulative_scale

  @property
  def author(self):
    '''Ethereum address of the creator of the Market, as a hexadecimal str.

    Returns str
    '''
    return self._author

  @property
  def creation_time(self):
    '''Timestamp when the Ethereum block containing the Market creation was
    created, in seconds.

    Returns datetime.datetime
    '''
    return self._creation_time

  @property
  def creation_block(self):
    '''Number of the Ethereum block containing the Market creation.

    Returns int
    '''
    return self._creation_block

  @property
  def creation_fee(self):
    '''Fee paid by the Market Creator to create the Market, in ETH.

    Returns decimal.Decimal
    '''
    return self._creation_fee

  @property
  def settlement_fee(self):
    '''Fee extracted when a Complete Set is Settled. It is the combination of
    the Creator Fee and the Reporting Fee.

    Returns decimal.Decimal
    '''
    return self._settlement_fee

  @property
  def reporting_fee_rate(self):
    '''Percentage rate of ETH sent to the Fee Window containing the Market
    whenever shares are settled. Reporting Fees are later used to pay REP
    holders for Reporting on the Outcome of Markets.

    Returns decimal.Decimal
    '''
    return self._reporting_fee_rate

  @property
  def market_creator_fee_rate(self):
    '''Percentage rate of ETH paid to the Market creator whenever shares are
    settled.

    Returns decimal.Decimal
    '''
    return self._market_creator_fee_rate

  @property
  def market_creator_fees_balance(self):
    '''Amount of claimable fees the Market creator has not collected from the
    Market, in ETH.

    Returns decimal.Decimal
    '''
    return self._market_creator_fees_balance

  @property
  def market_creator_mailbox(self):
    '''Ethereum address of the Market Creator, as a hexadecimal str.

    Returns str
    '''
    return self._market_creator_mailbox

  @property
  def market_creator_mailbox_owner(self):
    '''Ethereum address of the Market Creator Mailbox, as a hexadecimal str.

    Returns str
    '''
    return self._market_creator_mailbox_owner

  @property
  def initial_report_size(self):
    '''Size of the No-Show Bond (if the Initial Report was submitted by a First
    Public Reporter instead of the Designated Reporter).

    Returns decimal.Decimal or None
    '''
    return self._initial_report_size

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
  def open_interest(self):
    '''Open interest for the Market.

    Returns decimal.Decimal
    '''
    return self._open_interest

  @property
  def outstanding_shares(self):
    '''Number of Complete Sets in the Market.

    Returns decimal.Decimal
    '''
    return self._outstanding_shares

  @property
  def reporting_state(self):
    '''Reporting state name.

    Returns REPORTING_STATE or None
    '''
    return self._reporting_state

  @property
  def forking(self):
    '''Whether the Market has Forked.

    Returns bool
    '''
    return self._forking

  @property
  def needs_migration(self):
    '''Whether the Market needs to be migrated to its Universe's Child Universe
    (i.e., the Market is not Finalized, and the Forked Market in its Universe is
    Finalized).

    Returns bool
    '''
    return self._needs_migration

  @property
  def fee_window(self):
    '''Contract address of the Fee Window the Market is in, as a hexadecimal
    str.

    Returns str
    '''
    return self._fee_window

  @property
  def end_time(self):
    '''Timestamp when the Market event ends, in seconds.

    Returns datetime.datetime
    '''
    return self._end_time

  @property
  def finalization_block_int(self):
    '''Ethereum block int in which the Market was Finalized.

    Returns int or None
    '''
    return self._finalization_block_int

  @property
  def finalization_time(self):
    '''Timestamp when the Market was finalized (if any), in seconds.

    Returns datetime.datetime or None
    '''
    return self._finalization_time

  @property
  def last_trade_block_int(self):
    '''Ethereum block int in which the last trade occurred for this Market.

    Returns int or None
    '''
    return self._last_trade_block_int

  @property
  def last_trade_time(self):
    '''Unix timestamp when the last trade occurred in this Market.

    Returns datetime.datetime or None
    '''
    return self._last_trade_time

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
  def scalar_denomination(self):
    '''Denomination used for the numerical range of a Scalar Market (e.g.,
    dollars, degrees Fahrenheit, parts-per-billion).

    Returns str or None
    '''
    return self._scalar_denomination

  @property
  def designated_reporter(self):
    '''Ethereum address of the Market's designated report, as a hexadecimal
    str.

    Returns str
    '''
    return self._designated_reporter

  @property
  def designated_report_stake(self):
    '''Size of the Designated Reporter Stake, in attoETH, that the Designated
    Reporter must pay to submit the Designated Report for this Market.

    Returns decimal.Decimal
    '''
    return self._designated_report_stake

  @property
  def resolution_source(self):
    '''Reference source used to determine the Outcome of the Market event.

    Returns str or None
    '''
    return self._resolution_source

  @property
  def num_ticks(self):
    '''Number of possible prices, or ticks, between a Market's minimum price and
    maximum price.

    Returns decimal.Decimal
    '''
    return self._num_ticks

  @property
  def tick_size(self):
    '''Smallest recognized amount by which a price of a security or future may
    fluctuate in the Market.

    Returns decimal.Decimal
    '''
    return self._tick_size

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
