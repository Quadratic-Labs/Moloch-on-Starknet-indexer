from . import common

PROPOSAL = {
    "id": 1,
    "title": "Test Signaling Proposal",
    "type": "Signaling",
    "link": "https://link.somewhere",
    "submittedBy": b"0x1",
    "submittedAt": common.START_TIME,
    "majority": 50,
    "quorum": 50,
    "graceDuration": 10,
    "votingDuration": 10,
    "status": "submitted",
    "statusHistory": [["submitted", common.START_TIME]],
    "applicantAddress": b"0x2",
    "shares": 5,
    "loot": 0,
    "tributeOffered": 1,
    "tributeAddress": b"0x2",
    "memberAddress": b"0x1",
    "tokenName": "Some name",
    "tokenAddress": b"0x3",
    "paymentRequested": 0,
}

PROPOSAL_TYPE_MISMATCH = [
    {"id": "1"},  # should be int
    {"type": 1},  # should be string
    {"link": b"0x1"},  # should be string
    {"submittedAt": True},  # should be date
    {"submittedBy": "0x1"},  # should be binData (Python bytes)
    {"tributeAddress": 0},  # should be binData (Python bytes)
    {"tributeOffered": True},  # should be int
    {"status": {}},  # should be string,
    {"statusHistory": {}},  # should be array of tuple(string, date)
    {
        "statusHistory": [[1, common.START_TIME]]
    },  # should be array of tuple(string, date)
    {"applicantAddress": []},  # should be binData (Python bytes)
    {"shares": True},  # should be int
    {"loot": None},  # should be int
    {"tributeOffered": {}},  # should be int
    {"tributeAddress": None},  # should be binData (Python bytes)
    {"memberAddress": "0x1"},  # should be binData (Python bytes)
    {"tokenName": b"Some name"},  # should be string
    {"tokenAddress": 1},  # should be binData (Python bytes)
    {"paymentRequested": True},  # should be int
    {"paymentAddress": 1},  # should be binData (Python bytes)
]


PROPOSAL_WRONG_VALUES = [
    {"shares": -1},  # should be >= 0
    {"loot": -5},  # should be >= 0
    {"majority": -10},  # should be >= 0
    {"quorum": -2},  # should be >= 0
    {"majority": 120},  # should be =< 100
    {"quorum": 120},  # should be =< 100
    {"graceDuration": -15},  # should be >= 0
    {"votingDuration": -7},  # should be >= 0
    {"paymentRequested": -1},  # should be >= 0
    {"tributeOffered": -1},  # should be >= 0
]


def delete_dict_key(d: dict, key) -> dict:
    """Delete ~`key` from the given dict and return the new dict"""
    d = d.copy()
    d.pop(key, None)
    return d


PROPOSAL_REQUIRED_FIELDS = [
    "id",
    "title",
    "type",
    "link",
    "submittedAt",
    "submittedBy",
    "majority",
    "quorum",
    "votingDuration",
    "graceDuration",
    "status",
    "statusHistory",
]

# Create a test data by removing a required field at a time
PROPOSAL_MISSING_REQUIRED = [
    delete_dict_key(PROPOSAL, required_field)
    for required_field in PROPOSAL_REQUIRED_FIELDS
]
