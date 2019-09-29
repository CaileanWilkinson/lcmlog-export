"""
    Helper functions for logging

    Adapted by C. Wilkinson from the lcm-log2smat module by G. Troni (https://github.com/gtroni/lcm-log2smat)
    Itself the lcm-log2smat module was based on the libbot2 script bot-log2mat (https://github.com/libbot2/libbot2)
"""
import sys

is_verbose = False


def log(string: str, end="\n"):
    """
        Logs the given string always
    """
    print(string, end=end)


def error(string: str, end="\n"):
    """
        Logs the given string as an error
    """
    sys.stderr.write(string + end)


def if_verbose(string: str, end="\n"):
    """
        Logs the given string only if verbose flag was given in cmd options
    """
    if is_verbose:
        print(string, end=end)
