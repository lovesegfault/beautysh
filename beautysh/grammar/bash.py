"""PEG grammar for Bash shell scripts.

This module defines the parsimonious grammar for parsing Bash scripts.
The grammar follows the POSIX shell grammar with Bash extensions.

Key design decisions:
- Uses two-pass parsing for heredocs (markers in pass 1, content in pass 2)
- Preserves comments and blank lines for round-tripping
- Handles all three function definition styles
- Distinguishes heredocs from here-strings and arithmetic shift
"""

from parsimonious.grammar import Grammar
from parsimonious.exceptions import ParsimoniousError

from beautysh.ast import Script


class BashParseError(Exception):
    """Exception raised when parsing a Bash script fails."""
    pass

# The complete Bash grammar in PEG notation
BASH_GRAMMAR = Grammar(
    r"""
    # ============================================================
    # Entry Point
    # ============================================================

    script              = ws? (ws? (complete_command / blank_line / comment_line))* ws?

    # ============================================================
    # Complete Commands
    # ============================================================

    complete_command    = and_or_list (separator_op and_or_list)* list_terminator?
    list_terminator     = ws? (newline / ";") ws?

    and_or_list         = pipeline (and_or_op pipeline)*
    and_or_op           = ws? ("&&" / "||") ws?

    pipeline            = bang? pipe_sequence
    bang                = "!" ws
    pipe_sequence       = command (pipe command)*
    pipe                = ws? "|" !"|" ws?

    # ============================================================
    # Commands
    # ============================================================

    command             = compound_command redirect_list?
                        / function_def
                        / simple_command

    simple_command      = cmd_prefix cmd_word? cmd_suffix?
                        / cmd_word cmd_suffix?

    cmd_prefix          = (io_redirect / assignment_word)+
    cmd_word            = word
    cmd_suffix          = (ws (io_redirect / word))+

    # ============================================================
    # Compound Commands
    # ============================================================

    compound_command    = brace_group
                        / subshell
                        / if_clause
                        / for_clause
                        / while_clause
                        / until_clause
                        / case_clause
                        / select_clause

    brace_group         = "{" ws? compound_list ws? "}"
    subshell            = "(" ws? compound_list ws? ")"

    compound_list       = blank_newlines? compound_item (separator !reserved_word compound_item)* separator?
    compound_item       = standalone_comment / term
    standalone_comment  = ws? comment !~r"[^\n]"
    term                = !reserved_word and_or_list
    separator           = ws? inline_comment? (separator_op ws? blank_newlines? / blank_newlines)
    inline_comment      = comment
    separator_op        = (";" / "&") !(";" / "&")
    blank_newlines      = (ws? newline ws?)+
    newline_list        = (ws? comment? newline ws?)+

    # Reserved words that terminate/continue compound commands (not words that start new ones)
    # NOTE: Longer words must come before shorter prefixes (done before do) for PEG ordered choice
    reserved_word       = ("then" / "else" / "elif" / "fi" / "done" / "do"
                        / "esac" / "in" / "}") !~r"[a-zA-Z0-9_]"

    # ============================================================
    # Control Flow
    # ============================================================

    # If statement
    # sp allows space OR newline after keywords (Bash allows both)
    # sp_body uses blank_newlines to not consume standalone comments (those belong to compound_list)
    if_clause           = "if" sp compound_list separator?
                          "then" sp_body compound_list separator?
                          elif_clause*
                          else_clause?
                          "fi"
    elif_clause         = "elif" sp compound_list separator?
                          "then" sp_body compound_list separator?
    else_clause         = "else" sp_body compound_list separator?
    sp                  = ws / newline_list
    sp_body             = ws / blank_newlines

    # For loop
    for_clause          = "for" ws name ws? linebreak? in_clause? do_group
    in_clause           = "in" (ws word_list)? sequential_sep
    do_group            = "do" sp_body compound_list separator? "done"
    sequential_sep      = ws? (";" / newline) ws?
    linebreak           = newline_list?

    # While/until loops
    while_clause        = "while" sp compound_list do_group
    until_clause        = "until" sp compound_list do_group

    # Case statement
    case_clause         = "case" ws word ws "in" ws? newline_list? case_list? ws? "esac"
    case_list           = case_item+
    case_item           = ws? "("? pattern_list ")" ws? (compound_list? case_terminator / linebreak)
    case_terminator     = ws? (";;&" / ";&" / ";;") newline_list?
    pattern_list        = word (ws? "|" ws? word)*

    # Select statement
    select_clause       = "select" ws name ws? linebreak? in_clause? do_group

    # ============================================================
    # Functions
    # ============================================================

    # Three function definition styles, ordered for PEG (most specific first)
    function_def        = function_def_fnpar / function_def_fnonly / function_def_paronly

    function_def_fnpar  = "function" ws fname ws? "(" ws? ")" ws? linebreak? function_body
    function_def_fnonly = "function" ws fname ws? !("(") linebreak? function_body
    function_def_paronly= fname ws? "(" ws? ")" ws? linebreak? function_body

    function_body       = compound_command redirect_list?
    # Function names can include hyphens, colons, @ - put permissive rule first
    fname               = ~r"[a-zA-Z_][a-zA-Z0-9_:@-]*"

    # ============================================================
    # Words
    # ============================================================

    word                = (single_quoted / double_quoted / dollar_single_quoted
                        / ansi_c_quoted / expansion / brace_expansion
                        / escaped_char / unquoted_word)+

    word_list           = word (ws word)*

    # Single-quoted strings (no expansion)
    single_quoted       = "'" single_content "'"
    single_content      = ~r"[^']*"

    # Double-quoted strings (with expansion)
    double_quoted       = dquote double_part* dquote
    dquote              = '"'
    # literal_dollar handles $ not followed by valid expansion (e.g., "test$" or "test$.")
    double_part         = expansion / escaped_dquote / literal_dollar / dquoted_literal
    # Allow any character after backslash including newline (for line continuation)
    escaped_dquote      = "\\" ~r"[\s\S]"
    # Literal $ when not followed by valid expansion start (letter, digit, special, {, ()
    literal_dollar      = "$" !~r"[a-zA-Z_0-9@*#?$!{(-]"
    dquoted_literal     = ~r'[^$`"\\]+'

    # $'...' strings (ANSI-C quoting)
    dollar_single_quoted = "$'" dollar_single_content "'"
    dollar_single_content = ~r"([^'\\]|\\.)*"

    # $"..." strings (locale translation)
    ansi_c_quoted       = '$"' double_part* '"'

    # Brace expansion
    brace_expansion     = ~r"\{[^{}]+\}"

    # Unquoted word characters
    # Note: [ and ] are allowed since [ is the test command and ] ends test arguments
    unquoted_word       = ~r"[^\s\n|&;()<>\\\"'$`{}#]+"

    # Escaped character
    escaped_char        = "\\" ~r"."

    # ============================================================
    # Expansions
    # ============================================================

    expansion           = arith_expansion / command_sub / param_expansion

    # Parameter expansion
    param_expansion     = param_braced / param_simple
    param_braced        = "${" param_content "}"
    param_simple        = "$" simple_param
    simple_param        = ~r"[a-zA-Z_][a-zA-Z0-9_]*"
                        / ~r"[0-9]+"
                        / ~r"[@*#?$!-]"
    param_content       = ~r"[^}]+"

    # Command substitution
    command_sub         = command_sub_dollar / command_sub_backtick
    command_sub_dollar  = "$(" ws? compound_list? ws? ")"
    command_sub_backtick= "`" backtick_content "`"
    backtick_content    = ~r"[^`]*"

    # Arithmetic expansion
    arith_expansion     = "$((" arith_content "))"
    arith_content       = ~r"[^)]+(?:\)[^)])*"

    # ============================================================
    # Redirections
    # ============================================================

    redirect_list       = (ws? io_redirect)+
    io_redirect         = io_number? herestring_redirect
                        / io_number? redirect_op ws? redirect_target
                        / io_number? heredoc_redirect

    redirect_target     = word
    io_number           = ~r"[0-9]+"

    # Regular redirections (order matters for PEG)
    redirect_op         = ">>" / "<>" / "<&" / ">&" / ">|" / "<" / ">"

    # Here-string (<<<word) - must come before heredoc to avoid matching <<< as <<
    herestring_redirect = "<<<" ws? word

    # Heredoc redirections (handled specially)
    heredoc_redirect    = heredoc_op ws? heredoc_delimiter
    heredoc_op          = "<<-" / "<<"
    heredoc_delimiter   = heredoc_quoted / heredoc_bare
    heredoc_quoted      = "'" ~r"[^']+" "'" / '"' ~r'[^"]+' '"'
    heredoc_bare        = ~r"[a-zA-Z_][a-zA-Z0-9_]*"

    # ============================================================
    # Assignments
    # ============================================================

    assignment_word     = name assign_op (array_value / word)?
    array_value         = "(" array_ws? array_elements? array_ws? ")"
    array_elements      = array_element (array_ws array_element)*
    array_element       = word
    array_ws            = ~r"[ \t\n]+"
    assign_op           = "+=" / "="
    name                = ~r"[a-zA-Z_][a-zA-Z0-9_]*"

    # ============================================================
    # Comments and Whitespace
    # ============================================================

    comment             = ~r"#[^\n]*"
    comment_line        = ws? comment newline
    blank_line          = ws? newline

    # ws includes line continuation (backslash-newline) as invisible whitespace
    ws                  = ~r"([ \t]|\\\n)+"
    newline             = ~r"\n"
"""
)


