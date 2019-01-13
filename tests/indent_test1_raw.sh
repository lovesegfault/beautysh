#!/bin/bash

# this small snippet is to test against regressions for issue#29
#    https://github.com/bemeurer/beautysh/issues/29

function string_with_brackets_inside1()
{
    local re='^[\-]?[[0-9]+$'

    # following line contains wrong double TAB:
		echo "hello world"
}

function string_with_brackets_inside2()
{
    RESTORE="$(echo -en '\033[0m')"

    # following line contains wrong TAB:
	echo "hello world"
}

function quote_escapes1()
{
	T=$(echo "\"a\"")
	echo "command to indent"
}

function complex_mix1()
{
	while true; do
		for i in $(seq 1 100); do
			local str_with_brackets="[]]]]"
			local str_with_escapes="\"\"\"\""
			
			# try a command in a $() expansion
			if [ -z "$(echo)" ]; then
				quote_escapes1
				string_with_brackets_inside1
				string_with_brackets_inside2
			fi
		done
	done
}
