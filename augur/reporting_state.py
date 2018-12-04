from enum import Enum, auto

class ReportingState(Enum):
  '''Serves as an enum for the state of a Market.'''
  PRE_REPORTING = auto()
  DESIGNATED_REPORTING = auto()
  OPEN_REPORTING = auto()
  CROWDSOURCING_DISPUTE = auto()
  AWAITING_NEXT_WINDOW = auto()
  AWAITING_FINALIZATION = auto()
  FINALIZED = auto()
  FORKING = auto()
  AWAITING_NO_REPORT_MIGRATION = auto()
  AWAITING_FORK_MIGRATION = auto()
