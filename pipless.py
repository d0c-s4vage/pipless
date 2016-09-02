#!/usr/bin/env python
# encoding: utf-8
# Created by James "d0c_s4vage" Johnson
# https://github.com/d0c-s4vage/pipless
# MIT License


"""
pipless creates/activates a virtualenv in which the python process
will operate. pipless hooks the import process and automatically
installs missing packages into the current environment.  On process
exit, pipless will generate a new requirements.txt in the same
directory that the virtual env folder exists in.

pipless can be used in three ways:

1. To directly run scripts:

    pipless test.py --arg1 --arg2 val

2. Interactively. Running pipless without a script will drop you
   into an interactive shell:

        /tmp $ pipless
        Python 2.7.10 (default, Oct 14 2015, 16:09:02) 
        [GCC 5.2.1 20151010] on linux2
        Type "help", "copyright", "credits" or "license" for more information.
        (InteractiveConsole)
        >>> 
        
3. Importing and manually initializing pipless:

        import pipless
        pipless.init(..opts..)

See https://github.com/d0c-s4vage/pipless for more details.
"""

logo = """
               ░░┐            ▄▄▄       ▄▄▄▄▄▄▄▄▄   ▄▄▄▄▄▄▄▄▄   ▄▄▄▄▄▄▄▄▄ 
              ░░┌┘           ▐░░░▌     ▐░░░░░░░░░▌ ▐░░░░░░░░░▌ ▐░░░░░░░░░▌
             ░░┌┘            ▐░░░▌     ▐░░░▛▀▀▀▀▀  ▐░░░▛▀▀▀▀▀  ▐░░░▛▀▀▀▀▀ 
 +━━+        └─┘ +━━+        ▐░░░▌     ▐░░░▌       ▐░░░▌       ▐░░░▌      
 ┃╳╳━━━━━━━+ +━+ ┃╳╳━━━━━━━+ ▐░░░▌     ▐░░░▙▄▄▄▄▄  ▐░░░▙▄▄▄▄▄  ▐░░░▙▄▄▄▄▄ 
 ┃╳╳┃      ┃ ┃╳┃ ┃╳╳┃      ┃ ▐░░░▌     ▐░░░░░░░░░▌ ▐░░░░░░░░░▌ ▐░░░░░░░░░▌
 ┃╳╳┃      ┃ ┃╳┃ ┃╳╳┃      ┃ ▐░░░▌     ▐░░░▛▀▀▀▀▀   ▀▀▀▀▀▜░░░▌  ▀▀▀▀▀▜░░░▌
 ┃╳╳━━━━━━━+ +━+ ┃╳╳━━━━━━━+ ▐░░░▌     ▐░░░▌             ▐░░░▌       ▐░░░▌
 ┃╳╳┃            ┃╳╳┃        ▟░░░▙▄▄▄▄▄▟░░░▙▄▄▄▄▄▄▄▄▄▄▄▄▄▟░░░▙▄▄▄▄▄▄▄▟░░░▌
 ┃╳╳┃            ┃╳╳┃       ▐░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▌
 +━━+            +━━+        ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ 
"""


# these will be used before we wipe out __main__
import argparse
import atexit
import fnmatch
import code
import imp
import inspect
import pip
from pip.commands.search import SearchCommand
import os
import shutil
import sys


VENV_ACTIVATED = False


