from enum import Enum

import strawberry


class ProposalRawStatus(Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    # Can proceed to execution if any actions
    REJECTED = "rejected"
    # Sent directly to grace period by admin
    FORCED = "forced"


@strawberry.enum
class ProposalStatus(Enum):
    VOTING_PERIOD = "Voting Period"
    GRACE_PERIOD = "Grace Period"
    REJECTED_READY = "Rejected - Ready to Process"
    APPROVED_READY = "Approved - Ready to Process"
    REJECTED = "Rejected"
    APPROVED = "Approved"
    UNKNOWN = "Unknown"

    @property
    def is_active(self):
        return self in [
            ProposalStatus.VOTING_PERIOD,
            ProposalStatus.GRACE_PERIOD,
            ProposalStatus.REJECTED_READY,
            ProposalStatus.APPROVED_READY,
        ]
