"""Constants used throughout beautysh with pre-compiled regex patterns for performance."""

import re
from enum import IntEnum

# Default formatting settings
DEFAULT_TAB_SIZE = 4
DEFAULT_TAB_STRING = " "
TAB_CHARACTER = "\t"

# Function style names
FUNCTION_STYLE_FNPAR = "fnpar"
FUNCTION_STYLE_FNONLY = "fnonly"
FUNCTION_STYLE_PARONLY = "paronly"

# Variable style options
VARIABLE_STYLE_BRACES = "braces"


# Indentation changes
class IndentChange(IntEnum):
    """Enum for indentation level changes."""

    DECREASE = -1
    NONE = 0
    INCREASE = 1


# Pre-compiled regex patterns for performance
# Special directives
FORMATTER_OFF_DIRECTIVE = re.compile(r"#\s*@formatter:off")
FORMATTER_ON_DIRECTIVE = re.compile(r"#\s*@formatter:on")

# Bash keywords that affect indentation
INDENT_INCREASE_KEYWORDS = re.compile(r"(\s|\A|;)(case|then|do)(;|\Z|\s)")
INDENT_DECREASE_KEYWORDS = re.compile(r"(\s|\A|;)(esac|fi|done|elif)(;|\)|\||\Z|\s)")

# Bracket patterns
OPENING_BRACKETS = re.compile(r"(\{|\(|\[)")
CLOSING_BRACKETS = re.compile(r"(\}|\)|\])")
SQUARE_BRACKET_OPEN = re.compile(r"\[")
SQUARE_BRACKET_CLOSE = re.compile(r"\]")

# Here-doc patterns
HEREDOC_PATTERN = re.compile(r"<<-?")
HERESTRING_PATTERN = re.compile(r".*<<<")
ARITHMETIC_PATTERN = re.compile(r"\$\(\(.*<<.*\)\)")
HEREDOC_TERMINATOR = re.compile(r'.*<<-?\s*[\'|"]?([_|\w]+)[\'|"]?.*')

# Case statement patterns
CASE_KEYWORD_PATTERN = re.compile(r"(\s|\A|;)case\s")
ESAC_KEYWORD_PATTERN = re.compile(r"\besac\b")
CASE_CHOICE_PATTERN = re.compile(r"\A[^(]+\)")

# Other patterns
ELSE_ELIF_PATTERN = re.compile(r"^(else|elif\s.*?;\s+?then)")
SPACE_BEFORE_DOUBLE_SEMICOLON = re.compile(r"(\S);;")
LINE_CONTINUATION = re.compile(r"\\$")
DO_CASE_PATTERN = re.compile(r"(\s|\A|;)(do|then)(\s+)(case\s)")
CASE_SPLIT_PATTERN = re.compile(r"(\s+)(case\s)")

# String/comment removal patterns (for get_test_record)
ESCAPED_SINGLE_QUOTE = re.compile(r"\\'")
ESCAPED_DOUBLE_QUOTE = re.compile(r'\\"')
SINGLE_QUOTED_STRING = re.compile(r"\'.*?\'")
DOUBLE_QUOTED_STRING = re.compile(r'".*?"')
BACKTICK_STRING = re.compile(r"`.*?`")
WEIRD_BACKTICK_STRING = re.compile(r"\\`.*?\'")
ESCAPED_CHAR = re.compile(r"\\.")
COMMENT = re.compile(r"(\A|\s)(#.*)")

# Variable style patterns
SIMPLE_VARIABLE = re.compile(r"\$(?!{)([a-zA-Z_][a-zA-Z0-9_]*)\b")

# Multiline string continuation patterns
MULTILINE_STRING_START = re.compile(r'"[^"]*?\\$')
MULTILINE_STRING_END = re.compile(r'^[^"]*"')

# Legacy function style patterns (kept for backward compatibility with transformers)
# Note: FunctionStyle enum should be used instead for new code
FUNCTION_STYLE_PATTERNS = [
    r"\bfunction\s+([\w:@-]+)\s*\(\s*\)\s*",  # function foo()
    r"\bfunction\s+([\w:@-]+)\s*",  # function foo
    r"\b\s*([\w:@-]+)\s*\(\s*\)\s*",  # foo()
]

FUNCTION_STYLE_REPLACEMENTS = [
    r"function \g<1>() ",  # fnpar style
    r"function \g<1> ",  # fnonly style
    r"\g<1>() ",  # paronly style
]
