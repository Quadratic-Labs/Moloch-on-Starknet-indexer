from . import common

PROPOSALS = [
    {
        "id": 0,
        "title": "Indexer signaling event",
        "link": "Indexer signaling link",
        "type": "Signaling",
        "votingDuration": 60,  # one hour
        "graceDuration": 120,  # two hours
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
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
        "votingDuration": 60,  # one hour
        "graceDuration": 120,  # two hours
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
    },
    {
        "id": 2,
        "title": "Indexer guild kick event",
        "link": "Indexer guild kick link",
        "type": "GuildKick",
        "memberAddress": common.ADDRESSES[1].bytes,
        "votingDuration": 60,  # one hour
        "graceDuration": 120,  # two hours
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
    },
    {
        "id": 3,
        "title": "Indexer whitelist event",
        "link": "Indexer whitelist link",
        "type": "Whitelist",
        "tokenName": "Some Token",
        "tokenAddress": common.TOKEN_ADDRESS.bytes,
        "votingDuration": 60,  # one hour
        "graceDuration": 120,  # two hours
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
    },
    {
        "id": 4,
        "title": "Indexer unwhitelist event",
        "link": "Indexer unwhitelist link",
        "type": "UnWhitelist",
        "tokenName": "Some Token",
        "tokenAddress": common.TOKEN_ADDRESS.bytes,
        "votingDuration": 60,  # one hour
        "graceDuration": 120,  # two hours
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
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
        "votingDuration": 60,  # one hour
        "graceDuration": 120,  # two hours
        "submittedAt": common.START_TIME,
        "submittedBy": common.ADDRESSES[0].bytes,
        "rawStatus": "submitted",
        "rawStatusHistory": [["submitted", common.START_TIME]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": [common.ADDRESSES[0].bytes, common.ADDRESSES[1].bytes],
        "noVoters": [common.ADDRESSES[2].bytes, common.ADDRESSES[3].bytes],
    },
]
