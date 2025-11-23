"""AST nodes for Bash words and expansions.

This module defines all word-level AST nodes including literals, quoted strings,
and various types of expansions (parameter, command, arithmetic).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Sequence

from beautysh.ast.base import ASTNode, Word

if TYPE_CHECKING:
    from beautysh.ast.commands import CompoundList
    from beautysh.ast.base import Expression
    from beautysh.visitors.base import ASTVisitor


@dataclass
class LiteralWord(Word):
    """An unquoted literal word.

    Literal words may contain letters, numbers, and various special characters.
    They are subject to word splitting and glob expansion.

    Examples:
        hello
        file.txt
        path/to/file

    Attributes:
        value: The literal text value
    """

    value: str = ""

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_literal_word(self)


@dataclass
class SingleQuotedWord(Word):
    """A single-quoted string: 'text'

    Single-quoted strings preserve their contents literally with no
    expansion or interpretation of special characters.

    Example:
        'Hello $USER'  # $USER is NOT expanded

    Attributes:
        value: The string contents (without quotes)
    """

    value: str = ""

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_single_quoted_word(self)


@dataclass
class DoubleQuotedWord(Word):
    """A double-quoted string: "text with $expansions"

    Double-quoted strings allow parameter expansion, command substitution,
    and arithmetic expansion within them.

    Example:
        "Hello $USER, you are in $(pwd)"

    Attributes:
        parts: List of word parts (literals and expansions)
    """

    parts: list[Word] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_double_quoted_word(self)

    def children(self) -> Sequence[ASTNode]:
        return list(self.parts)


@dataclass
class ParameterExpansion(Word):
    """A parameter expansion: $var or ${var} or ${var:-default}

    Parameter expansions retrieve and optionally transform variable values.

    Examples:
        $HOME           # Simple expansion
        ${HOME}         # Braced expansion
        ${var:-default} # Default value if unset
        ${var:+alt}     # Alternative value if set
        ${#var}         # Length of value

    Attributes:
        name: The parameter name (without $)
        braced: Whether braces are used (${...} vs $...)
        operator: The expansion operator (e.g., ':-', ':+', '#'), or None
        argument: The operator argument word, or None
    """

    name: str = ""
    braced: bool = False
    operator: Optional[str] = None
    argument: Optional[Word] = None

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_parameter_expansion(self)

    def children(self) -> Sequence[ASTNode]:
        if self.argument:
            return [self.argument]
        return []


@dataclass
class CommandSubstitution(Word):
    """A command substitution: $(command) or `command`

    Command substitutions execute a command and substitute its stdout.

    Examples:
        $(pwd)
        $(cat file.txt)
        `date +%Y-%m-%d`  # Legacy backtick syntax

    Attributes:
        command: The command to execute (as a CompoundList)
        backtick_style: True if using `...` instead of $(...)
    """

    command: Optional[CompoundList] = None
    backtick_style: bool = False

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_command_substitution(self)

    def children(self) -> Sequence[ASTNode]:
        if self.command:
            return [self.command]
        return []


@dataclass
class ArithmeticExpansion(Word):
    """An arithmetic expansion: $((expression))

    Arithmetic expansions evaluate an arithmetic expression and substitute
    the result as a decimal number.

    Examples:
        $((1 + 2))
        $((x * y))
        $((count++))

    Attributes:
        expression: The arithmetic expression (as a string for now)
    """

    expression: str = ""

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_arithmetic_expansion(self)


@dataclass
class ConcatenatedWord(Word):
    """Multiple adjacent word parts forming one word.

    When multiple word elements appear without whitespace between them,
    they are concatenated into a single word.

    Examples:
        foo"bar"'baz'           # Three parts: foo, "bar", 'baz'
        ${prefix}_${suffix}     # Two expansions with literal underscore
        "hello "$name           # Quoted and unquoted parts

    Attributes:
        parts: List of adjacent word parts
    """

    parts: list[Word] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_concatenated_word(self)

    def children(self) -> Sequence[ASTNode]:
        return list(self.parts)
