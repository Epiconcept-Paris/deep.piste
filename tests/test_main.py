import unittest

import pytest
from dpiste import __main__


class HealthTest(unittest.TestCase):
    """
    Tests for basic CLI commands. These tests are health tests meaning
    that if they don't succeed, the package is not working in your
    environment.
    """

    @pytest.fixture(autouse=True)
    def capfd(self, capfd):
        """Define capfd, an object used to capture stdout and stderr"""
        self.capfd = capfd

    def test_main(self):
        """
        Nominal scenario: help on top-level parser 
        (Shortest command available)
        """
        with self.assertRaises(SystemExit) as status:
            __main__.main(['-h'])

        # Exit Status Code 0 = normal exit
        self.assertEqual(status.exception.code, 0)

        out, err = self.capfd.readouterr()
        # These are two messages that should be shown to the user
        basic_info = "[-h] {extract,transform,export,backup}"
        help_info = "show this help message and exit"
        self.assertIn(basic_info, out)
        self.assertIn(help_info, out)
