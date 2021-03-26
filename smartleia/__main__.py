import code
import sys

import smartleia as sl

leia = None


def t0():
    leia.configure_smartcard(protocol_to_use=0)


def t1():
    leia.configure_smartcard(protocol_to_use=1)


def configure(*args, **kwargs):
    leia.configure_smartcard(*args, **kwargs)


def dfu():
    leia.dfu()


if __name__ == "__main__":

    try:
        leia = sl.LEIA()
    except:
        print("Error: are you sure that your LEIA board is connected?")
        sys.exit(42)

    try:
        leia.configure_smartcard()
    except:
        try:
            leia.configure_smartcard(negotiate_pts=False)
        except:
            print("Error: are you sure that a smartcard is inserted in the LEIA board?")
            sys.exit(42)

    try:
        leia.pcsc_relay()
    except:
        print("Error: error in pcsc_relay, is PCSCD running? Launch in a terminal with 'pcscd -fad'")
        sys.exit(42)

    code.interact(
        local=locals(),
        banner="""

        The connection with LEIA is opened and is connected to pcscd through virtualsmartcard.

        You can change the link with the smartcard with the following commands :

            configure( protocol_to_use=0,
                       ETU_to_use=...,
                       freq_to_use=...,
                       negotiate_pts=True,
                       negotiate_baudate=True)

            t0()    Equivalent to configure(protocol_to_use=0)
            t1()    Equivalent to configure(protocol_to_use=1)
            dfu()

        You have access to leia through the `leia` variable.

        Type exit() or CTRL-D to exit.

        """,
    )

    leia.close()
    sys.exit(0)
