#!/usr/bin/env python
# encoding: utf-8


"""
TL;DR pipless let's you install packages as they are needed without
requiring code modification.

pipless hooks the import process and automatically installs packages
if they are not present in the current environment. By default
pipless will create a virtual environment into which packages
are installed.

The pipless module is intended to be run with the "-m" argument to
the python executable:

    python -m pipless [script_path [args..]]

If no script path is given, pipless will drop the user into an
interactive shell after activating a virtual environment and setting
up the pipless import hooks.

If a script path is given, the pipless import hooks will be installed
prior to running the script.

pipless can also be explicitly imported into the source code. Doing
so will install the necessary hooks and activate the virtual
environment.

The pipless experience becomes especially seamless when an alias
is made for python in your ~/.bashrc. E.g. alias python="python
-m pipless"

See https://github.com/d0c-s4vage/pipless for more details.
"""


# these will be used before we wipe out __main__
import argparse
import atexit
import code
import imp
import inspect
import pip
from pip.commands.search import SearchCommand
import os
import sys
import virtualenv


class DevNull(object):
    """Mock file-like object that does nothing
    """
    def seek(self, *args):
        pass
    def write(self, *args):
        pass
    def read(self, *args):
        return ""
    def close(self, *args):
        pass


class PipLess(object):
    """A class to automatically install missing python packages into
    a virtual environment.
    """

    def __init__(self, venv_path=None, quiet=True, no_venv=False, debug=False):
        """Initialize the package auto-installer and setup the
        virtual environment (if it doesn't already exist).
        
        If venv_path is None, a virtual environment named
        "venv" will be created in the current working directory
        """
        self.debug           = debug
        self.venv_home       = venv_path
        self.venv_parent_dir = os.path.dirname(self.venv_home)
        self.no_venv         = no_venv
        self.quiet           = quiet


        # keep a reference to these modules. We don't want to pollute
        # the global namespace by using normal imports. Plus this avoids
        # recursive import problems
        self._virtualenv     = virtualenv
        self._imp            = imp
        self._os             = os
        self._dev_null       = DevNull()
        self._pip            = pip
        self._sys            = sys
        self._search_command = SearchCommand
        self._refresh_pip    = _refresh_pip

        self._debug("created new PipLess")
        self._debug("    debug           : {}".format(self.debug))
        self._debug("    venv_home       : {}".format(self.venv_home))
        self._debug("    venv_parent_dir : {}".format(self.venv_parent_dir))
        self._debug("    no_venv         : {}".format(self.no_venv))
        self._debug("    quiet           : {}".format(self.quiet))


        if not no_venv and not os.path.exists(self.venv_home):
            self._debug("creating virtual environment at {}".format(self.venv_home))
            virtualenv.create_environment(
                self.venv_home,
                site_packages = False,
                clear         = True
            )
        else:
            self._debug("not creating virtual environment")
            import pdb; pdb.set_trace()

    def _info(self, msg):
        if self.quiet:
            return
        print("\n".join("[PIPLESS]:INF {}".format(x) for x in msg.split("\n")))
        self._sys.stdout.flush()

    def _debug(self, msg):
        if self.debug:
            print("\n".join("[PIPLESS]:DBG: {}".format(x) for x in msg.split("\n")))
            self._sys.stdout.flush()

    def activate(self):
        """Activate the virtual environment
        """
        if self.no_venv:
            self._debug("no_venv was set, not activating")
            return

        self._debug("activating virtual environment at {}".format(self.venv_home))
        activate_script = self._os.path.join(self.venv_home, "bin", "activate_this.py")
        execfile(activate_script, dict(__file__=activate_script))

        self._os.environ["VIRTUAL_ENV"] = self._os.path.abspath(self._os.path.join(self.venv_home))
        self._sys.executable = self._os.path.join(self.venv_home, "bin", "python")
        self._os.environ["_"] = self._sys.executable

        self._debug("new sys.path:")
        for path in self._sys.path:
            self._debug("    " + path)

        self._refresh_pip()

    def find_module(self, fullname, path=None):
        if "." in fullname:
            return None

        self._debug("finding module {}".format(fullname))

        try:
            mod_info = self._imp.find_module(fullname)
            self._debug("found module {} at {}".format(fullname, mod_info[1]))
        except ImportError as e:
            pass
        else:
            # it's already accessible, we don't need to do anything
            return None

        if self._package_exists_in_pypi(fullname):
            self._debug("module {} exists in pypi, installing".format(fullname))
            #self._sys.sdout = self._dev_null
            #self._sys.stderr = self._dev_null

            try:
                self._pip.main(["install", fullname])
            except SystemExit as e:
                pass
                #self._sys.stdout = self._sys.__stdout__
                #self._sys.stderr = self._sys.__stderr__

        # we've made it accessible to the normal import procedures
        # now, (should be on sys.path), so we'll return None which
        # will make Python attempt a normal import
        return None

    def _package_exists_in_pypi(self, fullname):
        searcher = self._search_command()
        options,args = searcher.parse_args([fullname])
        matches = searcher.search(args, options)
        found_match = None
        for match in matches:
            if match["name"] == fullname:
                return True
                break

        return False


def _refresh_pip():
    # Pip keeps track of the currently loaded modules in the current script
    # (and the current working set, etc) by creating a list of modules that
    # are accessible from sys.path (basically).
    # 
    # this list is generated when pip is first imported. This function
    # forces that list to be regenerated.
    from pip._vendor.pkg_resources import _initialize_master_working_set
    _initialize_master_working_set()