def _preprocess_heredocs(source: str) -> tuple[str, dict[str, str]]:
    """Preprocess source to extract heredoc content.

    Returns the source with heredoc content removed, plus a mapping
    from delimiter to content.
    """
    import re

    lines = source.split('\n')
    result_lines = []
    heredoc_content: dict[str, str] = {}

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for heredoc marker (<<EOF or <<-EOF or << 'EOF' etc.)
        # Match << or <<- followed by optional whitespace and delimiter
        # IMPORTANT: Don't match << inside arithmetic expressions $(( ))
        # Use lookahead/lookbehind to ensure we're in redirection context:
        # - Must be preceded by whitespace or start of line (or digit for fd redirect)
        # - Must NOT be preceded by another < (that would be <<< here-string)
        heredoc_pattern = r'(?:(?<=[ \t])|(?<=[0-9])|^)<<(-)?[ \t]*([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\2'
        match = re.search(heredoc_pattern, line)

        if match:
            strip_tabs = match.group(1) == '-'
            delimiter = match.group(3)
            result_lines.append(line)
            i += 1

            # Collect heredoc content until delimiter
            content_lines = []
            while i < len(lines):
                content_line = lines[i]
                # Check for closing delimiter (possibly with leading tabs if <<-)
                stripped = content_line.lstrip('\t') if strip_tabs else content_line
                if stripped.strip() == delimiter:
                    i += 1
                    break
                content_lines.append(content_line)
                i += 1

            heredoc_content[delimiter] = '\n'.join(content_lines)
        else:
            result_lines.append(line)
            i += 1

    return '\n'.join(result_lines), heredoc_content


