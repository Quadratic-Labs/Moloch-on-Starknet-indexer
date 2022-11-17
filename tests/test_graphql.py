from datetime import timedelta

from indexer.graphql import Proposal
from indexer.models import ProposalStatus, ProposalRawStatus
from indexer import utils

from pytest import MonkeyPatch


def test_proposal_basic():
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
    rawStatusHistory = [(rawStatus, submittedAt)]

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

    assert proposal.id == id_
    assert proposal.title == title
    assert proposal.type == type_
    assert proposal.link == link
    assert proposal.submittedAt == submittedAt
    assert proposal.submittedBy == submittedBy
    assert proposal.majority == majority
    assert proposal.quorum == quorum
    assert proposal.votingDuration == votingDuration
    assert proposal.graceDuration == graceDuration
    assert proposal.yesVoters == yesVoters
    assert proposal.noVoters == noVoters
    assert proposal.yesVotersMembers == yesVotersMembers
    assert proposal.noVotersMembers == noVotersMembers
    assert proposal.rawStatus == rawStatus
    assert proposal.rawStatusHistory == rawStatusHistory

    return proposal


def test_proposal_status(monkeypatch: MonkeyPatch):
    proposal = test_proposal_basic()

    votingPeriodEndingAt = proposal.submittedAt + timedelta(
        minutes=proposal.votingDuration
    )
    gracePeriodEndingAt = votingPeriodEndingAt + timedelta(
        minutes=proposal.graceDuration
    )

    assert proposal.votingPeriodEndingAt() == votingPeriodEndingAt
    assert proposal.gracePeriodEndingAt() == gracePeriodEndingAt

    assert proposal.approvedAt() == None
    assert proposal.rejectedAt() == None
    assert proposal.approvedToProcessAt() == None
    assert proposal.rejectedToProcessAt() == None

    assert proposal._get_raw_status_time(ProposalRawStatus.FORCED) == None

    # Proposal is at voting period since voting duration hasn't ended yet
    assert proposal.status() == ProposalStatus.VOTING_PERIOD
    assert proposal.active() == True
    now = utils.utcnow()
    monkeypatch.setattr(utils, "utcnow", lambda: now)
    assert proposal.timeRemaining() == int((now - votingPeriodEndingAt).total_seconds())

    # After the voting period, the proposal should be rejected ready to process
    # since the quorum and majority conditions aren't met
    monkeypatch.setattr(utils, "utcnow", lambda: votingPeriodEndingAt)
    assert proposal.status() == ProposalStatus.REJECTED_READY
    assert proposal.active() == True
    assert proposal.rejectedToProcessAt() == votingPeriodEndingAt
    assert proposal.timeRemaining() == None

    # When the majority and quorum conditions are met, the proposal should be
    # in grace period until the current time is gracePeriodEndingAt
    proposal.currentMajority = lambda: proposal.majority
    proposal.currentQuorum = lambda: proposal.quorum
    assert proposal.status() == ProposalStatus.GRACE_PERIOD
    assert proposal.active() == True
    now = utils.utcnow()
    monkeypatch.setattr(utils, "utcnow", lambda: now)
    assert proposal.timeRemaining() == int((now - gracePeriodEndingAt).total_seconds())

    # After the grace period, the proposal should be approved ready to process
    # since the quorum and majority conditions are met
    monkeypatch.setattr(utils, "utcnow", lambda: gracePeriodEndingAt)
    assert proposal.status() == ProposalStatus.APPROVED_READY
    assert proposal.active() == True
    assert proposal.approvedToProcessAt() == gracePeriodEndingAt
    assert proposal.timeRemaining() == None

    # simulate ProposalStatusUpdated with status=ACCEPTED
    proposal.rawStatus = ProposalRawStatus.ACCEPTED.value
    approvedAt = utils.utcnow()
    proposal.rawStatusHistory.append((ProposalRawStatus.ACCEPTED.value, approvedAt))
    assert proposal.status() == ProposalStatus.APPROVED
    assert proposal.active() == False
    assert proposal.approvedAt() == approvedAt
    assert proposal.processedAt() == approvedAt
    assert proposal.timeRemaining() == None

    # simulate ProposalStatusUpdated with status=REJECTED
    proposal.rawStatus = ProposalRawStatus.REJECTED.value
    rejectedAt = utils.utcnow()
    proposal.rawStatusHistory.append((ProposalRawStatus.REJECTED.value, rejectedAt))
    assert proposal.status() == ProposalStatus.REJECTED
    assert proposal.active() == False
    assert proposal.rejectedAt() == rejectedAt
    assert proposal.processedAt() == rejectedAt
    assert proposal.timeRemaining() == None

    proposal.rawStatus = ProposalRawStatus.FORCED.value
    proposal.status() == ProposalStatus.UNKNOWN


def test_proposal_member_did_vote():
    proposal = test_proposal_basic()

    memberAddress = "0x0"
    assert proposal.memberDidVote(memberAddress) == False

    proposal.noVoters = []
    proposal.yesVoters.append(memberAddress)
    assert proposal.memberDidVote(memberAddress) == True

    proposal.yesVoters = []
    proposal.noVoters.append(memberAddress)
    assert proposal.memberDidVote(memberAddress) == True


def test_proposal_memeber_did_vote():
    proposal = test_proposal_basic()

    memberAddress = "0x0"
    assert proposal.memberCanVote(memberAddress) == True


def test_proposal_majority_quorum():
    proposal = test_proposal_basic()

    assert proposal.currentMajority() == 0
    assert proposal.yesVotesTotal() == 0
    assert proposal.noVotesTotal() == 0
    # need info param and database (or mock) to get members
    # assert proposal.currentQuorum() == 0
    # assert proposal.totalVotableShares() == 0