def run_script(venv_dir, script_file, installer, gen_requirements=True):
    """Run the script at the provided path
    """
    builtins = __builtins__

    if gen_requirements:
        gen_requirements_on_exit(installer.venv_parent_dir)

    import __main__
    __main__.__dict__.clear()
    __main__.__dict__.update(dict(
        __name__     = "__main__",
        __file__     = script_file,
        __builtins__ = builtins
    ))
    globals = __main__.__dict__
    locals = globals

    installer.activate()

    # repr will put the script_file into quotes and escape any
    # unruly characters
    exec 'execfile({})'.format(repr(script_file)) in globals, locals


def run_interactive_shell(installer, gen_requirements=True):
    builtins = __builtins__
    code_ = code

    if gen_requirements:
        gen_requirements_on_exit(installer.venv_parent_dir)

    _refresh_pip_ = _refresh_pip

    import __main__
    __main__.__dict__.clear()
    __main__.__dict__.update(dict(
        __name__     = "__main__",

        # normal interactive shell leaves this undefined
        # __file__     = None,

        __builtins__ = builtins
    ))

    installer.activate()

    # should work better now with the virtualenv
    _refresh_pip_()

    code_.interact()


def _find_venv(start_dir):
    """Recursively search upwards in the directory tree until a
    venv folder is located. If not found, None is returned
    """
    venv_path = None
    curr_path = os.path.abspath(start_dir)
    while True:
        test_path = os.path.join(curr_path, "venv")
        if os.path.exists(test_path):
            venv_path = test_path
            break
        new_path = os.path.abspath(os.path.join(curr_path, ".."))
        if new_path == curr_path:
            break
        curr_path = new_path

    return venv_path


def init(venv_dir=None, gen_requirements=False, no_venv=False, debug=False):
    """Init pipless to work in the currently-running python script.

    Note that this function is intended to be used when the pipless module
    is manually imported into a script.

    E.g.

        import pipless
        pipless.init(... opts ...)

    Also note that the requirements.txt is generated at program exit using the
    `atexit` module.
    
    :param venv_dir: the virtual environment path to be used/created. Defaults to the current directory if None
    :param gen_requirements: generate a new requirements.txt before exiting
    :param no_venv: don't create/use a virtual environment (maybe we're already in one?)
    :param debug: print everything that's happening
    """
    currframe = inspect.currentframe()
    calling_frame_info = inspect.getouterframes(currframe, 2)[1]
    calling_frame,calling_file,_,_,_,_ = calling_frame_info

    if not no_venv and venv_dir is None:
        # TODO this may not always be correct - should maybe base it on the directory
        # containing the calling function?
        base_dir = os.path.dirname(calling_file)
        venv_dir = _find_venv(base_dir)
        if venv_dir is None:
            venv_dir = os.path.join(base_dir, "venv")

    installer = PipLess(
        venv_path = venv_dir,
        debug     = debug
    )
    sys.meta_path.append(installer)
    installer.activate()

    if gen_requirements:
        gen_requirements_on_exit(installer.venv_parent_dir)


def gen_requirements_on_exit(dest_dir):
    refresh_pip = _refresh_pip

    def on_exit():
        import pip
        import os
        import sys

        refresh_pip()

        with open(os.path.join(dest_dir, "requirements.txt"), "wb") as f:
            sys.stdout = f
            pip.main(["freeze"])
            sys.stdout = sys.__stdout__

    atexit.register(on_exit)


def main(script_file, venv_path=None, gen_requirements=True, no_venv=False, debug=False, quiet=False):
    """Find or create a virtual environment, setup the automatic
    importer, and run the provided script
    """
    if script_file is not None:
        # Replace pipless's dir with script's dir in front of module search path.
        sys.path[0] = os.path.dirname(script_file)

    # find the virtualenv folder if one wasn't supplied
    if script_file is None:
        venv_path = os.path.join(os.getcwd(), "venv")
    elif not no_venv and venv_path is None:
        venv_path = _find_venv(sys.path[0])
        if venv_path is None:
            # if we're running a script file through pipless, search from the script's
            # directory, not the cwd
            venv_path = os.path.join(os.path.dirname(script_file), "venv")

    installer = PipLess(
        venv_path = venv_path,
        no_venv   = no_venv,
        debug     = debug,
        quiet     = quiet,
    )
    # setup the automatic imports using the venv_path
    sys.meta_path.append(installer)

    if script_file is not None:
        # run the script
        run_script(
            script_file,
            installer,
            gen_requirements = gen_requirements,
        )

    # drop into an interactive shell (just as you would run running python with
    # no arguments)
    else:
        run_interactive_shell(
            installer,
            gen_requirements = gen_requirements,
        )


# someone directly ran the pipless.py file, or (more likely) ran python
# with "python -m pipless script_file [args...]". The latter is the intended
# usage.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        __file__,
        description=__doc__,
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
    parser.add_argument("-r", "--requirements",
        help="generate a fresh requirements.txt before exiting",
        action="store_true",
        default=False
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
    parser.add_argument("--clear",
        help="[venv] clear out the non-root install and start from scratch",
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

    main(
        script_file      = script_file,
        venv_path        = opts.venv,
        gen_requirements = opts.requirements,
        no_venv          = opts.no_venv,
        debug            = opts.debug,
        quiet            = opts.quiet,
    )
