#!/usr/bin/env python
# encoding: utf-8


import argparse
import os
import pipless
import sys


# this simplifies _do_arg_parse, but I don't really like this...
NOT_IN_LIST = 0xffffffff
def index_(item, list_):
    try:
        return list_.index(item)
    except ValueError as e:
        return NOT_IN_LIST


def _do_arg_parse(parser):
    """Correctly parse the arguments, handling the -m and -c options
    correctly
    """
    m_index = index_("-m", sys.argv[1:])
    c_index = index_("-c", sys.argv[1:])

    if m_index == NOT_IN_LIST and c_index == NOT_IN_LIST:
        args_to_parse = sys.argv[1:]
        remainder = None

    elif m_index < c_index:
        args_to_parse = sys.argv[1:m_index+3]
        remainder = sys.argv[m_index+3:]

    elif c_index < m_index:
        args_to_parse = sys.argv[1:c_index+3]
        remainder = sys.argv[c_index+3:]

    opts = parser.parse_args(args_to_parse)

    if remainder is None:
        remainder = opts.remainder

    return opts, remainder


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog            = "pipless",
        description     = pipless.logo+"\n"+pipless.__doc__,
        formatter_class = argparse.RawTextHelpFormatter,
    )

    parser.add_argument("-n", "--no-venv",
        help    = "don't use a virtual environment (maybe already in one?)",
        action  = "store_true",
        default = False
    )
    parser.add_argument("-v", "--venv",
        help    = "the path to the virtualenv to be used/created",
        default = None
    )
    parser.add_argument("--no-requirements",
        help    = "do not a fresh requirements.txt before exiting",
        action  = "store_false",
        default = True
    )
    parser.add_argument("--debug",
        help    = "show debug information while running",
        action  = "store_true",
        default = False
    )
    parser.add_argument("--quiet",
        help    = "show no output while running",
        action  = "store_true",
        default = False
    )
    parser.add_argument("--no-install",
        help    = "don't install anything, only activate the virtual environment. Implies --no-requirements",
        action  = "store_true",
        default = False
    )
    parser.add_argument("--no-color",
        help    = "Never colorize the output",
        action  = "store_true",
        default = False
    )
    parser.add_argument("--color",
        help    = "Always colorize the output",
        action  = "store_true",
        default = False
    )
    parser.add_argument("remainder",
        help  = "script-specific arguments (not pipless arguments)",
        nargs = argparse.REMAINDER
    )

    python_group = parser.add_argument_group("Common Python Options")
    python_group.add_argument("-c",
        help    = "A single command to run",
        metavar = "cmd",
        default = None,
        dest    = "python_cmd"
    )
    python_group.add_argument("-m",
        help    = "run library module as a script (terminates option list)",
        metavar = "mod",
        default = None,
        dest    = "python_module"
    )

    venv_group = parser.add_argument_group("Common virtualenv options")
    venv_group.add_argument("-p", "--python",
        help="""The Python interpreter to use, e.g.,
--python=python2.5 will use the python2.5 interpreter
to create the new environment.  The default is the
interpreter that virtualenv was installed with
(/usr/bin/python)""",
        dest = "venv_python"
    )
    venv_group.add_argument("--clear",
        help    = "Clear out the non-root install and start from scratch.",
        action  = "store_true",
        default = False,
        dest    = "venv_clear",
    )
    venv_group.add_argument("--system-site-packages",
        help    = """Give the virtual environment access to the global
site-packages.""",
        action  = "store_true",
        default = False,
        dest    = "venv_system_site_packages"
    )

    opts, remainder = _do_arg_parse(parser)

    script_file = None
    
    # this should mean that we're directly running a script
    if opts.python_cmd is None and opts.python_module is None and len(opts.remainder) > 0:
        script_file = opts.remainder[0]
        if not os.path.exists(script_file):
            print("Error: {!r} does not exist".format(script_file))
            sys.exit(1)

    # hide pipless.py from the argument list
    sys.argv[:] = remainder

    pipless.main(
        script_file      = script_file,
        venv_path        = opts.venv,
        gen_requirements = opts.no_requirements,
        no_venv          = opts.no_venv,
        debug            = opts.debug,
        quiet            = opts.quiet,
        no_install       = opts.no_install,
        color            = opts.color,
        no_color         = opts.no_color,

        # python-specific arguments
        python_module    = opts.python_module,
        python_cmd       = opts.python_cmd,

        # virtualenv-specific arguments
        venv_clear                = opts.venv_clear,
        venv_python               = opts.venv_python,
        venv_system_site_packages = opts.venv_system_site_packages,
    )
