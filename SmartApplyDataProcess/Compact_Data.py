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

def calculate_frames_to_consider(machine_speed_mph, nozzle_width, scan_frequency=25):
    """
    Calculate the number of frames to be considered based on machine speed (in mph) and nozzle width.

    :param machine_speed_mph: Speed of the machine in miles per hour.
    :param nozzle_width: Width covered by the nozzle in meters.
    :param scan_frequency: Frequency of the scan in Hz (default is 25 Hz).
    :return: Number of frames to be considered (rounded up to the nearest integer).
    """
    # Convert speed from miles per hour to meters per second
    machine_speed_mps = machine_speed_mph * 0.44704

    # Time taken to cover the nozzle width at the given speed
    time_to_cover_nozzle = nozzle_width / machine_speed_mps

    # Number of frames to be considered, rounded up to the nearest integer
    frames_to_consider = int(np.ceil(scan_frequency * time_to_cover_nozzle))

    return frames_to_consider

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
    SEGMENT_PER_FRAME=10
    POINTS_PER_DEGREE = 4  # Number of points per degree

    try:
        while True:  # Continuous data reception loop
            SPEED = 5  # Example speed in mph
            NOZZLE_WIDTH = 0.5
            number_of_frames = calculate_frames_to_consider(SPEED, NOZZLE_WIDTH)  # Example values
            total_points = (np.degrees(ANGLE_MAX) - np.degrees(ANGLE_MIN)) * POINTS_PER_DEGREE* number_of_frames
            detected_points = 0
            print(f"Total points to consider: {total_points}")
            print(f"Machine speed: {SPEED} mph")
            print(f"Nozzle width: {NOZZLE_WIDTH} m")
            print(f"Angle range: {np.degrees(ANGLE_MIN)} to {np.degrees(ANGLE_MAX)} degrees")
            print(f"Horizontal distance threshold: {HORIZONTAL_DISTANCE_THRESHOLD} m")
            print(f"Scan frequency: 25 Hz")
            print(f"Number of frames to consider: {number_of_frames}")
            (segments, frameNumbers, segmentCounters) = receiver.receive_segments(number_of_frames*SEGMENT_PER_FRAME)
            for segment in segments:  # Iterate through all segments
               for module in segment.get("Modules", []):  # Iterate through all modules
                    points_within_range = calculate_points_within_range(
                        module, ANGLE_MIN, ANGLE_MAX, HORIZONTAL_DISTANCE_THRESHOLD
                    )
                    detected_points += points_within_range
            density = detected_points / total_points
            print(f"Detected points: {detected_points}")
            print(f"Density: {density:.2f}")


    except KeyboardInterrupt:
        print("Data reception interrupted by user.")
    finally:
        receiver.close_connection()
