#!/usr/bin/python
"""
    Converts an LCM log file to .mat and .pkl files importable to Matlab.
    See readme.md for usage instructions

    Adapted by C. Wilkinson from the lcm-log2smat module by G. Troni (https://github.com/gtroni/lcm-log2smat)
    Itself the lcm-log2smat module was based on the libbot2 script bot-log2mat (https://github.com/libbot2/libbot2)
"""

import argparse
import os
import pickle
import sys
from typing import Dict, List

import scipy.io.matlab.mio
from lcm import EventLog, Event

import lcm_export.log as log
from lcm_export.scan_for_lcmtypes import get_lcmtype_dictionary

"""
    ==============
    CMD ARGUMENTS
    ==============
"""


def get_arguments() -> argparse.Namespace:
    """
        Parses the cmd line input to get the input log file and a dictionary of options

        :return: keyed options
    """
    # Setup allowed arguments
    argument_parser = argparse.ArgumentParser(
        description="Exports lcm log files to matlab .mat files and python .pkl files to enable data analysis in external tools"
    )
    argument_parser.add_argument("files", metavar="file", type=str, nargs="+")
    argument_parser.add_argument("-v", "--verbose",
                                 help="Enables verbose logging",
                                 action="store_true")
    argument_parser.add_argument("-m", "--matlab",
                                 help="Generates matlab .mat files (default)",
                                 action="store_true")
    argument_parser.add_argument("-p", "--python",
                                 help="Generates python .pkl files",
                                 action="store_true")
    argument_parser.add_argument("--lcmtypes", metavar="PATH",
                                 help="The folder to search for lcm types within. Recursively searches all subfolders",
                                 default=os.getcwd(),
                                 action="store")

    # Parse arguments
    options = argument_parser.parse_args()

    # If no output type given, default to matlab
    if not (options.matlab or options.python):
        options.matlab = True

    # Add lcm types root to the path to enable direct importing of python modules
    sys.path.insert(0, options.lcmtypes)

    # Setup verbose logging
    log.is_verbose = options.verbose

    return options


"""
    ============
    LOG PARSING
    ============
"""


def convert_to_primitive(data, timestamp=None):
    """
        Converts the given data to a primitive type usable by scipy arrays.

        - Primitive types are returned as-is,
        - Lists & tuples are returned as lists with values converted to primitives
        - LCM types are returned as dictionaries to be mapped to Matlab structs
    """
    # Return primitive types as-is
    if isinstance(data, (int, float, str, bytes)):
        return data

    # Expand lists & tuples recursively
    elif isinstance(data, (list, tuple)):
        # Lists of lcm types
        if any(hasattr(item, "__slots__") for item in data):
            dict = {}
            for item in data:
                msg_dict = convert_to_primitive(item, timestamp)
                for field in msg_dict.keys():
                    dict.setdefault(field[:31], []).append(msg_dict[field])
            return dict
        # Lists of other types
        else:
            return [convert_to_primitive(item, timestamp) for item in data]

    # Handle custom lcm types
    # All message fields are listed in its __slots__ attribute
    elif hasattr(data, "__slots__"):
        # todo - constants

        msg_dict = {"timestamp": timestamp}
        for field in data.__slots__:
            value = getattr(data, field)
            msg_dict[field[:31]] = convert_to_primitive(value, timestamp)

        return msg_dict

    # Trigger a crash on an unrecognised type
    else:
        log.error(f"Unrecognised data type {type(data)}")
        exit()


def parse_lcm_log(file: str, lcm_types: Dict) -> Dict:
    log.log(f"Parsing lcm log file {file}")

    # Open log as an LCM EventLog object
    lcm_log = EventLog(file, "r")

    first_timestamp = None
    events: Dict[str, Dict[str, List]] = {}  # {CHANNEL: {FIELD1: [values], FIELD2: [values]}}

    missing_channels = []
    for event in lcm_log:
        assert isinstance(event, Event)
        # Record the time of the first event as start time
        if not first_timestamp:
            first_timestamp = event.timestamp

        # todo - ignored channels

        log.if_verbose(f"Event on channel: {event.channel}", end="\t")

        # Match the message to an lcm type
        fingerprint = event.data[:8]
        lcm_type = lcm_types.get(fingerprint, None)
        if not lcm_type:
            if event.channel not in missing_channels:
                missing_channels.append(event.channel)
                log.error(f"Unable to find lcm type for events on channel {event.channel}")
            continue
        log.if_verbose(f"-> {lcm_type.__name__}")

        # Decode the message into a python object
        try:
            message = lcm_type.decode(event.data)
        except:
            log.error(f"Error decoding event on channel {event.channel}")
            continue

        # Convert the message into loggable form & store
        message_dict = convert_to_primitive(message, event.timestamp - first_timestamp)

        # Convert to list of values for each field
        for field in message_dict.keys():
            events.setdefault(event.channel, {}).setdefault(field, []).append(message_dict[field])

    return events


"""
    =============
    FILE WRITING
    =============
"""


def dump_to_matlab(data: Dict, output_file: str):
    """
        Creates a Matlab .mat file from teh given dictionary
    """
    log.log(f"Writing .mat file to {output_file}.mat")
    scipy.io.matlab.mio.savemat(output_file + ".mat", data, oned_as='column')


def dump_to_pickle(data: Dict, output_file: str):
    log.log(f"Writing .pkl file to {output_file}.pkl")
    with open(output_file + ".pkl", "wb") as file:
        pickle.dump(data, file, protocol=2)


"""
    ============
    MAIN SCRIPT
    ============
"""


def main():
    # Get the input variables
    cmd_options = get_arguments()

    # Find the lcm type definitions
    lcm_types = get_lcmtype_dictionary(cmd_options.lcmtypes)

    for file in cmd_options.files:
        # Parse event log
        events = parse_lcm_log(file, lcm_types)

        # Write data to files
        output_file = os.path.basename(file).replace(".", "_").replace("-", "_")
        if cmd_options.matlab:
            dump_to_matlab(events, output_file)
        if cmd_options.python:
            dump_to_pickle(events, output_file)


if __name__ == "__main__":
    main()
