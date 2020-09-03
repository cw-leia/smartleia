"""
Here is detailed the python API of the `smartleia` package.
"""


import ctypes
import threading
import time
from enum import Enum, IntEnum, IntFlag
from typing import List, Optional, Union

import serial
import serial.tools.list_ports

__all__ = [
    "TriggerPoints",
    "T",
    "Triggers",
    "TriggerStrategy",
    "create_APDU_from_bytes",
    "APDU",
    "RESP",
    "ATR",
    "LEIA",
]

__version__ = "1.0.0"

name = "smartleia"


COMMAND_LEN_SIZE = 4
RESPONSE_LEN_SIZE = 4
TRIGGER_DEPTH = 10
STRATEGY_MAX = 4
# Maximum size of APDU payload size
# NOTE: because of firmware SRAM constraints, we only
# support this size for now.
MAX_APDU_PAYLOAD_SIZE = 16384

ERR_FLAGS = {0x00: "OK", 0x01: "PLATFORM_ERR_CARD_NOT_INSERTED", 0xFF: "UNKNOWN_ERROR"}


class LEIAStructure(ctypes.Structure):
    """
    Base structure for exchanging data with LEIA.
    """

    def pack(self):
        return bytes(self)[:]

    def unpack(self, by):
        fit = min(len(by), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), by, fit)
        return self

    def normalized(self):
        return bytes(self)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return " ".join(["{:02x}".format(x) for x in self.normalized()])


class ByteStruct(LEIAStructure):
    _pack_ = 1
    _fields_ = [("value", ctypes.c_uint8)]


class Timers(LEIAStructure):
    _pack_ = 1
    _fields_ = [
        ("delta_t", ctypes.c_uint32),
        ("delta_t_answer", ctypes.c_uint32),
    ]

    def __init__(self, delta_t = 0, delta_t_answer = 0):
        """
        Create a Timers structure.

        Parameters:
            delta_t (int) : total time for the APDU.
            delta_t_answer (int) : answer time for the APDU.
        """
        LEIAStructure.__init__(self, delta_t = 0, delta_t_answer = 0)
        self.delta_t = self.delta_t_answer = 0

    def __str__(self) -> str:
        return f"""Timers(
        delta_t={self.delta_t:d} microseconds,
        delta_t_answer={self.delta_t_answer:d} microseconds,
        )"""
 
##### Triggers handling ######
class TriggerPoints(IntFlag):
    """
    Class utility to reference the trigger points available.
    """

    #: Point before getting the ATR.
    TRIG_GET_ATR_PRE = 1 << 0

    #: Point just after the ATR has been received.
    TRIG_GET_ATR_POST = 1 << 1

    #: Point just before sending a simple APDU in T=0.
    TRIG_PRE_SEND_APDU_SHORT_T0 = 1 << 2

    #: Point just before sending a fragmented APDU in T=0.
    TRIG_PRE_SEND_APDU_FRAGMENTED_T0 = 1 << 3

    #: Point just before sending an APDU in T=1.
    TRIG_PRE_SEND_APDU_T1 = 1 << 4

    #: Point just before sending an APDU
    TRIG_PRE_SEND_APDU = (
        TRIG_PRE_SEND_APDU_SHORT_T0
        | TRIG_PRE_SEND_APDU_FRAGMENTED_T0
        | TRIG_PRE_SEND_APDU_T1
    )

    #: Point just before receiving a RESP in T=0.
    TRIG_POST_RESP_T0 = 1 << 6

    #: Point just before receiving a RESP in T=1.
    TRIG_POST_RESP_T1 = 1 << 7

    #: Point just before receiving a RESP
    TRIG_POST_RESP = TRIG_POST_RESP_T0 | TRIG_POST_RESP_T1

    #: Point just after sending a byte through the ISO7816 interface.
    TRIG_IRQ_PUTC = 1 << 8

    #: Point juster afted a byte has been received through the ISO7816 interface.
    TRIG_IRQ_GETC = 1 << 9


class Triggers(Enum):
    # NOTE: you can improve your trigger strategies here by adding new ones
    # or existing ones!
    #: Triggers at the beginning and end of ATR: first trig just before
    # reading ATR, second trig after we have got the ATR
    MULTI_TRIG_ATR = [
        TriggerPoints.TRIG_GET_ATR_PRE,
        TriggerPoints.TRIG_GET_ATR_POST,
    ]
    #: Triggers after the first byte of an APDU has been sent: first trig
    # just after we have sent our APDU command, second trig when receiving
    # the first response byte from the card.
    MULTI_TRIG_AFTER_1ST_BYTE_SEND_APDU = [
        TriggerPoints.TRIG_PRE_SEND_APDU,
        TriggerPoints.TRIG_IRQ_PUTC,
    ]
    

