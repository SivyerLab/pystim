# NEED MUCH MORE COVERAGE

from pyStim.GammaCorrection import GammaValues
from pyStim import pyStimGUI
import unittest
import os


class TestParameters(unittest.TestCase):

    def setUp(self):
        self.params = pyStimGUI.Parameters()

    def test_read_config_file(self):
        a, b, = self.params.read_config_file(os.path.abspath(
            '.\psychopy\config.ini'))


if __name__ == '__main__':
    unittest.main()