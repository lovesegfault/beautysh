#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A beautifier for Bash shell scripts written in Python."""
import argparse
import re
import sys
import pkg_resources  # part of setuptools

# correct function style detection is obtained only if following regex are tested in sequence.
# styles are listed as follows:
# 0) function keyword, open/closed parentheses, e.g.      function foo()
# 1) function keyword, NO open/closed parentheses, e.g.   function foo
# 2) NO function keyword, open/closed parentheses, e.g.   foo()
FUNCTION_STYLE_REGEX = [
    r'\bfunction\s+(\w*)\s*\(\s*\)\s*',
    r'\bfunction\s+(\w*)\s*',
    r'\b\s*(\w*)\s*\(\s*\)\s*'
]

FUNCTION_STYLE_REPLACEMENT = [
    r'function \g<1>() ',
    r'function \g<1> ',
    r'\g<1>() '
]

def main():
    """Call the main function."""
    Beautify().main()


class Beautify:
    """Class to handle both module and non-module calls."""

    def __init__(self):
        """Set tab as space and it's value to 4."""
        self.tab_str = ' '
        self.tab_size = 4
        self.backup = False
        self.check_only = False
        self.apply_function_style = None # default is no change based on function style

    def read_file(self, fp):
        """Read input file."""
        with open(fp) as f:
            return f.read()

    def write_file(self, fp, data):
        """Write output to a file."""
        with open(fp, 'w', newline='\n') as f:
            f.write(data)

    def detect_function_style(self, test_record):
        """Returns the index for the function declaration style detected in the given string
           or None if no function declarations are detected."""
        index = 0
        # IMPORTANT: apply regex sequentially and stop on the first match:
        for regex in FUNCTION_STYLE_REGEX:
            if re.search(regex, test_record):
                return index
            index+=1
        return None

    def change_function_style(self, stripped_record, func_decl_style):
        """Converts a function definition syntax from the 'func_decl_style' to the one that has been
           set in self.apply_function_style and returns the string with the converted syntax."""
        if func_decl_style is None:
            return stripped_record
        if self.apply_function_style is None:
            # user does not want to enforce any specific function style
            return stripped_record
        regex = FUNCTION_STYLE_REGEX[func_decl_style]
        replacement = FUNCTION_STYLE_REPLACEMENT[self.apply_function_style]
        changed_record = re.sub(regex, replacement, stripped_record)
        return changed_record.strip()

    def get_test_record(self, source_line):
        """Takes the given Bash source code line and simplifies it by removing stuff that is not
           useful for the purpose of indentation level calculation"""
        # first of all, get rid of escaped special characters like single/double quotes
        # that may impact later "collapse" attempts
        test_record = source_line.replace("\\'", "")
        test_record = test_record.replace("\\\"", "")

        # collapse multiple quotes between ' ... '
        test_record = re.sub(r'\'.*?\'', '', test_record)
        # collapse multiple quotes between " ... "
        test_record = re.sub(r'".*?"', '', test_record)
        # collapse multiple quotes between ` ... `
        test_record = re.sub(r'`.*?`', '', test_record)
        # collapse multiple quotes between \` ... ' (weird case)
        test_record = re.sub(r'\\`.*?\'', '', test_record)
        # strip out any escaped single characters
        test_record = re.sub(r'\\.', '', test_record)
        # remove '#' comments
        test_record = re.sub(r'(\A|\s)(#.*)', '', test_record, 1)
        return test_record

    def beautify_string(self, data, path=''):
        """Beautify string (file part)."""
        tab = 0
        case_level = 0
        prev_line_had_continue = False
        continue_line = False
        started_multiline_quoted_string = False
        ended_multiline_quoted_string = False
        open_brackets = 0
        in_here_doc = False
        defer_ext_quote = False
        in_ext_quote = False
        ext_quote_string = ''
        here_string = ''
        output = []
        line = 1
        formatter = True
        for record in re.split('\n', data):
            record = record.rstrip()
            stripped_record = record.strip()

            # preserve blank lines
            if not stripped_record:
                output.append(stripped_record)
                continue

            # ensure space before ;; terminators in case statements
            if case_level:
                stripped_record = re.sub(r'(\S);;', r'\1 ;;', stripped_record)

            test_record = self.get_test_record(stripped_record)

            # detect whether this line ends with line continuation character:
            prev_line_had_continue = continue_line
            continue_line = True if (re.search(r'\\$', stripped_record)!=None) else False
            inside_multiline_quoted_string = prev_line_had_continue and continue_line and started_multiline_quoted_string

            if not continue_line and prev_line_had_continue and started_multiline_quoted_string:
                # remove contents of strings initiated on previous lines and that are ending on this line:
                [test_record, num_subs] = re.subn(r'^[^"]*"', '', test_record)
                ended_multiline_quoted_string = True if num_subs>0 else False
            else:
                ended_multiline_quoted_string = False

            if(in_here_doc) or (inside_multiline_quoted_string) or (ended_multiline_quoted_string):  # pass on with no changes
                output.append(record)
                # now test for here-doc termination string
                if(re.search(here_string, test_record) and not
                   re.search(r'<<', test_record)):
                    in_here_doc = False
            else:  # not in here doc or inside multiline-quoted

                if continue_line:
                    if prev_line_had_continue:
                        # this line is not STARTING a multiline-quoted string... we may be in the middle
                        # of such a multiline string though
                        started_multiline_quoted_string = False
                    else:
                        # remove contents of strings initiated on current line but that continue on next line
                        # (in particular we need to ignore brackets they may contain!)
                        [test_record, num_subs] = re.subn(r'"[^"]*?\\$', '', test_record)
                        started_multiline_quoted_string = True if num_subs>0 else False
                else:
                    # this line is not STARTING a multiline-quoted string
                    started_multiline_quoted_string = False

                if(re.search(r'<<-?', test_record)) and not (re.search(r'.*<<<', test_record)):
                    here_string = re.sub(
                        r'.*<<-?\s*[\'|"]?([_|\w]+)[\'|"]?.*', r'\1',
                        stripped_record, 1)
                    in_here_doc = (len(here_string) > 0)

                if(in_ext_quote):
                    if(re.search(ext_quote_string, test_record)):
                        # provide line after quotes
                        test_record = re.sub(
                            r'.*%s(.*)' % ext_quote_string, r'\1',
                            test_record, 1)
                        in_ext_quote = False
                else:  # not in ext quote
                    if(re.search(r'(\A|\s)(\'|")', test_record)):
                        # apply only after this line has been processed
                        defer_ext_quote = True
                        ext_quote_string = re.sub(
                            r'.*([\'"]).*', r'\1', test_record, 1)
                        # provide line before quote
                        test_record = re.sub(
                            r'(.*)%s.*' % ext_quote_string, r'\1',
                            test_record, 1)
                if(in_ext_quote or not formatter):
                    # pass on unchanged
                    output.append(record)
                    if(re.search(r'#\s*@formatter:on', stripped_record)):
                        formatter = True
                        continue
                else:  # not in ext quote
                    if(re.search(r'#\s*@formatter:off', stripped_record)):
                        formatter = False
                        output.append(record)
                        continue

                    # multi-line conditions are often meticulously formatted
                    if open_brackets:
                        output.append(record)
                    else:
                        inc = len(re.findall(
                            r'(\s|\A|;)(case|then|do)(;|\Z|\s)', test_record))
                        inc += len(re.findall(r'(\{|\(|\[)', test_record))
                        outc = len(re.findall(
                            r'(\s|\A|;)(esac|fi|done|elif)(;|\)|\||\Z|\s)',
                            test_record))
                        outc += len(re.findall(r'(\}|\)|\])', test_record))
                        if(re.search(r'\besac\b', test_record)):
                            if(case_level == 0):
                                sys.stderr.write(
                                    'File %s: error: "esac" before "case" in '
                                    'line %d.\n' % (path, line))
                            else:
                                outc += 1
                                case_level -= 1

                        # special handling for bad syntax within case ... esac
                        if re.search(r'\bcase\b', test_record):
                            inc += 1
                            case_level += 1

                        choice_case = 0
                        if case_level:
                            if(re.search(r'\A[^(]*\)', test_record)):
                                inc += 1
                                choice_case = -1

                        # detect functions
                        func_decl_style = self.detect_function_style(test_record)
                        if func_decl_style != None:
                             stripped_record = self.change_function_style(stripped_record, func_decl_style)

                        # an ad-hoc solution for the "else" or "elif" keyword
                        else_case = (0, -1)[re.search(r'^(else|elif)',
                                            test_record) is not None]
                        net = inc - outc
                        tab += min(net, 0)

                        # while 'tab' is preserved across multiple lines, 'extab' is not and is used for
                        # some adjustments:
                        extab = tab + else_case + choice_case
                        if prev_line_had_continue and not open_brackets and not ended_multiline_quoted_string:
                            extab+=1
                        extab = max(0, extab)
                        output.append((self.tab_str * self.tab_size * extab) +
                                      stripped_record)
                        tab += max(net, 0)
                if(defer_ext_quote):
                    in_ext_quote = True
                    defer_ext_quote = False

                # count open brackets for line continuation
                open_brackets += len(re.findall(r'\[', test_record))
                open_brackets -= len(re.findall(r'\]', test_record))
            line += 1
        error = (tab != 0)
        if(error):
            sys.stderr.write(
                'File %s: error: indent/outdent mismatch: %d.\n' % (path, tab))
        return '\n'.join(output), error

    def beautify_file(self, path):
        """Beautify bash script file."""
        error = False
        if(path == '-'):
            data = sys.stdin.read()
            result, error = self.beautify_string(data, '(stdin)')
            sys.stdout.write(result)
        else:  # named file
            data = self.read_file(path)
            result, error = self.beautify_string(data, path)
            if(data != result):
                if(self.check_only):
                    if not error:
                        # we want to return 0 (success) only if the given file is already
                        # well formatted:
                        error = (result != data)
                else:
                    if(self.backup):
                        self.write_file(path+'.bak', data)
                    self.write_file(path, result)
        return error

    def print_help(self, parser):
        parser.print_help()
        sys.stdout.write("\nBash function styles that can be specified via --force-function-style are:\n")
        sys.stdout.write("  fnpar: function keyword, open/closed parentheses, e.g.      function foo()\n")
        sys.stdout.write("  fnonly: function keyword, no open/closed parentheses, e.g.  function foo\n")
        sys.stdout.write("  paronly: no function keyword, open/closed parentheses, e.g. foo()\n")
        sys.stdout.write("\n")

    def parse_function_style(self, style_name):
        # map the user-provided function style to our range 0-2
        if style_name == "fnpar":
            return 0
        elif style_name == "fnonly":
            return 1
        elif style_name == "paronly":
            return 2
        return None

    def get_version(self):
        try:
            return pkg_resources.require("beautysh")[0].version
        except pkg_resources.DistributionNotFound:
            return "Not Available"

    def main(self):
        """Main beautifying function."""
        error = False
        parser = argparse.ArgumentParser(
            description="A Bash beautifier for the masses, version {}".format(self.get_version()), add_help=False)
        parser.add_argument('--indent-size', '-i', nargs=1, type=int, default=4,
                            help="Sets the number of spaces to be used in "
                                 "indentation.")
        parser.add_argument('--backup', '-b', action='store_true',
                            help="Beautysh will create a backup file in the "
                                 "same path as the original.")
        parser.add_argument('--check', '-c', action='store_true',
                            help="Beautysh will just check the files without doing "
                                 "any in-place beautify.")
        parser.add_argument('--tab', '-t', action='store_true',
                            help="Sets indentation to tabs instead of spaces.")
        parser.add_argument('--force-function-style', '-s', nargs=1,
                            help="Force a specific Bash function formatting. See below for more info.")
        parser.add_argument('--version', '-v', action='store_true',
                            help="Prints the version and exits.")
        parser.add_argument('--help', '-h', action='store_true',
                            help="Print this help message.")
        parser.add_argument('files', metavar='FILE', nargs='*',
                            help="Files to be beautified. This is mandatory. "
                            "If - is provided as filename, then beautysh reads "
                            "from stdin and writes on stdout.")
        args = parser.parse_args()
        if (len(sys.argv) < 2) or args.help:
            self.print_help(parser)
            exit()
        if args.version:
            sys.stdout.write("%s\n" % self.get_version())
            exit()
        if(type(args.indent_size) is list):
            args.indent_size = args.indent_size[0]
        if not args.files:
            sys.stdout.write("Please provide at least one input file\n")
            exit()
        self.tab_size = args.indent_size
        self.backup = args.backup
        self.check_only = args.check
        if (args.tab):
            self.tab_size = 1
            self.tab_str = '\t'
        if (type(args.force_function_style) is list):
            provided_style = self.parse_function_style(args.force_function_style[0])
            if provided_style is None:
                sys.stdout.write("Invalid value for the function style. See --help for details.\n")
                exit()
            self.apply_function_style = provided_style
        for path in args.files:
            error |= self.beautify_file(path)
        sys.exit((0, 1)[error])


# if not called as a module
if(__name__ == '__main__'):
    Beautify().main()