def _fill_heredoc_content(script: Script, heredoc_content: dict[str, str]) -> None:
    """Fill in heredoc content in the AST.

    Walks the AST and fills in HereDoc nodes with their content.
    """
    from beautysh.ast.literals import HereDoc
    from beautysh.ast.commands import SimpleCommand, Pipeline, AndOrList

    def fill_redirects(redirects):
        for redirect in redirects:
            if redirect.heredoc and redirect.heredoc.delimiter in heredoc_content:
                redirect.heredoc.content = heredoc_content[redirect.heredoc.delimiter]

    def walk(node):
        if isinstance(node, SimpleCommand):
            fill_redirects(node.redirects)
        elif hasattr(node, 'commands'):
            for cmd in node.commands:
                walk(cmd)
        elif hasattr(node, 'children'):
            children = node.children()
            if children:
                for child in children:
                    if child is not None:
                        walk(child)

    walk(script)


def parse_bash(source: str) -> Script:
    """Parse a Bash script source string into an AST.

    This is the main entry point for parsing Bash scripts. It handles
    two-pass parsing for heredocs and returns a complete AST.

    Args:
        source: The Bash script source code

    Returns:
        A Script AST node representing the parsed script

    Raises:
        ParseError: If the source cannot be parsed
    """
    from beautysh.grammar.visitors import ASTBuilder

    # Preprocess to extract heredoc content
    processed_source, heredoc_content = _preprocess_heredocs(source)

    try:
        tree = BASH_GRAMMAR.parse(processed_source)
        builder = ASTBuilder()
        script = builder.visit(tree)

        # Fill in heredoc content
        if heredoc_content:
            _fill_heredoc_content(script, heredoc_content)

        return script
    except ParsimoniousError as e:
        # Re-raise with our own exception type that has working __str__
        raise BashParseError(f"Failed to parse Bash script: {e}") from e
