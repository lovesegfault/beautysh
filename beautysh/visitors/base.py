"""Base visitor class for AST traversal.

This module defines the abstract base visitor that all AST visitors
must inherit from. It provides default traversal behavior that can
be overridden for specific node types.
"""

from __future__ import annotations

from abc import ABC
from typing import Any, Generic, Sequence, TypeVar

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
    BlankLine,
)

T = TypeVar("T")


class ASTVisitor(ABC, Generic[T]):
    """Abstract base visitor for Bash AST traversal.

    This class implements the Visitor pattern for processing AST nodes.
    Subclasses override specific visit_* methods to implement custom
    behavior for each node type.

    The default implementations traverse children and collect results,
    allowing subclasses to only override the methods they need.

    Type parameter T is the return type of visit methods.
    """

    def visit(self, node: ASTNode) -> T:
        """Visit a node by dispatching to its accept method.

        Args:
            node: The AST node to visit

        Returns:
            The result from the appropriate visit_* method
        """
        return node.accept(self)

    def visit_children(self, nodes: Sequence[ASTNode]) -> list[T]:
        """Visit all children and collect results.

        Args:
            nodes: Sequence of child nodes to visit

        Returns:
            List of results from visiting each child
        """
        return [self.visit(node) for node in nodes if node is not None]

    # ============================================================
    # Command visitors
    # ============================================================

    def visit_script(self, node: Script) -> T:
        """Visit a Script node (root of AST)."""
        return self.generic_visit(node)

    def visit_simple_command(self, node: SimpleCommand) -> T:
        """Visit a SimpleCommand node."""
        return self.generic_visit(node)

    def visit_pipeline(self, node: Pipeline) -> T:
        """Visit a Pipeline node."""
        return self.generic_visit(node)

    def visit_and_or_list(self, node: AndOrList) -> T:
        """Visit an AndOrList node."""
        return self.generic_visit(node)

    def visit_compound_list(self, node: CompoundList) -> T:
        """Visit a CompoundList node."""
        return self.generic_visit(node)

    def visit_subshell(self, node: Subshell) -> T:
        """Visit a Subshell node."""
        return self.generic_visit(node)

    def visit_brace_group(self, node: BraceGroup) -> T:
        """Visit a BraceGroup node."""
        return self.generic_visit(node)

    def visit_if_statement(self, node: IfStatement) -> T:
        """Visit an IfStatement node."""
        return self.generic_visit(node)

    def visit_for_loop(self, node: ForLoop) -> T:
        """Visit a ForLoop node."""
        return self.generic_visit(node)

    def visit_while_loop(self, node: WhileLoop) -> T:
        """Visit a WhileLoop node."""
        return self.generic_visit(node)

    def visit_until_loop(self, node: UntilLoop) -> T:
        """Visit an UntilLoop node."""
        return self.generic_visit(node)

    def visit_case_statement(self, node: CaseStatement) -> T:
        """Visit a CaseStatement node."""
        return self.generic_visit(node)

    def visit_case_clause(self, node: CaseClause) -> T:
        """Visit a CaseClause node."""
        return self.generic_visit(node)

    def visit_function_def(self, node: FunctionDef) -> T:
        """Visit a FunctionDef node."""
        return self.generic_visit(node)

    # ============================================================
    # Word visitors
    # ============================================================

    def visit_literal_word(self, node: LiteralWord) -> T:
        """Visit a LiteralWord node."""
        return self.generic_visit(node)

    def visit_single_quoted_word(self, node: SingleQuotedWord) -> T:
        """Visit a SingleQuotedWord node."""
        return self.generic_visit(node)

    def visit_double_quoted_word(self, node: DoubleQuotedWord) -> T:
        """Visit a DoubleQuotedWord node."""
        return self.generic_visit(node)

    def visit_parameter_expansion(self, node: ParameterExpansion) -> T:
        """Visit a ParameterExpansion node."""
        return self.generic_visit(node)

    def visit_command_substitution(self, node: CommandSubstitution) -> T:
        """Visit a CommandSubstitution node."""
        return self.generic_visit(node)

    def visit_arithmetic_expansion(self, node: ArithmeticExpansion) -> T:
        """Visit an ArithmeticExpansion node."""
        return self.generic_visit(node)

    def visit_concatenated_word(self, node: ConcatenatedWord) -> T:
        """Visit a ConcatenatedWord node."""
        return self.generic_visit(node)

    # ============================================================
    # Literal visitors
    # ============================================================

    def visit_heredoc(self, node: HereDoc) -> T:
        """Visit a HereDoc node."""
        return self.generic_visit(node)

    def visit_herestring(self, node: HereString) -> T:
        """Visit a HereString node."""
        return self.generic_visit(node)

    def visit_redirect(self, node: Redirect) -> T:
        """Visit a Redirect node."""
        return self.generic_visit(node)

    def visit_comment(self, node: Comment) -> T:
        """Visit a Comment node."""
        return self.generic_visit(node)

    def visit_assignment(self, node: Assignment) -> T:
        """Visit an Assignment node."""
        return self.generic_visit(node)

    def visit_blank_line(self, node: BlankLine) -> T:
        """Visit a BlankLine node."""
        return self.generic_visit(node)

    # ============================================================
    # Generic visit
    # ============================================================

    def generic_visit(self, node: ASTNode) -> T:
        """Default visit implementation that traverses children.

        Override this method to change the default behavior for
        all node types, or override specific visit_* methods for
        targeted behavior.

        Args:
            node: The AST node being visited

        Returns:
            Result of visiting children (as a list), or None for leaf nodes
        """
        children = node.children()
        if children:
            results = self.visit_children(children)
            # Return the list of results cast to T
            # Subclasses should override for specific behavior
            return results  # type: ignore[return-value]
        return None  # type: ignore[return-value]
