from enum import Enum, auto

class ReportingState(Enum):
  '''Serves as an enum for the state of a Market.'''

  '''Market’s end time has not yet come to pass.'''
  PRE_REPORTING = auto()

  '''Market’s end time has occurred, and it is pending a Designated Report.'''
  DESIGNATED_REPORTING = auto()

  '''The Designated Reporter failed to submit a Designated Report within the
  allotted time, causing the Market to enter the Open Reporting Phase.'''
  OPEN_REPORTING = auto()

  '''An Initial Report for the Market has been submitted, and the Market’s
  Tentative Outcome is open to being Disputed.'''
  CROWDSOURCING_DISPUTE = auto()

  '''Either the Market had an Initial Report submitted in the current Fee
  Window, or one of the Market’s Dispute Crowdsourcers received enough REP to
  Challenge the Market’s Tentative Outcome. In either case, the Market is
  awaiting the next Fee Window in order to enter another Dispute Round.'''
  AWAITING_NEXT_WINDOW = auto()

  '''The Market has been Finalized, but the Post-Finalization Waiting Period
  has not elapsed.'''
  AWAITING_FINALIZATION = auto()

  '''An Outcome for the Market has been determined.'''
  FINALIZED = auto()

  '''The Dispute Crowdsourcer for one of the Market’s Outcomes received enough
  REP to reach the Fork Threshold, causing a fork. Users can migrate their REP
  to the Universe of their choice.'''
  FORKING = auto()

  '''Either the Designated Report was Disputed, or the Designated Reporter
  failed to submit a Report, and the Market is waiting for the next reporting
  phase to begin.'''
  AWAITING_NO_REPORT_MIGRATION = auto()

  '''Market is waiting for another Market’s Fork to be resolved. This means its
  Tentative Outcome has been reset to the Outcome submitted in the Initial
  Report, and all Stake in the Market’s Dispute Crowdsourcers has been refunded
  to the users who Staked on them.'''
  AWAITING_FORK_MIGRATION = auto()
