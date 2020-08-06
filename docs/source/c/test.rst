.. _c/test:

Firmware Doc
------------


Protocol
========

In order to communicate with LEIA, a simple communication protocol over uart is used. It permits to select a command, and execute it with specific data. The data produced by the command can finally be returned.

Only one data buffer :c:type:`command_cb_args_t` is used as the commands are executed one after one. As there is no need to keep trace of the result of the previous command, we can reuse the same buffer.

.. c:macro:: COMMANDS_BUFFER_MAX_LEN

        Constant to define the max size of the buffers used by the protocol (:c:type:`command_cb_args_t.buffer` and :c:type:`command_cb_args_t.response`).


.. c:struct:: command_cb_args

    Structure which handle the buffer send to a callback, and a buffer for the response of the callback.

        .. c:member:: uint32_t buffer_size

                Actual size of ``buffer``.

        .. c:member:: uint8_t buffer[COMMANDS_BUFFER_MAX_LEN]

                Buffer for the data which is send to the callback.

        .. c:member:: uint32_t response_size

                Actual size of the ``response`` buffer.

        .. c:member:: uint8_t response[COMMANDS_BUFFER_MAX_LEN]

                Buffer for the data produced by the callback.


To define a command, one have to create a :c:type:`command_t`. It needs a simple name (:c:type:`command_t.name`), which is used when debugging, a byte which is used to identify the command (:c:type:`command_t.o_command`), the maximal number of byte that can be send to the command (:c:type:`command_t.max_size`) and finally a callback to the function that will handle the command (:c:type:`command_t.callback`).

.. c:struct:: command_t

     Structure which describe a command to be exposed through LEIA API.

        .. c:member:: char name[30]

                Command name

        .. c:member:: uint8_t o_command

                Char which identify the command

        .. c:member:: uint32_t max_size

                Data max size (<= COMMANDS_BUFFER_MAX_LEN)

        .. c:member:: cb_command callback

                Callback to the function

.. c:struct:: protocol_config_pts_t

     Structure which codes the parameters to use when doing PTS negotiation.

        .. c:member:: uint8_t protocol

                Actual protocol to use:

                * 0 if no protocol is forced,
                * 1 for T=0,
                * 2 for T=1.

        .. c:member:: uint32_t etu

                ETU value.

        .. c:member:: uint32_t freq

                Actual frequency to use: 

                * 0 for the default one,
                * x for forcing a value.

        .. c:member:: uint8_t negotiate_pts

                * 0 for no negotiation
                * 1 for enabling negotiation           

        .. c:member:: uint8_t negotiate_baudrate

                * 0 for no baudrate negotiation
                * 1 for enabling baudrate negotiation

.. c:struct:: protocol_config_trigger_set_t
        
        Structure which code a strategy and an index to store the strategy at.

        .. c:member:: uint8_t index

                The index of the bank where the strategy will be saved.

        .. c:member:: trigger_strategy_t  strategy

                The strategy to save.

.. c:function:: uint8_t protocol_get_timers(SC_Card *card, command_cb_args_t *args)
        
        Callback to return timers values.

.. c:function:: uint8_t protocol_send_APDU(SC_Card *card, command_cb_args_t *args)

        Callback to process an APDU.

.. c:function:: uint8_t protocol_configure_pts(SC_Card *card, command_cb_args_t *args)

        Callback to configure a smartcard.

.. c:function:: uint8_t protocol_trigger_set_strategy(SC_Card *card, command_cb_args_t *args)

        Callback to set a trigger strategy.

.. c:function:: uint8_t protocol_trigger_get_strategy(SC_Card *card, command_cb_args_t *args)

        Callback to get a trigger strategy.

.. c:function:: uint8_t protocol_is_card_inserted(SC_Card *card, command_cb_args_t *args)

        Callback to check if the smartcard is inserted in LEIA.

.. c:function:: uint8_t protocol_reset_card(SC_Card *card, command_cb_args_t *args)

        Callback to reset the smartcard.

.. c:function:: uint8_t protocol_get_ATR(SC_Card *card, command_cb_args_t *args)

        Callback to send the ATR.

.. c:function:: int protocol_read_char_uart(volatile s_ring_t* ring_buffer, char* command)

        Read data from the uart, and put it in a ring buffer.

.. c:function:: void protocol_parse_cmd(volatile s_ring_t* ring_buffer)
        
        Parse a ring buffer to find a command to execute, call the corresponding callback.



Timers
======

Blabla


.. c:macro:: TIMERS_DEPTH 

        Constant to define the depth of a timer. TODO

.. c:struct:: command_cb_args_t

    Structure which handle the buffer send to a callback, and a buffer for the response of the callback.

        .. c:member:: uint32_t buffer_size

                Actual size of ``buffer``.

        .. c:member:: uint8_t buffer[COMMANDS_BUFFER_MAX_LEN]

                Buffer for the data which is send to the callback.

        .. c:member:: uint32_t response_size

                Actual size of the ``response`` buffer.

        .. c:member:: uint8_t response[COMMANDS_BUFFER_MAX_LEN]

                Buffer for the data produced by the callback.

.. c:function:: int get_timers_params(uint8_t depth)

        TODO

.. c:function:: int timgers_get_times()

        TODO

.. c:function:: inline unsigned int get_cortex_m4_cycles(void)

        TODO

.. c:function:: inline uint64_t platform_get_microseconds_ticks(void)

        Return the number of cycles of the CPU.

.. c:function:: int timeit(uint8_t timen)

        Increase the corresponding timer.


Triggers
========


.. c:macro:: TRIGGER_DEPTH 
.. c:macro:: STRATEGY_MAX

.. c:macro:: TRIG_GET_ATR_PRE
.. c:macro:: TRIG_GET_ATR_POST

.. c:macro:: TRIG_PRE_SEND_APDU_SHORT_T0       
.. c:macro:: TRIG_PRE_SEND_APDU_FRAGMENTED_T0  
.. c:macro:: TRIG_PRE_SEND_APDU_T1             
.. c:macro:: TRIG_POST_RESP_T0                 
.. c:macro:: TRIG_POST_RESP_T1                 


.. c:macro:: TRIG_SEND_APDU_FRAGMENTED_T0_PRE
.. c:macro:: TRIG_SEND_APDU_SIMPLE_T0_PRE
.. c:macro:: TRIG_GET_RESP_FRAGMENTED_T0_PRE
.. c:macro:: TRIG_GET_RESP_SIMPLE_T0_PRE

.. c:macro:: TRIG_IRG_PUTC
.. c:macro:: TRIG_IRQ_GETC

.. c:macro:: TRIG_PRE_RESP_T0

.. c:struct:: trigger_strategy_t

    Structure which handle the buffer send to a callback, and a buffer for the response of the callback.

        .. c:member:: uint8_t size

                TODO

        .. c:member:: uint32_t delay

                TODO

        .. c:member:: uint32_t delay_cnt

                TODO

        .. c:member:: uint8_t list[TRIGGER_DEPTH]

                TODO

.. c:function:: static inline int cmp(trigger_strategy_t* s)

        TODO

.. c:function:: int trig(uint8_t trign)

       Record the passage point.

