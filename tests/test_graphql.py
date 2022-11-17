from datetime import timedelta

from indexer.graphql import Proposal
from indexer.models import ProposalStatus, ProposalRawStatus
from indexer import utils

from pytest import MonkeyPatch


def test_proposal_status(monkeypatch: MonkeyPatch):
    id_ = 1
    title = "Test Proposal"
    type_ = "TestType"
    link = "Test Link"
    submittedAt = utils.utcnow()
    submittedBy = "0x0"
    majority = 60
    quorum = 40
    votingDuration = 5
    graceDuration = 5
    yesVoters = []
    noVoters = []
    yesVotersMembers = []
    noVotersMembers = []
    rawStatus = ProposalRawStatus.SUBMITTED.value
    rawStatusHistory = [(submittedAt, rawStatus)]

    proposal = Proposal(
        id=id_,
        title=title,
        type=type_,
        link=link,
        submittedAt=submittedAt,
        submittedBy=submittedBy,
        majority=majority,
        quorum=quorum,
        votingDuration=votingDuration,
        graceDuration=graceDuration,
        yesVoters=yesVoters,
        noVoters=noVoters,
        yesVotersMembers=yesVotersMembers,
        noVotersMembers=noVotersMembers,
        rawStatus=rawStatus,
        rawStatusHistory=rawStatusHistory,
    )

    votingPeriodEndingAt = submittedAt + timedelta(minutes=votingDuration)
    gracePeriodEndingAt = votingPeriodEndingAt + timedelta(minutes=graceDuration)

    assert proposal.id == id_
    assert proposal.submittedAt == submittedAt
    assert proposal.submittedBy == submittedBy
    # TODO: add all other fields
    assert proposal.currentMajority() == 0
    assert proposal.yesVotesTotal() == 0
    assert proposal.noVotesTotal() == 0
    assert proposal.votingPeriodEndingAt() == votingPeriodEndingAt
    assert proposal.gracePeriodEndingAt() == gracePeriodEndingAt
    # need info param and database (or mock) to get members
    # assert proposal.currentQuorum() == 0
    # assert proposal.totalVotableShares() == 0

    assert proposal.status() == ProposalStatus.VOTING_PERIOD
    assert proposal.active() == True

    monkeypatch.setattr(utils, "utcnow", lambda: votingPeriodEndingAt)
    assert proposal.status() == ProposalStatus.REJECTED_READY
    assert proposal.active() == True

    proposal.currentMajority = lambda: majority
    proposal.currentQuorum = lambda: quorum
    assert proposal.status() == ProposalStatus.GRACE_PERIOD
    assert proposal.active() == True

    monkeypatch.setattr(utils, "utcnow", lambda: gracePeriodEndingAt)
    assert proposal.status() == ProposalStatus.APPROVED_READY
    assert proposal.active() == True

    # simulate ProposalStatusUpdated with status=ACCEPTED
    proposal.rawStatus = ProposalRawStatus.ACCEPTED.value
    assert proposal.status() == ProposalStatus.APPROVED
    assert proposal.active() == False

    # simulate ProposalStatusUpdated with status=REJECTED
    proposal.rawStatus = ProposalRawStatus.REJECTED.value
    assert proposal.status() == ProposalStatus.REJECTED
    assert proposal.active() == False
