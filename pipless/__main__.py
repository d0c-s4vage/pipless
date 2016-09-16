#!/usr/bin/env python
# encoding: utf-8


import argparse
import os
import pipless
import sys


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        __file__,
        description=pipless.logo+"\n"+pipless.__doc__,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-n", "--no-venv",
        help="don't use a virtual environment (maybe already in one?)",
        action="store_true",
        default=False
    )
    parser.add_argument("-v", "--venv",
        help="the path to the virtualenv to be used/created",
        default=None
    )
    parser.add_argument("-r", "--no-requirements",
        help="do not a fresh requirements.txt before exiting",
        action="store_false",
        default=True
    )
    parser.add_argument("--debug",
        help="show debug information while running",
        action="store_true",
        default=False
    )
    parser.add_argument("--quiet",
        help="show no output while running",
        action="store_true",
        default=False
    )
    parser.add_argument("-p", "--python",
        help="path to the python executable to use in the virtual environment",
        action="store_true",
        default=False
    )
    parser.add_argument("remainder",
        help="script-specific arguments (not pipless arguments)",
        nargs=argparse.REMAINDER
    )
    opts = parser.parse_args(sys.argv[1:])

    script_file = None
    if len(opts.remainder) > 0:
        script_file = opts.remainder[0]
        if not os.path.exists(script_file):
            print("Error: {!r} does not exist".format(script_file))
            sys.exit(1)

# hide pipless.py from the argument list
    sys.argv[:] = opts.remainder

    pipless.main(
        script_file      = script_file,
        venv_path        = opts.venv,
        gen_requirements = opts.no_requirements,
        no_venv          = opts.no_venv,
        debug            = opts.debug,
        quiet            = opts.quiet,
    )
