from indexer import utils

start_time = utils.utcnow()

members = [
    {
        "memberAddress": "0x1",
        "onboardedAt": start_time,
        "shares": 1,
        "loot": 50,
    },
    {
        "memberAddress": "0x2",
        "onboardedAt": start_time,
        "shares": 2,
        "loot": 50,
    },
    {
        "memberAddress": "0x3",
        "onboardedAt": start_time,
        "shares": 1,
        "loot": 50,
    },
    {
        "memberAddress": "0x4",
        "onboardedAt": start_time,
        "shares": 1,
        "loot": 50,
    },
    {
        "memberAddress": "0x5",
        "onboardedAt": start_time,
        "shares": 4,
        "loot": 50,
    },
]

proposals = [
    {
        "id": 0,
        "title": "Indexer signaling event",
        "type": "Signaling",
        "votingDuration": 5000,
        "graceDuration": 5,
        "submittedAt": start_time,
        "submittedBy": "0x1",
        "rawStatus": 1,
        "rawStatusHistory": [[1, start_time]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": ["0x1", "0x2"],
        "noVoters": ["0x3", "0x4"],
    }
]

list_proposals_query_expected_result = [
    {
        "id": 0,
        "title": "Indexer signaling event",
        "type": "Signaling",
        "votingDuration": 5000,
        "graceDuration": 5,
        "submittedAt": start_time,
        "submittedBy": "0x1",
        "rawStatus": 1,
        "rawStatusHistory": [[1, start_time]],
        "majority": 50,
        "quorum": 80,
        "yesVoters": ["0x1", "0x2"],
        "yesVotersMembers": [
            {
                "memberAddress": "0x1",
                "onboardedAt": start_time,
                "shares": 1,
                "loot": 50,
            },
            {
                "memberAddress": "0x2",
                "onboardedAt": start_time,
                "shares": 2,
                "loot": 50,
            },
        ],
        "noVoters": ["0x3", "0x4"],
        "noVotersMembers": [
            {
                "memberAddress": "0x3",
                "onboardedAt": start_time,
                "shares": 1,
                "loot": 50,
            },
            {
                "memberAddress": "0x4",
                "onboardedAt": start_time,
                "shares": 1,
                "loot": 50,
            },
        ],
    }
]