class TriggerStrategy(LEIAStructure):
    """
    Attributes:
        delay (int): the delay between event detection and effective trig on GPIO in milliseconds.
        point_list (list[int]): the list of events to match.
    """

    _pack_ = 1
    _fields_ = [
        ("size", ctypes.c_uint8),
        ("delay", ctypes.c_uint32),
        ("single", ctypes.c_uint8),
        ("_list", ctypes.c_uint32 * TRIGGER_DEPTH),
        ("_list_trigged", ctypes.c_uint32 * TRIGGER_DEPTH),
        ("_cnt_trigged", ctypes.c_uint32 * TRIGGER_DEPTH),
        ("_event_time", ctypes.c_uint32 * TRIGGER_DEPTH),
        ("_apply_delay", ctypes.c_uint32 * TRIGGER_DEPTH),
    ]

    def __init__(self, delay=0, single=0, point_list=None):
        if point_list is None:
            point_list = []

        LEIAStructure.__init__(self, size=0, delay=delay, single=single)
        self.point_list = point_list

    def _translate_point_list(self, point_list):
        if isinstance(point_list, Triggers):
            point_list = point_list.value

        return list(map(lambda point: TriggerPoints(point).value, point_list))

    def __str__(self) -> str:
        return f"TriggerStrategy(single={self.single}, delay={self.delay}, point_list={self.point_list}, point_list_trigged={self.point_list_trigged}, cnt_list_trigged={self.cnt_list_trigged}, event_time={self.event_time_list})"

    @property
    def point_list(self):
        _point_list = list(self._list)[0 : self.size]
        try:
            r = Triggers(_point_list)
        except Exception:
            r = list(map(lambda i: TriggerPoints(i), _point_list))

        return r

    @point_list.setter
    def point_list(self, value):
        value = self._translate_point_list(value)

        if not isinstance(value, list):
            raise Exception("data should be a list")
        if len(value) > len(self._list):
            raise Exception("Size of data too high")
        for i, v in enumerate(value):
            self._list[i] = value[i]
        self.size = len(value)

    @property
    def point_list_trigged(self):
        _point_list_trigged = list(self._list_trigged)[0 : self.size]
        try:
            r = Triggers(_point_list_trigged)
        except Exception:
            r = list(map(lambda i: TriggerPoints(i), _point_list_trigged))

        return r

    @property
    def cnt_list_trigged(self):
        _cnt_list_trigged = list(self._cnt_trigged)[0 : self.size]

        return _cnt_list_trigged

    @property
    def event_time_list(self):
        _event_time_list = list(self._event_time)[0 : self.size]

        return _event_time_list



class SetTriggerStrategy(LEIAStructure):
    _pack_ = 1
    _fields_ = [("index", ctypes.c_uint8), ("strategy", TriggerStrategy)]

    def __str__(self) -> str:
        return f"SetTriggerStrategy(index={self.index}, strategy={self.strategy})"


