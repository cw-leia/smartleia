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

    leia = sl.LEIA()
    leia.configure_smartcard()

    leia.pcsc_relay()

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
