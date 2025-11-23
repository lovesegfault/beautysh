"""Base AST node classes for Bash scripts.

This module defines the foundational classes for all AST nodes, including
source location tracking and the visitor pattern interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Sequence

if TYPE_CHECKING:
    from beautysh.visitors.base import ASTVisitor


@dataclass
class SourceLocation:
    """Source location for error reporting and round-tripping.

    Tracks the exact position of an AST node in the original source code,
    enabling precise error messages and source map generation.

    Attributes:
        line: Line number (1-indexed)
        column: Column number (0-indexed)
        offset: Byte offset from start of file
        length: Length of the source text in bytes
    """

    line: int
    column: int
    offset: int
    length: int

    def __str__(self) -> str:
        return f"{self.line}:{self.column}"


@dataclass
class ASTNode(ABC):
    """Base class for all AST nodes.

    All AST nodes inherit from this class, which provides:
    - Source location tracking for error messages
    - Visitor pattern support via the accept() method
    - Child node enumeration for generic traversal

    Attributes:
        location: Optional source location for this node
    """

    location: Optional[SourceLocation] = field(default=None, repr=False, compare=False)

    @abstractmethod
    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        """Accept a visitor for tree traversal.

        This method implements the Visitor pattern, allowing external
        operations to be performed on the AST without modifying node classes.

        Args:
            visitor: The visitor to accept

        Returns:
            The result from the visitor's visit method
        """
        pass

    def children(self) -> Sequence[ASTNode]:
        """Return child nodes for generic traversal.

        Override in subclasses to return all child nodes. The default
        implementation returns an empty sequence for leaf nodes.

        Returns:
            Sequence of child ASTNode objects
        """
        return []


@dataclass
class Statement(ASTNode):
    """Base class for statement nodes.

    Statements are executable units that can appear at the top level of
    a script or inside compound commands. Examples include simple commands,
    pipelines, and control flow structures.
    """

    pass


@dataclass
class Expression(ASTNode):
    """Base class for expression nodes.

    Expressions produce values and appear in arithmetic contexts ($((...))),
    boolean contexts ([[ ... ]]), and array subscripts.
    """

    pass


@dataclass
class Word(ASTNode):
    """Base class for word nodes.

    Words are the fundamental unit of the Bash "word" sublanguage. They
    can be literals, quoted strings, or contain expansions. Words appear
    as command arguments, variable values, and in various other contexts.
    """

    pass