class ATR(LEIAStructure):
    """This class is used to represent an ATR.

       Attributes:
           ts (ctypes.c_uint8): Description of `attr1`.
           t0 (ctypes.c_uint8): Description of `attr2`.
           ta (ctypes.c_uint8[4]): Description of `attr1`.
           tb (ctypes.c_uint8[4]): Description of `attr2`.
           tc (ctypes.c_uint8[4]): Description of `attr1`.
           td (ctypes.c_uint8[4]): Description of `attr2`.
           h (ctypes.c_uint8[16]): Description of `attr1`.
           t_mask (ctypes.c_uint8[4]): Description of `attr2`.
           h_num (ctypes.c_uint8): Description of `attr1`.
           tck (ctypes.c_uint8): Description of `attr2`.
           tck_present (ctypes.c_uint8): Description of `attr1`.
           D_i_curr (ctypes.c_uint32): Description of `attr2`.
           F_i_curr (ctypes.c_uint32): Description of `attr1`.
           f_max_curr (ctypes.c_uint32): Description of `attr2`.
           T_protocol_curr (ctypes.c_uint8): Description of `attr1`.
           ifsc (ctypes.c_uint8): Description of `attr2`.
    """

    _pack_ = 1
    _fields_ = [
        ("ts", ctypes.c_uint8),
        ("t0", ctypes.c_uint8),
        ("ta", ctypes.c_uint8 * 4),
        ("tb", ctypes.c_uint8 * 4),
        ("tc", ctypes.c_uint8 * 4),
        ("td", ctypes.c_uint8 * 4),
        ("h", ctypes.c_uint8 * 16),
        ("t_mask", ctypes.c_uint8 * 4),
        ("h_num", ctypes.c_uint8),
        ("tck", ctypes.c_uint8),
        ("tck_present", ctypes.c_uint8),
        ("D_i_curr", ctypes.c_uint32),
        ("F_i_curr", ctypes.c_uint32),
        ("f_max_curr", ctypes.c_uint32),
        ("T_protocol_curr", ctypes.c_uint8),
        ("ifsc", ctypes.c_uint8),
    ]

    def normalized(self) -> bytes:
        b = b""
        b += ctypes.string_at(ctypes.addressof(self), ATR.ts.size + ATR.t0.size)
        for i in range(0, 4):
            if self.t_mask[0] & (0x1 << i) != 0:
                b += ctypes.string_at(ctypes.addressof(self) + ATR.ta.offset + i, 1)
            if self.t_mask[1] & (0x1 << i) != 0:
                b += ctypes.string_at(ctypes.addressof(self) + ATR.tb.offset + i, 1)
            if self.t_mask[2] & (0x1 << i) != 0:
                b += ctypes.string_at(ctypes.addressof(self) + ATR.tc.offset + i, 1)
            if self.t_mask[3] & (0x1 << i) != 0:
                b += ctypes.string_at(ctypes.addressof(self) + ATR.td.offset + i, 1)
        b += ctypes.string_at(ctypes.addressof(self) + ATR.h.offset, self.h_num)
        if self.tck_present == 1:
            b += ctypes.string_at(ctypes.addressof(self) + ATR.tck.offset, 1)
        return b

    def pretty_print(self):
        print("TS = 0x%02x" % self.ts)
        print("T0 = 0x%02x" % self.t0)
        for i in range(0, 4):
            if self.t_mask[0] & (0x1 << i) != 0:
                print("TA[%d] = 0x%02x" % (i, self.ta[i]))
        for i in range(0, 4):
            if self.t_mask[1] & (0x1 << i) != 0:
                print("TB[%d] = 0x%02x" % (i, self.tb[i]))
        for i in range(0, 4):
            if self.t_mask[2] & (0x1 << i) != 0:
                print("TC[%d] = 0x%02x" % (i, self.tc[i]))
        for i in range(0, 4):
            if self.t_mask[3] & (0x1 << i) != 0:
                print("TD[%d] = 0x%02x" % (i, self.td[i]))
        for i in range(0, self.h_num):
            print("H[%d] = 0x%02x" % (i, self.h[i]))
        if self.tck_present == 1:
            print("TCK =  0x%02x" % (self.tck))
        print("------ Protocol information")
        print("  Current protocol T = %d" % (self.T_protocol_curr))
        print(
            "  Di = %d, Fi = %d, f_max_curr = %d MHz"
            % (self.D_i_curr, self.F_i_curr, self.f_max_curr)
        )
        print("  IFSC = %d" % (self.ifsc))
        return

    def __str__(self) -> str:
        return f"""ATR(
    ts=0x{self.ts:02X},
    t0=0x{self.t0:02X},
    ta=[0x{self.ta[0]:02X}, 0x{self.ta[1]:02X}, 0x{self.ta[2]:02X}, 0x{self.ta[3]:02X}],
    tb=[0x{self.tb[0]:02X}, 0x{self.tb[1]:02X}, 0x{self.tb[2]:02X}, 0x{self.tb[3]:02X}],
    tc=[0x{self.tc[0]:02X}, 0x{self.tc[1]:02X}, 0x{self.tc[2]:02X}, 0x{self.tc[3]:02X}],
    td=[0x{self.td[0]:02X}, 0x{self.td[1]:02X}, 0x{self.td[2]:02X}, 0x{self.td[3]:02X}],
    h=[0x{self.h[ 0]:02X}, 0x{self.h[ 1]:02X}, 0x{self.h[ 2]:02X}, 0x{self.h[ 3]:02X},
       0x{self.h[ 4]:02X}, 0x{self.h[ 5]:02X}, 0x{self.h[ 6]:02X}, 0x{self.h[ 7]:02X},
       0x{self.h[ 8]:02X}, 0x{self.h[ 9]:02X}, 0x{self.h[10]:02X}, 0x{self.h[11]:02X},
       0x{self.h[12]:02X}, 0x{self.h[13]:02X}, 0x{self.h[14]:02X}, 0x{self.h[15]:02X}],
    t_mask=[0x{self.t_mask[0]:02X}, 0x{self.t_mask[1]:02X}, 0x{self.t_mask[2]:02X}, 0x{self.t_mask[3]:02X}],
    h_num=0x{self.h_num:02X},
    tck=0x{self.tck:02X},
    tck_present=0x{self.tck_present:02X},
    D_i_curr={self.D_i_curr},
    F_i_curr={self.F_i_curr},
    f_max_curr={self.f_max_curr},
    T_protocol_curr={self.T_protocol_curr},
    ifsc={self.ifsc}
)"""


