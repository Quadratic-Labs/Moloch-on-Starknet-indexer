# pylint: disable=redefined-builtin
from typing import Optional

from apibara import Info
from apibara.model import BlockHeader

from dao import config, utils
from dao.indexer import logger


async def update_proposal(
    proposal_id: int,
    update: dict,
    info: Info,
):
    logger.debug("Updating proposal %s with %s", proposal_id, update)
    existing = await info.storage.find_one_and_update(
        collection="proposals",
        filter={"id": proposal_id},
        update=update,
    )
    logger.debug("Existing proposal %s", existing)


async def update_member(
    member_address: bytes,
    update: dict,
    info: Info,
    filter: Optional[dict] = None,
):
    if filter is None:
        filter = {}

    logger.debug("Updating member %s with %s", member_address, update)
    existing = await info.storage.find_one_and_update(
        filter={"memberAddress": member_address, **filter},
        collection="members",
        update=update,
    )
    logger.debug("Existing member %s", existing)


async def get_member(
    member_address: bytes,
    info: Info,
    filter: Optional[dict] = None,
):
    if filter is None:
        filter = {}

    return await info.storage.find_one(
        collection="members",
        filter={"memberAddress": member_address, **filter},
    )


async def update_bank(
    update: dict,
    info: Info,
    filter: Optional[dict] = None,
):
    if filter is None:
        filter = {}

    bank_address = utils.int_to_bytes(config.BANK_ADDRESS)

    # C
    if not await info.storage.find_one("bank", {"bankAddress": bank_address}):
        logger.debug(
            "Bank not found, creating it with %s", {"bankAddress": bank_address}
        )
        await info.storage.insert_one("bank", {"bankAddress": bank_address})

    logger.debug("Updating bank with %s", update)

    existing = await info.storage.find_one_and_update(
        collection="bank",
        filter={"bankAddress": bank_address, **filter},
        update=update,
    )
    logger.debug("Existing bank %s", existing)


async def get_bank(info: Info, filter: Optional[dict] = None):
    if filter is None:
        filter = {}

    bank_address = utils.int_to_bytes(config.BANK_ADDRESS)
    bank = await info.storage.find_one("bank", {"bankAddress": bank_address, **filter})
    return bank


async def add_token_if_not_exists(
    member_address: bytes, token_address: bytes, token_name: str, info: Info
):
    token_address_filter = {"balances.tokenAddress": token_address}

    bank_address = utils.int_to_bytes(config.BANK_ADDRESS)
    if member_address == bank_address:
        bank = await get_bank(info=info, filter=token_address_filter)
        # The member doesn't have the token in his balances list
        # TODO: make it clearer and easier. Ex: use another functions get_balances
        # to avoid checking if the member is None to know if the query returned
        # or not
        if not bank:
            await update_bank(
                info=info,
                update={
                    "$push": {
                        "balances": {
                            "tokenAddress": token_address,
                            "tokenName": token_name,
                        }
                    }
                },
            )

    else:
        member = await get_member(
            member_address=member_address, info=info, filter=token_address_filter
        )
        # The member doesn't have the token in his balances list
        # TODO: make it clearer and easier. Ex: use another functions get_balances
        # to avoid checking if the member is None to know if the query returned
        # or not
        if not member:
            await update_member(
                info=info,
                member_address=member_address,
                update={
                    "$push": {
                        "balances": {
                            "tokenAddress": token_address,
                            "tokenName": token_name,
                        }
                    }
                },
            )


async def get_token_name(info: Info, token_address: bytes) -> Optional[str]:
    bank = await get_bank(info) or {}
    for whitelisted_token in bank.get("whitelistedTokens", []):
        if whitelisted_token["tokenAddress"] == token_address:
            return whitelisted_token["tokenName"]


async def update_balance(
    info: Info,
    block: BlockHeader,
    member_address: bytes,
    token_address: bytes,
    amount: int,
):
    bank_address = utils.int_to_bytes(config.BANK_ADDRESS)
    token_name = await get_token_name(token_address=token_address, info=info)

    await add_token_if_not_exists(
        info=info,
        member_address=member_address,
        token_name=token_name,
        token_address=token_address,
    )

    add_amount_filter = {"balances.tokenAddress": token_address}
    add_amount = {
        "$inc": {"balances.$.amount": amount},
        "$push": {
            "transactions": {
                "tokenAddress": token_address,
                "timestamp": utils.get_block_datetime_utc(block),
                "amount": amount,
            },
        },
    }

    if member_address == bank_address:
        await update_bank(info=info, update=add_amount, filter=add_amount_filter)
    else:
        await update_member(
            info=info,
            member_address=member_address,
            update=add_amount,
            filter=add_amount_filter,
        )
