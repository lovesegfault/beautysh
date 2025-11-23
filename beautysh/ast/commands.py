"""AST nodes for Bash commands and control structures.

This module defines all statement-level AST nodes including simple commands,
pipelines, control flow structures (if, for, while, case), and function
definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Sequence

from beautysh.ast.base import ASTNode, Statement, Word
from beautysh.types import FunctionStyle

if TYPE_CHECKING:
    from beautysh.ast.literals import Assignment, Redirect
    from beautysh.visitors.base import ASTVisitor


@dataclass
class Script(ASTNode):
    """Root node representing an entire Bash script.

    A script is a sequence of complete commands, which may be separated
    by newlines, semicolons, or ampersands.

    Attributes:
        commands: List of top-level statements in the script
    """

    commands: list[Statement] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_script(self)

    def children(self) -> Sequence[ASTNode]:
        return list(self.commands)


@dataclass
class SimpleCommand(Statement):
    """A simple command with optional assignments, arguments, and redirects.

    This is the most basic command type: [assignments] name [args...] [redirects...]

    Examples:
        echo hello
        FOO=bar echo $FOO
        cat file.txt > output.txt

    Attributes:
        name: The command name (first word), or None for assignment-only commands
        arguments: List of argument words following the command name
        redirects: List of I/O redirections
        assignments: List of variable assignments preceding the command
    """

    name: Optional[Word] = None
    arguments: list[Word] = field(default_factory=list)
    redirects: list[Redirect] = field(default_factory=list)
    assignments: list[Assignment] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_simple_command(self)

    def children(self) -> Sequence[ASTNode]:
        children: list[ASTNode] = []
        children.extend(self.assignments)
        if self.name:
            children.append(self.name)
        children.extend(self.arguments)
        children.extend(self.redirects)
        return children


@dataclass
class Pipeline(Statement):
    """A pipeline of commands connected by pipes.

    Commands in a pipeline are executed concurrently with the stdout of
    each command connected to the stdin of the next.

    Examples:
        cat file | grep pattern | wc -l
        ! grep -q pattern file  # Negated pipeline

    Attributes:
        commands: List of commands in the pipeline (at least one)
        negated: Whether the pipeline is negated with !
    """

    commands: list[Statement] = field(default_factory=list)
    negated: bool = False

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_pipeline(self)

    def children(self) -> Sequence[ASTNode]:
        return list(self.commands)


@dataclass
class AndOrList(Statement):
    """A list of pipelines connected by && or ||.

    Commands are executed left-to-right with short-circuit evaluation:
    - && executes the right command only if the left succeeds
    - || executes the right command only if the left fails

    Examples:
        mkdir dir && cd dir
        test -f file || touch file

    Attributes:
        first: The first pipeline in the list
        rest: List of (operator, pipeline) pairs for subsequent commands
    """

    first: Statement = field(default_factory=lambda: Pipeline())
    rest: list[tuple[str, Statement]] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_and_or_list(self)

    def children(self) -> Sequence[ASTNode]:
        children: list[ASTNode] = [self.first]
        for _, cmd in self.rest:
            children.append(cmd)
        return children


@dataclass
class CompoundList(Statement):
    """A list of commands separated by newlines or semicolons.

    This is the basic building block for command sequences inside
    compound commands like if-then-fi, for-do-done, etc.

    Attributes:
        commands: List of statements in the compound list
    """

    commands: list[Statement] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_compound_list(self)

    def children(self) -> Sequence[ASTNode]:
        return list(self.commands)


@dataclass
class Subshell(Statement):
    """A subshell command group: ( commands )

    Commands inside a subshell execute in a child process, so variable
    assignments and other state changes do not affect the parent shell.

    Example:
        (cd /tmp && make)

    Attributes:
        body: The compound list to execute in the subshell
    """

    body: CompoundList = field(default_factory=CompoundList)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_subshell(self)

    def children(self) -> Sequence[ASTNode]:
        return [self.body]


@dataclass
class BraceGroup(Statement):
    """A brace command group: { commands; }

    Commands inside braces execute in the current shell, but are grouped
    for purposes of redirection and control flow.

    Example:
        { echo start; process_files; echo done; } > log.txt

    Attributes:
        body: The compound list to execute in the brace group
    """

    body: CompoundList = field(default_factory=CompoundList)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_brace_group(self)

    def children(self) -> Sequence[ASTNode]:
        return [self.body]


@dataclass
class IfStatement(Statement):
    """An if-then-elif-else-fi conditional statement.

    Example:
        if test -f file; then
            cat file
        elif test -d file; then
            ls file
        else
            echo "not found"
        fi

    Attributes:
        condition: The condition compound list for the if clause
        then_body: Commands to execute if condition succeeds
        elif_clauses: List of (condition, body) pairs for elif clauses
        else_body: Commands for the else clause, or None if no else
    """

    condition: CompoundList = field(default_factory=CompoundList)
    then_body: CompoundList = field(default_factory=CompoundList)
    elif_clauses: list[tuple[CompoundList, CompoundList]] = field(default_factory=list)
    else_body: Optional[CompoundList] = None

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_if_statement(self)

    def children(self) -> Sequence[ASTNode]:
        children: list[ASTNode] = [self.condition, self.then_body]
        for cond, body in self.elif_clauses:
            children.extend([cond, body])
        if self.else_body:
            children.append(self.else_body)
        return children


@dataclass
class ForLoop(Statement):
    """A for loop: for var [in words...]; do commands; done

    If words is None, the loop iterates over positional parameters ($@).

    Examples:
        for file in *.txt; do cat "$file"; done
        for arg; do echo "$arg"; done

    Attributes:
        variable: The loop variable name
        words: List of words to iterate over, or None for $@
        body: Commands to execute for each iteration
    """

    variable: str = ""
    words: Optional[list[Word]] = None
    body: CompoundList = field(default_factory=CompoundList)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_for_loop(self)

    def children(self) -> Sequence[ASTNode]:
        children: list[ASTNode] = []
        if self.words:
            children.extend(self.words)
        children.append(self.body)
        return children


@dataclass
class WhileLoop(Statement):
    """A while loop: while condition; do commands; done

    Executes body repeatedly as long as condition succeeds.

    Example:
        while read line; do echo "$line"; done < file.txt

    Attributes:
        condition: The condition compound list
        body: Commands to execute while condition is true
        redirects: List of I/O redirections after the loop
    """

    condition: CompoundList = field(default_factory=CompoundList)
    body: CompoundList = field(default_factory=CompoundList)
    redirects: list[Redirect] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_while_loop(self)

    def children(self) -> Sequence[ASTNode]:
        children: list[ASTNode] = [self.condition, self.body]
        children.extend(self.redirects)
        return children


@dataclass
class UntilLoop(Statement):
    """An until loop: until condition; do commands; done

    Executes body repeatedly until condition succeeds.

    Example:
        until test -f ready.flag; do sleep 1; done

    Attributes:
        condition: The condition compound list
        body: Commands to execute until condition is true
    """

    condition: CompoundList = field(default_factory=CompoundList)
    body: CompoundList = field(default_factory=CompoundList)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_until_loop(self)

    def children(self) -> Sequence[ASTNode]:
        return [self.condition, self.body]


@dataclass
class CaseClause(ASTNode):
    """A single clause within a case statement.

    Each clause has one or more patterns and an optional body.

    Example:
        *.txt)
            echo "text file"
            ;;

    Attributes:
        patterns: List of pattern words (separated by | in source)
        body: Commands to execute if pattern matches, or None for empty
        terminator: The clause terminator (;;, ;&, or ;;&)
    """

    patterns: list[Word] = field(default_factory=list)
    body: Optional[CompoundList] = None
    terminator: str = ";;"

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_case_clause(self)

    def children(self) -> Sequence[ASTNode]:
        children: list[ASTNode] = list(self.patterns)
        if self.body:
            children.append(self.body)
        return children


@dataclass
class CaseStatement(Statement):
    """A case statement: case word in pattern) commands;; ... esac

    Example:
        case "$1" in
            start) start_service ;;
            stop) stop_service ;;
            *) echo "Usage: $0 {start|stop}" ;;
        esac

    Attributes:
        word: The word to match against patterns
        clauses: List of case clauses
    """

    word: Word = field(default_factory=lambda: LiteralWord())
    clauses: list[CaseClause] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_case_statement(self)

    def children(self) -> Sequence[ASTNode]:
        children: list[ASTNode] = [self.word]
        children.extend(self.clauses)
        return children


@dataclass
class FunctionDef(Statement):
    """A function definition.

    Supports three styles:
    - FNPAR:   function foo() { ... }
    - FNONLY:  function foo { ... }
    - PARONLY: foo() { ... }

    Example:
        greet() {
            echo "Hello, $1!"
        }

    Attributes:
        name: The function name
        body: The function body (usually a BraceGroup)
        style: The declaration style
    """

    name: str = ""
    body: Statement = field(default_factory=lambda: BraceGroup())
    style: FunctionStyle = FunctionStyle.PARONLY  # Default to paronly (most common)

    def accept(self, visitor: ASTVisitor[Any]) -> Any:
        return visitor.visit_function_def(self)

    def children(self) -> Sequence[ASTNode]:
        return [self.body]


# Import at end to avoid circular imports
from beautysh.ast.words import LiteralWord  # noqa: E402