class ResponseSizeStruct(LEIAStructure):
    """
    Attributes:
            response_size (ctypes.c_uint32): number of bytes of the response.
    """

    _pack_ = 1
    _fields_ = [("response_size", ctypes.c_uint32)]


class APDU(LEIAStructure):
    """Object for representing an APDU.

    Attributes:
        cla (ctypes.c_uint8): the `CLA` field of the APDU.
        ins (ctypes.c_uint8): the `INS` field of the APDU.
        p1 (ctypes.c_uint8): the `P1` field of the APDU.
        p2 (ctypes.c_uint8): the `P2` field of the APDU.
        lc (ctypes.c_uint16): the `Lc` field of the APDU.
        le (ctypes.c_uint32): the `Le` field of the APDU.
        send_le (ctypes.c_uint8): Description of `attr1`.
        data (list[int]): the `data` field of the APDU.

    """

    _pack_ = 1
    _fields_ = [
        ("cla", ctypes.c_uint8),
        ("ins", ctypes.c_uint8),
        ("p1", ctypes.c_uint8),
        ("p2", ctypes.c_uint8),
        ("lc", ctypes.c_uint16),
        ("le", ctypes.c_uint32),
        ("send_le", ctypes.c_uint8),
        ("_data", ctypes.c_uint8 * MAX_APDU_PAYLOAD_SIZE),
    ]

    def __init__(
        self,
        cla: int = 0,
        ins: int = 0,
        p1: int = 0,
        p2: int = 0,
        lc: int = None,
        le: int = 0,
        send_le: int = 1,
        data: Optional[List[int]] = None,
    ):
        """
        Create an APDU structure.

        Parameters:
            cla: the `CLA` field of the APDU.
            ins: the `INS` field of the APDU.
            p1: the `P1` field of the APDU.
            p2: the `P2` field of the APDU.
            lc: the `Lc` (data length) field of the APDU.
            le: the `Le` (expected length) field of the APDU.
            send_le: TODO.
            data: the list of bytes to send.
        """
        if data is None:
            data = []
        elif hasattr(data, "__iter__"):
            data = list(data)

        if lc is None:
            lc = len(data)
        LEIAStructure.__init__(
            self, cla=cla, ins=ins, p1=p1, p2=p2, lc=lc, le=le, send_le=send_le
        )
        self.data = data

    def pack(self):
        return LEIAStructure.pack(self)[: APDU._data.offset + self.lc]

    def __str__(self) -> str:
        return (
            f"APDU(cla={hex(self.cla)}, ins={hex(self.ins)}, p1={hex(self.p1)}, p2={hex(self.p2)}, lc={self.lc}, le={self.le}, send_le={self.send_le}"
            + (f", data={self.data}" if self.lc != 0 else "")
            + ")"
        )

    @property
    def data(self):
        return list(self._data)[0 : self.lc]

    @data.setter
    def data(self, value):
        if not isinstance(value, list):
            raise Exception("data should be a list")
        if len(value) > len(self._data):
            raise Exception("Size of data too high")
        for i, v in enumerate(value):
            self._data[i] = value[i]
        self.lc = len(value)

    def normalized(self) -> bytes:
        b = b""
        b += ctypes.string_at(ctypes.addressof(self), APDU.lc.offset)
        if self.lc != 0:
            b += ctypes.string_at(ctypes.addressof(self) + APDU.lc.offset, APDU.lc.size)
            b += ctypes.string_at(ctypes.addressof(self) + APDU._data.offset, self.lc)
        if self.send_le != 0:
            b += ctypes.string_at(ctypes.addressof(self) + APDU.le.offset, APDU.le.size)
        if self.lc == 0 and self.send_le == 0:
            b += ctypes.string_at(ctypes.addressof(self) + APDU.lc.offset, APDU.lc.size)
        return b


