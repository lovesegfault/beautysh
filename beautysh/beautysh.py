#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A beautifier for Bash shell scripts written in Python."""
import argparse
import re
import sys


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

    def read_file(self, fp):
        """Read input file."""
        with open(fp) as f:
            return f.read()

    def write_file(self, fp, data):
        """Write output to a file."""
        with open(fp, 'w') as f:
            f.write(data)

    def beautify_string(self, data, path=''):
        """Beautify string (file part)."""
        tab = 0
        case_stack = []
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

            # collapse multiple quotes between ' ... '
            test_record = re.sub(r'\'.*?\'', '', stripped_record)
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
            if(not in_here_doc):
                if(re.search('<<-?', test_record)):
                    here_string = re.sub(
                        '.*<<-?\s*[\'|"]?([_|\w]+)[\'|"]?.*', '\\1',
                        stripped_record, 1)
                    in_here_doc = (len(here_string) > 0)
            if(in_here_doc):  # pass on with no changes
                output.append(record)
                # now test for here-doc termination string
                if(re.search(here_string, test_record) and not
                   re.search('<<', test_record)):
                    in_here_doc = False
            else:  # not in here doc
                if(in_ext_quote):
                    if(re.search(ext_quote_string, test_record)):
                        # provide line after quotes
                        test_record = re.sub(
                            '.*%s(.*)' % ext_quote_string, '\\1',
                            test_record, 1)
                        in_ext_quote = False
                else:  # not in ext quote
                    if(re.search(r'(\A|\s)(\'|")', test_record)):
                        # apply only after this line has been processed
                        defer_ext_quote = True
                        ext_quote_string = re.sub(
                            '.*([\'"]).*', '\\1', test_record, 1)
                        # provide line before quote
                        test_record = re.sub(
                            '(.*)%s.*' % ext_quote_string, '\\1',
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

                    inc = len(re.findall(
                        '(\s|\A|;)(case|then|do)(;|\Z|\s)', test_record))
                    inc += len(re.findall('(\{|\(|\[)', test_record))
                    outc = len(re.findall(
                        '(\s|\A|;)(esac|fi|done|elif)(;|\)|\||\Z|\s)',
                        test_record))
                    outc += len(re.findall('(\}|\)|\])', test_record))
                    if(re.search(r'\besac\b', test_record)):
                        if(len(case_stack) == 0):
                            sys.stderr.write(
                                'File %s: error: "esac" before "case" in '
                                'line %d.\n' % (path, line))
                        else:
                            outc += case_stack.pop()
                    # sepcial handling for bad syntax within case ... esac
                    if(len(case_stack) > 0):
                        if(re.search('\A[^(]*\)', test_record)):
                            # avoid overcount
                            outc -= 2
                            case_stack[-1] += 1
                        if(re.search(';;', test_record)):
                            outc += 1
                            case_stack[-1] -= 1
                    # an ad-hoc solution for the "else" keyword
                    else_case = (0, -1)[re.search('^(else|elif)',
                                        test_record) is not None]
                    net = inc - outc
                    tab += min(net, 0)
                    extab = tab + else_case
                    extab = max(0, extab)
                    output.append((self.tab_str * self.tab_size * extab) +
                                  stripped_record)
                    tab += max(net, 0)
                if(defer_ext_quote):
                    in_ext_quote = True
                    defer_ext_quote = False
                if(re.search(r'\bcase\b', test_record)):
                    case_stack.append(0)
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
                if(self.backup):
                    self.write_file(path+'.bak', data)
                self.write_file(path, result)
        return error

    def main(self):
        """Main beautifying function."""
        error = False
        parser = argparse.ArgumentParser(description="A Bash beautifier for the"
                                                     " masses")
        parser.add_argument('--indent-size', '-i', nargs=1, type=int, default=4,
                            help="Sets the number of spaces to be used in "
                                 "indentation.")
        parser.add_argument('--files', '-f', nargs='*',
                            help="Files to be beautified.")
        parser.add_argument('--backup', '-b', action='store_true',
                            help="Beautysh will create a backup file in the "
                                 "same path as the original.")
        parser.add_argument('--tab', '-t', action='store_true',
                            help="Sets indentation to tabs instead of spaces")
        args = parser.parse_args()
        if (len(sys.argv) < 2):
            parser.print_help()
            exit()
        if(type(args.indent_size) is list):
            args.indent_size = args.indent_size[0]
        self.tab_size = args.indent_size
        self.backup = args.backup
        if (args.tab):
            self.tab_size = 1
            self.tab_str = '\t'
        for path in args.files:
            error |= self.beautify_file(path)
        sys.exit((0, 1)[error])


# if not called as a module
if(__name__ == '__main__'):
    Beautify().main()
