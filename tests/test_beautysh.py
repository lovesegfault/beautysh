from beautysh import Beautify
from unittest import TestCase
import os

TEST_BASIC_FILENAME = os.path.join(os.path.dirname(__file__), 'basictest.sh')

class TestBasic(TestCase):
    
    def read_file(self, fp):
        """Read input file."""
        with open(fp) as f:
            return f.read()
        
    def test_basic(self):
        testdata = self.read_file(TEST_BASIC_FILENAME)
        result, error = Beautify().beautify_string(testdata)
        self.assertFalse(error);  # we expect no parsing error
        self.assertTrue(testdata == result) # we expect no change in formatting
