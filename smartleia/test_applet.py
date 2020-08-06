import argparse
import sys

import pytest

from smartleia import APDU, LEIA

STEP = 14


parser = argparse.ArgumentParser(description="Run tests on the the LEIA test applet.")
parser.add_argument(
    "--device", type=str, default="", help="the device to use (eg. /dev/ttyACM0)"
)
parser.add_argument(
    "--output-file", default="output.csv", help="the name of the output file"
)
parser.add_argument(
    "-T0", default=False, const=True, action="store_const", help="Do the tests for T=0"
)
parser.add_argument(
    "-T1", default=False, const=True, action="store_const", help="Do the tests for T=1"
)

args = parser.parse_args()

if args.T0 and args.T1:
    TEST_T0 = True
    TEST_T1 = True
elif args.T0:
    TEST_T0 = True
    TEST_T1 = False
elif args.T1:
    TEST_T0 = False
    TEST_T1 = True
else:
    TEST_T0 = True
    TEST_T1 = True


reader = LEIA(args.device)


#: Set protoctol T=0
@pytest.fixture(scope="function")
def mode_t0():
    reader.configure_smartcard(protocol_to_use=0)


#: Set protoctol T=1
@pytest.fixture(scope="function")
def mode_t1():
    reader.configure_smartcard(protocol_to_use=1)


#: Select the test applet
@pytest.fixture(scope="function")
def select_applet():
    apdu = APDU(
        cla=0x00,
        ins=0xA4,
        p1=0x04,
        p2=0x00,
        lc=0x0A,
        le=0x00,
        data=[0x45, 0x75, 0x74, 0x77, 0x74, 0x75, 0x36, 0x41, 0x70, 0x80],
        send_le=0,
    )
    reader.send_APDU(apdu)


############################################################################################

#: Case 1 is we send an APDU with no data, and we expect a simple 90 00 resp
#: with no data
def case1(record_property):
    record_property("case", 1)
    record_property("extended", False)
    apdu = APDU(cla=0x00, ins=0x01, p1=0x00, p2=0x00, lc=0x00, le=0x00, send_le=1)
    print(apdu)
    record_property("apdu", apdu)

    resp = reader.send_APDU(apdu)
    print(resp)
    record_property("resp", resp)

    assert hex(resp.sw1) == hex(0x90)
    assert hex(resp.sw2) == hex(0x00)

    assert resp.le == 0


if TEST_T0:

    def test_case1_t0(mode_t0, select_applet, record_property):
        record_property("T", 0)
        case1(record_property)


if TEST_T1:

    def test_case1_t1(mode_t1, select_applet, record_property):
        record_property("T", 1)
        case1(record_property)


############################################################################################

#: Case 2 is we sned an APDU with no data, and we except a 90 00 resp with
#: recv bytes of data.
def case2(recv, record_property):
    record_property("case", 2)
    record_property("extended", False if recv < 256 else True)

    # Compute recv on two bytes
    ab = recv // 256
    cd = recv % 256

    # Adapt the case where we need an extended APDU
    send_le = 1 if recv < 256 else 2

    # Prepare the APDU
    apdu = APDU(
        cla=0x00, ins=0x02, p1=ab, p2=cd, lc=0x0, le=0, send_le=send_le
    )  # le = recv
    print(apdu)
    record_property("apdu", apdu)

    # Send the APDU and get the response
    resp = reader.send_APDU(apdu)
    print(resp)
    record_property("resp", resp)

    # Check for 90 00
    assert hex(resp.sw1) == hex(0x90) or hex(resp.sw1) == hex(0x6C)
    assert hex(resp.sw2) == hex(0x00) or (
        hex(resp.sw2) == hex(cd) and hex(resp.sw1) == hex(0x6C)
    )

    # If 90 00 check that the length of the response is recv
    if resp.sw1 == 0x90 and resp.sw2 == 0:
        assert resp.le == recv
    else:
        assert resp.le == 0

    # Check each byte of the resp
    if resp.le == recv:
        for v in range(recv):
            assert resp.data[v] == v % 256


if TEST_T0:

    @pytest.mark.parametrize("recv", range(1, 300, STEP))
    def test_case2_t0(mode_t0, select_applet, recv, record_property):
        record_property("T", 0)
        case2(recv, record_property)


if TEST_T1:

    @pytest.mark.parametrize("x", range(1, 300, STEP))
    def test_case2_t1(mode_t1, select_applet, x, record_property):
        record_property("T", 1)
        case2(x, record_property)


def case3(send, record_property):
    record_property("case", 3)

    apdu = APDU(
        cla=0x00,
        ins=0x03,
        p1=0x00,
        p2=0x00,
        lc=send,
        data=range(send),
        le=0x00,
        send_le=0,
    )
    if send >= 256:
        record_property("extended", True)
    else:
        record_property("extended", False)

    print(apdu)
    record_property("apdu", apdu)

    resp = reader.send_APDU(apdu)
    print(resp)
    record_property("resp", resp)

    assert resp.sw1 == 0x90
    assert resp.sw2 == 0x00

    assert resp.le == 0


if TEST_T0:

    @pytest.mark.parametrize("send", range(1, 300, STEP))
    def test_case3_t0(mode_t0, select_applet, send, record_property):
        record_property("T", 0)
        case3(send, record_property)


if TEST_T1:

    @pytest.mark.parametrize("send", range(1, 300, STEP))
    def test_case3_t1(mode_t1, select_applet, send, record_property):
        record_property("T", 1)
        case3(send, record_property)


def case4(send, recv, record_property):
    record_property("case", 4)

    ab = recv // 256
    cd = recv % 256

    send_le = 1 if recv < 256 else 2

    apdu = APDU(
        cla=0x00,
        ins=0x04,
        p1=ab,
        p2=cd,
        lc=send,
        le=0,
        data=range(send),
        send_le=send_le,
    )
    if send >= 256 or recv >= 256:
        record_property("extended", True)
    else:
        record_property("extended", False)

    print(apdu)
    record_property("apdu", apdu)

    resp = reader.send_APDU(apdu)
    print(resp)
    record_property("resp", resp)

    assert resp.sw1 == 0x90
    assert resp.sw2 == 0x00
    assert resp.le == recv


if TEST_T0:

    @pytest.mark.parametrize("send", range(1, 300, STEP))
    @pytest.mark.parametrize("recv", range(1, 300, STEP))
    def test_case4_t0(mode_t0, select_applet, send, recv, record_property):
        record_property("T", 0)
        case4(send, recv, record_property)


if TEST_T1:

    @pytest.mark.parametrize("send", range(1, 300, STEP))
    @pytest.mark.parametrize("recv", range(1, 300, STEP))
    def test_case4_t1(mode_t1, select_applet, send, recv, record_property):
        record_property("T", 1)
        case4(send, recv, record_property)


def main(output_file="output.csv"):
    args = [
        sys.argv[0],
        "--csv",
        output_file,
        "--csv-columns",
        "module,doc,success,parameters_as_columns,properties_as_columns",
    ]
    pytest.main(args)


if __name__ == "__main__":
    main(args.output_file)
