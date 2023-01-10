from . import common
from .members import MEMBERS
from .proposals import PROPOSALS


def delete_dict_key(d: dict, key) -> dict:
    """Delete ~`key` from the given dict and return the new dict"""
    d = d.copy()
    d.pop(key, None)
    return d


# proposals
PROPOSAL_TYPE_MISMATCH = [
    {"id": "1"},  # should be int
    {"type": 1},  # should be string
    {"link": b"0x1"},  # should be string
    {"submittedAt": True},  # should be date
    {"submittedBy": "0x1"},  # should be binData
    {"majority": 1.0},  # should be int
    {"quorum": True},  # should be int
    {"graceDuration": {}},  # should be int
    {"votingDuration": ""},  # should be int
    {"tributeAddress": 0},  # should be binData
    {"tributeOffered": True},  # should be int
    {"rawStatus": {}},  # should be string,
    {"rawStatusHistory": {}},  # should be array of tuple(string, date)
    {
        "rawStatusHistory": [[1, common.START_TIME]]
    },  # should be array of tuple(string, date)
    {"yesVoters": ["0x1"]},  # should be array of binData
    {"yesVoters": [b"0x1", None]},  # should be array of tuple(string, date)
    {"noVoters": ["0x2"]},  # should be array of binData
    {"noVoters": [b"0x2", None]},  # should be array of tuple(string, date)
    {"rawStatusHistory": [[1, common.START_TIME]]},
    {"applicantAddress": []},  # should be binData
    {"shares": True},  # should be int
    {"loot": None},  # should be int
    {"tributeOffered": {}},  # should be int
    {"tributeAddress": None},  # should be binData
    {"memberAddress": "0x1"},  # should be binData
    {"tokenName": b"Some name"},  # should be string
    {"tokenAddress": 1},  # should be binData
    {"paymentRequested": True},  # should be int
    {"paymentAddress": 1},  # should be binData
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
    {
        "rawStatusHistory": [[1, common.START_TIME], [1, common.START_TIME]]
    },  # should be unique
]


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
    "rawStatus",
    "rawStatusHistory",
]

# Create a test data by removing a required field from a valid proposal at a time
PROPOSAL_MISSING_REQUIRED = [
    delete_dict_key(PROPOSALS[0], required_field)
    for required_field in PROPOSAL_REQUIRED_FIELDS
]


# proposal_params
PROPOSAL_PARAMS_TYPE_MISMATCH = [
    {"type": 1},  # should be string
    {"majority": 1.0},  # should be int
    {"quorum": True},  # should be int
    {"graceDuration": {}},  # should be int
    {"votingDuration": ""},  # should be int
]


PROPOSAL_PARAMS_WRONG_VALUES = [
    {"majority": -10},  # should be >= 0
    {"quorum": -2},  # should be >= 0
    {"majority": 120},  # should be =< 100
    {"quorum": 120},  # should be =< 100
    {"graceDuration": -15},  # should be >= 0
    {"votingDuration": -7},  # should be >= 0
]


PROPOSAL_PARAMS_REQUIRED_FIELDS = [
    "type",
    "majority",
    "quorum",
    "votingDuration",
    "graceDuration",
]

# Create a test data by removing a required field from a valid proposal at a time
PROPOSAL_PARAMS_MISSING_REQUIRED = [
    delete_dict_key(PROPOSALS[0], required_field)
    for required_field in PROPOSAL_PARAMS_REQUIRED_FIELDS
]

# members
MEMBER_TYPE_MISMATCH = [
    {"memberAddress": "0x1"},  # should be binData
    {"delegateAddress": []},  # should be binData
    {"shares": True},  # should be int
    {"loot": None},  # should be int
    {"onboardedAt": True},  # should be date
    {"jailedAt": True},  # should be date
    {"exitedAt": True},  # should be date
    {"roles": {}},  # should be array of array of string
    {"roles": ["admin", None]},  # should be array of string
    {"yesVotes": {}},  # should be array of int
    {"yesVotes": [1, "2", None]},  # should be array of int
    {"noVotes": True},  # should be array of int
    {"noVotes": [True, 1, None]},  # should be array of int
    {
        "balances": [{"tokenName": 1, "tokenAddress": b"0x1"}]
    },  # tokenName should be string
    {
        "balances": [{"tokenName": "SomeToken", "tokenAddress": "0x1"}]
    },  # tokenAddress should be binData
    {
        "transactions": [
            {"tokenAddress": "0x1", "timestamp": common.START_TIME, "amount": 10}
        ]
    },  # tokenAddress should be binData
    {
        "transactions": [{"tokenAddress": b"0x1", "timestamp": 1, "amount": 10}]
    },  # timestamp should be int
    {
        "transactions": [
            {"tokenAddress": b"0x1", "timestamp": common.START_TIME, "amount": "5"}
        ]
    },  # amount should be int
]


MEMBER_WRONG_VALUES = [
    {"shares": -1},  # should be >= 0
    {"loot": -5},  # should be >= 0
    {"roles": ["admin", "admin"]},  # should be unique
    {"yesVotes": [1, 1]},  # should be unique
    {"noVotes": [2, 2]},  # should be unique
]

