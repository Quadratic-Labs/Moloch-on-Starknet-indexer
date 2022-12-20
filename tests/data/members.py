from . import common

MEMBERS = [
    {
        "memberAddress": common.ADDRESSES[0].bytes,
        "delegateAddress": common.ADDRESSES[1].bytes,
        "onboardedAt": common.START_TIME,
        "shares": 7,
        "loot": 5,
        "jailedAt": None,
        "exitedAt": None,
        "balances": [
            {
                "tokenAddress": common.TOKEN_ADDRESS.bytes,
                "tokenName": common.TOKEN_NAME,
                "amount": common.AMOUNT,
            }
        ],
        "transactions": [
            {
                "tokenAddress": common.TOKEN_ADDRESS.bytes,
                "timestamp": common.START_TIME,
                "amount": common.AMOUNT,
            }
        ],
    },
    {
        "memberAddress": common.ADDRESSES[1].bytes,
        "delegateAddress": common.ADDRESSES[0].bytes,
        "onboardedAt": common.START_TIME,
        "shares": 8,
        "loot": 5,
        "jailedAt": common.VOTING_PERIOD_ENDING_AT,
        "exitedAt": None,
        "balances": [],
        "transactions": [],
        "roles": [],
    },
    {
        "memberAddress": common.ADDRESSES[2].bytes,
        "onboardedAt": common.START_TIME,
        "shares": 2,
        "loot": 2,
        "jailedAt": None,
        "exitedAt": common.VOTING_PERIOD_ENDING_AT,
        "roles": ["admin"],
    },
    {
        "memberAddress": common.ADDRESSES[3].bytes,
        "onboardedAt": common.START_TIME,
        "shares": 3,
        "loot": 3,
        "jailedAt": common.VOTING_PERIOD_ENDING_AT,
        "exitedAt": common.VOTING_PERIOD_ENDING_AT,
        "roles": ["admin", "govern"],
    },
    {
        "memberAddress": common.ADDRESSES[4].bytes,
        "onboardedAt": common.START_TIME,
        "shares": 5,
        "loot": 0,
    },
]
