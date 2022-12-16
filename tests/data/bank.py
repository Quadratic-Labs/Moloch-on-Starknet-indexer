from . import common

BANK = {
    "bankAddress": common.BANK_ADDRESS.bytes,
    "whitelistedTokens": [
        {
            "tokenName": common.TOKEN_NAME,
            "tokenAddress": common.TOKEN_ADDRESS.bytes,
            "whitelistedAt": common.START_TIME,
        }
    ],
    "unWhitelistedTokens": [
        {
            "tokenName": common.TOKEN_NAME,
            "tokenAddress": common.TOKEN_ADDRESS.bytes,
            "unWhitelistedAt": common.START_TIME,
        }
    ],
    "balances": [
        {
            "tokenName": common.TOKEN_NAME,
            "tokenAddress": common.TOKEN_ADDRESS.bytes,
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
}
