# Beautysh

<sup>A bash beautifier for the masses</sup>

________________________________________________________________________________

Beautysh takes upon itself the hard task of beautifying Bash scripts (yeesh).
Beautifying Bash scripts is not trivial. Bash scripts aren't like C or Java
programs — they have a lot of ambiguous syntax, and (shudder) keywords can be
used as variables. Years ago, while testing the first version of this program,
I encountered this example:
```shell
done=3;echo done;done
```
Same name, but three distinct meanings (sigh). The Bash interpreter can sort out
 this perversity, but I decided not to try to recreate the Bash interpreter just
 to beautify a script. This means there will be some border cases this Python
program won't be able to process. But in tests with many large Linux system
Bash scripts, its error-free score was roughly 99%.

## Installation

Simply run
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

Beautysh has three modes of operation:

1.  If presented with a list of file names —
    ```shell
    beautysh.py file1.sh file2.sh file3.sh
    ```
    — for each file name, it will create a backup (i.e. file1.sh~) and overwrite
     the original file with a beautified replacement.

2.  If given '-' as a command-line argument, it will use stdin as its source and
stdout as its sink:
    ```shell
    beautysh.py - < infile.sh > outfile.sh
    ```

3.  If called as a module, it will behave itself and not execute its main()
function:
    ```shell
    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    from beautysh import Beautysh

    [ ... ]

    result,error = Beautysh().beautify_string(source)
    ```

As written, Beautysh can beautify large numbers of Bash scripts when called
from ... well, among other things, a Bash script:
```shell
#!/bin/sh

for path in `find /path -name '*.sh'`
do
   beautysh.py $path
done
```
As well as the more obvious example:
```shell
    $ beautysh.py *.sh
```

> **CAUTION**: Because Beautysh overwrites all the files submitted to it, this
> could have disastrous consequences if the files include some of the
> increasingly common Bash scripts that have appended binary content (a regime
> where Beautysh's behavior is undefined). So please — back up your files,
> and don't treat Beautysh as though it is a harmless utility. That's only true
> most of the time.

Beautysh handles Bash here-docs very carefully (and there are probably some
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
________________________________________________________________________________

Originally written by [Paul Lutus](http://arachnoid.com/python/beautify_bash_program.html)
