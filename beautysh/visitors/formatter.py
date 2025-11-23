"""Formatter visitor for producing formatted Bash output.

This module implements a visitor that traverses the AST and produces
properly formatted Bash code with consistent indentation.
"""

from __future__ import annotations

from beautysh.visitors.base import ASTVisitor
from beautysh.ast.base import ASTNode
from beautysh.ast.commands import (
    Script,
    SimpleCommand,
    Pipeline,
    AndOrList,
    CompoundList,
    Subshell,
    BraceGroup,
    IfStatement,
    ForLoop,
    WhileLoop,
    UntilLoop,
    CaseStatement,
    CaseClause,
    FunctionDef,
)
from beautysh.ast.words import (
    LiteralWord,
    SingleQuotedWord,
    DoubleQuotedWord,
    ParameterExpansion,
    CommandSubstitution,
    ArithmeticExpansion,
    ConcatenatedWord,
)
from beautysh.ast.literals import (
    HereDoc,
    HereString,
    Redirect,
    Comment,
    Assignment,
    ArrayValue,
    BlankLine,
)
from beautysh.types import FunctionStyle, VariableStyle


class FormatterVisitor(ASTVisitor[str]):
    """Visitor that formats AST nodes into Bash code.

    The visitor traverses the AST and produces properly formatted
    Bash code with consistent indentation.
    """

    def __init__(
        self,
        indent_size: int = 4,
        use_tabs: bool = False,
        function_style: FunctionStyle | None = None,
        variable_style: VariableStyle | None = None,
    ):
        """Initialize the formatter.

        Args:
            indent_size: Number of spaces per indent level
            use_tabs: If True, use tabs instead of spaces
            function_style: Force function style, or None to preserve original
            variable_style: Force variable style, or None to preserve original
        """
        self.indent_size = indent_size
        self.use_tabs = use_tabs
        self.function_style = function_style
        self.variable_style = variable_style
        self._indent_level = 0
        self._pending_heredocs: list[HereDoc] = []

    @property
    def _indent(self) -> str:
        """Current indentation string."""
        if self.use_tabs:
            return '\t' * self._indent_level
        return ' ' * (self._indent_level * self.indent_size)

    def _increase_indent(self) -> None:
        """Increase indentation level."""
        self._indent_level += 1

    def _decrease_indent(self) -> None:
        """Decrease indentation level."""
        self._indent_level = max(0, self._indent_level - 1)

    # ============================================================
    # Command visitors
    # ============================================================

    def visit_script(self, node: Script) -> str:
        """Format a Script node."""
        lines = []
        for cmd in node.commands:
            formatted = self.visit(cmd)
            if formatted is not None:
                lines.append(formatted)
        return '\n'.join(lines)

    def visit_simple_command(self, node: SimpleCommand) -> str:
        """Format a SimpleCommand node."""
        parts = []

        # Assignments first
        for assign in node.assignments:
            parts.append(self.visit(assign))

        # Command name
        if node.name:
            parts.append(self.visit(node.name))

        # Arguments
        for arg in node.arguments:
            parts.append(self.visit(arg))

        # Redirections
        for redirect in node.redirects:
            parts.append(self.visit(redirect))
            if redirect.heredoc:
                self._pending_heredocs.append(redirect.heredoc)

        result = ' '.join(parts)

        # Add pending heredocs after the command
        if self._pending_heredocs:
            heredocs = self._pending_heredocs
            self._pending_heredocs = []
            for heredoc in heredocs:
                result += '\n' + self._format_heredoc_content(heredoc)

        return result

    def _format_heredoc_content(self, heredoc: HereDoc) -> str:
        """Format heredoc content."""
        content = heredoc.content

        # Apply variable style transformation to unquoted heredoc content
        # (quoted heredocs suppress expansion, so we don't transform them)
        if self.variable_style == VariableStyle.BRACES and not heredoc.quoted:
            content = self._transform_variables_in_text(content)

        lines = [content, heredoc.delimiter]
        return '\n'.join(lines)

    def _transform_variables_in_text(self, text: str) -> str:
        """Transform simple $VAR to ${VAR} in raw text.

        Used for heredoc content where variables are not parsed into AST.
        """
        import re

        def replace_var(match: re.Match) -> str:
            name = match.group(1)
            # Don't transform special variables
            if self._is_special_param(name):
                return match.group(0)
            return f'${{{name}}}'

        # Match $VAR but not ${VAR} or $? etc.
        # Pattern: $ followed by identifier, not preceded by { and not followed by {
        pattern = r'\$([a-zA-Z_][a-zA-Z0-9_]*)'
        return re.sub(pattern, replace_var, text)

    def visit_pipeline(self, node: Pipeline) -> str:
        """Format a Pipeline node."""
        parts = []
        if node.negated:
            parts.append('!')

        cmd_strs = [self.visit(cmd) for cmd in node.commands]
        parts.append(' | '.join(cmd_strs))

        return ' '.join(parts)

    def visit_and_or_list(self, node: AndOrList) -> str:
        """Format an AndOrList node."""
        if not node.rest:
            return self.visit(node.first)

        parts = [self.visit(node.first)]
        for op, cmd in node.rest:
            parts.append(f' {op} ')
            parts.append(self.visit(cmd))

        return ''.join(parts)

    def visit_compound_list(self, node: CompoundList) -> str:
        """Format a CompoundList node."""
        lines = []
        for cmd in node.commands:
            formatted = self.visit(cmd)
            if formatted:
                lines.append(self._indent + formatted)

        return '\n'.join(lines)

    def visit_subshell(self, node: Subshell) -> str:
        """Format a Subshell node."""
        self._increase_indent()
        body = self.visit(node.body)
        self._decrease_indent()
        return f'(\n{body}\n{self._indent})'

    def visit_brace_group(self, node: BraceGroup) -> str:
        """Format a BraceGroup node."""
        self._increase_indent()
        body = self.visit(node.body)
        self._decrease_indent()
        return '{\n' + body + '\n' + self._indent + '}'

    def visit_if_statement(self, node: IfStatement) -> str:
        """Format an IfStatement node."""
        lines = []

        # if condition; then
        self._increase_indent()
        cond = self.visit(node.condition)
        self._decrease_indent()
        lines.append(f'if {cond.strip()}; then')

        # then body
        self._increase_indent()
        then_body = self.visit(node.then_body)
        self._decrease_indent()
        lines.append(then_body)

        # elif clauses
        for elif_cond, elif_body in node.elif_clauses:
            self._increase_indent()
            elif_cond_str = self.visit(elif_cond)
            self._decrease_indent()
            lines.append(f'{self._indent}elif {elif_cond_str.strip()}; then')
            self._increase_indent()
            elif_body_str = self.visit(elif_body)
            self._decrease_indent()
            lines.append(elif_body_str)

        # else clause
        if node.else_body:
            lines.append(f'{self._indent}else')
            self._increase_indent()
            else_body = self.visit(node.else_body)
            self._decrease_indent()
            lines.append(else_body)

        lines.append(f'{self._indent}fi')
        return '\n'.join(lines)

    def visit_for_loop(self, node: ForLoop) -> str:
        """Format a ForLoop node."""
        lines = []

        # for var in words; do
        words_str = ' '.join(self.visit(w) for w in node.words)
        if words_str:
            lines.append(f'for {node.variable} in {words_str}; do')
        else:
            lines.append(f'for {node.variable}; do')

        # body
        self._increase_indent()
        body = self.visit(node.body)
        self._decrease_indent()
        lines.append(body)

        lines.append(f'{self._indent}done')
        return '\n'.join(lines)

    def visit_while_loop(self, node: WhileLoop) -> str:
        """Format a WhileLoop node."""
        lines = []

        self._increase_indent()
        cond = self.visit(node.condition)
        self._decrease_indent()
        lines.append(f'while {cond.strip()}; do')

        self._increase_indent()
        body = self.visit(node.body)
        self._decrease_indent()
        lines.append(body)

        # Format done with optional redirects
        done_line = f'{self._indent}done'
        if node.redirects:
            redirect_strs = [self.visit(r) for r in node.redirects]
            done_line += ' ' + ' '.join(redirect_strs)
        lines.append(done_line)
        return '\n'.join(lines)

    def visit_until_loop(self, node: UntilLoop) -> str:
        """Format an UntilLoop node."""
        lines = []

        self._increase_indent()
        cond = self.visit(node.condition)
        self._decrease_indent()
        lines.append(f'until {cond.strip()}; do')

        self._increase_indent()
        body = self.visit(node.body)
        self._decrease_indent()
        lines.append(body)

        lines.append(f'{self._indent}done')
        return '\n'.join(lines)

    def visit_case_statement(self, node: CaseStatement) -> str:
        """Format a CaseStatement node."""
        lines = []
        word = self.visit(node.word)
        lines.append(f'case {word} in')

        self._increase_indent()
        for clause in node.clauses:
            lines.append(self.visit(clause))
        self._decrease_indent()

        lines.append(f'{self._indent}esac')
        return '\n'.join(lines)

    def visit_case_clause(self, node: CaseClause) -> str:
        """Format a CaseClause node."""
        patterns = ' | '.join(self.visit(p) for p in node.patterns)
        line = f'{self._indent}{patterns})'

        if node.body:
            self._increase_indent()
            body = self.visit(node.body)
            self._decrease_indent()
            return f'{line}\n{body}\n{self._indent}{node.terminator}'
        else:
            return f'{line}\n{self._indent}{node.terminator}'

    def visit_function_def(self, node: FunctionDef) -> str:
        """Format a FunctionDef node.

        Function definition styles:
            FNPAR:   function name() { ... }
            FNONLY:  function name { ... }
            PARONLY: name() { ... }
        """
        lines = []

        # Use forced style if specified, otherwise preserve original
        style = self.function_style if self.function_style is not None else node.style

        # Format function header based on style
        if style == FunctionStyle.FNPAR:
            lines.append(f'function {node.name}() {{')
        elif style == FunctionStyle.FNONLY:
            lines.append(f'function {node.name} {{')
        else:
            # PARONLY
            lines.append(f'{node.name}() {{')

        # If body is a BraceGroup, visit its inner body directly
        # (since we already added the braces above)
        if isinstance(node.body, BraceGroup):
            self._increase_indent()
            body = self.visit(node.body.body)
            self._decrease_indent()
        else:
            self._increase_indent()
            body = self.visit(node.body)
            self._decrease_indent()
        lines.append(body)

        lines.append(f'{self._indent}}}')
        return '\n'.join(lines)

    # ============================================================
    # Word visitors
    # ============================================================

    def visit_literal_word(self, node: LiteralWord) -> str:
        """Format a LiteralWord node."""
        return node.value

    def visit_single_quoted_word(self, node: SingleQuotedWord) -> str:
        """Format a SingleQuotedWord node."""
        return f"'{node.value}'"

    def visit_double_quoted_word(self, node: DoubleQuotedWord) -> str:
        """Format a DoubleQuotedWord node."""
        parts = [self.visit(p) for p in node.parts]
        return '"' + ''.join(parts) + '"'

    def visit_parameter_expansion(self, node: ParameterExpansion) -> str:
        """Format a ParameterExpansion node."""
        # Check if we should force braces for simple variables
        force_braces = False
        if (self.variable_style == VariableStyle.BRACES
            and not node.braced
            and not self._is_special_param(node.name)):
            force_braces = True

        if node.braced or force_braces:
            if node.operator and node.argument:
                arg_str = self.visit(node.argument)
                return f'${{{node.name}{node.operator}{arg_str}}}'
            elif node.operator:
                return f'${{{node.name}{node.operator}}}'
            else:
                return f'${{{node.name}}}'
        else:
            return f'${node.name}'

    def _is_special_param(self, name: str) -> bool:
        """Check if parameter is special (should not be transformed).

        Special parameters: $?, $@, $*, $#, $$, $!, $-
        Positional parameters: $0, $1, $2, ... (single or multi-digit)
        """
        # Special variables that shouldn't get braces by convention
        if name in ('?', '@', '*', '#', '$', '!', '-'):
            return True
        # Positional parameters (numeric only)
        if name.isdigit():
            return True
        return False

    def visit_command_substitution(self, node: CommandSubstitution) -> str:
        """Format a CommandSubstitution node."""
        if node.command:
            body = self.visit(node.command)
            if node.backtick_style:
                return f'`{body.strip()}`'
            else:
                return f'$({body.strip()})'
        else:
            # No parsed command, use raw text
            return '$()' if not node.backtick_style else '``'

    def visit_arithmetic_expansion(self, node: ArithmeticExpansion) -> str:
        """Format an ArithmeticExpansion node."""
        return f'$(({node.expression}))'

    def visit_concatenated_word(self, node: ConcatenatedWord) -> str:
        """Format a ConcatenatedWord node."""
        return ''.join(self.visit(p) for p in node.parts)

    # ============================================================
    # Literal visitors
    # ============================================================

    def visit_heredoc(self, node: HereDoc) -> str:
        """Format a HereDoc node (just the delimiter, operator comes from Redirect)."""
        if node.quoted:
            quote = node.quote_char or "'"
            return f"{quote}{node.delimiter}{quote}"
        else:
            return node.delimiter

    def visit_herestring(self, node: HereString) -> str:
        """Format a HereString node."""
        return f'<<<{self.visit(node.word)}'

    def visit_redirect(self, node: Redirect) -> str:
        """Format a Redirect node."""
        parts = []
        if node.fd is not None:
            parts.append(str(node.fd))
        parts.append(node.operator)

        if node.heredoc:
            parts.append(self.visit_heredoc(node.heredoc))
        elif node.here_string:
            # For here-string, add space after <<< and format the word
            parts.append(' ')
            parts.append(self.visit(node.here_string.word))
        elif node.target:
            parts.append(self.visit(node.target))

        return ''.join(parts)

    def visit_comment(self, node: Comment) -> str:
        """Format a Comment node."""
        return f'#{node.text}'

    def visit_assignment(self, node: Assignment) -> str:
        """Format an Assignment node."""
        op = '+=' if node.append else '='
        if node.value:
            value = self.visit(node.value)
            return f'{node.name}{op}{value}'
        else:
            return f'{node.name}{op}'

    def visit_array_value(self, node: ArrayValue) -> str:
        """Format an ArrayValue node."""
        if node.elements:
            elements = ' '.join(self.visit(e) for e in node.elements)
            return f'({elements})'
        else:
            return '()'

    def visit_blank_line(self, node: BlankLine) -> str:
        """Format a BlankLine node."""
        return ''

    # ============================================================
    # Generic visit
    # ============================================================

    def generic_visit(self, node: ASTNode) -> str:
        """Default visit for unhandled node types."""
        # For unknown nodes, try to visit children
        children = node.children()
        if children:
            return ' '.join(self.visit(c) for c in children if c is not None)
        return ''


def format_bash(source: str, indent_size: int = 4, use_tabs: bool = False) -> str:
    """Format Bash source code.

    Args:
        source: The Bash source code to format
        indent_size: Number of spaces per indent level
        use_tabs: If True, use tabs instead of spaces

    Returns:
        Formatted Bash source code
    """
    from beautysh.grammar.bash import parse_bash

    ast = parse_bash(source)
    formatter = FormatterVisitor(indent_size=indent_size, use_tabs=use_tabs)
    return formatter.visit(ast)
