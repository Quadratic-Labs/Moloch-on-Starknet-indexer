from datetime import timedelta

from pymongo import MongoClient
from pytest import MonkeyPatch

from indexer import storage, utils
from indexer.graphql import Proposal, schema
from indexer.models import ProposalRawStatus, ProposalStatus

from .data import data, graphql_queries


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

    info = None

    assert proposal.votingPeriodEndingAt() == votingPeriodEndingAt
    assert proposal.gracePeriodEndingAt() == gracePeriodEndingAt

    assert proposal.approvedAt(info) is None
    assert proposal.rejectedAt(info) is None
    assert proposal.approvedToProcessAt(info) is None
    assert proposal.rejectedToProcessAt(info) is None

    assert proposal._get_raw_status_time(ProposalRawStatus.FORCED) is None

    # Proposal is at voting period since voting duration hasn't ended yet
    assert proposal.status(info) == ProposalStatus.VOTING_PERIOD
    assert proposal.active(info) is True
    now = utils.utcnow()
    monkeypatch.setattr(utils, "utcnow", lambda: now)
    assert proposal.timeRemaining(info) == int(
        (now - votingPeriodEndingAt).total_seconds()
    )

    # After the voting period, the proposal should be rejected ready to process
    # since the quorum and majority conditions aren't met
    monkeypatch.setattr(utils, "utcnow", lambda: votingPeriodEndingAt)
    assert proposal.status(info) == ProposalStatus.REJECTED_READY
    assert proposal.active(info) is True
    assert proposal.rejectedToProcessAt(info) == votingPeriodEndingAt
    assert proposal.timeRemaining(info) is None

    # When the majority and quorum conditions are met, the proposal should be
    # in grace period until the current time is gracePeriodEndingAt
    proposal.currentMajority = lambda: proposal.majority
    proposal.currentQuorum = lambda info: proposal.quorum
    assert proposal.status(info) == ProposalStatus.GRACE_PERIOD
    assert proposal.active(info) is True
    now = utils.utcnow()
    monkeypatch.setattr(utils, "utcnow", lambda: now)
    assert proposal.timeRemaining(info) == int(
        (now - gracePeriodEndingAt).total_seconds()
    )

    # After the grace period, the proposal should be approved ready to process
    # since the quorum and majority conditions are met
    monkeypatch.setattr(utils, "utcnow", lambda: gracePeriodEndingAt)
    assert proposal.status(info) == ProposalStatus.APPROVED_READY
    assert proposal.active(info) is True
    assert proposal.approvedToProcessAt(info) == gracePeriodEndingAt
    assert proposal.timeRemaining(info) is None

    # simulate ProposalStatusUpdated with status=ACCEPTED
    proposal.rawStatus = ProposalRawStatus.APPROVED.value
    approvedAt = utils.utcnow()
    proposal.rawStatusHistory.append((ProposalRawStatus.APPROVED.value, approvedAt))
    assert proposal.status(info) == ProposalStatus.APPROVED
    assert proposal.active(info) is False
    assert proposal.approvedAt(info) == approvedAt
    assert proposal.processedAt(info) == approvedAt
    assert proposal.timeRemaining(info) is None

    # simulate ProposalStatusUpdated with status=REJECTED
    proposal.rawStatus = ProposalRawStatus.REJECTED.value
    rejectedAt = utils.utcnow()
    proposal.rawStatusHistory.append((ProposalRawStatus.REJECTED.value, rejectedAt))
    assert proposal.status(info) == ProposalStatus.REJECTED
    assert proposal.active(info) is False
    assert proposal.rejectedAt(info) == rejectedAt
    assert proposal.processedAt(info) == rejectedAt
    assert proposal.timeRemaining(info) is None

    proposal.rawStatus = ProposalRawStatus.FORCED.value
    assert proposal.status(info) == ProposalStatus.UNKNOWN


