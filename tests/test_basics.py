#!/usr/bin/env python
# encoding: utf-8

"""
Test basic functionality of pipless
"""


import os
import tempfile
import shutil
import subprocess
import sys
import unittest

# so we can import pipless
sys.path.insert(0, os.path.dirname(__file__))


class TestBasics(unittest.TestCase):
    """
    Test the basic functionality of pipless
    """

    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.pipless = os.path.join(self.base_dir, "scripts", "pipless")
        self.tmpdir = tempfile.mkdtemp()

        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmpdir)

    # ---------------------

    def _run(self, *cmd_args, **env):
        new_environ = dict(os.environ)
        if len(env) == 0:
            new_environ["PYTHONPATH"] = self.base_dir + ":" + new_environ.get("PYTHONPATH", "")
            new_environ["PATH"] = os.path.join(self.base_dir, "scripts") + ":" + new_environ.get("PATH", "")
        else:
            new_environ.update(env)

        proc = subprocess.Popen(
            cmd_args,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            env    = new_environ
        )
        stdout,stderr = proc.communicate()
        return stdout

    # ---------------------

    def test_venv_in_current_directory(self):
        test_filename = "test.py"
        with open(test_filename, "wb") as f:
            f.write("\n".join([
                "import sys",
                "import tabulate",
                "print(tabulate)",
                "print(sys.argv)"
            ]))

        test_args = [test_filename, "arg1", "arg2", "--arg3"]
        output = self._run("pipless", *test_args)
        lines = output.split("\n")

        expected_lines = [
            "Collecting tabulate",
            "Installing collected packages: tabulate",
            "Successfully installed tabulate-",
            "<module 'tabulate' from ",
            "['test.py', 'arg1', 'arg2', '--arg3']",
            "",
        ]
        self.assertEqual(len(expected_lines), len(lines))

        req_file = "requirements.txt"
        self.assertTrue(req_file, "requirements.txt not created in current directory")
        with open(req_file, "rb") as f:
            req_lines = f.read().split("\n")

        req_lines = filter(lambda x: x.strip() != "", req_lines)
        self.assertEquals(1, len(req_lines))
        self.assertIn("tabulate==", req_lines[0])

    def test_venv_in_specific_directory(self):
        tmpdir2 = tempfile.mkdtemp()
        venv_tmpdir = os.path.join(tmpdir2, "venv")

        try:
            test_filename = "test.py"
            with open(test_filename, "wb") as f:
                f.write("\n".join([
                    "import sys",
                    "import tabulate",
                    "print(tabulate)",
                    "print(sys.argv)"
                ]))

            test_args = [test_filename, "arg1", "arg2", "--arg3"]
            output = self._run("pipless", "--venv", venv_tmpdir, *test_args)
            lines = output.split("\n")

            expected_lines = [
                "Collecting tabulate",
                "Installing collected packages: tabulate",
                "Successfully installed tabulate-",
                "<module 'tabulate' from ",
                "['test.py', 'arg1', 'arg2', '--arg3']",
                "",
            ]
            self.assertEqual(len(expected_lines), len(lines))

            req_file = os.path.join(tmpdir2, "requirements.txt")
            self.assertTrue(
                os.path.exists(req_file),
                "requirements.txt not created in same directory as specific venv"
            )
            with open(req_file, "rb") as f:
                req_lines = f.read().split("\n")

            req_lines = filter(lambda x: x.strip() != "", req_lines)
            self.assertEquals(1, len(req_lines))
            self.assertIn("tabulate==", req_lines[0])

        finally:
            shutil.rmtree(tmpdir2)

    def test_quiet(self):
        test_filename = "test.py"
        with open(test_filename, "wb") as f:
            f.write("\n".join([
                "import sys",
                "import tabulate",
                "print(tabulate)",
                "print(sys.argv)"
            ]))

        test_args = [test_filename, "arg1", "arg2", "--arg3"]
        output = self._run("pipless", "--quiet", *test_args)
        lines = output.split("\n")

        expected_lines = [
            "<module 'tabulate' from ",
            "['test.py', 'arg1', 'arg2', '--arg3']",
            "",
        ]
        self.assertEqual(len(expected_lines), len(lines))

        req_file = "requirements.txt"
        self.assertTrue(
            os.path.exists(req_file),
            "requirements.txt not created in current directory"
        )
        with open(req_file, "rb") as f:
            req_lines = f.read().split("\n")

        req_lines = filter(lambda x: x.strip() != "", req_lines)
        self.assertEquals(1, len(req_lines))
        self.assertIn("tabulate==", req_lines[0])

    def test_no_requirements_txt(self):
        test_filename = "test.py"
        with open(test_filename, "wb") as f:
            f.write("\n".join([
                "import sys",
                "import tabulate",
                "print(tabulate)",
                "print(sys.argv)"
            ]))

        test_args = [test_filename, "arg1", "arg2", "--arg3"]
        output = self._run("pipless", "--no-requirements", *test_args)
        lines = output.split("\n")

        expected_lines = [
            "Collecting tabulate",
            "Installing collected packages: tabulate",
            "Successfully installed tabulate-",
            "<module 'tabulate' from ",
            "['test.py', 'arg1', 'arg2', '--arg3']",
            "",
        ]
        self.assertEqual(len(expected_lines), len(lines))

        req_file = "requirements.txt"
        self.assertFalse(
            os.path.exists(req_file),
            "requirements.txt was created in current directory"
        )

    def test_import_in_script(self):
        test_filename = "test.py"
        with open(test_filename, "wb") as f:
            f.write("\n".join([
                "import sys",
                "import pipless",
                "pipless.init()",
                "import tabulate",
                "print(tabulate)",
                "print(sys.argv)"
            ]))

        self._run("virtualenv", "venv")

        venv_home = os.path.abspath("venv")
        test_args = [test_filename, "arg1", "arg2", "--arg3"]

        # "activate" the virtual environment we created above by
        # setting a few environment variables. We need to do this
        # because directly calling pipless.init() assumes that we
        # are either already in a virtual environment, or that we
        # have permissions to do a normal "pip install".
        output = self._run(
            "python",
            *test_args,
            **{
                "_": os.path.join(venv_home, "bin", "python"),
                "VIRTUAL_ENV": venv_home,
                "PATH": os.path.join(venv_home, "bin") + ":" + os.environ["PATH"],
                # pipless will be able to be imported in the new process
                "PYTHONPATH": self.base_dir + ":" + os.environ.get("PYTHONPATH", "")
            }
        )
        lines = output.split("\n")

        expected_lines = [
            "Collecting tabulate",
            "Installing collected packages: tabulate",
            "Successfully installed tabulate-",
            "<module 'tabulate' from ",
            "['test.py', 'arg1', 'arg2', '--arg3']",
            "",
        ]
        self.assertEqual(len(expected_lines), len(lines))

        req_file = "requirements.txt"
        self.assertTrue(
            os.path.exists(req_file),
            "requirements.txt not created in current directory"
        )
        with open(req_file, "rb") as f:
            req_lines = f.read().split("\n")

        req_lines = filter(lambda x: x.strip() != "", req_lines)
        self.assertEquals(1, len(req_lines))
        self.assertIn("tabulate==", req_lines[0])


if __name__ == "__main__":
    unittest.main()
