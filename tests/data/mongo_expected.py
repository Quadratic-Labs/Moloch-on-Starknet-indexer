from . import common

LIST_PROPOSALS = [
    {
        "id": 0,
        "title": "Indexer signaling event",
        "link": "Indexer signaling link",
        "type": "Signaling",
        "votingDuration": 60,
        "graceDuration": 120,
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "yesVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[0].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 7,
                "loot": 5,
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
                "onboardedAt": common.START_TIME,
                "shares": 8,
                "loot": 5,
                "balances": [],
                "transactions": [],
            },
        ],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
        "noVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[2].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 2,
                "loot": 5,
            },
            {
                "memberAddress": common.ADDRESSES[3].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 3,
                "loot": 5,
            },
        ],
    },
    {
        "id": 1,
        "title": "Indexer onboard event",
        "link": "Indexer onboard link",
        "type": "Onboard",
        "applicantAddress": common.ADDRESSES[1].bytes,
        "shares": 1,
        "loot": 1,
        "tributeOffered": 1,
        "tributeAddress": common.TOKEN_ADDRESS.bytes,
        "votingDuration": 60,
        "graceDuration": 120,
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "yesVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[0].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 7,
                "loot": 5,
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
                "onboardedAt": common.START_TIME,
                "shares": 8,
                "loot": 5,
                "balances": [],
                "transactions": [],
            },
        ],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
        "noVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[2].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 2,
                "loot": 5,
            },
            {
                "memberAddress": common.ADDRESSES[3].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 3,
                "loot": 5,
            },
        ],
    },
    {
        "id": 2,
        "title": "Indexer guild kick event",
        "link": "Indexer guild kick link",
        "type": "GuildKick",
        "memberAddress": common.ADDRESSES[1].bytes,
        "votingDuration": 60,
        "graceDuration": 120,
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "yesVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[0].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 7,
                "loot": 5,
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
                "onboardedAt": common.START_TIME,
                "shares": 8,
                "loot": 5,
                "balances": [],
                "transactions": [],
            },
        ],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
        "noVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[2].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 2,
                "loot": 5,
            },
            {
                "memberAddress": common.ADDRESSES[3].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 3,
                "loot": 5,
            },
        ],
    },
    {
        "id": 3,
        "title": "Indexer whitelist event",
        "link": "Indexer whitelist link",
        "type": "Whitelist",
        "tokenName": "Some Token",
        "tokenAddress": common.TOKEN_ADDRESS.bytes,
        "votingDuration": 60,
        "graceDuration": 120,
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "yesVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[0].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 7,
                "loot": 5,
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
                "onboardedAt": common.START_TIME,
                "shares": 8,
                "loot": 5,
                "balances": [],
                "transactions": [],
            },
        ],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
        "noVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[2].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 2,
                "loot": 5,
            },
            {
                "memberAddress": common.ADDRESSES[3].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 3,
                "loot": 5,
            },
        ],
    },
    {
        "id": 4,
        "title": "Indexer unwhitelist event",
        "link": "Indexer unwhitelist link",
        "type": "UnWhitelist",
        "tokenName": "Some Token",
        "tokenAddress": common.TOKEN_ADDRESS.bytes,
        "votingDuration": 60,
        "graceDuration": 120,
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "yesVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[0].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 7,
                "loot": 5,
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
                "onboardedAt": common.START_TIME,
                "shares": 8,
                "loot": 5,
                "balances": [],
                "transactions": [],
            },
        ],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
        "noVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[2].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 2,
                "loot": 5,
            },
            {
                "memberAddress": common.ADDRESSES[3].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 3,
                "loot": 5,
            },
        ],
    },
    {
        "id": 5,
        "title": "Indexer swap event",
        "link": "Indexer swap link",
        "type": "Swap",
        "tributeOffered": 1,
        "tributeAddress": common.TOKEN_ADDRESS.bytes,
        "paymentRequested": 1,
        "paymentAddress": common.TOKEN_ADDRESS.bytes,
        "votingDuration": 60,
        "graceDuration": 120,
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "yesVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[0].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 7,
                "loot": 5,
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
                "onboardedAt": common.START_TIME,
                "shares": 8,
                "loot": 5,
                "balances": [],
                "transactions": [],
            },
        ],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
        "noVotersMembers": [
            {
                "memberAddress": common.ADDRESSES[2].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 2,
                "loot": 5,
            },
            {
                "memberAddress": common.ADDRESSES[3].bytes,
                "onboardedAt": common.START_TIME,
                "shares": 3,
                "loot": 5,
            },
        ],
    },
]