def create_APDU_from_bytes(_bytes) -> APDU:
    """Create an :class:`APDU` instance from a list of bytes.

    Example:
        >>> create_APDU_from_bytes([0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09])
        APDU(cla=0x00, ins=0x01, p1=0x02, p2=0x03, lc=0x04, data=[0x05, 0x06, 0x07, 0x08], le=0x09, send_le=1)
    """
    apdu = APDU()
    apdu.cla, apdu.ins, apdu.p1, apdu.p2 = _bytes[:4]
    apdu.send_le = 0

    if len(_bytes) < 5:
        raise NotImplementedError(
            "Error in decoding APDU buffer of size %d is too small" % (len(_bytes))
        )
    if len(_bytes) == 5:
        apdu.lc, apdu.le = 0, _bytes[4]
        apdu.send_le = 1
    else:
        apdu.lc, apdu.le = _bytes[4], 0
        if apdu.lc == 0x00 and len(_bytes) >= 8:
            # This is an extended APDU, try to decode Lc on 16 bits
            apdu.send_le = 2
            apdu.lc = (_bytes[5] << 16) + _bytes[6]
            # Get the data
            if len(_bytes) >= (apdu.lc + 7):
                if apdu.lc >= len(apdu._data):
                    raise NotImplementedError(
                        "Error in decoding extended APDU: buffer %d exceeds LEIA size %d"
                        % (apdu.lc, len(apdu._data))
                    )
                for i in range(apdu.lc):
                    apdu._data[i] = _bytes[7 + i]
                # Get Le if present
                if len(_bytes) >= (apdu.lc + 7 + 3):
                    if _bytes[apdu.lc + 7] != 0x00:
                        raise NotImplementedError("Error in decoding extended APDU Le")
                    apdu.le = (_bytes[apdu.lc + 7 + 1] << 16) + _bytes[apdu.lc + 7 + 2]
            else:
                # Lc is not present and we have in fact Le on 3 bytes
                apdu.le = apdu.lc
                apdu.lc = 0
        elif apdu.lc == 0:
            # Short APDU with no data
            if len(_bytes) == 6:
                apdu.le = _bytes[5]
                apdu.send_le = 1
            else:
                # Should be covered otherwise
                apdu.le = 0
                apdu.send_le = 1
        else:
            # Short APDU with data
            for i in range(apdu.lc):
                apdu._data[i] = _bytes[5 + i]
                if len(_bytes) == 5 + apdu.lc + 1:
                    apdu.le = _bytes[5 + apdu.lc]
                    apdu.send_le = 1
    return apdu


class RESP(LEIAStructure):
    """This class is used to represent an RESP.

    Attributes:
        sw1 (ctypes.c_uint8): The value of `SW1` field.
        sw2 (ctypes.c_uint8): The value of `SW2` field.
        le (ctypes.c_uint32): The length of the data.
        data (list[byte]): The value of the `data` field.
    """

    _pack_ = 1
    _fields_ = [
        ("le", ctypes.c_uint32),
        ("sw1", ctypes.c_uint8),
        ("sw2", ctypes.c_uint8),
        ("delta_t", ctypes.c_uint32),
        ("delta_t_answer", ctypes.c_uint32),
        ("_data", ctypes.c_uint8 * MAX_APDU_PAYLOAD_SIZE),
    ]

    def __init__(self, sw1=0, sw2=0, data=None, delta_t=0, delta_t_answer=0):
        """
        Create an RESP structure.

        Parameters:
            le (int): the `Le` field of the RESP.
            sw1 (int): the `SW1` field of the RESP.
            sw2 (int): the `SW2` field of the RESP.
            delta_t (int) : total time for the APDU.
            delta_t_answer (int) : answer time for the APDU.
            data (list[int]): the list of bytes received.
        """

        if data is None:
            data = []

        LEIAStructure.__init__(
            self, sw1=sw1, sw2=sw2, delta_t=delta_t, delta_t_answer=delta_t_answer
        )
        self.data = data

    def __str__(self) -> str:
        return (
            f"RESP(sw1=0x{self.sw1:02X}, sw2=0x{self.sw2:02X}, le={hex(self.le)}"
            + (f", data={self.data}" if self.le != 0 else "")
            + (f")\ndelta_t={self.delta_t:d} microseconds, delta_t_answer={self.delta_t_answer:d} microseconds")
        )

    @property
    def data(self):
        return list(self._data)[0 : self.le]

    @data.setter
    def data(self, value):
        if not isinstance(value, list):
            raise Exception("data should be a list")
        if len(value) > len(self._data):
            raise Exception("Size of data too high")
        for i, v in enumerate(value):
            self._data[i] = value[i]
        self.le = len(value)

    def normalized(self) -> bytes:
        b = b""
        b += ctypes.string_at(ctypes.addressof(self) + RESP._data.offset, self.le)
        b += ctypes.string_at(ctypes.addressof(self) + RESP.sw1.offset, RESP.sw1.size)
        b += ctypes.string_at(ctypes.addressof(self) + RESP.sw2.offset, RESP.sw2.size)
        return b


class T(IntEnum):
    """
    ISO7816 protocol selection.
    """

    #: The protocol is negotiated.
    AUTO = -1

    #: The protocol is T=0
    T0 = 0

    #: The protocol is T=1
    T1 = 1


class ConfigureSmartcardCommand(LEIAStructure):
    _pack_ = 1
    _fields_ = [
        ("protocol", ctypes.c_uint8),
        ("etu", ctypes.c_uint32),
        ("freq", ctypes.c_uint32),
        ("negotiate_pts", ctypes.c_uint8),
        ("negotiate_baudrate", ctypes.c_uint8),
    ]

    def __init__(
        self,
        protocol=None,
        etu=None,
        freq=None,
        negotiate_pts=True,
        negotiate_baudrate=True,
    ):
        LEIAStructure.__init__(
            self,
            protocol=protocol,
            etu=etu,
            freq=freq,
            negotiate_pts=negotiate_pts,
            negotiate_baudrate=negotiate_baudrate,
        )


