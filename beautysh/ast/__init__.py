"""AST node definitions for Bash scripts.

This module provides a complete Abstract Syntax Tree representation for Bash
scripts, enabling proper structural parsing and visitor-based transformations.
"""

from beautysh.ast.base import ASTNode, SourceLocation, Statement, Expression, Word
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
    BlankLine,
)

__all__ = [
    # Base
    "ASTNode",
    "SourceLocation",
    "Statement",
    "Expression",
    "Word",
    # Commands
    "Script",
    "SimpleCommand",
    "Pipeline",
    "AndOrList",
    "CompoundList",
    "Subshell",
    "BraceGroup",
    "IfStatement",
    "ForLoop",
    "WhileLoop",
    "UntilLoop",
    "CaseStatement",
    "CaseClause",
    "FunctionDef",
    # Words
    "LiteralWord",
    "SingleQuotedWord",
    "DoubleQuotedWord",
    "ParameterExpansion",
    "CommandSubstitution",
    "ArithmeticExpansion",
    "ConcatenatedWord",
    # Literals
    "HereDoc",
    "HereString",
    "Redirect",
    "Comment",
    "Assignment",
    "BlankLine",
]
