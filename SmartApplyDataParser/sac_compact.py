#
# Copyright (c) 2023-2024 SICK AG
# SPDX-License-Identifier: MIT
#
#
# This program receives scan segments in compact or
# MSGPACK format and prints the content of all segments with the SegmentCounter = 2 to the console.
#
# The received data consists of a list of segments where
# each segment is represented as a dictionary, a list
# with frame counters and a list with segment counters
# which have the same length as the list of segments.
# This data is processed in the example below.
#
# All segments with the segment counter 2 are extracted.
# For all these segments the frame number and the segment
# counter for the first module and the start angle of the
# first scan of the first module are retrieved and printed.

import logging  # Reintroduce logging module
import scansegmentapi.msgpack as MsgpackApi
import scansegmentapi.compact as CompactApi
from scansegmentapi.tcp_handler import TCPHandler
from scansegmentapi.compact_stream_extractor import CompactStreamExtractor
from scansegmentapi.msgpack_stream_extractor import MsgpackStreamExtractor
from scansegmentapi.udp_handler import UDPHandler

import numpy as np
import os

###############################################################################################
#                                     CONFIGURATION                                           #
###############################################################################################

# Protocol to be used, select "Compact" or "MSGPACK"
PROTOCOL = "COMPACT"

# Select the printed beam information.
#       False   = Print the distance data of the first beam, layer 0, echo 0
#       True    = Print all captured distance data for each beam such as properties, rssi and
#                 distance values for all echos on layer 0
ALL_MEASURMENT_DATA = True

# Port used for data streaming. Enter the port configured in your device.
PORT = 2115

# If UDP is configured this should be the IP of the receiver.
# If TCP is configured this should be the IP of the SICK device.
IP = "172.16.0.10"

# Select with which transport protocol the data should be received. Select "TCP" or "UDP".
TRANSPORT_PROTOCOL = "UDP"


###############################################################################################

# Configure logging
log_file = os.path.join(os.getcwd(), "frame_data.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

if __name__ == "__main__":
    if "UDP" == TRANSPORT_PROTOCOL:
        transportLayer = UDPHandler(IP, PORT, 65535)
    else:
        if "MSGPACK" == PROTOCOL:
            streamExtractor = MsgpackStreamExtractor()
        else:
            streamExtractor = CompactStreamExtractor()
        transportLayer = TCPHandler(streamExtractor, IP, PORT, 1024)

    if "MSGPACK" == PROTOCOL:
        receiver = MsgpackApi.Receiver(transportLayer)
    else:
        receiver = CompactApi.Receiver(transportLayer)

    try:
        while True:  # Continuous data reception loop
            (segments, frameNumbers, segmentCounters) = receiver.receive_segments(50)

            # Log all frame data
            for segment in segments:
                logging.info(f"Segment Data: {segment}")

    except KeyboardInterrupt:
        print("Data reception stopped by user.")
    finally:
        receiver.close_connection()