MEMBER_REQUIRED_FIELDS = [
    "memberAddress",
    "delegateAddress",
    "shares",
    "loot",
    "onboardedAt",
]

# Create a test data by removing a required field from a valid member at a time
MEMBER_MISSING_REQUIRED = [
    delete_dict_key(MEMBERS[0], required_field)
    for required_field in MEMBER_REQUIRED_FIELDS
] + [
    {"balances": [{"tokenAddress": b"0x1"}]},
    {"balances": [{"tokenName": 1}]},
    {"transactions": [{"tokenAddress": b"0x1"}]},
    {"transactions": [{"amount": 1}]},
    {"transactions": [{"timestamp": common.START_TIME}]},
]

# bank
BANK_TYPE_MISMATCH = [
    {"bankAddress": "0x1"},  # should be binData
    {"whitelistedTokens": {}},  # should be array of objects
    {"unWhitelistedTokens": True},  # should be array of objects
    {
        "whitelistedTokens": [
            {
                "tokenName": 1,
                "tokenAddress": b"0x1",
                "whitelistedAt": common.START_TIME,
            }
        ]
    },  # tokenName should be string
    {
        "whitelistedTokens": [
            {
                "tokenName": "SomeToken",
                "tokenAddress": "0x1",
                "whitelistedAt": common.START_TIME,
            },
        ]
    },  # tokenAddress should be binData
    {
        "whitelistedTokens": [
            {
                "tokenName": "SomeToken",
                "tokenAddress": b"0x1",
                "whitelistedAt": True,
            },
        ]
    },  # whitelistedAt should be date
    {
        "unWhitelistedTokens": [
            {
                "tokenName": 5,
                "tokenAddress": b"0x5",
                "unWhitelistedAt": common.START_TIME,
            }
        ]
    },  # tokenName should be string
    {
        "unWhitelistedTokens": [
            {
                "tokenName": "SomeOtherToken",
                "tokenAddress": "0x5",
                "unWhitelistedAt": common.START_TIME,
            },
        ]
    },  # tokenAddress should be binData
    {
        "unWhitelistedTokens": [
            {
                "tokenName": "SomeOtherToken",
                "tokenAddress": b"0x5",
                "unWhitelistedAt": 1.0,
            },
        ]
    },  # unWhitelistedAt should be date
    {
        "balances": [{"tokenName": 1, "tokenAddress": b"0x1"}]
    },  # tokenName should be string
    {
        "balances": [{"tokenName": "SomeToken", "tokenAddress": "0x1"}]
    },  # tokenAddress should be binData
    {
        "transactions": [
            {"tokenAddress": "0x1", "timestamp": common.START_TIME, "amount": 10}
        ]
    },  # tokenAddress should be binData
    {
        "transactions": [{"tokenAddress": b"0x1", "timestamp": 1, "amount": 10}]
    },  # timestamp should be int
    {
        "transactions": [
            {"tokenAddress": b"0x1", "timestamp": common.START_TIME, "amount": "5"}
        ]
    },  # amount should be int
]

BANK_WRONG_VALUES = [
    {
        "whitelistedTokens": [
            {
                "tokenName": "SomeToken",
                "tokenAddress": b"0x1",
                "whitelistedAt": common.START_TIME,
            },
            {
                "tokenName": "SomeToken",
                "tokenAddress": b"0x1",
                "whitelistedAt": common.START_TIME,
            },
        ]
    },  # should be unique
    {
        "unWhitelistedTokens": [
            {
                "tokenName": "SomeOtherToken",
                "tokenAddress": b"0x2",
                "unWhitelistedAt": common.START_TIME,
            },
            {
                "tokenName": "SomeOtherToken",
                "tokenAddress": b"0x2",
                "unWhitelistedAt": common.START_TIME,
            },
        ]
    },  # should be unique
]

# Create a test data by removing a required field from a valid member at a time
BANK_MISSING_REQUIRED = [
    {},  # missing bankAddress
    {"balances": [{"tokenAddress": b"0x1"}]},
    {"balances": [{"tokenName": 1}]},
    {"transactions": [{"tokenAddress": b"0x1", "timestamp": common.START_TIME}]},
    {"transactions": [{"tokenAddress": b"0x1", "amount": 1}]},
    {"transactions": [{"amount": 1, "timestamp": common.START_TIME}]},
    {
        "whitelistedTokens": [
            {
                "tokenName": "SomeOtherToken",
                "tokenAddress": b"0x2",
            },
        ]
    },
    {
        "whitelistedTokens": [
            {
                "tokenName": "SomeOtherToken",
                "whitelistedAt": common.START_TIME,
            },
        ]
    },
    {
        "whitelistedTokens": [
            {
                "tokenAddress": b"0x2",
                "whitelistedAt": common.START_TIME,
            },
        ]
    },
    {
        "unWhitelistedTokens": [
            {
                "tokenName": "SomeOtherToken",
                "tokenAddress": b"0x2",
            },
        ]
    },
    {
        "unWhitelistedTokens": [
            {
                "tokenName": "SomeOtherToken",
                "unWhitelistedAt": common.START_TIME,
            },
        ]
    },
    {
        "unWhitelistedTokens": [
            {
                "tokenAddress": b"0x2",
                "unWhitelistedAt": common.START_TIME,
            },
        ]
    },
]
