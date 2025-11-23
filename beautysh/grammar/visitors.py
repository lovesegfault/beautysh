"""Parsimonious NodeVisitor for building AST from parse trees.

This module defines the ASTBuilder class which traverses parsimonious
parse trees and constructs the corresponding AST nodes.
"""

from __future__ import annotations

from typing import Any, Optional

from parsimonious.nodes import Node, NodeVisitor

from beautysh.ast.base import SourceLocation
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
from beautysh.types import FunctionStyle


def make_location(node: Node) -> SourceLocation:
    """Create a SourceLocation from a parsimonious Node."""
    # Calculate line and column from offset
    text_before = node.full_text[: node.start]
    line = text_before.count("\n") + 1
    last_newline = text_before.rfind("\n")
    column = node.start - last_newline - 1 if last_newline >= 0 else node.start
    return SourceLocation(
        line=line,
        column=column,
        offset=node.start,
        length=node.end - node.start,
    )


class ASTBuilder(NodeVisitor):
    """Builds AST from parsimonious parse tree.

    This visitor traverses the parse tree produced by parsimonious and
    constructs the corresponding AST nodes. It handles:

    - Flattening nested structures
    - Extracting text values from terminals
    - Creating proper AST node instances
    - Tracking source locations
    """

    def __init__(self) -> None:
        self.heredoc_markers: list[dict[str, Any]] = []

    # ============================================================
    # Script and Top-Level
    # ============================================================

    def visit_script(self, node: Node, visited_children: list) -> Script:
        """Build Script node from parsed script."""
        if len(visited_children) >= 3:
            _, commands, _ = visited_children
        elif len(visited_children) == 1:
            commands = visited_children[0]
        else:
            commands = visited_children

        # Flatten and filter commands - handle both list and single item
        flat_commands = []
        if commands is None:
            pass
        elif isinstance(commands, list):
            for item in self._flatten(commands):
                if item is not None and hasattr(item, 'accept'):
                    flat_commands.append(item)
        elif hasattr(commands, 'accept'):
            # Single AST node
            flat_commands.append(commands)

        return Script(commands=flat_commands, location=make_location(node))

    def visit_blank_line(self, node: Node, visited_children: list) -> BlankLine:
        """Build BlankLine node."""
        return BlankLine(location=make_location(node))

    def visit_comment_line(self, node: Node, visited_children: list) -> Comment:
        """Build Comment node from comment line."""
        _, comment, _ = visited_children
        return comment

    def visit_comment(self, node: Node, visited_children: list) -> Comment:
        """Build Comment node."""
        text = node.text[1:]  # Remove leading #
        return Comment(text=text, location=make_location(node))

    # ============================================================
    # Commands
    # ============================================================

    def visit_complete_command(self, node: Node, visited_children: list) -> Any:
        """Build command from complete_command."""
        first, rest, _ = visited_children
        if not rest:
            return first

        # Build AndOrList if there are multiple commands
        commands = [first]
        for item in rest:
            if isinstance(item, list):
                for subitem in item:
                    if isinstance(subitem, tuple) and len(subitem) == 2:
                        op, cmd = subitem
                        commands.append((op, cmd))
        if len(commands) == 1:
            return first
        return AndOrList(
            first=commands[0],
            rest=[(op, cmd) for op, cmd in commands[1:]] if len(commands) > 1 else [],
            location=make_location(node),
        )

    def visit_and_or_list(self, node: Node, visited_children: list) -> Any:
        """Build AndOrList node."""
        if not visited_children:
            return Pipeline(commands=[])
        first = visited_children[0] if visited_children else None
        rest = visited_children[1] if len(visited_children) > 1 else []

        if not rest or (isinstance(rest, list) and not rest):
            return first

        # Flatten rest to get alternating [op, pipeline, op, pipeline, ...]
        flat_rest = self._flatten(rest)

        # Pair up operators with pipelines
        rest_items = []
        i = 0
        while i < len(flat_rest):
            item = flat_rest[i]
            # Look for string operators followed by Pipeline
            if isinstance(item, str) and item in ('&&', '||'):
                if i + 1 < len(flat_rest):
                    next_item = flat_rest[i + 1]
                    if isinstance(next_item, Pipeline):
                        rest_items.append((item, next_item))
                        i += 2
                        continue
            # Look for Pipeline objects (operator might be embedded or missing)
            elif isinstance(item, Pipeline) and rest_items:
                # If we have a Pipeline without preceding operator, use the default
                pass
            i += 1

        if not rest_items:
            return first

        return AndOrList(first=first, rest=rest_items, location=make_location(node))

    def visit_and_or_op(self, node: Node, visited_children: list) -> str:
        """Extract operator from and_or_op."""
        # visited_children is [[ws], ['&&'/'||'], [ws]]
        _, op_list, _ = visited_children
        op = op_list[0] if isinstance(op_list, list) else op_list
        return op

    def visit_pipeline(self, node: Node, visited_children: list) -> Pipeline:
        """Build Pipeline node."""
        bang, pipe_seq = visited_children
        negated = bang is not None and bang != []
        commands = pipe_seq if isinstance(pipe_seq, list) else [pipe_seq]
        # Flatten commands
        flat_commands = []
        for cmd in commands:
            if isinstance(cmd, list):
                flat_commands.extend(c for c in cmd if c is not None)
            elif cmd is not None:
                flat_commands.append(cmd)
        return Pipeline(
            commands=flat_commands, negated=bool(negated), location=make_location(node)
        )

    def visit_pipe_sequence(self, node: Node, visited_children: list) -> list:
        """Build list of piped commands."""
        if not visited_children:
            return []
        first = visited_children[0] if visited_children else None
        rest = visited_children[1] if len(visited_children) > 1 else []
        commands = [first] if first is not None else []
        if rest:
            for item in self._flatten(rest):
                if item is not None and not isinstance(item, str):
                    commands.append(item)
        return commands

    def visit_command(self, node: Node, visited_children: list) -> Any:
        """Process command alternatives.

        Grammar: command = compound_command redirect_list?
                         / function_def
                         / simple_command
        """
        if not visited_children:
            return None

        # Flatten to get actual values
        flat = self._flatten(visited_children)
        if not flat:
            return None

        # Get the main command
        result = flat[0]
        if result is None:
            return None

        # Check for redirects after compound command
        # They come as a list of Redirect objects after the compound command
        redirects = []
        for item in flat[1:]:
            if isinstance(item, Redirect):
                redirects.append(item)

        # Attach redirects to compound commands that support them
        if redirects and hasattr(result, 'redirects'):
            result.redirects = redirects

        return result

    def visit_simple_command(self, node: Node, visited_children: list) -> SimpleCommand:
        """Build SimpleCommand node."""
        parts = visited_children
        assignments = []
        name = None
        arguments = []
        redirects = []

        for part in self._flatten(parts):
            if isinstance(part, Assignment):
                if name is None:
                    assignments.append(part)
                else:
                    # Assignment after command name is an argument
                    arguments.append(
                        LiteralWord(value=f"{part.name}={part.value}")
                    )
            elif isinstance(part, Redirect):
                redirects.append(part)
            elif isinstance(part, (LiteralWord, SingleQuotedWord, DoubleQuotedWord,
                                   ConcatenatedWord, ParameterExpansion,
                                   CommandSubstitution, ArithmeticExpansion)):
                if name is None:
                    name = part
                else:
                    arguments.append(part)

        return SimpleCommand(
            name=name,
            arguments=arguments,
            redirects=redirects,
            assignments=assignments,
            location=make_location(node),
        )

    # ============================================================
    # Compound Commands
    # ============================================================

    def visit_compound_command(self, node: Node, visited_children: list) -> Any:
        """Process compound command alternatives."""
        return visited_children[0]

    def visit_brace_group(self, node: Node, visited_children: list) -> BraceGroup:
        """Build BraceGroup node."""
        _, _, body, _, _ = visited_children
        return BraceGroup(body=body, location=make_location(node))

    def visit_subshell(self, node: Node, visited_children: list) -> Subshell:
        """Build Subshell node."""
        _, _, body, _, _ = visited_children
        return Subshell(body=body, location=make_location(node))

    def visit_compound_list(self, node: Node, visited_children: list) -> CompoundList:
        """Build CompoundList node."""
        _, first, rest, _ = visited_children
        commands = [first] if first else []
        for item in self._flatten(rest):
            if item is not None and not isinstance(item, str):
                commands.append(item)
        return CompoundList(commands=commands, location=make_location(node))

    def visit_compound_item(self, node: Node, visited_children: list) -> Any:
        """Unwrap compound_item (standalone_comment or term)."""
        return visited_children[0]

    def visit_standalone_comment(self, node: Node, visited_children: list) -> Comment:
        """Build Comment node from standalone comment in compound list."""
        _, comment, _ = visited_children
        return comment

    # ============================================================
    # Control Flow
    # ============================================================

    def visit_if_clause(
        self, node: Node, visited_children: list
    ) -> IfStatement:
        """Build IfStatement node."""
        (_, _, condition, _, _, _, then_body, _,
         elif_clauses, else_clause, _) = visited_children

        # Process elif clauses
        elifs = []
        for item in self._flatten(elif_clauses):
            if isinstance(item, tuple) and len(item) == 2:
                elifs.append(item)

        # Process else clause
        else_body = None
        if else_clause and isinstance(else_clause, CompoundList):
            else_body = else_clause
        elif isinstance(else_clause, list):
            for item in self._flatten(else_clause):
                if isinstance(item, CompoundList):
                    else_body = item
                    break

        return IfStatement(
            condition=condition,
            then_body=then_body,
            elif_clauses=elifs,
            else_body=else_body,
            location=make_location(node),
        )

    def visit_elif_clause(
        self, node: Node, visited_children: list
    ) -> tuple[CompoundList, CompoundList]:
        """Build elif clause tuple."""
        _, _, condition, _, _, _, body, _ = visited_children
        return (condition, body)

    def visit_else_clause(
        self, node: Node, visited_children: list
    ) -> CompoundList:
        """Build else clause."""
        _, _, body, _ = visited_children
        return body

    def visit_for_clause(self, node: Node, visited_children: list) -> ForLoop:
        """Build ForLoop node."""
        _, _, name, _, _, in_clause, do_group = visited_children
        words = None
        if in_clause:
            words = in_clause if isinstance(in_clause, list) else None
        return ForLoop(
            variable=name if isinstance(name, str) else str(name),
            words=words,
            body=do_group,
            location=make_location(node),
        )

    def visit_in_clause(self, node: Node, visited_children: list) -> Optional[list]:
        """Build in clause word list."""
        _, words, _ = visited_children
        if words:
            return self._flatten(words)
        return None

    def visit_do_group(self, node: Node, visited_children: list) -> CompoundList:
        """Build do group."""
        _, _, body, _, _ = visited_children
        return body

    def visit_while_clause(self, node: Node, visited_children: list) -> WhileLoop:
        """Build WhileLoop node."""
        _, _, condition, do_group = visited_children
        return WhileLoop(
            condition=condition, body=do_group, location=make_location(node)
        )

    def visit_until_clause(self, node: Node, visited_children: list) -> UntilLoop:
        """Build UntilLoop node."""
        _, _, condition, do_group = visited_children
        return UntilLoop(
            condition=condition, body=do_group, location=make_location(node)
        )

    def visit_case_clause(self, node: Node, visited_children: list) -> CaseStatement:
        """Build CaseStatement node."""
        # case ws word ws "in" ws? newline_list? case_list? ws? "esac"
        _, _, word, _, _, _, _, case_list, _, _ = visited_children
        clauses = []
        for item in self._flatten(case_list):
            if isinstance(item, CaseClause):
                clauses.append(item)
        return CaseStatement(word=word, clauses=clauses, location=make_location(node))

    def visit_case_item(self, node: Node, visited_children: list) -> CaseClause:
        """Build CaseClause node."""
        _, _, patterns, _, _, body_and_term = visited_children
        pattern_list = self._flatten(patterns)
        body = None
        terminator = ";;"
        for item in self._flatten(body_and_term):
            if isinstance(item, CompoundList):
                body = item
            elif isinstance(item, str) and item in (";;", ";&", ";;&"):
                terminator = item
        return CaseClause(
            patterns=pattern_list,
            body=body,
            terminator=terminator,
            location=make_location(node),
        )

    def visit_case_terminator(self, node: Node, visited_children: list) -> str:
        """Extract case terminator."""
        _, term, _ = visited_children
        return term.text if hasattr(term, "text") else str(term)

    def visit_pattern_list(self, node: Node, visited_children: list) -> list:
        """Build pattern list."""
        first, rest = visited_children
        patterns = [first]
        for item in self._flatten(rest):
            if item is not None and not isinstance(item, str):
                patterns.append(item)
        return patterns

    # ============================================================
    # Functions
    # ============================================================

    def visit_function_def(self, node: Node, visited_children: list) -> FunctionDef:
        """Process function_def alternatives."""
        return visited_children[0]

    def visit_function_def_fnpar(
        self, node: Node, visited_children: list
    ) -> FunctionDef:
        """Build FunctionDef with fnpar style."""
        _, _, name, _, _, _, _, _, _, body = visited_children
        return FunctionDef(
            name=str(name),
            body=body,
            style=FunctionStyle.FNPAR,
            location=make_location(node),
        )

    def visit_function_def_fnonly(
        self, node: Node, visited_children: list
    ) -> FunctionDef:
        """Build FunctionDef with fnonly style."""
        _, _, name, _, _, _, body = visited_children
        return FunctionDef(
            name=str(name),
            body=body,
            style=FunctionStyle.FNONLY,
            location=make_location(node),
        )

    def visit_function_def_paronly(
        self, node: Node, visited_children: list
    ) -> FunctionDef:
        """Build FunctionDef with paronly style."""
        name, _, _, _, _, _, _, body = visited_children
        return FunctionDef(
            name=str(name),
            body=body,
            style=FunctionStyle.PARONLY,
            location=make_location(node),
        )

    def visit_function_body(self, node: Node, visited_children: list) -> Any:
        """Build function body."""
        body, redirects = visited_children
        # TODO: Handle redirects on function body
        return body

    def visit_fname(self, node: Node, visited_children: list) -> str:
        """Extract function name."""
        return node.text

    # ============================================================
    # Words
    # ============================================================

    def visit_word(self, node: Node, visited_children: list) -> Any:
        """Build word from parts."""
        parts = self._flatten(visited_children)
        if len(parts) == 1:
            return parts[0]
        return ConcatenatedWord(parts=parts, location=make_location(node))

    def visit_word_list(self, node: Node, visited_children: list) -> list:
        """Build word list."""
        first, rest = visited_children
        words = [first]
        for item in self._flatten(rest):
            if item is not None and not isinstance(item, str):
                words.append(item)
        return words

    def visit_single_quoted(self, node: Node, visited_children: list) -> SingleQuotedWord:
        """Build SingleQuotedWord node."""
        _, content, _ = visited_children
        value = content.text if hasattr(content, "text") else str(content)
        return SingleQuotedWord(value=value, location=make_location(node))

    def visit_single_content(self, node: Node, visited_children: list) -> str:
        """Extract single-quoted content."""
        return node.text

    def visit_double_quoted(self, node: Node, visited_children: list) -> DoubleQuotedWord:
        """Build DoubleQuotedWord node."""
        _, parts, _ = visited_children
        flat_parts = []
        for part in self._flatten(parts):
            if isinstance(part, str):
                flat_parts.append(LiteralWord(value=part))
            elif part is not None:
                flat_parts.append(part)
        return DoubleQuotedWord(parts=flat_parts, location=make_location(node))

    def visit_double_part(self, node: Node, visited_children: list) -> Any:
        """Process double_part alternatives."""
        return visited_children[0]

    def visit_dquoted_literal(self, node: Node, visited_children: list) -> str:
        """Extract double-quoted literal."""
        return node.text

    def visit_escaped_dquote(self, node: Node, visited_children: list) -> str:
        """Process escaped character in double quotes."""
        return node.text

    def visit_dollar_single_quoted(
        self, node: Node, visited_children: list
    ) -> SingleQuotedWord:
        """Build $'...' quoted string."""
        _, _, content, _ = visited_children
        return SingleQuotedWord(
            value=content if isinstance(content, str) else str(content),
            location=make_location(node),
        )

    def visit_unquoted_word(self, node: Node, visited_children: list) -> LiteralWord:
        """Build LiteralWord from unquoted text."""
        return LiteralWord(value=node.text, location=make_location(node))

    def visit_escaped_char(self, node: Node, visited_children: list) -> LiteralWord:
        """Build LiteralWord from escaped character."""
        return LiteralWord(value=node.text, location=make_location(node))

    # ============================================================
    # Expansions
    # ============================================================

    def visit_expansion(self, node: Node, visited_children: list) -> Any:
        """Process expansion alternatives."""
        return visited_children[0]

    def visit_param_expansion(self, node: Node, visited_children: list) -> Any:
        """Process param_expansion alternatives."""
        return visited_children[0]

    def visit_param_braced(
        self, node: Node, visited_children: list
    ) -> ParameterExpansion:
        """Build braced parameter expansion."""
        # Grammar: "${" param_content "}" -> 3 children
        _, content, _ = visited_children
        content_str = content if isinstance(content, str) else str(content)
        # Parse content for operator
        name = content_str
        operator = None
        argument = None
        # Simple parsing - could be enhanced
        for op in (":-", ":=", ":+", ":?", "-", "=", "+", "?", "#", "##", "%", "%%"):
            if op in content_str:
                idx = content_str.index(op)
                name = content_str[:idx]
                operator = op
                arg_str = content_str[idx + len(op) :]
                if arg_str:
                    argument = LiteralWord(value=arg_str)
                break
        return ParameterExpansion(
            name=name,
            braced=True,
            operator=operator,
            argument=argument,
            location=make_location(node),
        )

    def visit_param_simple(
        self, node: Node, visited_children: list
    ) -> ParameterExpansion:
        """Build simple parameter expansion."""
        _, name = visited_children
        return ParameterExpansion(
            name=str(name),
            braced=False,
            location=make_location(node),
        )

    def visit_simple_param(self, node: Node, visited_children: list) -> str:
        """Extract simple parameter name."""
        return node.text

    def visit_param_content(self, node: Node, visited_children: list) -> str:
        """Extract parameter content."""
        return node.text

    def visit_command_sub(self, node: Node, visited_children: list) -> Any:
        """Process command_sub alternatives."""
        return visited_children[0]

    def visit_command_sub_dollar(
        self, node: Node, visited_children: list
    ) -> CommandSubstitution:
        """Build $(...) command substitution."""
        # Grammar: "$(" ws? compound_list? ws? ")" -> 5 children
        _, _, body, _, _ = visited_children
        return CommandSubstitution(
            command=body if isinstance(body, CompoundList) else None,
            backtick_style=False,
            location=make_location(node),
        )

    def visit_command_sub_backtick(
        self, node: Node, visited_children: list
    ) -> CommandSubstitution:
        """Build `...` command substitution."""
        _, content, _ = visited_children
        # For backticks, we store the raw content
        # Full parsing would require recursive handling
        return CommandSubstitution(
            command=None,  # Would need recursive parse
            backtick_style=True,
            location=make_location(node),
        )

    def visit_backtick_content(self, node: Node, visited_children: list) -> str:
        """Extract backtick content."""
        return node.text

    def visit_arith_expansion(
        self, node: Node, visited_children: list
    ) -> ArithmeticExpansion:
        """Build arithmetic expansion."""
        # Grammar: "$((" arith_content "))" -> 3 children
        _, content, _ = visited_children
        return ArithmeticExpansion(
            expression=content if isinstance(content, str) else str(content),
            location=make_location(node),
        )

    def visit_arith_content(self, node: Node, visited_children: list) -> str:
        """Extract arithmetic content."""
        return node.text

    # ============================================================
    # Redirections
    # ============================================================

    def visit_redirect_list(self, node: Node, visited_children: list) -> list:
        """Build redirect list."""
        return self._flatten(visited_children)

    def visit_io_redirect(self, node: Node, visited_children: list) -> Redirect:
        """Build Redirect node."""
        parts = self._flatten(visited_children)
        fd = None
        operator = ">"
        target = None
        heredoc = None
        here_string = None

        for part in parts:
            if isinstance(part, int):
                fd = part
            elif isinstance(part, str) and part in ("<", ">", ">>", "<>", "<&", ">&", ">|"):
                operator = part
            elif isinstance(part, HereDoc):
                heredoc = part
                operator = "<<-" if part.strip_tabs else "<<"
            elif isinstance(part, HereString):
                here_string = part
                operator = "<<<"
            elif isinstance(part, (LiteralWord, SingleQuotedWord, DoubleQuotedWord,
                                   ConcatenatedWord, ParameterExpansion, CommandSubstitution,
                                   ArithmeticExpansion)):
                target = part

        return Redirect(
            fd=fd,
            operator=operator,
            target=target,
            heredoc=heredoc,
            here_string=here_string,
            location=make_location(node),
        )

    def visit_io_number(self, node: Node, visited_children: list) -> int:
        """Extract I/O number."""
        return int(node.text)

    def visit_redirect_op(self, node: Node, visited_children: list) -> str:
        """Extract redirect operator."""
        return node.text

    def visit_herestring_redirect(self, node: Node, visited_children: list) -> HereString:
        """Build HereString node."""
        _, _, word = visited_children
        return HereString(word=word, location=make_location(node))

    def visit_heredoc_redirect(self, node: Node, visited_children: list) -> HereDoc:
        """Build HereDoc marker."""
        op, _, delimiter = visited_children
        strip_tabs = "-" in str(op)
        # Determine if quoted and which quote character
        delim_str = str(delimiter)
        quoted = delim_str.startswith(("'", '"'))
        quote_char = None
        if quoted:
            quote_char = delim_str[0]
            delim_str = delim_str[1:-1]
        return HereDoc(
            delimiter=delim_str,
            content="",  # Content collected in second pass
            strip_tabs=strip_tabs,
            quoted=quoted,
            quote_char=quote_char,
            location=make_location(node),
        )

    def visit_heredoc_op(self, node: Node, visited_children: list) -> str:
        """Extract heredoc operator."""
        return node.text

    def visit_heredoc_delimiter(self, node: Node, visited_children: list) -> str:
        """Extract heredoc delimiter."""
        return node.text

    # ============================================================
    # Assignments
    # ============================================================

    def visit_assignment_word(self, node: Node, visited_children: list) -> Assignment:
        """Build Assignment node."""
        name, op, value = visited_children
        append = "+=" in str(op)
        # Flatten value - might be nested list from (array_value / word)?
        actual_value = None
        for item in self._flatten(value):
            if item is not None and hasattr(item, 'accept'):
                actual_value = item
                break
        return Assignment(
            name=str(name),
            value=actual_value,
            append=append,
            location=make_location(node),
        )

    def visit_array_value(self, node: Node, visited_children: list) -> ArrayValue:
        """Build ArrayValue node."""
        # Grammar: "(" ws? array_elements? ws? ")"
        _, _, elements, _, _ = visited_children
        flat_elements = []
        for item in self._flatten(elements):
            if item is not None and hasattr(item, 'accept'):
                flat_elements.append(item)
        return ArrayValue(elements=flat_elements, location=make_location(node))

    def visit_array_element(self, node: Node, visited_children: list) -> Any:
        """Process array element."""
        return visited_children[0]

    def visit_assign_op(self, node: Node, visited_children: list) -> str:
        """Extract assignment operator."""
        return node.text

    def visit_name(self, node: Node, visited_children: list) -> str:
        """Extract variable name."""
        return node.text

    # ============================================================
    # Helpers
    # ============================================================

    def _flatten(self, items: Any) -> list:
        """Flatten nested lists."""
        result = []
        if items is None:
            return result
        if not isinstance(items, list):
            return [items]
        for item in items:
            if isinstance(item, list):
                result.extend(self._flatten(item))
            elif item is not None:
                result.append(item)
        return result

    def generic_visit(self, node: Node, visited_children: list) -> Any:
        """Default visitor - return children or node text."""
        if visited_children:
            # Filter out None and empty lists
            filtered = [c for c in visited_children if c is not None and c != []]
            if len(filtered) == 0:
                # Return empty list for empty matches, not None
                return []
            if len(filtered) == 1:
                return filtered[0]
            return filtered
        # For leaf nodes, return text if meaningful
        text = node.text
        if text and text.strip():
            return text
        return []
