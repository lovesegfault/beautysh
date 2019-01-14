# Beautysh [![Build Status](https://travis-ci.org/bemeurer/beautysh.svg?branch=master)](https://travis-ci.org/bemeurer/beautysh)

This program takes upon itself the hard task of beautifying Bash scripts
(yeesh). Processing Bash scripts is not trivial, they aren't like C or Java
programs — they have a lot of ambiguous syntax, and (shudder) you can use
keywords as variables. Years ago, while testing the first version of this
program, I encountered this example:

```shell
done=3;echo done;done
```
Same name, but three distinct meanings (sigh). The Bash interpreter can sort out
this perversity, but I decided not to try to recreate the Bash interpreter to
beautify a script. This means there will be some border cases this Python
program won't be able to process. But in tests with large Linux system
Bash scripts, its error-free score was ~99%.

## Installation

If you have `pip` set up you can do

```shell
pip install beautysh
```

or clone the repo and install:

```shell
git clone https://github.com/bemeurer/beautysh
cd beautysh
python setup.py install
```

## Usage

You can call Beautysh from the command line such as

```shell
beautysh.py -f file1.sh file2.sh file3.sh
```

in which case it will beautify each one of the files.

Available flags are:

| Flag            | Short | Meaning                                    | Usage              |
| --------------- | ----- | ------------------------------------------ |------------------- |
| `--files`       | `-f`  | Files to beautify                          | `-f foo.sh bar.sh` |
| `--indent-size` | `-i`  | Number of spaces to use as indentation     | `-i 4`             |
| `--backup`      | `-b`  | Create a backup file before beautifying    | `-b`               |
| `--tab`         | `-t`  | Use tabs instead of spaces                 | `-t`               |

You can use `-` as an argument to `-f` and beautysh will use stdin as it's
source and stdout as it's sink

```shell
beautysh.py - < infile.sh > outfile.sh
```

You can also call beautysh as a module:

```shell
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from beautysh import Beautysh

[ ... ]

result,error = Beautysh().beautify_string(source)
```

As written, beautysh can beautify large numbers of Bash scripts when called
from a variety of means,including a Bash script:

```shell
#!/bin/sh

for path in `find /path -name '*.sh'`
do
   beautysh.py -f $path
done
```

As well as the more obvious example:

```shell
$ beautysh.py -f *.sh
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

________________________________________________________________________________

Originally written by [Paul Lutus](http://arachnoid.com/python/beautify_bash_program.html)
