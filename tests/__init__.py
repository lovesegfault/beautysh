from pathlib import Path
from typing import Tuple

from beautysh import Beautify


class BeautyshTest:
    def __init__(self, fixture_dir: Path):
        self.fixture_dir = fixture_dir

    def read_file(self, file: Path) -> str:
        """Read file into string."""
        with open(file) as f:
            return f.read()

    def highlight_string(self, string: str) -> str:
        if len(string) == 0:
            return string

        output = ""
        idx = 0
        while string[idx] == " " or string[idx] == "\t":
            if string[idx] == " ":
                output += "."
            elif string[idx] == "\t":
                output += "T"
            idx += 1
        output += string[idx:]
        return output

    def assert_equal_multiline_strings(self, actual: str, expected: str):
        actual_lines = actual.split("\n")
        expected_lines = expected.split("\n")
        assert len(actual_lines) == len(expected_lines), "Mismatched line counts"
        for idx in range(0, len(expected_lines)):
            assert expected_lines[idx] == actual_lines[idx], (
                "Mismatch on line {}:\n" "Expected: {}\n" "Got: {}\n"
            ).format(
                idx + 1,
                self.highlight_string(expected_lines[idx]),
                self.highlight_string(actual_lines[idx]),
            )

    def generate_test_tuple(self, test_name: str) -> Tuple[str, str]:
        raw = self.fixture_dir / "{}_raw.sh".format(test_name)
        formatted = self.fixture_dir / "{}_formatted.sh".format(test_name)
        return self.read_file(raw), self.read_file(formatted)

    def assert_formatting(self, test_name: str):
        raw, formatted = self.generate_test_tuple(test_name)
        test, error = Beautify().beautify_string(raw)
        assert not error
        self.assert_equal_multiline_strings(test, formatted)

