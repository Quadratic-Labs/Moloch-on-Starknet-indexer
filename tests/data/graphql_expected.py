from . import data

BANK = {
    "bankAddress": data.BANK_ADDRESS.string,
    "whitelistedTokens": [
        {
            "tokenName": data.TOKEN_NAME,
            "tokenAddress": data.TOKEN_ADDRESS.string,
            "whitelistedAt": data.START_TIME_STRING,
        }
    ],
    "unWhitelistedTokens": [
        {
            "tokenName": data.TOKEN_NAME,
            "tokenAddress": data.TOKEN_ADDRESS.string,
            "unWhitelistedAt": data.START_TIME_STRING,
        }
    ],
    "balances": [
        {
            "tokenName": data.TOKEN_NAME,
            "tokenAddress": data.TOKEN_ADDRESS.string,
            "amount": data.AMOUNT,
        }
    ],
    "transactions": [
        {
            "tokenAddress": data.TOKEN_ADDRESS.string,
            "timestamp": data.START_TIME_STRING,
            "amount": data.AMOUNT,
        }
    ],
}
