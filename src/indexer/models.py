from enum import IntEnum


class ProposalStatus(IntEnum):
    SUBMITTED = 1
    ACCEPTED = 2
    # Can proceed to execution if any actions
    REJECTED = 3
    FORCED = 7
    # Sent directly to grace period by admin
    # The remaining states are final
    ABORTED = 4
    # Did not go completely through voting
    EXECUTED = 5
    # Execution is finalised and successful
    FAILED = 6
    # Execution failed
    NOTFOUND = -1