class LEIA:
    """
    This class connects to a LEIA board and provides an access to all the device functionnality.
    """

    USB_VID = 0x3483
    USB_PID = 0x0BB9

    def __init__(
        self,
        device: str = "",
        serial_factory: Optional[serial.Serial] = None,
        auto_open=True,
    ):
        """
        Parameters:
            device: the serial port to use with LEIA (like /dev/ttyUSB0).

        Raises:
            Exception: if no serial port is provided.
        """

        self.reconfigured = False
        self.pcsc_stop = False
        self.pcsc_relay_thread = None
        self.curr_atr = None

        self.lock = threading.Lock()

        if serial_factory is None:
            serial_factory = serial.Serial

        self.device = device
        self.serial_factory = serial_factory

        if auto_open:
            self.open()

    def _testWaitingFlag(self):
        """
        Verify the presence of the waiting flag.
        """

        self.ser.read_all()
        self.ser.write(b" ")
        time.sleep(0.1)
        d = self.ser.read() + self.ser.read_all()

        if len(d) == 0 or d[-1] != 87:  # b"W"
            raise ConnectionError("Can not connect to LEIA.")

    def _checkAck(self):
        """
        Verify the presence of the acknowledge flag.
        """

        if self.ser.read() != b"R":
            raise IOError("No response ack received.")

    def _checkStatus(self):
        """
        Verify the presence of the status flag.
        """

        s = self.read()

        while s == b"w":
            # This is a 'wait extension' flag, try to read again
            s = self.read()

        if len(s) == 0:
            raise IOError("No status flag received.")

        if s == b"U":
            raise IOError("LEIA firmware do not handle this command.")
        elif s == b"E":
            raise IOError("Unkwown error (E).")
        elif s != b"S":
            raise IOError("Invalid status flag '{s}' received.")

        status = self.read()

        if status == b"":
            raise IOError("Status not received.")
        elif status != b"\x00":
            raise IOError(ERR_FLAGS[ord(status)])
        return status

    def _read_response_size(self):
        """
        Read and parse the "response size" field.
        """

        return (
            ResponseSizeStruct().unpack(self.ser.read(RESPONSE_LEN_SIZE)).response_size
        )

    def reset(self):
        """
        Reset LEIA.
        """

        with self.lock:
            self._testWaitingFlag()
            self._send_command(b"r")

    def open(self):
        """
        Open LEIA.
        """
        if not self.device:
            # Try to find automatically the device
            possible_ports = []
            for port in serial.tools.list_ports.comports():
                if port.pid == self.USB_PID and port.vid == self.USB_VID:
                    possible_ports.append(port)

            if len(possible_ports) > 2:
                raise RuntimeError(
                    f"Too much {self.USB_VID}/{self.USB_PID} devices found! I don't know which one to use."
                )
            elif len(possible_ports) == 0:
                raise RuntimeError(f"No {self.USB_VID}/{self.USB_PID} device found")

            for possible_port in possible_ports:
                self.device = possible_port.device
                try:
                    self.ser = self.serial_factory(
                        self.device, timeout=1, baudrate=115200
                    )

                    while True:
                        d = self.read_all()
                        if len(d) == 0:
                            break

                    self._testWaitingFlag()
                    self.ser.timeout = 10
                except ConnectionError:
                    self.ser.close()
                except serial.SerialException:
                    pass
                else:
                    break
        else:
            self.ser = self.serial_factory(self.device, timeout=1, baudrate=115200)
            while True:
                d = self.read_all()
                if len(d) == 0:
                    break

            self._testWaitingFlag()
            self.ser.timeout = 10

    def configure_smartcard(
        self,
        protocol_to_use: Optional[T] = None,
        ETU_to_use: Optional[int] = None,
        freq_to_use: Optional[int] = None,
        negotiate_pts: Optional[bool] = True,
        negotiate_baudrate: Optional[bool] = True,
    ):
        """Configure a smartcard connection.

        Method to configure a smartcard.
        By default, the smartcard reader will negociate with the smartcard the mode (T=0 or T=1), the ETU and
        the frequence to use.
        It is possible to:

        - force a mode (by setting protocol_to_use to 0 for T=0, and to 1 for T=1)
        - force an ETU (by setting the ETU_to_use parameter)
        - force a frequence (by setting the freq_to_use parameter)

        Example:
            >>> leia.configure_smartcard(T.T0, ETU_to_use=372)

        Parameters:
            protocol_to_use: The protocol to use (0: T=0, 1: T=1).
            ETU_to_use: The ETU value to force. If None, will be negociated (or default will be used).
            freq_to_use: The ISO7816 clock frequency to use. If None, will be negociated (or default will be used).
            negotiate_pts: if LEIA can try to negotiate the PTS.
            negotiate_baudrate: if LEIA can negotiate the baudrate. There is not impact if `ETU_to_use` and `freq_to_use` are set.
        """

        with self.lock:
            self._testWaitingFlag()

            self.reconfigured = True
            self.curr_atr = None

            if protocol_to_use is None:
                protocol_to_use = T.AUTO

            try:
                _protocol_to_use = T(protocol_to_use).value + 1
            except ValueError:
                raise NotImplementedError("Unknown protocol value.")

            if ETU_to_use is None:
                ETU_to_use = 0

            if freq_to_use is None:
                freq_to_use = 0

            negotiate_pts = True if negotiate_pts else False
            negotiate_baudrate = True if negotiate_baudrate else False

            # We always try to negotiate a T=1 communication if not specifically asked otherwise
            # Fallback to auto if this is not possible!
            if protocol_to_use == T.AUTO:
                try:
                    struct = ConfigureSmartcardCommand(
                        T(T.T1).value + 1,
                        ETU_to_use,
                        freq_to_use,
                        negotiate_pts,
                        negotiate_baudrate,
                    )
                    self._send_command(b"c", struct)
                except Exception:
                    struct = ConfigureSmartcardCommand(
                        T(T.AUTO).value + 1,
                        ETU_to_use,
                        freq_to_use,
                        negotiate_pts,
                        negotiate_baudrate,
                    )
                    self._send_command(b"c", struct)
            else:
                struct = ConfigureSmartcardCommand(
                    _protocol_to_use,
                    ETU_to_use,
                    freq_to_use,
                    negotiate_pts,
                    negotiate_baudrate,
                )
                self._send_command(b"c", struct)

    def get_trigger_strategy(self, SID: int) -> TriggerStrategy:
        """
        Returns the strategy N°SID.

        Parameters:
            SID: The trigger strategy's ID to get.

        Returns:
            TriggerStrategy: The trigger strategy N°SID.
        """

        with self.lock:
            if SID >= STRATEGY_MAX:
                raise Exception("get_trigger_strategy: asked SID=%d exceeds STRATEGY_MAX=%d" % (SID, STRATEGY_MAX))
           
            self._send_command(b"o", ByteStruct(SID))

            r_size = self._read_response_size()
            r = TriggerStrategy(TRIGGER_DEPTH).unpack(self.ser.read(r_size))

        return r

    def set_trigger_strategy(
        self, SID: int, point_list: Union[int, List[int]], delay: int = 0, single: int = 0
    ):
        """
        Set and activate a trigger strategy.

        Parameters:
            SID: the strategy bank ID to use.
            point_list: the sequence to match for the trigger.
            delay: the delay (in milliseconds) between the moment of the detection and the moment where the trigger is actually set high.
        """

        with self.lock:
            if SID >= STRATEGY_MAX:
                raise Exception("get_trigger_strategy: asked SID=%d exceeds STRATEGY_MAX=%d" % (SID, STRATEGY_MAX))

            if isinstance(point_list, int):
                size = 1
                point_list = [point_list]

            size = len(point_list)

            sts = SetTriggerStrategy(SID, TriggerStrategy(delay = delay, single = single, point_list = point_list))

            self._send_command(b"O", sts)

    def get_timers(self) -> ATR:
        """
        Return the `timers` of the last command.

        Returns:
            Timers: The `Timer` object.
        """

        with self.lock:
            self._send_command(b"m")

            r_size = self._read_response_size()
            r = Timers().unpack(self.ser.read(r_size))

        return r

    def get_ATR(self) -> ATR:
        """
        Return the `ATR`.

        Returns:
            ATR: The `ATR` object.
        """

        with self.lock:
            self._send_command(b"t")

            r_size = self._read_response_size()
            r = ATR().unpack(self.ser.read(r_size))

        return r

    def is_card_inserted(self) -> bool:
        """
        Return `True` if a smartcard is inserted in LEIA.

        Returns:
            `True` if a smartcard is inserted, else `False`.
        """

        with self.lock:
            self._send_command(b"?")

            r_size = self._read_response_size()
            if r_size != 1:
                raise Exception(
                    "Invalid response size for 'is_card_inserted' (?) command."
                )
            r = self.ser.read(1)

        return True if r == b"\x01" else False

    def dfu(self) -> None:
        """
        Reboot LEIA in DFU mode.
        """
        with self.lock:
            try:
                self._send_command(b"u")
            except serial.SerialException:
                pass

    def send_APDU(self, apdu: APDU) -> RESP:
        """
        Send an `APDU`.

        Parameters:
            apdu: The `APDU` object.

        Returns:
            RESP: The `RESP` object.
        """
        with self.lock:
            self._send_command(b"a", apdu)

            r_size = self._read_response_size()
            r = RESP().unpack(self.ser.read(r_size))

        return r

    def _send_command(self, command: bytes, struct: LEIAStructure = None):
        """
        Send a command to LEIA.

        Parameters:
            command: the ID of the command.
            struct: the data of the command.
        """

        self._testWaitingFlag()

        self.ser.write(command)
        if struct is not None:
            compacted = struct.pack()
            size = len(compacted).to_bytes(COMMAND_LEN_SIZE, byteorder="big")
            self.ser.write(size)
            self.ser.write(compacted)
        else:
            self.ser.write((0).to_bytes(COMMAND_LEN_SIZE, byteorder="big"))
        self._checkStatus()
        self._checkAck()

    def __getattr__(self, attr):
        if hasattr(self.ser, attr):
            return getattr(self.ser, attr)

        raise AttributeError(f"no attribute '{attr}'")

    # Handle connection with a virtual smart card reader
    # on localhost or elsewhere on the network
    def _pcsc_relay_thread(self, host, port):  # noqa: C901
        import binascii
        import socket
        import struct

        print("Starting LEIA PCSC relay for host %s:%d" % (host, port))

        while not self.pcsc_stop:
            if not self.is_card_inserted():
                self.curr_atr = None
                time.sleep(0.5)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((host, port))
            except Exception as e:
                print(
                    "Error: cannot connect to %s:%d. Is PCSCD running with virtual smartcard readers?"
                    % (host, port)
                )
                raise (e)

            s.settimeout(10)

            while (
                self.is_card_inserted() and not self.reconfigured and not self.pcsc_stop
            ):
                # Now wait for data to come
                # Get the comrand
                data = b""
                while len(data) != 2:
                    if self.pcsc_stop:
                        break
                    try:
                        data += s.recv(1)
                    except socket.timeout:
                        pass

                if self.pcsc_stop:
                    break

                length = struct.unpack("!H", data)[0]
                if length == 1:
                    # We received a Power Off, Power On, Reset or Get ATR command
                    data = s.recv(1)
                    if data == b"\x00":
                        # print("Received Power Off command!")
                        pass
                    elif data == b"\x01":
                        # print("Received Power On command!")
                        pass
                    elif data == b"\x02":
                        # print("Received Reset command!")
                        pass
                    elif data == b"\x04":
                        # print("Received Get ATR command!")
                        # Format our length
                        if not self.is_card_inserted():
                            # print("Card not inserted!")
                            s.sendall(b"\x00\x00")
                        else:
                            if self.curr_atr is None:
                                self.curr_atr = self.get_ATR()

                            if self.curr_atr.ts == 0x00:
                                # Card not configured, configure it
                                try:
                                    self.configure_smartcard()
                                except Exception:
                                    pass
                                self.curr_atr = self.get_ATR()
                            # Send the ATR
                            length = struct.pack("!H", len(self.curr_atr.normalized()))
                            s.sendall(length + self.curr_atr.normalized())
                    else:
                        print(
                            "LEIA PCSC relay error: received unknown command %s"
                            % binascii.hexlify(data)
                        )
                else:
                    # We received an APDU
                    # print("Received APDU command of size %d!" % length)
                    data = s.recv(length)
                    # Format and send the APDU
                    apdu = create_APDU_from_bytes(data)
                    r = self.send_APDU(apdu)
                    # If we have a 61XX response, handle the GET_RESPONSE here!
                    if r.sw1 == 0x61:
                        r = self.send_APDU(
                            APDU(
                                cla=apdu.cla,
                                ins=0xC0,
                                p1=0x00,
                                p2=0x00,
                                le=r.sw2,
                                send_le=1,
                            )
                        )
                    # If we have a 6Cxx (wrong length), adapt the APDU
                    if r.sw1 == 0x6C:
                        apdu.le = r.sw2
                        apdu.send_le = 1
                        r = self.send_APDU(apdu)
                    # If we have 67XX, adapt the APDU
                    if r.sw1 == 0x67:
                        apdu.le = 0x00
                        apdu.send_le = 1
                        r = self.send_APDU(apdu)
                    # Format the response and send it
                    length = struct.pack("!H", len(r.normalized()))
                    s.sendall(length + r.normalized())
            s.close()
            self.reconfigured = False

        self.pcsc_stop = False
        print("End of the relay.")

    def pcsc_relay(self, host="127.0.0.1", port=0x8C7B):

        self.pcsc_relay_thread = threading.Thread(
            name="LEIA PCSC relay", target=self._pcsc_relay_thread, args=(host, port)
        )
        self.pcsc_relay_thread.daemon = True
        self.pcsc_relay_thread.start()

    def pcsc_relay_stop(self):
        self.pcsc_stop = True