def test_proposal_member_did_vote():
    proposal = test_proposal_basic()

    memberAddress = "0x0"
    assert proposal.memberDidVote(memberAddress) is False

    proposal.noVoters = []
    proposal.yesVoters.append(memberAddress)
    assert proposal.memberDidVote(memberAddress) is True

    proposal.yesVoters = []
    proposal.noVoters.append(memberAddress)
    assert proposal.memberDidVote(memberAddress) is True


def test_proposal_memeber_did_vote():
    proposal = test_proposal_basic()

    memberAddress = "0x0"
    assert proposal.memberCanVote(memberAddress) is True


def test_proposal_majority_quorum(monkeypatch: MonkeyPatch):
    proposal = test_proposal_basic()

    info = None

    monkeypatch.setattr(
        storage, "list_votable_members", lambda info, *args, **kwargs: []
    )

    assert proposal.currentMajority() == 0
    assert proposal.currentQuorum(info) == 0
    assert proposal.yesVotesTotal() == 0
    assert proposal.noVotesTotal() == 0

    now = utils.utcnow()

    yesVotersMembers = [
        {"memberAddress": "0x0", "shares": 10, "loot": 0, "onboardedAt": now},
        {"memberAddress": "0x1", "shares": 3, "loot": 0, "onboardedAt": now},
        {"memberAddress": "0x2", "shares": 1, "loot": 0, "onboardedAt": now},
        {"memberAddress": "0x3", "shares": 1, "loot": 0, "onboardedAt": now},
    ]
    noVotersMembers = [
        {"memberAddress": "0x10", "shares": 2, "loot": 0, "onboardedAt": now},
        {"memberAddress": "0x20", "shares": 1, "loot": 0, "onboardedAt": now},
        {"memberAddress": "0x30", "shares": 2, "loot": 0, "onboardedAt": now},
    ]

    otherMembers = [
        {"memberAddress": "0x100", "shares": 4, "loot": 0, "onboardedAt": now},
        {"memberAddress": "0x200", "shares": 1, "loot": 0, "onboardedAt": now},
    ]

    members = yesVotersMembers + noVotersMembers + otherMembers

    monkeypatch.setattr(
        storage, "list_votable_members", lambda info, *args, **kwargs: members
    )

    proposal.yesVoters = [member["memberAddress"] for member in yesVotersMembers]

    proposal.yesVotersMembers = yesVotersMembers

    proposal.noVoters = [member["memberAddress"] for member in noVotersMembers]
    proposal.noVotersMembers = noVotersMembers

    assert proposal.currentQuorum(info) == 80
    assert proposal.totalVotableShares(info) == 25
    assert proposal.currentMajority() == 75


def test_empty_query(mongomock_client: MongoClient):
    context_value = {"db": mongomock_client.db}

    query = """
        query Proposals {
            proposals {
                id
            }
        }
    """

    result = schema.execute_sync(query, context_value=context_value)

    assert result.errors is None
    assert result.data["proposals"] == []


def test_proposals_query(mongomock_client: MongoClient):
    context_value = {"db": mongomock_client.db}

    mongomock_client.db.proposals.insert_many(data.PROPOSALS)
    mongomock_client.db.members.insert_many(data.MEMBERS)

    result = schema.execute_sync(
        graphql_queries.LIST_PROPOSALS, context_value=context_value
    )

    assert result.errors is None
    assert result.data["proposals"] == data.LIST_PROPOSALS_GRAPHQL_QUERY_EXPECTED_RESULT


def test_members_query(mongomock_client: MongoClient):
    context_value = {"db": mongomock_client.db}

    mongomock_client.db.members.insert_many(data.MEMBERS)

    result = schema.execute_sync(
        graphql_queries.LIST_MEMBERS, context_value=context_value
    )

    assert result.errors is None
    assert result.data["members"] == data.LIST_MEMBERS_GRAPHQL_QUERY_EXPECTED_RESULT
