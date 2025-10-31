# beautysh [![CI](https://github.com/lovesegfault/beautysh/actions/workflows/ci.yaml/badge.svg)](https://github.com/lovesegfault/beautysh/actions/workflows/ci.yaml)

This program takes upon itself the hard task of beautifying Bash scripts
(yeesh). Processing Bash scripts is not trivial, they aren't like C or Java
programs — they have a lot of ambiguous syntax, and (shudder) you can use
keywords as variables. Years ago, while testing the first version of this
program, I encountered this example:

```shell
done=0;while (( $done <= 10 ));do echo done=$done;done=$((done+1));done
```

Same name, but three distinct meanings (sigh). The Bash interpreter can sort out
this perversity, but I decided not to try to recreate the Bash interpreter to
beautify a script. This means there will be some border cases this Python
program won't be able to process. But in tests with large Linux system
Bash scripts, its error-free score was ~99%.

## Installation

### Using pip

```shell
pip install beautysh
```

### Using Nix (recommended for development)

```shell
nix run github:lovesegfault/beautysh -- --help
```

Or add to your `flake.nix`:

```nix
{
  inputs.beautysh.url = "github:lovesegfault/beautysh";
  # ...
}
```

### From source with uv

```shell
git clone https://github.com/lovesegfault/beautysh
cd beautysh
uv sync
```

## Usage

You can call Beautysh from the command line such as

```shell
beautysh file1.sh file2.sh file3.sh
```

in which case it will beautify each one of the files.

### Configuration

Beautysh supports multiple configuration sources with the following priority (highest to lowest):

1. **Command-line arguments** (highest priority)
1. **Explicit config file** (specified via `--config`)
1. **.beautyshrc** (in current working directory)
1. **pyproject.toml** - `[tool.beautysh]` section
1. **EditorConfig** - `.editorconfig` files (lowest priority)

#### .beautyshrc

The `.beautyshrc` file, located in the current working directory, is a configuration file read in TOML format. It can contain configuration options at the root level, or under the `[tool.beautysh]` or `[beautysh]` sections.

Example `.beautyshrc` content:

```toml
[beautysh]
indent_size = 2
tab = true
backup = true
check = true
force_function_style = "paronly"  # Options: fnpar, fnonly, paronly
variable_style = "braces"  # Options: braces
```

#### pyproject.toml

```toml
[tool.beautysh]
indent_size = 4
tab = false
backup = false
check = false
force_function_style = "fnpar"  # Options: fnpar, fnonly, paronly
variable_style = "braces"  # Options: braces
```

#### EditorConfig

