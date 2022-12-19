from pymongo import MongoClient

from dao.graphql.schema import schema

from .. import data


def test_empty_query(mongomock_client: MongoClient):
    context_value = {"db": mongomock_client.db}

    query = """
        query Proposals {
            proposals {
                id
            }
        }
    """

    result = schema.execute_sync(query, context_value=context_value)

    assert result.errors is None
    assert result.data["proposals"] == []


def test_proposals_query(mongomock_client: MongoClient):
    context_value = {"db": mongomock_client.db}

    mongomock_client.db.proposals.insert_many(data.PROPOSALS)
    mongomock_client.db.members.insert_many(data.MEMBERS)

    result = schema.execute_sync(
        data.graphql_queries.LIST_PROPOSALS, context_value=context_value
    )

    assert result.errors is None
    assert result.data["proposals"] == data.graphql_expected.LIST_PROPOSALS


def test_members_query(mongomock_client: MongoClient):
    context_value = {"db": mongomock_client.db}

    mongomock_client.db.bank.insert_one(data.BANK)
    mongomock_client.db.members.insert_many(data.MEMBERS)

    result = schema.execute_sync(
        data.graphql_queries.LIST_MEMBERS, context_value=context_value
    )

    assert result.errors is None
    assert result.data["members"] == data.graphql_expected.LIST_MEMBERS


def test_bank_query(mongomock_client: MongoClient):
    context_value = {"db": mongomock_client.db}

    mongomock_client.db.bank.insert_one(data.BANK)
    mongomock_client.db.members.insert_many(data.MEMBERS)

    result = schema.execute_sync(data.graphql_queries.BANK, context_value=context_value)

    assert result.errors is None
    assert result.data["bank"] == data.graphql_expected.BANK
