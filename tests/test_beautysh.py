from beautysh import Beautify
from unittest import TestCase
import os

TEST_BASIC_FILENAME = os.path.join(os.path.dirname(__file__), 'basictest.sh')
TEST_INDENT1_RAW_FILENAME = os.path.join(os.path.dirname(__file__), 'indent_test1_raw.sh')
TEST_INDENT1_BEAUTIFIED_FILENAME = os.path.join(os.path.dirname(__file__), 'indent_test1_beautified.sh')

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

    def test_indent1(self):
        testdata = self.read_file(TEST_INDENT1_RAW_FILENAME)
        expecteddata = self.read_file(TEST_INDENT1_BEAUTIFIED_FILENAME)
        result, error = Beautify().beautify_string(testdata)
        self.assertFalse(error);  # we expect no parsing error
        self.assertTrue(expecteddata == result) # we expect no change in formatting