Beautysh respects [EditorConfig](https://editorconfig.org/) settings:

```ini
[*.sh]
indent_style = space  # or "tab"
indent_size = 4
```

Supported EditorConfig properties:

- `indent_style`: Maps to `--tab` flag (space/tab)
- `indent_size`: Maps to `--indent-size` option

### Command-Line Options

Available flags are:

```
  --config CONFIG       Path to a specific configuration file (e.g., .beautyshrc).
                        Overrides auto-discovered config files.
  --indent-size INDENT_SIZE, -i INDENT_SIZE
                        Sets the number of spaces to be used in indentation.
  --backup, -b          Beautysh will create a backup file in the same path as
                        the original.
  --check, -c           Beautysh will just check the files without doing any
                        in-place beautify.
  --tab, -t             Sets indentation to tabs instead of spaces.
  --force-function-style FORCE_FUNCTION_STYLE, -s FORCE_FUNCTION_STYLE
                        Force a specific Bash function formatting. See below
                        for more info.
  --variable-style VARIABLE_STYLE
                        Force a specific variable style. See below for options.
  --version, -v         Prints the version and exits.
  --help, -h            Print this help message.

Bash function styles that can be specified via --force-function-style are:
  fnpar: function keyword, open/closed parentheses, e.g.      function foo()
  fnonly: function keyword, no open/closed parentheses, e.g.  function foo
  paronly: no function keyword, open/closed parentheses, e.g. foo()

Variable styles that can be specified via --variable-style are:
  braces: transform $VAR to ${VAR} for consistency (e.g., $HOME becomes ${HOME})
          Note: Special variables ($?, $1, etc.) and parameter expansions
          (${VAR:-default}) are left unchanged.
```

You can also call beautysh as a module:

```python3
from beautysh import BashFormatter

source = "my_string"

formatter = BashFormatter(indent_size=4)
result, error = formatter.beautify_string(source)
```

For more control, you can use individual components:

```python3
from beautysh import BashParser, StyleTransformer, BashFormatter

# Parse and analyze Bash syntax
parser = BashParser()
test_record = parser.get_test_record('if [ "$x" = "y" ]; then')

# Transform styles
transformer = StyleTransformer()
transformed = transformer.apply_variable_style('echo $HOME', 'braces')  # -> 'echo ${HOME}'

# Format complete scripts
formatter = BashFormatter(indent_size=2, variable_style='braces')
formatted, error = formatter.beautify_string(script)
```

As written, beautysh can beautify large numbers of Bash scripts when called
from a variety of means,including a Bash script:

```shell
#!/bin/sh

for path in `find /path -name '*.sh'`
do
   beautysh $path
done
```

As well as the more obvious example:

```shell
$ beautysh *.sh
```

> **CAUTION**: Because Beautysh overwrites all the files submitted to it, this
> could have disastrous consequences if the files include some of the
> increasingly common Bash scripts that have appended binary content (a regime
> where Beautysh has undefined behaviour ). So please — back up your files,
> and don't treat Beautysh as a harmless utility. Even if that is true
> most of the time.

Beautysh handles Bash here-docs with care(and there are probably some
border cases it doesn't handle). The basic idea is that the originator knew what
format he wanted in the here-doc, and a beautifier shouldn't try to outguess
him. So Beautysh does all it can to pass along the here-doc content
unchanged:

```shell
if true
then

   echo "Before here-doc"

   # Insert 2 lines in file, then save.
   #--------Begin here document-----------#
vi $TARGETFILE <<x23LimitStringx23
i
This is line 1 of the example file.
This is line 2 of the example file.
^[
ZZ
x23LimitStringx23
   #----------End here document-----------#

   echo "After here-doc"

fi
```

Special comments `@formatter:off` and `@formatter:on` are available to disable formatting around a block of statements.

```shell
# @formatter:off
command \
    --option1 \
        --option2 \
            --option3 \
# @formatter:on

```

This takes inspiration from the Eclipse feature.

## Development

### Using Nix (recommended)

The easiest way to start developing is with Nix:

```shell
# Enter development shell with all dependencies
nix develop

# Run tests
pytest tests/

# Run type checker
mypy beautysh/

# Run linter and formatter
ruff check beautysh/ tests/
ruff format beautysh/ tests/

# Format all code (Nix, YAML, Markdown, Python)
nix fmt

# Run all pre-commit checks
pre-commit run --all-files
```

The development shell provides:

- Python 3.12 with all dependencies
- Editable install (changes to code are immediately reflected)
- All development tools (pytest, mypy, ruff, hypothesis)
- Pre-commit hooks automatically installed

### Architecture

Beautysh has a modular architecture for maintainability:

- **`beautysh/parser.py`** - Bash syntax parsing and analysis
- **`beautysh/formatter.py`** - Core formatting logic with indentation calculation
- **`beautysh/transformers.py`** - Style transformations (function/variable styles)
- **`beautysh/config.py`** - Configuration loading (pyproject.toml, EditorConfig, .beautyshrc)
- **`beautysh/cli.py`** - Command-line interface
- **`beautysh/diff.py`** - Diff output for check mode
- **`beautysh/types.py`** - Type definitions and dataclasses
- **`beautysh/constants.py`** - Pre-compiled regex patterns and constants

### Performance Tools

The `tools/` directory contains performance analysis scripts:

```shell
# Benchmark formatter performance
python tools/benchmark.py

# Profile with cProfile to identify hotspots
python tools/profile_formatter.py
```

See [tools/README.md](tools/README.md) for details.

### Using uv

```shell
# Install dependencies
uv sync

# Activate virtual environment and run tests
uv run pytest tests/
```

## Contributing

Contributions are welcome and appreciated, however test cases must be added to
prevent regression. Adding a test case is easy, and involves the following:

1. Create a file `tests/fixtures/my_test_name_raw.sh` containing the unformatted version
   of your test case.
1. Create a file `tests/fixtures/my_test_name_formatted.sh` containing the formatted version
   of your test case.
1. Register your test case in `tests/test_integration.py`. It should look
   something like this:

```python
def test_my_test_name(fixture_dir):
    assert_formatting(fixture_dir, "my_test_name")
```

Before submitting a PR, please ensure:

- All tests pass: `pytest tests/`
- Code is formatted and linted: `ruff check --fix . && ruff format .`
- Type checking passes: `mypy beautysh/`

Or simply run all checks at once:

```shell
pre-commit run --all-files
```

This will run:

- pytest (all 172 tests including property-based tests)
- mypy (type checking)
- ruff (linting and formatting)
- treefmt (Nix, YAML, Markdown formatting)

______________________________________________________________________

Originally written by [Paul Lutus](http://arachnoid.com/python/beautify_bash_program.html)
