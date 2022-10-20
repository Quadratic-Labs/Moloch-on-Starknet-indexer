"""Inherit from `FromEventMixin` to get a free `from_event` method that creates
in instance from a `StarkNetEvent`, the from_event method uses the type hints
given in the dataclass to know how to deserialize the values
"""

from dataclasses import dataclass
from .deserializer import FromEventMixin, BlockNumber


@dataclass
class ProposalAdded(FromEventMixin):
    id: int
    title: str
    type: str
    description: str
    submittedAt: BlockNumber
    submittedBy: bytes


@dataclass
class OnboardProposalAdded(FromEventMixin):
    id: int
    address: bytes
    shares: int
    loot: int
    tributeOffered: int
    tributeAddress: bytes
