# NEED MUCH MORE COVERAGE

from stimprogram.GammaCorrection import GammaValues
from stimprogram import StimProgramGUI
import unittest
import os


class TestParameters(unittest.TestCase):

    def setUp(self):
        self.params = StimProgramGUI.Parameters()

    def test_read_config_file(self):
        a, b, = self.params.read_config_file(os.path.abspath(
            '.\psychopy\config.ini'))


if __name__ == '__main__':
    unittest.main()