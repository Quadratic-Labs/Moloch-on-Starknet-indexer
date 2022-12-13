from typing import Any, Callable, Coroutine, Type

from apibara import Info
from apibara.model import BlockHeader, NewEvents, StarkNetEvent

from dao.indexer import bank, logger, members, proposals
from dao.indexer.base_event import BaseEvent
from dao.indexer.deserializer import deserialize_starknet_event

EventHandler = Callable[[Info, BlockHeader, StarkNetEvent], Coroutine[Any, Any, None]]

ALL_EVENTS: dict[str, Type[BaseEvent]] = {
    "ProposalStatusUpdated": proposals.ProposalStatusUpdated,
    "ProposalParamsUpdated": proposals.ProposalParamsUpdated,
    "ProposalAdded": proposals.ProposalAdded,
    "OnboardProposalAdded": proposals.OnboardProposalAdded,
    "GuildKickProposalAdded": proposals.GuildKickProposalAdded,
    "WhitelistProposalAdded": proposals.WhitelistProposalAdded,
    "UnWhitelistProposalAdded": proposals.UnWhitelistProposalAdded,
    "SwapProposalAdded": proposals.SwapProposalAdded,
    "VoteSubmitted": members.VoteSubmitted,
    "MemberAdded": members.MemberAdded,
    "MemberUpdated": members.MemberUpdated,
    "TokenWhitelisted": bank.TokenWhitelisted,
    "TokenUnWhitelisted": bank.TokenUnWhitelisted,
    "UserTokenBalanceIncreased": bank.UserTokenBalanceIncreased,
    "UserTokenBalanceDecreased": bank.UserTokenBalanceDecreased,
}


async def default_new_events_handler(
    info: Info,
    block_events: NewEvents,
    event_classes: dict[str, Type[BaseEvent]] = None,
):
    if event_classes is None:
        event_classes = ALL_EVENTS

    for starknet_event in block_events.events:
        if event_class := event_classes.get(starknet_event.name):
            logger.debug(
                "Handling event=%s emitted during block=%s with event_class=%s",
                block_events.block,
                starknet_event.name,
                event_class,
            )
            kwargs = await deserialize_starknet_event(
                fields=event_class.__annotations__,
                info=info,
                block=block_events.block,
                starknet_event=starknet_event,
            )
            event = event_class(**kwargs)

            await event.handle(
                info=info, block=block_events.block, starknet_event=starknet_event
            )
        else:
            logger.error("Cannot find event class for %s", starknet_event)