class PipLess(object):
    """A class to automatically install missing python packages into
    a virtual environment.
    """

    def __init__(self, venv_path=None, quiet=True, no_venv=False, debug=False, requirements=True):
        """Initialize the package auto-installer and setup the
        virtual environment (if it doesn't already exist).
        
        If venv_path is None, a virtual environment named
        "venv" will be created in the current working directory

        :param str venv_path: The path to the virtual environment. The requirements.txt wil be saved into
            this path's parent directory.
        :param bool quiet: do not print any output
        :param bool no_venv: do not create or activate a virtual environment
        :param bool debug: print verbose debug output
        :param bool requirements: generate a requirements.txt on program exit
        """
        self.debug               = debug

        self.venv_home           = venv_path
        if self.venv_home is not None:
            self.venv_home       = os.path.abspath(venv_path)
            self.venv_parent_dir = os.path.dirname(self.venv_home)
        else:
            self.venv_parent_dir = ""
        self.no_venv             = no_venv
        self.quiet               = quiet
        self.no_requirements     = (not requirements)

        if requirements:
            atexit.register(self._on_exit)


        # keep a reference to these modules. We don't want to pollute
        # the global namespace by using normal imports. Plus this avoids
        # recursive import problems
        self._imp            = imp
        self._os             = os
        self._pip            = pip
        self._sys            = sys
        self._search_command = SearchCommand

        self._debug("created new PipLess")
        self._debug("    debug           : {}".format(self.debug))
        self._debug("    venv_home       : {}".format(self.venv_home))
        self._debug("    venv_parent_dir : {}".format(self.venv_parent_dir))
        self._debug("    no_venv         : {}".format(self.no_venv))
        self._debug("    quiet           : {}".format(self.quiet))


        if not no_venv:
            self._create_virtual_env()
        else:
            self._debug("not creating virtual environment")

    def _on_exit(self):
        import pip
        import os
        import sys

        self._refresh_pip()

        req_path = os.path.join(self.venv_parent_dir, "requirements.txt")
        self._debug("saving requirements.txt to {!r}".format(req_path))

        with open(req_path, "wb") as f:
            sys.stdout = f
            pip.main(["freeze"])
            sys.stdout = sys.__stdout__

    def _refresh_pip(self):
        self._debug("refreshing pip's module list")

        # Pip keeps track of the currently loaded modules in the current script
        # (and the current working set, etc) by creating a list of modules that
        # are accessible from sys.path (basically).
        # 
        # this list is generated when pip is first imported. This function
        # forces that list to be regenerated.
        from pip._vendor.pkg_resources import _initialize_master_working_set
        _initialize_master_working_set()

    def _info(self, msg):
        if self.quiet:
            return
        print("\n".join("[PIPLESS]:INF {}".format(x) for x in msg.split("\n")))
        self._sys.stdout.flush()

    def _debug(self, msg):
        if self.quiet:
            return

        if self.debug:
            print("\n".join("[PIPLESS]:DBG: {}".format(x) for x in msg.split("\n")))
            self._sys.stdout.flush()

    def activate(self):
        """Activate the virtual environment.
        
        This actually restarts the pipless script using `os.execve()` to
        replace itself with a subprocess that uses the correct python binary
        from the venv/bin directory with the correct environment variables.
        """
        if self.no_venv:
            self._debug("no_venv was set, not activating")
            return

        new_environ = dict(os.environ)
        new_environ["PATH"] = os.path.join(self.venv_home, "bin") + ":" + new_environ["PATH"]
        new_environ["VIRTUAL_ENV"] = os.path.abspath(self.venv_home)
        new_environ["_"] = os.path.join(self.venv_home, "bin", "python")

        self._debug("replacing current process with new python in new env from venv")
        self._debug("venv found at {!r}".format(self.venv_home))
        venv_python_path = os.path.join(self.venv_home, "bin", "python")

        new_args = [
            venv_python_path,
            "-m", "pipless",
            "--no-venv",

            # even though we say to not use the venv, this is still
            # used to determine where to save the requirements.txt file
            "--venv", self.venv_home
        ]
        if self.debug:
            new_args.append("--debug")
        if self.quiet:
            new_args.append("--quiet")
        if self.no_requirements:
            new_args.append("--no-requirements")

        os.execve(
            venv_python_path,
            new_args + sys.argv,
            new_environ
        )

    def _create_virtual_env(self):
        """Create the new virtual environment if it does not yet exist.
        
        Also ensure that pipless.py and the pipless script get copied into
        the new virtual environment (the new virtual environment should use
        the same version of pipless as the previou environment).
        """
        import virtualenv
        self._debug("creating virtual environment at {}".format(self.venv_home))
        virtualenv.create_environment(
            self.venv_home,
            site_packages = False,
            clear         = True
        )

        site_packages_dirs = []
        for root, dirnames, filesnames in os.walk(self.venv_home):
            for dirname in dirnames:
                if dirname == "site-packages":
                    site_packages_dirs.append(os.path.join(root, dirname))

        self._debug("copying 'bin/pipless' into virtual env")
        shutil.copy(self._which("pipless"), os.path.join(self.venv_home, "bin", "pipless"))

        for site_packages_dir in site_packages_dirs:
            new_pipless = os.path.join(site_packages_dir, "pipless.py")
            self._debug("copying pipless.py module into virtual env at '{}'".format(new_pipless))
            shutil.copy(__file__, new_pipless)

    def _which(self, program):
        """Simple function to determine the path of an executable.

        Borrowed from https://github.com/amoffat/sh/blob/master/sh.py#L300.
        Thanks Andrew Moffat! sh is pretty awesome :^)
        """
        def is_exe(fpath):
            return (os.path.exists(fpath) and
                    os.access(fpath, os.X_OK) and
                    os.path.isfile(os.path.realpath(fpath)))

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            if "PATH" not in os.environ:
                return None
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None

    def find_module(self, fullname, path=None):
        """This is called as the finder part of the sys.meta_path hook that
        was installed.  See PEP 302 (https://www.python.org/dev/peps/pep-0302/)
        for more details.

        Instead of acting as both the finder and the loader object as defined
        in PEP 302, we only act as the finder object. If a package is not yet
        installed, but can be installed through PyPI, we install the package,
        and then return None, meaning that we did not find the package and
        could not return a loader object with which the package should be loaded.

        Returning None from this method will cause the normal Python import
        process to resume, which will pick up our newly installed python
        package.

        :param str fullname: The fullname of the module being imported
        :param str path: Not used by pipless - see PEP 302
        """
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

            if self.quiet:
                import logging
                pip_log = logging.getLogger("pip")
                _level = pip_log.level
                pip_log.setLevel(logging.CRITICAL)

            try:
                self._pip.main(["install", fullname])
            finally:
                if self.quiet:
                    pip_log.setLevel(_level)

        # we've made it accessible to the normal import procedures
        # now, (should be on sys.path), so we'll return None which
        # will make Python attempt a normal import
        return None

    def _package_exists_in_pypi(self, fullname):
        """Check pypi using pip to see if the package exists.
        """
        # TODO maybe use xmlrpclib directly instead of going through pip? - see
        # https://wiki.python.org/moin/PyPIXmlRpc for a good example.

        # TODO: use a pre-compiled mapping of import names
        # to install names. Until then, going by exact matches
        # will have to do
        searcher = self._search_command()
        options,args = searcher.parse_args([fullname])
        matches = searcher.search(args, options)
        found_match = None
        for match in matches:
            if match["name"] == fullname:
                return True
                break

        return False


