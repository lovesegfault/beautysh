"""AST nodes for Bash literals and miscellaneous constructs.

This module defines AST nodes for heredocs, redirections, comments,
assignments, and other supporting constructs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Sequence

from beautysh.ast.base import ASTNode, Word

if TYPE_CHECKING:
    from beautysh.visitors.base import ASTVisitor


@dataclass
class HereDoc(ASTNode):
    """A here-document: <<[-]DELIMITER ... DELIMITER

    Here-documents provide multi-line string input to commands.
    The content is preserved exactly as written until the delimiter.

    Examples:
        cat <<EOF
        Hello, World!
        EOF

        cat <<-INDENTED
            This content
            can be indented
        INDENTED

    Attributes:
        delimiter: The terminator string (without quotes)
        content: The heredoc content (captured in second pass)
        strip_tabs: True if <<- was used (strip leading tabs)
        quoted: True if delimiter was quoted (suppresses expansion)
        quote_char: The quote character used ("'" or '"'), or None if unquoted
    """

    delimiter: str = ""
    content: str = ""
    strip_tabs: bool = False
    quoted: bool = False
    quote_char: Optional[str] = None

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_heredoc(self)


@dataclass
class HereString(Word):
    """A here-string: <<<word

    Here-strings provide the expansion of a word as stdin to a command.

    Example:
        grep pattern <<<"$text"

    Attributes:
        word: The word to expand and provide as input
    """

    word: Optional[Word] = None

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_herestring(self)

    def children(self) -> Sequence[ASTNode]:
        if self.word:
            return [self.word]
        return []


@dataclass
class Redirect(ASTNode):
    """An I/O redirection: [n]operator target

    Redirections control where command input/output goes.

    Examples:
        > file.txt      # Redirect stdout to file
        2>&1            # Redirect stderr to stdout
        < input.txt     # Redirect stdin from file
        >> log.txt      # Append stdout to file
        <<EOF           # Heredoc (target is HereDoc)
        <<<word         # Here-string

    Attributes:
        fd: File descriptor number, or None for default
        operator: The redirection operator (<, >, >>, <>, <&, >&, >|, <<, <<-, <<<)
        target: The target word (filename, fd number, etc.)
        heredoc: For << and <<-, the associated HereDoc node
        here_string: For <<<, the associated HereString node
    """

    fd: Optional[int] = None
    operator: str = ">"
    target: Optional[Word] = None
    heredoc: Optional[HereDoc] = None
    here_string: Optional[HereString] = None

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_redirect(self)

    def children(self) -> Sequence[ASTNode]:
        children: list[ASTNode] = []
        if self.target:
            children.append(self.target)
        if self.heredoc:
            children.append(self.heredoc)
        if self.here_string:
            children.append(self.here_string)
        return children


@dataclass
class Comment(ASTNode):
    """A comment: # text

    Comments are preserved in the AST for round-tripping and
    for potential documentation extraction.

    Example:
        # This is a comment

    Attributes:
        text: The comment text (without the leading #)
    """

    text: str = ""

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_comment(self)


@dataclass
class ArrayValue(Word):
    """An array value: (word word ...)

    Array values are used in array assignments.

    Examples:
        arr=(a b c)
        arr=()
        arr+=("new")

    Attributes:
        elements: List of words in the array
    """

    elements: list[Word] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_array_value(self)

    def children(self) -> Sequence[ASTNode]:
        return self.elements


@dataclass
class Assignment(ASTNode):
    """A variable assignment: name=value or name+=value

    Assignments can appear before commands or standalone.

    Examples:
        FOO=bar
        PATH+=:/usr/local/bin
        EMPTY=
        arr=(a b c)

    Attributes:
        name: The variable name
        value: The assigned value (as a Word or ArrayValue), or None for empty
        append: True if += was used instead of =
    """

    name: str = ""
    value: Optional[Word] = None
    append: bool = False

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_assignment(self)

    def children(self) -> Sequence[ASTNode]:
        if self.value:
            return [self.value]
        return []


@dataclass
class BlankLine(ASTNode):
    """A preserved blank line.

    Blank lines are tracked to preserve the formatting of the original
    script when round-tripping through the formatter.

    Attributes:
        None - this is a marker node
    """

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_blank_line(self)
