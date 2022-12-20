import pytest

from dao.graphql.common import parse_hex


def test_parse_hex():
    with pytest.raises(ValueError, match=".*it should start with 0x.*"):
        parse_hex("not a hex value")
