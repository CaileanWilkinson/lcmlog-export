#!/usr/bin/python

"""
    Helper functions for searching for & sorting lcm type definitions

    Adapted by C. Wilkinson from the lcm-log2smat module by G. Troni (https://github.com/gtroni/lcm-log2smat)
    Itself the lcm-log2smat module was based on the libbot2 script bot-log2mat (https://github.com/libbot2/libbot2)
"""
import os
import pyclbr
import re
import sys
from binascii import hexlify
from typing import List, Dict, Type

from lcm_export import log

# Regex validators
filename_validator = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*\.py")


def __find_lcmtypes(root_path: str) -> List[str]:
    """
        Searches recursively from `root_path` for lcm types.

        Finds all python files matching the above regex of valid matlab names,
        imports their details using pyclbr and keeps a record of any which contain
        functions usually associated with lcm types.

        Returns a list of files containing lcm types as python modules to be imported
        e.g. root_path/dir/some_type.py -> dir.some_type
    """
    log.log(f"Searching for lcm types in root directory {root_path}")

    found_lcmtypes: List[str] = []
    for root, dirs, files in os.walk(root_path):
        log.if_verbose("Searching directory {}".format(root))

        # The python package will be the relative path to the file
        python_package = os.path.relpath(root, root_path).replace(os.sep, ".")
        if python_package == ".":
            python_package = ""

        for file in files:
            # Ensure file name (and hence lcm-type name) is importable to matlab
            if not filename_validator.fullmatch(file):
                continue

            log.if_verbose(f"Testing file: {file}", end=" ")

            lcmtype_name = file[:-3]
            module_name = f"{python_package}.{lcmtype_name}".strip(".")
            log.if_verbose(f"-> {module_name}")

            # Load python class from type definition & check validity as lcm type
            # To be valid, must have `_get_packed_fingerprint` and `decode` methods
            try:
                klass = pyclbr.readmodule(module_name)[lcmtype_name]
                if "decode" in klass.methods and "_get_packed_fingerprint" in klass.methods:
                    found_lcmtypes.append(module_name)
                    log.if_verbose(f"Found lcm definition {klass.name} in file: {file}")

            except (ImportError, KeyError):
                continue

    # Raise error if no lcm type definitions found (nothing will be decoded)
    if not found_lcmtypes:
        raise FileNotFoundError("No lcm type definitions found")
    return found_lcmtypes


def get_lcmtype_dictionary(root_path: str) -> Dict[bytes, Type]:
    """
    Searches recursively from `root_path` for any lcm type definitions
    and imports as python classes.

    Returns a dictionary of lcm type classes keyed by the type's fingerprint
    """
    # Search the given root path for lcm types
    lcmtypes_list = __find_lcmtypes(root_path)
    log.log(f"Found {len(lcmtypes_list)} lcm types")
    log.log("Importing lcm types")

    # Import each lcm type file as a python class & store keyed by fingerprint
    lcmtypes: Dict[bytes, Type] = {}
    for module_name in lcmtypes_list:
        log.if_verbose(f"Importing {module_name}", end="\t")
        try:
            # Import the lcm type file & get a reference to the module
            __import__(module_name)
            module = sys.modules[module_name]
            # Pick out the lcm type class from the module
            class_name = module_name.split(".")[-1]
            class_reference = getattr(module, class_name)
            # Store the class by its fingerprint
            fingerprint = class_reference._get_packed_fingerprint()
            lcmtypes[fingerprint] = class_reference
            log.if_verbose(f"-> {hexlify(fingerprint)}")
        except Exception as error:
            log.error(f"Error importing {module_name}")
            raise error

    return lcmtypes


# For testing only. Pass root_path as first argument when running file
if __name__ == "__main__":
    log.is_verbose = True
    sys.path.insert(0, sys.argv[1])
    get_lcmtype_dictionary(sys.argv[1])
