# pylint: disable=line-too-long
from dataclasses import dataclass
from datetime import datetime, timezone

START_TIME = datetime(2022, 11, 18, 0, 0, 0, tzinfo=timezone.utc)
VOTING_PERIOD_ENDING_AT = datetime(2022, 11, 18, 1, 0, 0, tzinfo=timezone.utc)

# ISO format
START_TIME_STRING = "2022-11-18T00:00:00+00:00"
VOTING_PERIOD_ENDING_AT_STRING = "2022-11-18T01:00:00+00:00"
GRACE_PERIOD_ENDING_AT_STRING = "2022-11-18T03:00:00+00:00"

TOKEN_NAME = "Test Token"
ANOTHER_TOKEN_NAME = "Another Test Token"
AMOUNT = 102


@dataclass
class Address:
    integer: int
    string: str
    bytes: bytes


BANK_ADDRESS = Address(integer=0x0CCC, string="0x0ccc", bytes=b"\x0c\xcc")

TOKEN_ADDRESS = Address(
    integer=0x62230EA046A9A5FBC261AC77D03C8D41E5D442DB2284587570AB46455FD2488,
    string="0x062230ea046a9a5fbc261ac77d03c8d41e5d442db2284587570ab46455fd2488",
    bytes=b'\x06"0\xea\x04j\x9a_\xbc&\x1a\xc7}\x03\xc8\xd4\x1e]D-\xb2(E\x87W\n\xb4dU\xfd$\x88',
)

ANOTHER_TOKEN_ADDRESS = Address(
    integer=0x92230EA046A9A5FBC261AC77D03C8D41E5D442DB2284587570AB46455FD2499,
    string="0x092230ea046a9a5fbc261ac77d03c8d41e5d442db2284587570ab46455fd2499",
    bytes=b'\x09"0\xea\x04j\x9a_\xbc&\x1a\xc7}\x03\xc8\xd4\x1e]D-\xb2(E\x87W\n\xb4dU\xfd$\x99',
)

ADDRESSES: list[Address] = [
    Address(
        integer=0x363B71D002935E7822EC0B1BAF02EE90D64F3458939B470E3E629390436510B,
        string="0x0363b71d002935e7822ec0b1baf02ee90d64f3458939b470e3e629390436510b",
        bytes=b"\x03c\xb7\x1d\x00)5\xe7\x82.\xc0\xb1\xba\xf0.\xe9\rd\xf3E\x899\xb4p\xe3\xe6)9\x046Q\x0b",
    ),
    Address(
        integer=0x0521AD70DF444D0027481E3D0DA89E2DA48BA93F5462EC718C2899A37CB77472,
        string="0x0521ad70df444d0027481e3d0da89e2da48ba93f5462ec718c2899a37cb77472",
        bytes=b"\x05!\xadp\xdfDM\x00'H\x1e=\r\xa8\x9e-\xa4\x8b\xa9?Tb\xecq\x8c(\x99\xa3|\xb7tr",
    ),
    Address(
        integer=0x0019E104C4E33F87670744A5BDE7E5F737988DA3AED24FE30E832ADA4EA8232E,
        string="0x0019e104c4e33f87670744a5bde7e5f737988da3aed24fe30e832ada4ea8232e",
        bytes=b"\x00\x19\xe1\x04\xc4\xe3?\x87g\x07D\xa5\xbd\xe7\xe5\xf77\x98\x8d\xa3\xae\xd2O\xe3\x0e\x83*\xdaN\xa8#.",
    ),
    Address(
        integer=0x06C7D7EE8319F43FC62F8CC41442C6D61C50C176B59A67CA2ECBD16B0EBAAE2B,
        string="0x06c7d7ee8319f43fc62f8cc41442c6d61c50c176b59a67ca2ecbd16b0ebaae2b",
        bytes=b"\x06\xc7\xd7\xee\x83\x19\xf4?\xc6/\x8c\xc4\x14B\xc6\xd6\x1cP\xc1v\xb5\x9ag\xca.\xcb\xd1k\x0e\xba\xae+",
    ),
    Address(
        integer=0x04AD3B428ACE200BCBCC7C5412A869AFCD783E0A20B1BE9A84D1CD1BD734563B,
        string="0x04ad3b428ace200bcbcc7c5412a869afcd783e0a20b1be9a84d1cd1bd734563b",
        bytes=(
            b"\x04\xad;B\x8a\xce \x0b\xcb\xcc|T\x12\xa8i\xaf\xcdx>\n"
            b" \xb1\xbe\x9a\x84\xd1\xcd\x1b\xd74V;"
        ),
    ),
    Address(
        integer=0x00F1102779415ADA31E259CB97D2163FE0FCAA70BD82483A4AA0E3AB11AF4DE2,
        string="0x00f1102779415ada31e259cb97d2163fe0fcaa70bd82483a4aa0e3ab11af4de2",
        bytes=b"\x00\xf1\x10'yAZ\xda1\xe2Y\xcb\x97\xd2\x16?\xe0\xfc\xaap\xbd\x82H:J\xa0\xe3\xab\x11\xafM\xe2",
    ),
    Address(
        integer=0x04924CA066427BA06DDE113EC4E6BEA149D3FE9A340E9FA22878BE335AB65890,
        string="0x04924ca066427ba06dde113ec4e6bea149d3fe9a340e9fa22878be335ab65890",
        bytes=b"\x04\x92L\xa0fB{\xa0m\xde\x11>\xc4\xe6\xbe\xa1I\xd3\xfe\x9a4\x0e\x9f\xa2(x\xbe3Z\xb6X\x90",
    ),
    Address(
        integer=0x0256F2B63B82F2853923A110FD9253B389B5DAB1F914E25F0417E9F004CD280A,
        string="0x0256f2b63b82f2853923a110fd9253b389b5dab1f914e25f0417e9f004cd280a",
        bytes=b"\x02V\xf2\xb6;\x82\xf2\x859#\xa1\x10\xfd\x92S\xb3\x89\xb5\xda\xb1\xf9\x14\xe2_\x04\x17\xe9\xf0\x04\xcd(\n",
    ),
    Address(
        integer=0x06F4FF72C6782F0A60ECBBD6875624434E8505F918F8564D96F2EDA4F59F4E5B,
        string="0x06f4ff72c6782f0a60ecbbd6875624434e8505f918f8564d96f2eda4f59f4e5b",
        bytes=b"\x06\xf4\xffr\xc6x/\n`\xec\xbb\xd6\x87V$CN\x85\x05\xf9\x18\xf8VM\x96\xf2\xed\xa4\xf5\x9fN[",
    ),
]
