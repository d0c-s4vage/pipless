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
import re
import six
import shutil
import subprocess
import sys


__version__ = "0.1.2"


VENV_ACTIVATED = False


class PiplessException(Exception): pass
class IgnoreMissingImport(PiplessException): pass


class PipLessMapping(object):
    """A class that loads a pipless mapping file
    """

    def __init__(self):
        """
        """
        self.mapping = {}

    def load(self, path):
        """Load a pipless mapping file into this PipLessMapping instance.
        Loading a new mapping may overwrite existing (default) mapping
        entries. No errors are raised if ``path`` does not exist.

        A mapping file consists of zero or more mapping lines, optionally
        with comment lines (beginning with ``#``).
        
        Each mapping begins with the package name (what you import with),
        followed by the distribution name (what you install with). E.g.:

        .. code-block:: text

           # this is a comment
           flask  Flask
   
           yaml   PyYaml # another comment
           jinja2 Jinja2


        :param str path: The path of the mapping file to load.
        """
        if not os.path.exists(path):
            return

        with open(path, "rb") as f:
            data = f.read()

        # remove comment lines
        data = re.sub(r'#.*', '', data)
        mapping_lines = filter(lambda x: x.strip() != "", data.split("\n"))

        for line in mapping_lines:
            line = line.strip()
            
            # split on whitespace
            parts = line.split()
            if not parts[0].startswith("-") and len(parts) < 2:
                continue

            if parts[0].startswith("-"):
                package_name = parts[0][1:]
                distro_name = IgnoreMissingImport
            else:
                package_name = parts[0]
                distro_name = parts[1]

            self.mapping[package_name] = distro_name

    def get(self, import_name):
        """Return the distribution name from the mapping for
        the package name, or ``None`` if it is not defined.

        :param str import_name: The package name to look up the distribution name for
        """
        res = self.mapping.get(import_name, None)
        if res == IgnoreMissingImport:
            raise IgnoreMissingImport()
        return res


