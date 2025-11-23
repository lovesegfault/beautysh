"""Visitor implementations for AST traversal.

This module provides the visitor pattern infrastructure for processing
Bash AST nodes. Visitors enable separation of concerns by allowing
different operations (formatting, analysis, transformation) to be
implemented without modifying the AST classes.
"""

from beautysh.visitors.base import ASTVisitor
from beautysh.visitors.formatter import FormatterVisitor, format_bash

__all__ = [
    "ASTVisitor",
    "FormatterVisitor",
    "format_bash",
]
