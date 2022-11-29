from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer


from .. import constants, utils


async def test_signaling(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    title="Signaling event",
    link="Signaling event link",
):
    # TODO: test link with more than 31 chars

    invoke_result = await contract.functions["submitSignaling"].invoke(
        title=title, link=link, max_fee=10**16
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = contract_events["ProposalAdded"]

    # ProposalAdded.emit(id=info.id, title=info.title, link=info.link, type=info.type, submittedBy=info.submittedBy, submittedAt=info.submittedAt);

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    assert python_data.id == 0
    assert utils.felt_to_str(python_data.title) == title
    assert utils.felt_to_str(python_data.link) == link
    assert python_data.submittedAt == transaction_receipt.block_number
    assert python_data.submittedBy == client.address

    return transaction_receipt


async def test_onboard(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    title="Onboard event",
    link="Onboard event link",
    address=constants.FEE_TOKEN_ADDRESS,
    shares=1,
    loot=1,
    tribute_address=constants.FEE_TOKEN_ADDRESS,
    tribute_offered=0,
):
    invoke_result = await contract.functions["submitOnboard"].invoke(
        title=utils.str_to_felt(title),
        link=utils.str_to_felt(link),
        address=address,
        shares=shares,
        loot=loot,
        tributeAddress=tribute_address,
        tributeOffered=utils.int_to_uint256_dict(tribute_offered),
        max_fee=10**16,
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events emitted by our contract from transaction receipt
    events = [
        event
        for event in transaction_receipt.events
        if event.from_address == contract.address
    ]

    # Both ProposalAdded and OnboardProposalAdded events should be emitted
    # assert len(events) == 2

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    event_abi = contract_events["OnboardProposalAdded"]

    # The first event is ProposalAdded, the second is OnBoardProposalAdded
    event_data = events[1].data

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=event_abi["data"], values=event_data
    )

    assert python_data.id == 0
    assert python_data.applicantAddress == address
    assert python_data.loot == loot
    assert python_data.shares == shares
    assert python_data.tributeAddress == tribute_address
    assert python_data.tributeOffered == tribute_offered

    return transaction_receipt


async def test_swap(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    title="Onboard event",
    link="Onboard event link",
    tributeAddress=constants.FEE_TOKEN_ADDRESS,
    tributeOffered=0,
    paymentAddress=constants.FEE_TOKEN_ADDRESS,
    paymentRequested=0,
):
    invoke_result = await contract.functions["submitSwap"].invoke(
        title=utils.str_to_felt(title),
        link=utils.str_to_felt(link),
        tributeAddress=tributeAddress,
        tributeOffered=utils.int_to_uint256_dict(tributeOffered),
        paymentAddress=paymentAddress,
        paymentRequested=utils.int_to_uint256_dict(paymentRequested),
        max_fee=10**16,
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events emitted by our contract from transaction receipt
    events = [
        event
        for event in transaction_receipt.events
        if event.from_address == contract.address
    ]

    # Both ProposalAdded and OnboardProposalAdded events should be emitted
    # assert len(events) == 2

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    event_abi = contract_events["SwapProposalAdded"]

    # The first event is ProposalAdded, the second is SwapProposalAdded
    event_data = events[1].data

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=event_abi["data"], values=event_data
    )

    assert python_data.id == 0
    assert python_data.tributeOffered == tributeOffered
    assert python_data.tributeAddress == tributeAddress
    assert python_data.paymentAddress == paymentAddress
    assert python_data.paymentRequested == paymentRequested

    return transaction_receipt


async def test_guild_kick(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    title="GuildKick event",
    link="GuildKick event link",
    memberAddress=constants.ACCOUNT_ADDRESS,
):
    invoke_result = await contract.functions["submitGuildKick"].invoke(
        title=utils.str_to_felt(title),
        link=utils.str_to_felt(link),
        memberAddress=memberAddress,
        max_fee=10**16,
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events emitted by our contract from transaction receipt
    events = [
        event
        for event in transaction_receipt.events
        if event.from_address == contract.address
    ]

    # Both ProposalAdded and OnboardProposalAdded events should be emitted
    # assert len(events) == 2

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    event_abi = contract_events["GuildKickProposalAdded"]

    # The first event is ProposalAdded, the second is SwapProposalAdded
    event_data = events[1].data

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=event_abi["data"], values=event_data
    )

    assert python_data.id == 0
    assert python_data.memberAddress == memberAddress

    return transaction_receipt


async def test_whitelist(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    title="Whitelist event",
    link="Whitelist event link",
    tokenName="Some Token",
    tokenAddress=constants.ACCOUNT_ADDRESS,
):
    invoke_result = await contract.functions["submitWhitelist"].invoke(
        title=utils.str_to_felt(title),
        link=utils.str_to_felt(link),
        tokenName=utils.str_to_felt(tokenName),
        tokenAddress=tokenAddress,
        max_fee=10**16,
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events emitted by our contract from transaction receipt
    events = [
        event
        for event in transaction_receipt.events
        if event.from_address == contract.address
    ]

    # Both ProposalAdded and OnboardProposalAdded events should be emitted
    # assert len(events) == 2

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    event_abi = contract_events["WhitelistProposalAdded"]

    # The first event is ProposalAdded, the second is SwapProposalAdded
    event_data = events[1].data

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=event_abi["data"], values=event_data
    )

    assert python_data.id == 0
    assert python_data.tokenName == utils.str_to_felt(tokenName)
    assert python_data.tokenAddress == tokenAddress

    return transaction_receipt


async def test_unwhitelist(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    title="UnWhitelist event",
    link="Whitelist event link",
    tokenName="Some Token",
    tokenAddress=constants.FEE_TOKEN_ADDRESS,
):
    invoke_result = await contract.functions["submitUnWhitelist"].invoke(
        title=utils.str_to_felt(title),
        link=utils.str_to_felt(link),
        tokenName=utils.str_to_felt(tokenName),
        tokenAddress=tokenAddress,
        max_fee=10**16,
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events emitted by our contract from transaction receipt
    events = [
        event
        for event in transaction_receipt.events
        if event.from_address == contract.address
    ]

    # Both ProposalAdded and OnboardProposalAdded events should be emitted
    # assert len(events) == 2

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    event_abi = contract_events["UnWhitelistProposalAdded"]

    # The first event is ProposalAdded, the second is SwapProposalAdded
    event_data = events[1].data

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=event_abi["data"], values=event_data
    )

    assert python_data.id == 0
    assert python_data.tokenName == utils.str_to_felt(tokenName)
    assert python_data.tokenAddress == tokenAddress

    return transaction_receipt