class PipLess(object):
    """A class to automatically install missing python packages into
    a virtual environment.
    """

    def __init__(
            self,
            venv_path    = None,
            quiet        = True,
            no_venv      = False,
            debug        = False,
            no_install   = False,
            requirements = True,
            venv_opts    = None,
            python_opts  = None,
            color        = False,
            no_color     = False,
        ):
        """Initialize the package auto-installer and setup the
        virtual environment (if it doesn't already exist).
        
        If venv_path is None, a virtual environment named
        "venv" will be created in the current working directory

        :param str venv_path: The path to the virtual environment. The requirements.txt wil be saved into
            this path's parent directory.
        :param bool quiet: do not print any output
        :param bool no_venv: do not create or activate a virtual environment
        :param bool debug: print verbose debug output
        :param bool no_install: don't install anything, implies ``requirements=False``
        :param bool requirements: generate a requirements.txt on program exit
        :param dict venv_opts: options for ``clear``, ``python``, and ``system_site_packages``
        :param bool color_override: if ``True``, color will always be used in the output
        """
        if venv_opts is None:
            venv_opts = {}
        self.venv_opts = venv_opts
        self.venv_clear = venv_opts.get("clear", False)
        self.venv_system_site_packages = venv_opts.get("system_site_packages", False)
        self.venv_python = venv_opts.get("python", None)

        if python_opts is None:
            python_opts = {}
        self.python_opts = python_opts

        self.no_install          = no_install
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
        self.no_color            = no_color
        self.color               = color

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

        # load the mapping files
        self._mapping        = PipLessMapping()
        self._mapping.load(
            os.path.join(os.path.dirname(__file__), "mappings.txt")
        )
        self._mapping.load(
            os.path.expanduser(os.path.join("~", ".config", "pipless", "mappings.txt"))
        )

        self._debug("created new PipLess")
        self._debug("    debug                       : {}".format(self.debug))
        self._debug("    venv_home                   : {}".format(self.venv_home))
        self._debug("    venv_parent_dir             : {}".format(self.venv_parent_dir))
        self._debug("    no_venv                     : {}".format(self.no_venv))
        self._debug("    quiet                       : {}".format(self.quiet))
        self._debug("    venv --clear                : {}".format(self.venv_clear))
        self._debug("    venv --python               : {}".format(self.venv_python))
        self._debug("    venv --system-site-packages : {}".format(self.venv_system_site_packages))
        self._debug("    python opts: {}".format(self.python_opts))

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

    def _should_color(self):
        return (sys.stdout.isatty() or self.color) and not self.no_color

    def _debug(self, msg):
        if self.quiet:
            return

        if self._should_color():
            # yellow
            color_start = "\x1b[34m"
            color_end = "\x1b[0m"
        else:
            color_start = ""
            color_end = ""

        if self.debug:
            print(
                color_start + \
                "\n".join("[PIPLESS]:DBG: {}".format(x) for x in msg.split("\n")) + \
                color_end
            )
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
        if self.venv_clear:
            new_args.append("--clear")
        if self._should_color():
            new_args.append("--color")
        if self.venv_system_site_packages:
            new_args.append("--system-site-packages")
        if self.venv_python is not None:
            new_args.append("--python")
            new_args.append(self.venv_python)

        if self.python_opts.get("module", None) is not None:
            new_args.append("-m")
            new_args.append(self.python_opts.get("module"))
        if self.python_opts.get("cmd", None) is not None:
            new_args.append("-c")
            new_args.append(self.python_opts.get("cmd"))

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
        if os.path.exists(self.venv_home) and self.venv_clear == False:
            self._debug("virtualenv already exists at '{}' and --clear was not set".format(
                self.venv_home
            ))
            return

        import virtualenv
        self._debug("creating virtual environment at {}".format(self.venv_home))

        venv_args = ["virtualenv"]

        if self.venv_clear:
            venv_args.append("--clear")
        if self.venv_system_site_packages:
            venv_args.append("--system-site-packages")
        if self.venv_python:
            venv_args.append("--python")
            venv_args.append(self.venv_python)

        venv_args.append(self.venv_home)

        self._debug("executing virtualenv: {}".format(venv_args))
        proc = subprocess.Popen(venv_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout,_ = proc.communicate()
        if proc.poll() != 0:
            raise Exception("Error creating the virtual environment!\n\n{}" + stdout)

        site_packages_dirs = []
        for root, dirnames, filesnames in os.walk(self.venv_home):
            for dirname in dirnames:
                if dirname == "site-packages":
                    site_packages_dirs.append(os.path.join(root, dirname))

        self._debug("copying six module into virtual env")
        six_file = six.__file__.replace(".pyc", ".py")
        dest_six_file = os.path.join(site_packages_dirs[0], "six.py")
        shutil.copy(six_file, dest_six_file)

        self._debug("copying 'bin/pipless' into virtual env")
        shutil.copy(self._which("pipless"), os.path.join(self.venv_home, "bin", "pipless"))

        filenames = [
            "__init__.py",
            "__main__.py",
            "mappings.txt"
        ]

        for filename in filenames:
            file_to_copy = os.path.join(os.path.dirname(__file__), filename)

            site_packages_dir = site_packages_dirs[0]
            new_file = os.path.join(site_packages_dir, "pipless", filename)
            if not os.path.exists(os.path.dirname(new_file)):
                os.makedirs(os.path.dirname(new_file))

            self._debug("copying {} into virtual env at '{}'".format(
                file_to_copy,
                new_file
            ))
            shutil.copy(file_to_copy, new_file)

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

        try:
            distro_name = self._get_pypi_distro_name(fullname)
        except IgnoreMissingImport:
            self._debug("told to ignore '{}' import, ignoring".format(fullname))
            return None

        if distro_name is not None:
            stack = inspect.stack()
            last_frame = stack[1]
            self._debug("import from {}:{} ({!r})".format(
                last_frame[1], last_frame[2], last_frame[4]
            ))
            self._debug("module {} exists in pypi, installing".format(fullname))

            if self.quiet:
                import logging
                pip_log = logging.getLogger("pip")
                _level = pip_log.level
                pip_log.setLevel(logging.CRITICAL)
            elif self._should_color():
                self._sys.stdout.write("\x1b[36m")

            try:
                self._pip.main(["install", fullname])
            finally:
                if self.quiet:
                    pip_log.setLevel(_level)
                elif self._should_color():
                    self._sys.stdout.write("\x1b[0m")

        # we've made it accessible to the normal import procedures
        # now, (should be on sys.path), so we'll return None which
        # will make Python attempt a normal import
        return None

    def _get_pypi_distro_name(self, fullname):
        """Lookup a mapping for the import name ``fullname`` in the
        mapping files. If a mapping of the package name to the distribution name
        does not exist, check if an exact match exists in PyPI.

        :param str fullname: the fullname of the package
        :returns: returns None if the distribution name is unknown, else
        the distribution (install) name
        """
        mapped_name = self._package_pypi_mapping_defined(fullname)
        if mapped_name is not None:
            return mapped_name

        # TODO maybe use xmlrpclib directly instead of going through pip? - see
        # https://wiki.python.org/moin/PyPIXmlRpc for a good example.
        searcher = self._search_command()
        options,args = searcher.parse_args([fullname])
        matches = searcher.search(args, options)
        found_match = None
        for match in matches:
            if match["name"] == fullname:
                return fullname
                break

        return None

    def _package_pypi_mapping_defined(self, fullname):
        """Check the global pipless-mappings file as well as the user's
        ~/.config/pipless/mappings file (if it exists) to see if a mapping
        of the package name to the distribution name exists
        """
        res = self._mapping.get(fullname)
        if res is not None:
            self._debug("found mapping! {} <-> {}".format(
                fullname, res
            ))
        return res


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


def _run_single_command(cmd):
    """Run a single command inside the virtual environment
    """
    builtins = __builtins__

    # this is how the python -c command works
    sys.argv.insert(0, "-c")

    import __main__
    __main__.__dict__.clear()
    __main__.__dict__.update(dict(
        __name__     = "__main__",

        # file is not defined when 'python -c "print(__file__)"' is run
        #__file__     = script_file,

        __builtins__ = builtins
    ))
    globals = __main__.__dict__
    locals = globals

    code = compile(cmd, "<string>", "single")
    exec code in globals, locals


def _find_module_path(module_name, mod_path=None):
    """Recursively find the module path. ImportError will
    be raised if the module cannot be found.
    """
    parts = module_name.split(".")

    find_args = [parts[0]]
    if mod_path is not None:
        find_args.append([mod_path])

    file_,mod_path,desc = imp.find_module(*find_args)

    if len(parts) > 1:
        return _find_module_path(".".join(parts[1:]), mod_path)

    return mod_path


def _run_python_module(module_name):
    """Run a python module (just like python -m modulename)
    """
    try:
        mod_path = _find_module_path(module_name)
    except ImportError as e:
        sys.stderr.write("{}: No module named {}\n".format(__file__, module_name))
        exit(1)

    if os.path.isfile(mod_path):
        sys.argv.insert(0, mod_path)
        _run_script(mod_path)
        return

    elif os.path.isdir(mod_path):
        # TODO what if it's just a .pyc file? that should work, right?
        main_file = os.path.join(mod_path, "__main__.py")
        if not os.path.exists(main_file):
            sys.stderr.write("{}: No module named {}.__main__\n".format(__file__, module_name))

        sys.argv.insert(0, main_file)
        _run_script(main_file)
        return


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


def init(
        gen_requirements     = True,
        debug                = False,
        quiet                = False,
        clear                = False,
        system_site_packages = False,
        python               = None
    ):
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
    :param bool clear: if virtualenv should be run with --clear
    :param bool system_site_packages: if virtualenv should be run with --system-site-packages
    :param str python: the path to the python executable to use in the virtual environment.
    """
    currframe = inspect.currentframe()
    calling_frame_info = inspect.getouterframes(currframe, 2)[1]
    calling_frame,calling_file,_,_,_,_ = calling_frame_info

    pipless_import_hook = PipLess(
        no_venv      = True,
        debug        = debug,
        requirements = gen_requirements,
        quiet        = quiet,
        venv_opts    = dict(
            clear                = clear,
            system_site_packages = system_site_packages,
            python               = python
        ),
    )
    # NOTE: do not activate it!
    sys.meta_path.append(pipless_import_hook)


# TODO it might be time to pull all of these options out into
# a generic **kwargs dict and set defaults on them. Not my favorite,
# as it's easy to get out of sync with the documentation though.
def main(
        script_file               = None,
        venv_path                 = None,
        gen_requirements          = True,
        no_venv                   = False,
        debug                     = False,
        quiet                     = False,
        no_install                = False,
        color                     = False,
        no_color                  = False,
        python_cmd                = None,
        python_module             = None,
        venv_clear                = False,
        venv_python               = None,
        venv_system_site_packages = False,
    ):
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
    :param bool no_install: Don't install anything, only use the virtual environment. Implies ``gen_requirements=False``
    :param bool quiet: Do not display any text while executing
    :param bool color: Always use color in the output (default only when a tty is attached)
    :param bool no_color: Never use color in the output
    :param str python_module: The python module to run as a script (just like python -m)
    :param str python_cmd: The single python command to run (just like python -c)
    :param bool venv_clear: Clear out the virtual environment and start over (virtualenv --clear)
    :param str venv_python: The python executable to use (virtualenv --python)
    :param bool venv_system_site_packages: Use system site packages when create the virtual environment (virtualenv --system-site-packages)
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
        requirements = gen_requirements,
        no_install   = no_install,
        color        = color,
        no_color     = no_color,
        venv_opts    = dict(
            clear                = venv_clear,
            python               = venv_python,
            system_site_packages = venv_system_site_packages
        ),
        python_opts = dict(
            module = python_module,
            cmd    = python_cmd
        )
    )
    pipless_import_hook.activate()

    if not no_install:
        # setup the automatic imports using the venv_path
        sys.meta_path.append(pipless_import_hook)

    if script_file is not None:
        _run_script(script_file)

    elif python_cmd is not None:
        _run_single_command(python_cmd)

    elif python_module is not None:
        _run_python_module(python_module)

    # drop into an interactive shell (just as you would run running python with
    # no arguments)
    else:
        _run_interactive_shell()