def _run_script(script_file):
    """Run the script at the provided path

    :param str script_file: A path to a python script to run
    """
    builtins = __builtins__

    import __main__
    __main__.__dict__.clear()
    __main__.__dict__.update(dict(
        __name__     = "__main__",
        __file__     = script_file,
        __builtins__ = builtins
    ))
    globals = __main__.__dict__
    locals = globals

    # repr will put the script_file into quotes and escape any
    # unruly characters

    # NOTE that at this point, sys.argv will already have been reset
    # so that it will look like (from script_file's point of view),
    # that it was the first file run instead of pipless.
    exec 'execfile({})'.format(repr(script_file)) in globals, locals


def _run_interactive_shell():
    """Run an interactive shell as if it were the first thing being
    run.
    """
    builtins = __builtins__
    code_ = code

    import __main__
    __main__.__dict__.clear()
    __main__.__dict__.update(dict(
        __name__     = "__main__",

        # normal interactive shell leaves this undefined
        # __file__     = None,

        __builtins__ = builtins
    ))

    code_.interact()


def _find_venv(start_dir):
    """Recursively search upwards in the directory tree until a
    venv folder is located. If not found, None is returned

    :param str start_dir: The start directory from which to search upwards for a venv folder
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


def init(gen_requirements=True, debug=False, quiet=False):
    """Init pipless to work in the currently-running python script.

    Note that it is assumed that the currently-running script is already
    either in a virtual environment, or is able to install things
    normally via "pip install"

    This function is intended to be used when the pipless module
    is manually imported into a script.

    E.g.

        import pipless
        pipless.init(... opts ...)
    
    :param bool gen_requirements: generate a new requirements.txt before exiting 
    :param bool debug: print all debug statements
    :param bool quiet: print nothing
    """
    currframe = inspect.currentframe()
    calling_frame_info = inspect.getouterframes(currframe, 2)[1]
    calling_frame,calling_file,_,_,_,_ = calling_frame_info

    pipless_import_hook = PipLess(
        no_venv      = True,
        debug        = debug,
        requirements = gen_requirements,
        quiet        = quiet
    )
    # NOTE: do not activate it!
    sys.meta_path.append(pipless_import_hook)


def main(script_file=None, venv_path=None, gen_requirements=True, no_venv=False, debug=False, quiet=False):
    """Find or create a virtual environment, setup the automatic
    importer, and run an interactive shell or a script at the provided path.

    Note that if no ``venv_path`` is specified, all parent directories will be
    searched for a ``venv`` folder.

    E.g., if pipless is run in the directory ``/tmp/test/a/b/c``, and ``venv_path`` is
    not specified, then the following directories will be checked for existence and used
    as the ``venv_path`` if found:

    .. code-block:: text

        /tmp/test/a/b/c/venv
        /tmp/test/a/b/venv
        /tmp/test/a/venv
        /tmp/test/venv
        /tmp/venv/
        /venv

    The ``requirements.txt`` file will always be written into the directory
    containing the virtual environment folder.

    :param str script_file: The python script to run. (can be None)
    :param str venv_path: The path at which to create/activate the virtual environment
    :param bool gen_requirements: If a requirements.txt should be generated at process exit.
    :param bool no_venv: If a virtual environment should not be created/activated.
    :param bool debug: Display verbose debug statements
    :param bool quiet: Do not display any text while executing
    """
    if script_file is not None:
        # Replace pipless's dir with script's dir in front of module search path.
        sys.path[0] = os.path.dirname(script_file)

        if venv_path is None:
            # if we're running a script file through pipless, search from the script's
            # directory, not the cwd
            venv_path = _find_venv(sys.path[0])
            if venv_path is None:
                venv_path = os.path.join(os.path.dirname(script_file), "venv")

    elif venv_path is None:
        venv_path = os.path.join(os.getcwd(), "venv")

    pipless_import_hook = PipLess(
        venv_path    = venv_path,
        no_venv      = no_venv,
        debug        = debug,
        quiet        = quiet,
        requirements = gen_requirements
    )
    pipless_import_hook.activate()

    # setup the automatic imports using the venv_path
    sys.meta_path.append(pipless_import_hook)

    if script_file is not None:
        # run the script
        _run_script(script_file)

    # drop into an interactive shell (just as you would run running python with
    # no arguments)
    else:
        _run_interactive_shell()


# someone directly ran the pipless.py file, ran python with
# "python -m pipless script_file [args...]", or ran the pipless
# executable script. The latter is the intended usage.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        __file__,
        description=logo+"\n"+__doc__,
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

    main(
        script_file      = script_file,
        venv_path        = opts.venv,
        gen_requirements = opts.no_requirements,
        no_venv          = opts.no_venv,
        debug            = opts.debug,
        quiet            = opts.quiet,
    )
