from beautysh import Beautify
from unittest import TestCase
import os

def get_string(s):
    return string.printable + s + string.printable

TEST_BASIC_FILENAME = os.path.join(os.path.dirname(__file__), 'basictest.sh')
TEST_GETOPTS1_RAW_FILENAME = os.path.join(os.path.dirname(__file__), 'getopts1_raw.sh')
TEST_GETOPTS1_BEAUTIFIED_FILENAME = os.path.join(os.path.dirname(__file__), 'getopts1_beautified.sh')
TEST_INDENT1_RAW_FILENAME = os.path.join(os.path.dirname(__file__), 'indent_test1_raw.sh')
TEST_INDENT1_BEAUTIFIED_FILENAME = os.path.join(os.path.dirname(__file__), 'indent_test1_beautified.sh')
TEST_FUNCSTYLES_RAW_FILENAME = os.path.join(os.path.dirname(__file__), 'func_styles_raw.sh')
TEST_FUNCSTYLES_BEAUTIFIED_STYLE_FILENAME = [
    os.path.join(os.path.dirname(__file__), 'func_styles_beautified_style0.sh'),
    os.path.join(os.path.dirname(__file__), 'func_styles_beautified_style1.sh'),
    os.path.join(os.path.dirname(__file__), 'func_styles_beautified_style2.sh')
]

class TestBasic(TestCase):
    
    # internal utilities:
    
    def read_file(self, fp):
        """Read input file."""
        with open(fp) as f:
            return f.read()
    
    def assertIdenticalMultilineStrings(self, expected, value):
        expectedlines = expected.split('\n')
        valuelines = value.split('\n')
        #self.assertEqual(len(valuelines), len(expectedlines), "expected is {} while value is {}".format(expected, value))
        self.assertEqual(len(valuelines), len(expectedlines), "Wrong line count in actual value:\n{}".format(value))
        for idx in range(0,len(expectedlines)):
            self.assertEqual(expectedlines[idx], valuelines[idx])

    # unit tests:
        
    def test_basic(self):
        testdata = self.read_file(TEST_BASIC_FILENAME)
        result, error = Beautify().beautify_string(testdata)
        self.assertFalse(error);  # we expect no parsing error
        self.assertTrue(testdata == result) # we expect no change in formatting

    def test_getopts1(self):
        testdata = self.read_file(TEST_GETOPTS1_RAW_FILENAME)
        expecteddata = self.read_file(TEST_GETOPTS1_BEAUTIFIED_FILENAME)
        result, error = Beautify().beautify_string(testdata)
        self.assertFalse(error);  # we expect no parsing error
        self.assertIdenticalMultilineStrings(expecteddata, result) # we expect no change in formatting

    def test_indent1(self):
        testdata = self.read_file(TEST_INDENT1_RAW_FILENAME)
        expecteddata = self.read_file(TEST_INDENT1_BEAUTIFIED_FILENAME)
        result, error = Beautify().beautify_string(testdata)
        self.assertFalse(error);  # we expect no parsing error
        self.assertIdenticalMultilineStrings(expecteddata, result) # we expect no change in formatting

    def test_func_style0(self):
        testdata = self.read_file(TEST_FUNCSTYLES_RAW_FILENAME)
        for idx in range(0,2):
            expecteddata = self.read_file(TEST_FUNCSTYLES_BEAUTIFIED_STYLE_FILENAME[idx])
            bb = Beautify()
            bb.apply_function_style = idx
            result, error = bb.beautify_string(testdata)
            self.assertFalse(error);  # we expect no parsing error
            self.assertIdenticalMultilineStrings(expecteddata, result) # we expect no change in formatting


if __name__ == "__main__":
    unittest.main()
