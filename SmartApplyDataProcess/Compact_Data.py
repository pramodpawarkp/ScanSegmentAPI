#
# Copyright (c) 2023-2024 SICK AG
# SPDX-License-Identifier: MIT
#
# This program receives scan segments in Compact format.
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

import numpy as np
import scansegmentapi.compact as CompactApi
from scansegmentapi.tcp_handler import TCPHandler
from scansegmentapi.compact_stream_extractor import CompactStreamExtractor
from scansegmentapi.udp_handler import UDPHandler

# Port used for data streaming. Enter the port configured in your device.
PORT = 2115

# If UDP is configured this should be the IP of the receiver.
# If TCP is configured this should be the IP of the SICK device.
IP = "172.16.0.10"

# Select with which transport protocol the data should be received. Select "TCP" or "UDP".
TRANSPORT_PROTOCOL = "UDP"


def calculate_points_within_range(module, angle_min, angle_max, horizontal_distance_threshold):
    """
    Calculate the number of points within a specific angle range and horizontal distance threshold for a module.

    :param module: The module dictionary containing segment data.
    :param angle_min: Minimum angle in radians.
    :param angle_max: Maximum angle in radians.
    :param horizontal_distance_threshold: Horizontal distance threshold.
    :return: Number of points within the specified range.
    """
    theta_start = module.get("ThetaStart", [])
    theta_stop = module.get("ThetaStop", [])
    segment_data = module.get("SegmentData", [])

    if theta_start and theta_stop and segment_data:
        theta_values = np.array(segment_data[0].get("ChannelTheta", []))  # Convert to NumPy array
        distances = np.array(segment_data[0].get("Distance", []))  # Convert to NumPy array

        if theta_values.size > 0 and distances.size > 0:  # Explicitly check if arrays are not empty
            # Flatten arrays for processing
            theta_values = theta_values.flatten()
            distances = distances.flatten()

            # Calculate horizontal distances
            # Ensure theta_values are in radians for trigonometric calculations
            horizontal_distances = distances * np.sin(np.radians(theta_values))

            # Filter points within the angle range and horizontal distance threshold
            mask = (theta_values >= angle_min) & (theta_values <= angle_max) & \
                   (horizontal_distances < horizontal_distance_threshold)
            return np.sum(mask)
    return 0


if __name__ == "__main__":
    if "UDP" == TRANSPORT_PROTOCOL:
        transportLayer = UDPHandler(IP, PORT, 65535)
    else:
        streamExtractor = CompactStreamExtractor()
        transportLayer = TCPHandler(streamExtractor, IP, PORT, 1024)

    receiver = CompactApi.Receiver(transportLayer)

    # Define the angle range (in radians) and horizontal distance threshold
    ANGLE_MIN = -2.40  # Minimum angle in radians
    ANGLE_MAX = 2.40  # Maximum angle in radians
    HORIZONTAL_DISTANCE_THRESHOLD = 130  # Horizontal distance threshold

    try:
        while True:  # Continuous data reception loop
            (segments, frameNumbers, segmentCounters) = receiver.receive_segments(50)
            for segment in segments:  # Iterate through all segments
                print("-----------------------------------------------------------------------------------")
                for module in segment.get("Modules", []):  # Iterate through all modules
                    points_within_range = calculate_points_within_range(
                        module, ANGLE_MIN, ANGLE_MAX, HORIZONTAL_DISTANCE_THRESHOLD
                    )
                    print(f"Module FrameNumber: {module.get('FrameNumber', 'N/A')}")
                    print(f"Points within range: {points_within_range}")
                print("-----------------------------------------------------------------------------------")
    except KeyboardInterrupt:
        print("Data reception interrupted by user.")
    finally:
        receiver.close_connection()
