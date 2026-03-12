"""Constants used throughout beautysh with pre-compiled regex patterns for performance."""

import re

# Default formatting settings
DEFAULT_TAB_SIZE = 4
TAB_CHARACTER = "\t"

# Pre-compiled regex patterns for performance
# Special directives
FORMATTER_OFF_DIRECTIVE = re.compile(r"#\s*@formatter:off")
FORMATTER_ON_DIRECTIVE = re.compile(r"#\s*@formatter:on")

# Bash keywords that affect indentation.
# Keywords only have special meaning at command position: after start-of-line
# or a command separator (; } ) & |), with only whitespace between. This avoids
# false positives on e.g. 'echo done' where 'done' is a command argument.
# Trailing context uses lookahead so findall() can match 'done; done' twice.
INDENT_INCREASE_KEYWORDS = re.compile(r"(?:\A\s*|[;}\)&|]\s*)(case|then|do)(?=;|\Z|\s)")
INDENT_DECREASE_KEYWORDS = re.compile(
    r"(?:\A\s*|[;}\)&|]\s*)(esac|fi|done|elif)(?=;|\)|\||&|\Z|\s)"
)

# Bracket patterns
OPENING_BRACKETS = re.compile(r"(\{|\(|\[)")
CLOSING_BRACKETS = re.compile(r"(\}|\)|\])")
SQUARE_BRACKET_OPEN = re.compile(r"\[")
SQUARE_BRACKET_CLOSE = re.compile(r"\]")

# Here-doc patterns
HEREDOC_PATTERN = re.compile(r"<<-?")
HERESTRING_PATTERN = re.compile(r".*<<<")
ARITHMETIC_PATTERN = re.compile(r"\(\(.*<<.*\)\)")
LET_SHIFT_PATTERN = re.compile(r"\blet\b.*<<")
HEREDOC_TERMINATOR = re.compile(r'.*<<-?\s*[\'"]?(\w+)[\'"]?.*')
HEREDOC_QUOTED_PATTERN = re.compile(r'<<-?\s*([\'"]|[^\s]*\\)')

# Case statement patterns
CASE_KEYWORD_PATTERN = re.compile(r"(?:\A\s*|[;}\)&|]\s*)case\s")
ESAC_KEYWORD_PATTERN = re.compile(r"(?:\A\s*|[;}\)&|]\s*)esac(?=;|\)|\||&|\Z|\s)")
CASE_CHOICE_PATTERN = re.compile(r"\A[^(]+\)")
# Pattern to detect quoted case patterns (including empty quotes) before quote removal
# Matches patterns like: "") or '') or " ") or "foo")
QUOTED_CASE_PATTERN = re.compile(r'^\s*["\'].*?["\'].*?\)')

# Other patterns
ELSE_ELIF_PATTERN = re.compile(r"^(else|elif\s.*?;\s+?then)")
SPACE_BEFORE_DOUBLE_SEMICOLON = re.compile(r"(\S);;")
LINE_CONTINUATION = re.compile(r"\\$")
DO_CASE_PATTERN = re.compile(r"(?:\A\s*|[;}\)&|]\s*)(do|then)(\s+)(case\s)")
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
