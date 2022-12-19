LIST_PROPOSALS = """query Proposals {
  proposals {
    id
    title
    link
    type
    votingDuration
    graceDuration
    submittedAt
    votingPeriodEndingAt
    gracePeriodEndingAt
    rejectedAt
    approvedAt
    approvedToProcessAt
    rejectedToProcessAt
    submittedBy
    status
    active
    majority
    quorum
    currentMajority
    currentQuorum
    yesVoters
    yesVotesTotal
    noVoters
    noVotesTotal
    totalVotableShares
    timeRemaining
    didVoteTrue: memberDidVote(
      memberAddress: "0x0363b71d002935e7822ec0b1baf02ee90d64f3458939b470e3e629390436510b"
    )
    didVoteFalse: memberDidVote(
      memberAddress: "0x0363b71d002935e7822ec0b1baf02ee90d64f3458939b470e3e629390436511b"
    )

    ... on Onboard {
      applicantAddress
      shares
      loot
      tributeAddress
      tributeOffered
    }

    ... on GuildKick {
        memberAddress
    }

    ... on Whitelist {
        tokenName
        tokenAddress
    }

    ... on UnWhitelist {
        tokenName,
        tokenAddress
    }

    ... on Swap {
        tributeAddress
        tributeOffered
        paymentAddress
        paymentRequested
    }
  }
}
"""


LIST_MEMBERS = """query Proposals {
  members {
    memberAddress
    shares
    loot
    onboardedAt
    roles
    balances {
      tokenName
      tokenAddress
      amount
    }
    transactions {
      tokenAddress
      timestamp
      amount
    }
  }
}
"""

BANK = """query Bank {
  bank {
    bankAddress
    totalShares
    totalLoot
    whitelistedTokens {
      tokenName
      tokenAddress
      whitelistedAt
    }
    unWhitelistedTokens {
      tokenName
      tokenAddress
      unWhitelistedAt
    }
    balances {
      tokenName
      tokenAddress
      amount
    }
    transactions {
      tokenAddress
      timestamp
      amount
    }
  }
}
"""
